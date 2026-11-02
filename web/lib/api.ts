// Calls to the FilingCheck API. The base URL comes from NEXT_PUBLIC_API_URL.

import type { Citation } from "./citations.ts";
import { createSseParser } from "./sse.ts";

export const API_URL = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(
  /\/$/,
  "",
);

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
};

export type Company = { ticker: string; name: string; fiscal_years: number[] };

export type Question = { question: string; ticker?: string; fiscal_year?: number };

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
    else if (response.status === 422) detail = "The question could not be read; please edit it.";
  } catch {
    // keep the generic message
  }
  return new ApiError(response.status, detail);
}

export type Health = "ok" | "no-model" | "unreachable";

/** Whether the API answers /health within `timeoutMs`. */
export async function checkHealth(timeoutMs: number): Promise<Health> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(`${API_URL}/health`, { signal: controller.signal });
    return response.ok ? "ok" : "no-model";
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
export async function ask(question: Question): Promise<Answer> {
  const response = await fetch(`${API_URL}/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(question),
  });
  if (!response.ok) throw await apiError(response);
  return (await response.json()) as Answer;
}

/**
 * The answer from POST /ask/stream, calling `onText` with the text so far as it arrives.
 * Falls back to POST /ask when the browser cannot read the stream or the connection
 * fails before any text has arrived. An `error` event means the text so far must be
 * discarded; it is raised as an ApiError with the API's message.
 */
export async function askStreaming(
  question: Question,
  onText: (textSoFar: string) => void,
): Promise<Answer> {
  let received = "";
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
          answer?: Answer;
          detail?: string;
        };
        if (event.event === "token" && data.text) {
          received += data.text;
          onText(received);
        } else if (event.event === "final" && data.answer) {
          return data.answer;
        } else if (event.event === "error") {
          throw new ApiError(503, data.detail ?? "The answer could not be finished.");
        }
      }
    }
  } catch (error) {
    if (error instanceof ApiError) throw error;
    if (!received) return ask(question);
    throw new ApiError(0, "The connection dropped before the answer finished; please try again.");
  }
  throw new ApiError(0, "The answer stopped before it finished; please try again.");
}
