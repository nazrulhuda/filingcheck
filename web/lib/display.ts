// Text the page shows about an answer, kept here so it can be tested without rendering.

import type { Answer, AskResult, Question } from "./api.ts";

/** Where a shown answer came from: a new model call, a clicked example, or a saved example's
 * answer served after the daily limit. */
export type AnswerSource = "new" | "example" | "after-limit";

export const NO_NEW_CALL = "Saved example answer · no new model call";

export const LIMIT_NOTICE =
  "Today's limit has been reached; this is the saved answer to a similar example question:";

/** The notice for a saved example's answer served after the daily limit, else null. */
export function cachedNotice(result: AskResult): string | null {
  if (!result.cached) return null;
  return result.example ? `${LIMIT_NOTICE} ${result.example.question}` : LIMIT_NOTICE;
}

function seconds(ms: number): string {
  return `${(ms / 1000).toFixed(1)} s`;
}

/** Who answered, how long it took and what it cost. A saved answer served after the daily
 * limit cost nothing this time, so it shows no time or cost. */
export function costLine(answer: Answer, source: AnswerSource): string {
  if (source === "after-limit") return NO_NEW_CALL;
  const cost = answer.cost_usd === null ? "cost unknown" : `$${answer.cost_usd.toFixed(5)}`;
  const tokens = `${answer.usage.prompt_tokens ?? "?"} + ${answer.usage.completion_tokens ?? "?"} tokens`;
  const saved = source === "example" ? "Saved example answer. " : "";
  const degraded = answer.degraded
    ? " · keyword search only (the embedding service was unavailable)"
    : "";
  return `${saved}${answer.model_used} · ${seconds(answer.latency_ms)} · ${tokens} · ${cost}${degraded}`;
}

/** What the page sends: the agent, whose checks are on unless a request turns them off. A
 * fiscal year counts only with a company, as the page lists the years of the chosen company. */
export function pageQuestion(text: string, ticker: string, year: string): Question {
  return {
    question: text,
    mode: "agent",
    ...(ticker ? { ticker } : {}),
    ...(ticker && year ? { fiscal_year: Number(year) } : {}),
  };
}

/** The filters a saved example was asked with: its company (the ticker if the name is
 * missing) and fiscal year, or "any" for a filter left open. */
export function askedWith(
  companyName: string | null,
  ticker: string | null,
  fiscalYear: number | null,
): string {
  const company = companyName ?? ticker ?? "any company";
  const year = fiscalYear ? `fiscal ${fiscalYear}` : "any year";
  return `Asked with: ${company} · ${year}`;
}
