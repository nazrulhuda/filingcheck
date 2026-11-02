// Text the page shows about an answer, kept here so it can be tested without rendering.

import type { AskResult } from "./api.ts";

export const LIMIT_NOTICE =
  "Today's limit has been reached; this is the saved answer to a similar example question:";

/** The notice for a saved example's answer served after the daily limit, else null. */
export function cachedNotice(result: AskResult): string | null {
  if (!result.cached) return null;
  return result.example ? `${LIMIT_NOTICE} ${result.example.question}` : LIMIT_NOTICE;
}
