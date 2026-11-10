// The line under an answer, for each place an answer can come from.
import assert from "node:assert/strict";
import { test } from "node:test";

import type { Answer } from "./api.ts";
import { NO_NEW_CALL, costLine, pageQuestion } from "./display.ts";

const ANSWER: Answer = {
  text: "Peso swings [1].",
  citations: [],
  model_used: "openrouter:openai/gpt-oss-20b",
  retriever_name: "hybrid",
  usage: { prompt_tokens: 1800, completion_tokens: 150 },
  latency_ms: 1234,
  cost_usd: 0.000198,
  finish_reason: "stop",
  abstained: false,
  has_uncited_claims: false,
  degraded: false,
};

test("a new answer shows its model, time, tokens and cost", () => {
  assert.equal(
    costLine(ANSWER, "new"),
    "openrouter:openai/gpt-oss-20b · 1.2 s · 1800 + 150 tokens · $0.00020",
  );
});

test("a saved answer served after the daily limit says no new model call was made", () => {
  assert.equal(NO_NEW_CALL, "Saved example answer · no new model call");
  // Not the original answer's time and cost, which this request did not spend.
  assert.equal(costLine(ANSWER, "after-limit"), NO_NEW_CALL);
  assert.equal(costLine({ ...ANSWER, degraded: true }, "after-limit"), NO_NEW_CALL);
});

test("a clicked example shows what its original answer took and cost", () => {
  assert.equal(
    costLine(ANSWER, "example"),
    "Saved example answer. openrouter:openai/gpt-oss-20b · 1.2 s · 1800 + 150 tokens · $0.00020",
  );
});

test("an unknown cost, missing token counts and keyword-only search are said plainly", () => {
  const answer: Answer = {
    ...ANSWER,
    cost_usd: null,
    usage: { prompt_tokens: null, completion_tokens: null },
    degraded: true,
  };
  assert.equal(
    costLine(answer, "new"),
    "openrouter:openai/gpt-oss-20b · 1.2 s · ? + ? tokens · cost unknown" +
      " · keyword search only (the embedding service was unavailable)",
  );
});

test("the page asks the agent, with the checks left on by default", () => {
  assert.deepEqual(pageQuestion("What was Coca-Cola's net income in fiscal 2024?", "", ""), {
    question: "What was Coca-Cola's net income in fiscal 2024?",
    mode: "agent",
  });
  assert.deepEqual(pageQuestion("Risks?", "WMT", "2025"), {
    question: "Risks?",
    mode: "agent",
    ticker: "WMT",
    fiscal_year: 2025,
  });
  // A year only counts with a company, as the page's year list depends on the company.
  assert.deepEqual(pageQuestion("Risks?", "", "2025"), { question: "Risks?", mode: "agent" });
});
