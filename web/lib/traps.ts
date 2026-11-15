// "Try a trap question": saved answers to development trap questions (web/data/trap_examples.json,
// from `make trap-examples`), plus saved examples the page already held, in the plan's order.

import type { Answer } from "./api.ts";

export type Example = {
  question: string;
  ticker: string | null;
  fiscal_year: number | null;
  company_name: string | null;
  answer: Answer;
};

export type TrapExample = Example & { id: string; trap: string };

// The plan's kinds of trap, in its order; "fact-002" is the Nike example the page already held
// (eval/questions/page_examples.jsonl), shown as it was saved.
export const TRAP_ORDER = ["dev-001", "dev-067", "dev-050", "fact-002", "dev-014", "dev-076"];
const SAVED: Record<string, { question: string; trap: string }> = {
  "fact-002": { question: "How much revenue did Nike make last year?", trap: "A relative year" },
};

export const TRAP_NOTE =
  "Saved examples, chosen to show a check at work. How often the checks work is in the results.";

/** The picked trap answers and the saved examples shown as traps, in the plan's order. */
export function trapExamples(picked: TrapExample[], examples: Example[]): TrapExample[] {
  const saved = Object.entries(SAVED).map(([id, { question, trap }]) => {
    const example = examples.find((e) => e.question === question);
    if (!example) throw new Error(`no saved example for ${id}`);
    return { ...example, id, trap };
  });
  const rank = (id: string) => {
    const i = TRAP_ORDER.indexOf(id);
    return i === -1 ? TRAP_ORDER.length : i;
  };
  return [...picked, ...saved].sort((a, b) => rank(a.id) - rank(b.id));
}

/** The saved examples not shown as traps, so none is shown twice. */
export function plainExamples(examples: Example[], traps: TrapExample[]): Example[] {
  const shown = new Set(traps.map((t) => t.question));
  return examples.filter((e) => !shown.has(e.question));
}
