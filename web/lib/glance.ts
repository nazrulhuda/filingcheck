// The page's first screen and its tiles. The result tiles read their numbers from
// web/data/results.json (written by `make report`); the control tile and the six "What's inside"
// tiles are matched with their source files by glance.test.ts. No number here is new.

import type { Results } from "./results.ts";
import { TRAP_NOTE } from "./traps.ts";

/** The page's heading and the line under it: the one sentence, split in two. */
export const HEADLINE = "Ask about 25 companies' annual reports";
export const SUBLINE =
  "Before the AI looks anything up, the server checks its request, and every number in the " +
  "answer is labeled against the SEC data it cites.";
/** The whole sentence, for the meta description and the link preview. */
export const SENTENCE = `${HEADLINE}. ${SUBLINE}`;

/** The privacy note under the options row; its first sentence ("Each question stands alone (no
 * chat history).") is said in "What you can ask" instead. */
export const PRIVACY_NOTE =
  "Questions are logged to improve the demo. Each question is sent to OpenAI to search the " +
  "filings, and through OpenRouter to Groq, or to Google if that is busy, to write the answer; " +
  "please don't enter personal information.";

export type ExampleCard = { tag: string; question: string };

/** "Try an example": a tag for what each saved question shows, and the full question. */
export const EXAMPLE_CARDS: ExampleCard[] = [
  { tag: "Number lookup", question: "What was Costco's operating income in fiscal 2025?" },
  {
    tag: "Calculation",
    question: "How much did NVIDIA's revenue grow from fiscal 2024 to fiscal 2025, in percent?",
  },
  {
    tag: "Text search",
    question: "How much money does Citi have tied up in Argentina, and how does it handle the peso?",
  },
  { tag: "Trap: a relative year", question: "How much revenue did Nike make last year?" },
  { tag: "Trap: an ambiguous company name", question: "how much net revenue did morgan make in 2024" },
];

/** The other saved examples, shown when "More examples" is opened. */
export const MORE_CARDS: ExampleCard[] = [
  {
    tag: "Text search",
    question: "What does Netflix say about others claiming it infringed their intellectual property?",
  },
  {
    tag: "Text search",
    question: "How much of UnitedHealth's debt carries a fixed rate that isn't swapped?",
  },
  {
    tag: "Text search",
    question:
      "How much would Walmart's currency swaps change in value if the dollar weakened by ten percent?",
  },
  {
    tag: "Text search",
    question: "What framework did American Express management use to judge its internal controls?",
  },
];

/** Whether the whole answer card is on the screen; if not, the page brings its top to just under
 * the top of the screen. */
export function answerInView(top: number, bottom: number, viewport: number): boolean {
  return top >= 0 && bottom <= viewport;
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

/** The top bar's links, the same on both pages and on every screen size, in the order of a
 * visitor's questions: what it is, does it work, more detail, the code (last, as it leaves the site). */
export const JUMP_LINKS = [
  { label: "How it works", href: "/#how-it-works" },
  { label: "Results", href: "/about#results" },
  { label: "About", href: "/about" },
  { label: "GitHub", href: "https://github.com/nazrulhuda/filingcheck" },
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
  ciJobs: 4,
};

const n = (value: number) => value.toLocaleString("en-US");

/** The six "What's inside" tiles, the README's first six "By the numbers" rows: what each part
 * is, with no claim about its effect. */
export function insideTiles(f: typeof INSIDE_FIGURES): { name: string; text: string }[] {
  return [
    {
      name: "Data",
      text:
        `${n(f.reports)} annual reports (10-Ks) from ${n(f.companies)} companies, ${f.years} ` +
        "years each, downloaded from SEC EDGAR, pinned by accession number and split into " +
        `${n(f.passages)} passages, searched by meaning and by keyword.`,
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
      name: "Evaluation",
      text:
        `${n(f.answers)} test answers across ${f.setups} setups; every published number ` +
        "recomputed by one command.",
    },
    {
      name: "Engineering",
      text:
        `Unit and integration tests and ${f.ciJobs} CI jobs on every pull request; a FastAPI ` +
        "service in Docker on Render, Postgres + pgvector on Neon, the page on Vercel.",
    },
  ];
}

export const INSIDE = insideTiles(INSIDE_FIGURES);
