// Calls to the FilingCheck API. The base URL comes from NEXT_PUBLIC_API_URL.

import type { Override } from "./checks.ts";
import type { Citation, FactCitation, FactUsed } from "./citations.ts";
import type { NumberLabel } from "./labels.ts";
import { createSseParser } from "./sse.ts";

export const API_URL = (
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"
).replace(/\/$/, "");

export type Answer = {
  text: string;
  citations: Citation[];
  model_used: string;
  retriever_name: string;
  usage: { prompt_tokens: number | null; completion_tokens: number | null };
  latency_ms: number;
  cost_usd: number | null;
  finish_reason: string;
  abstained: boolean;
  has_uncited_claims: boolean;
  degraded: boolean;
  // Each figure's label against the sources the answer used; absent in answers saved before.
  number_labels?: NumberLabel[];
  // The agent's answers only: what it looked up and what its checks did.
  mode?: "agent";
  checks?: boolean;
  tool_calls?: { name: string; status: string }[];
  fact_citations?: FactCitation[];
  facts_used?: FactUsed[];
  overrides?: Override[];
};

export type Company = { ticker: string; name: string; fiscal_years: number[] };

/** The example question a cached answer belongs to (not the visitor's question). */
export type ExampleRef = {
  question: string;
  ticker: string | null;
  fiscal_year: number | null;
};

/** An answer, and whether it is a saved example's answer served after the daily limit. */
export type AskResult = {
  answer: Answer;
  cached: boolean;
  example: ExampleRef | null;
};

export type Question = {
  question: string;
  mode?: "baseline" | "agent";
  ticker?: string;
  fiscal_year?: number;
};

/** One tool call the agent made, as the page shows it while the answer is on its way. */
export type Step = { label: string; status: string };

/** The agent's tool calls so far; after a restart, only the new model's, and why. */
export type Progress = { steps: Step[]; restarted: string | null };

/** An HTTP error with the message the API sent, safe to show. */
export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function apiError(response: Response): Promise<ApiError> {
  let detail = `The API answered with HTTP ${response.status}.`;
  try {
    const body = (await response.json()) as { detail?: unknown };
    if (typeof body.detail === "string") detail = body.detail;
    else if (response.status === 422)
      detail = "The question could not be read; please edit it.";
  } catch {
    // keep the generic message
  }
  return new ApiError(response.status, detail);
}

export type Health = "ok" | "no-model" | "unreachable";

/**
 * The API's state from /health within `timeoutMs`: "ok" only on 200, "no-model" only on
 * the API's own 503 saying no model key is set. Anything else (no answer, or a
 * platform's 502 or 503 page while the app restarts) counts as not reachable yet.
 */
export async function checkHealth(timeoutMs: number): Promise<Health> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(`${API_URL}/health`, {
      signal: controller.signal,
    });
    if (response.status === 200) return "ok";
    if (response.status === 503) {
      const body = (await response.json().catch(() => null)) as {
        status?: unknown;
      } | null;
      if (body?.status === "no model key") return "no-model";
    }
    return "unreachable";
  } catch {
    return "unreachable";
  } finally {
    clearTimeout(timer);
  }
}

export async function getCompanies(): Promise<Company[]> {
  const response = await fetch(`${API_URL}/companies`);
  if (!response.ok) throw await apiError(response);
  return (await response.json()) as Company[];
}

/** One answer from POST /ask, without streaming. */
export async function ask(question: Question): Promise<AskResult> {
  const response = await fetch(`${API_URL}/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(question),
  });
  if (!response.ok) throw await apiError(response);
  const body = (await response.json()) as Answer & {
    request_id?: string;
    cached?: boolean;
    example?: ExampleRef | null;
  };
  const { cached, example, ...answer } = body;
  return { answer, cached: cached === true, example: example ?? null };
}

/**
 * The answer from POST /ask/stream, calling `onText` with the text so far as it arrives
 * and `onProgress` with the agent's tool calls so far. A `restart` event means another
 * model started the question again, so the tool calls shown so far are dropped.
 * Falls back to POST /ask when the browser cannot read the stream or the connection
 * fails before any text has arrived. An `error` event means the text so far must be
 * discarded; it is raised as an ApiError with the API's message.
 */
export async function askStreaming(
  question: Question,
  onText: (textSoFar: string) => void,
  onProgress: (progress: Progress) => void = () => {},
): Promise<AskResult> {
  let received = "";
  let progress: Progress = { steps: [], restarted: null };
  let response: Response;
  try {
    response = await fetch(`${API_URL}/ask/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(question),
    });
  } catch {
    return ask(question);
  }
  if (!response.ok) throw await apiError(response);
  if (!response.body) return ask(question);
  const reader = response.body.pipeThrough(new TextDecoderStream()).getReader();
  const parser = createSseParser();
  try {
    for (;;) {
      const { value, done } = await reader.read();
      if (done) break;
      for (const event of parser.push(value)) {
        const data = JSON.parse(event.data) as {
          text?: string;
          label?: string;
          status?: string;
          answer?: Answer;
          cached?: boolean;
          example?: ExampleRef | null;
          detail?: string;
        };
        if (event.event === "tool" && data.label) {
          progress = {
            ...progress,
            steps: [
              ...progress.steps,
              { label: data.label, status: data.status ?? "" },
            ],
          };
          onProgress(progress);
        } else if (event.event === "restart") {
          progress = {
            steps: [],
            restarted: data.detail ?? "Starting again with another model.",
          };
          onProgress(progress);
        } else if (event.event === "token" && data.text) {
          received += data.text;
          onText(received);
        } else if (event.event === "final" && data.answer) {
          return {
            answer: data.answer,
            cached: data.cached === true,
            example: data.example ?? null,
          };
        } else if (event.event === "error") {
          throw new ApiError(
            503,
            data.detail ?? "The answer could not be finished.",
          );
        }
      }
    }
  } catch (error) {
    if (error instanceof ApiError) throw error;
    if (!received) return ask(question);
    throw new ApiError(
      0,
      "The connection dropped before the answer finished; please try again.",
    );
  }
  throw new ApiError(
    0,
    "The answer stopped before it finished; please try again.",
  );
}
