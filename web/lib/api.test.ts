// The API calls with `fetch` stubbed: the paths the browser check did not reach.
import assert from "node:assert/strict";
import { afterEach, test } from "node:test";

import { ApiError, ask, askStreaming, checkHealth } from "./api.ts";
import { LIMIT_NOTICE, cachedNotice } from "./display.ts";

const realFetch = globalThis.fetch;
afterEach(() => {
  globalThis.fetch = realFetch;
});

type Call = { url: string; init?: RequestInit };

/** Replace fetch with `handler`, recording every call. */
function stub(handler: (call: Call) => Response | Promise<Response>): Call[] {
  const calls: Call[] = [];
  globalThis.fetch = (async (input: string | URL | Request, init?: RequestInit) => {
    const call = { url: String(input), init };
    calls.push(call);
    return handler(call);
  }) as typeof fetch;
  return calls;
}

const ANSWER = {
  text: "Peso swings [1].",
  citations: [
    {
      number: 1,
      chunk_id: 101,
      ticker: "C",
      fiscal_year: 2025,
      item: "7",
      source_url: "https://www.sec.gov/c.htm",
      quote: "Argentina",
    },
  ],
  model_used: "groq:openai/gpt-oss-20b",
  retriever_name: "hybrid",
  usage: { prompt_tokens: 1800, completion_tokens: 150 },
  latency_ms: 1200,
  cost_usd: 0.0002,
  finish_reason: "stop",
  abstained: false,
  has_uncited_claims: false,
  degraded: false,
};

function json(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function sse(...events: [string, unknown][]): Response {
  const body = events.map(([name, data]) => `event: ${name}\ndata: ${JSON.stringify(data)}\n\n`);
  return new Response(body.join(""), { headers: { "Content-Type": "text/event-stream" } });
}

// ---------------------------------------------------------------- /health

test("health is ok only on 200", async () => {
  stub(() => json({ status: "ok", model: "groq:openai/gpt-oss-20b" }));
  assert.equal(await checkHealth(1000), "ok");
});

test("the API's own 503 'no model key' means no model is configured", async () => {
  stub(() => json({ status: "no model key", model: "groq:openai/gpt-oss-20b" }, 503));
  assert.equal(await checkHealth(1000), "no-model");
});

test("any other answer, such as the platform's 502 while the app restarts, is unreachable", async () => {
  for (const response of [
    () => new Response("<html>Bad Gateway</html>", { status: 502 }),
    () => new Response("<html>Service Unavailable</html>", { status: 503 }),
    () => json({ status: "something else" }, 503),
    () => json({ detail: "Not Found" }, 404),
  ]) {
    stub(response);
    assert.equal(await checkHealth(1000), "unreachable");
  }
});

test("no answer within the time limit, or a network error, is unreachable", async () => {
  globalThis.fetch = ((_input: string | URL | Request, init?: RequestInit) =>
    new Promise((_resolve, reject) => {
      init?.signal?.addEventListener("abort", () => reject(new DOMException("aborted", "AbortError")));
    })) as typeof fetch;
  assert.equal(await checkHealth(50), "unreachable");
  stub(() => {
    throw new TypeError("fetch failed");
  });
  assert.equal(await checkHealth(1000), "unreachable");
});

// ---------------------------------------------------------------- asking

test("a 429 raises with the API's own message", async () => {
  const detail = "Too many questions from your address; the limit is 20 an hour.";
  stub(() => json({ detail }, 429));
  await assert.rejects(askStreaming({ question: "Q?" }, () => {}), (error: unknown) => {
    assert.ok(error instanceof ApiError);
    assert.equal(error.status, 429);
    assert.equal(error.message, detail);
    return true;
  });
});

test("a stream whose fetch fails falls back to /ask", async () => {
  const calls = stub(({ url }) => {
    if (url.endsWith("/ask/stream")) throw new TypeError("fetch failed");
    return json({ request_id: "r1", cached: false, example: null, ...ANSWER });
  });
  const result = await askStreaming({ question: "Q?", ticker: "C" }, () => {});
  assert.deepEqual(
    calls.map((c) => c.url.replace(/^.*(\/ask(\/stream)?)$/, "$1")),
    ["/ask/stream", "/ask"],
  );
  assert.equal(calls[1].init?.body, JSON.stringify({ question: "Q?", ticker: "C" }));
  assert.equal(result.answer.text, "Peso swings [1].");
  assert.equal(result.cached, false);
});

test("an error event raises with the API's message and the text so far is not an answer", async () => {
  const detail = "The answer was cut off before it finished; please try again.";
  const seen: string[] = [];
  stub(() => sse(["token", { text: "Peso " }], ["error", { request_id: "r1", detail }]));
  await assert.rejects(askStreaming({ question: "Q?" }, (t) => seen.push(t)), (error: unknown) => {
    assert.ok(error instanceof ApiError);
    assert.equal(error.message, detail);
    return true;
  });
  assert.deepEqual(seen, ["Peso "]);
});

test("a streamed answer arrives piece by piece, then whole", async () => {
  const seen: string[] = [];
  stub(() =>
    sse(
      ["token", { text: "Peso " }],
      ["token", { text: "swings [1]." }],
      ["final", { request_id: "r1", cached: false, example: null, answer: ANSWER }],
    ),
  );
  const result = await askStreaming({ question: "Q?" }, (t) => seen.push(t));
  assert.deepEqual(seen, ["Peso ", "Peso swings [1]."]);
  assert.deepEqual(result, { answer: ANSWER, cached: false, example: null });
});

// ---------------------------------------------------------------- cached answers

const EXAMPLE = {
  question: "How much money does Citi have tied up in Argentina, and how does it handle the peso?",
  ticker: "C",
  fiscal_year: 2025,
};

test("a cached answer from /ask keeps the example it answers", async () => {
  stub(() => json({ request_id: "r1", cached: true, example: EXAMPLE, ...ANSWER }));
  const result = await ask({ question: "Citi in Argentina?" });
  assert.equal(result.cached, true);
  assert.deepEqual(result.example, EXAMPLE);
  assert.equal(result.answer.text, ANSWER.text);
  assert.equal("example" in result.answer, false);
});

test("a cached streamed answer keeps the example it answers", async () => {
  stub(() =>
    sse(
      ["token", { text: ANSWER.text }],
      ["final", { request_id: "r1", cached: true, example: EXAMPLE, answer: ANSWER }],
    ),
  );
  const result = await askStreaming({ question: "Citi in Argentina?" }, () => {});
  assert.equal(result.cached, true);
  assert.deepEqual(result.example, EXAMPLE);
});

test("a cached answer shows the limit notice with the example's question", () => {
  assert.equal(
    LIMIT_NOTICE,
    "Today's limit has been reached; this is the saved answer to a similar example question:",
  );
  assert.equal(
    cachedNotice({ answer: ANSWER, cached: true, example: EXAMPLE }),
    `${LIMIT_NOTICE} ${EXAMPLE.question}`,
  );
  assert.equal(cachedNotice({ answer: ANSWER, cached: false, example: null }), null);
});
