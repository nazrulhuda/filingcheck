// Notes from the review, shown under a saved example. The saved answers are never edited, so
// a fault the review found in one is pointed out here instead, keyed by the example's question.

export const REVIEW_NOTES: Record<string, string> = {
  "How much would Walmart's currency swaps change in value if the dollar weakened by ten percent?":
    "Review note: the $0.7 billion is from the filing; the words '10-year-old' are not. " +
    "FilingCheck checks numbers, not wording, yet.",
};

/** The review note for a saved example's question, or null if it has none. */
export function reviewNote(question: string): string | null {
  return REVIEW_NOTES[question] ?? null;
}
