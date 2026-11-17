// The page's first screen and its tiles. The result tiles read their numbers from
// web/data/results.json (written by `make report`); the control tile and the six "What's inside"
// tiles are matched with their source files by glance.test.ts. No number here is new.

import type { Results } from "./results.ts";
import { TRAP_NOTE } from "./traps.ts";

export const SENTENCE =
  "Ask about 25 companies' annual reports. Before the AI looks anything up, the server checks " +
  "its request, and every number in the answer is labeled against the SEC data it cites.";

/** The privacy note under the options row; its first sentence ("Each question stands alone (no
 * chat history).") is said in "What you can ask" instead. */
export const PRIVACY_NOTE =
  "Questions are logged to improve the demo. Each question is sent to OpenAI to search the " +
  "filings, and through OpenRouter to Groq, or to Google if that is busy, to write the answer; " +
  "please don't enter personal information.";

export type Chip = { label: string; question: string };

/** The "Try:" row: a short label for each saved question; a chip shows its saved answer. */
export const CHIPS: Chip[] = [
  { label: "Costco: operating income", question: "What was Costco's operating income in fiscal 2025?" },
  {
    label: "Citi: money in Argentina",
    question: "How much money does Citi have tied up in Argentina, and how does it handle the peso?",
  },
  {
    label: "Netflix: IP claims",
    question: "What does Netflix say about others claiming it infringed their intellectual property?",
  },
  { label: "Trap: Nike, 'last year'", question: "How much revenue did Nike make last year?" },
  { label: "Trap: 'morgan'", question: "how much net revenue did morgan make in 2024" },
];

/** The other saved examples, shown when "More" is opened. */
export const MORE_CHIPS: Chip[] = [
  {
    label: "UnitedHealth: fixed-rate debt",
    question: "How much of UnitedHealth's debt carries a fixed rate that isn't swapped?",
  },
  {
    label: "Walmart: currency swaps",
    question:
      "How much would Walmart's currency swaps change in value if the dollar weakened by ten percent?",
  },
  {
    label: "American Express: controls",
    question: "What framework did American Express management use to judge its internal controls?",
  },
];

/** Whether the answer card's top is on the screen with at least `margin` px of it showing. */
export function answerInView(top: number, viewport: number, margin = 96): boolean {
  return top >= 0 && top <= viewport - margin;
}

/** How to scroll to the answer: no animation for visitors who ask for reduced motion. */
export function scrollBehavior(reducedMotion: boolean): ScrollBehavior {
  return reducedMotion ? "auto" : "smooth";
}

/** The saved example shown on first load (a trap example, so its card says it was chosen). */
export const FIRST_EXAMPLE = "How much revenue did Nike make last year?";

/** What the answer card is, said once in its strip: the model at work, a live answer, or a saved
 * example (a trap example says it was chosen, and where to find how often the checks work). */
export function cardLine(
  state: "working" | "new" | "example" | "after-limit",
  trap: boolean,
): string {
  if (state === "working") return "Answering…";
  if (state === "new") return "Answer";
  return trap ? TRAP_NOTE : "Saved example";
}

/** Enter asks the question; Shift+Enter starts a new line, and nothing happens mid-composition. */
export function enterAsks(key: string, shift: boolean, composing: boolean): boolean {
  return key === "Enter" && !shift && !composing;
}

/** The header's jump links: three sections lower on the page, then the code. */
export const JUMP_LINKS = [
  { label: "How it works", href: "#how-it-works" },
  { label: "Results", href: "#results" },
  { label: "What's inside", href: "#whats-inside" },
  { label: "Code", href: "https://github.com/nazrulhuda/filingcheck" },
];

export const STEPS = [
  "You ask a question",
  "The server checks each lookup the AI requests",
  "Every number is labeled against its source",
];

export const TRAP_LINE =
  "Trap questions are written to trigger a known mistake, for example an unclear company name, " +
  "'last year', a figure for one division of a company, or a metric the data does not hold.";

export const STACK =
  "Built with Python, LangGraph, FastAPI, Postgres + pgvector, Next.js/TypeScript, Docker, " +
  "GitHub Actions.";

export type Tile = { figure: string; text: string; note?: string };

/** The control set, checks on (final report, section 6 and the control accuracy row). */
export const CONTROL = { questions: 50, runs: 150, falseRepairs: 0, accuracy: "90.0%" };

/** The four result tiles, in the README's order: the prompt-rules result first. */
export function resultTiles(r: Results): Tile[] {
  const p = r.prompt_rules;
  const h = r.headline;
  const verdict = !p.accuracy_clear
    ? "No clear difference in accuracy"
    : p.accuracy_difference.startsWith("-")
      ? "The prompt did better"
      : "The server checks did better";
  return [
    {
      figure: `${p.accuracy} vs ${p.accuracy_checks}`,
      text:
        `Accuracy on the ${r.held_out.questions} held-out trap questions, the rules in the ` +
        `prompt against the server checks. ${verdict}, at about ${p.cost_ratio} times the cost ` +
        "per question.",
    },
    {
      figure: `${h.checks_off} → ${h.checks_on}`,
      text:
        "Confidently wrong answers on the same questions, checks off to checks on: the " +
        `pre-registered headline (95% interval of the difference ${h.low} to ${h.high} points).`,
    },
    {
      figure: `${CONTROL.falseRepairs} of ${CONTROL.runs}`,
      text:
        `Runs on the ${CONTROL.questions} normal (control) questions, with the checks on, in ` +
        "which a check repaired or rejected a number lookup.",
      note:
        `${CONTROL.accuracy} of these runs were answered correctly. This is a development set: ` +
        "the fiscal-year check on searches was built after a dry run on these questions.",
    },
    {
      figure: `${r.held_out.questions} × ${r.held_out.runs}`,
      text: "Sealed held-out trap questions and runs each, scored by rules fixed in advance.",
    },
  ];
}

/** The size of each part of the system; each figure is matched with its source by the test. */
export const INSIDE_FIGURES = {
  reports: 75,
  companies: 25,
  years: 3,
  passages: 42612,
  metrics: 13,
  agreements: 1123,
  disagreements: 0,
  tools: 3,
  rules: 6,
  answers: 3855,
  setups: 5,
};

const n = (value: number) => value.toLocaleString("en-US");

/** The six "What's inside" tiles: what each part is, with no claim about its effect. */
export function insideTiles(f: typeof INSIDE_FIGURES): { name: string; text: string }[] {
  return [
    {
      name: "Data",
      text:
        `${n(f.reports)} annual reports (10-Ks) from ${n(f.companies)} companies, ${f.years} ` +
        "years each, each pinned by its SEC accession number.",
    },
    {
      name: "Search",
      text:
        `${n(f.passages)} passages from Items 1, 1A, 7, 7A and 8 of each report, searched by ` +
        "meaning and by keyword.",
    },
    {
      name: "Numbers",
      text:
        `${f.metrics} financial metrics read from each filing's own XBRL data; ` +
        `${n(f.agreements)} figures cross-checked against the SEC's companyfacts file, ` +
        `${f.disagreements} disagreements.`,
    },
    { name: "Agent", text: `${f.tools} tools (search, number lookup, exact calculator).` },
    {
      name: "Checks",
      text: `${f.rules} server-side rules on the model's lookups, every decision logged and shown.`,
    },
    {
      name: "Testing",
      text:
        `${n(f.answers)} test answers across ${f.setups} setups; every published number ` +
        "recomputed by one command.",
    },
  ];
}

export const INSIDE = insideTiles(INSIDE_FIGURES);
