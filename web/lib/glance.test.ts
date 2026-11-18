// The page's first screen and its tiles: every figure is read from web/data/results.json or
// compared here with the file it comes from, so no number on the page is typed by hand.
import assert from "node:assert/strict";
import { readFileSync, readdirSync } from "node:fs";
import { test } from "node:test";

import { checkReport } from "./checks.ts";
import {
  answerInView,
  cardLine,
  CONTROL,
  enterAsks,
  EXAMPLE_CARDS,
  FIRST_EXAMPLE,
  HEADLINE,
  INSIDE,
  INSIDE_FIGURES,
  insideTiles,
  JUMP_LINKS,
  MORE_CARDS,
  PRIVACY_NOTE,
  resultTiles,
  scrollBehavior,
  SENTENCE,
  STEPS,
  SUBLINE,
} from "./glance.ts";
import { readmeSections } from "./readme.ts";
import type { Results } from "./results.ts";
import { type Example, TRAP_NOTE, type TrapExample, trapExamples } from "./traps.ts";

const repo = (path: string) => new URL(`../../${path}`, import.meta.url);
const read = (path: string) => readFileSync(repo(path), "utf8");
const RESULTS = JSON.parse(read("web/data/results.json")) as Results;
const REPORT = read("eval/results/2026-11-14_final_report.md");

test("the result tiles keep the README's order, with the numbers from results.json", () => {
  assert.deepEqual(resultTiles(RESULTS), [
    {
      figure: "85.2% vs 75.5%",
      text:
        "Accuracy on the 110 held-out trap questions, the rules in the prompt against the " +
        "server checks. The prompt did better, at about 2.5 times the cost per question.",
    },
    {
      figure: "18.5% → 10.6%",
      text:
        "Confidently wrong answers on the same questions, checks off to checks on: the " +
        "pre-registered headline (95% interval of the difference -12.7 to -3.6 points).",
    },
    {
      figure: "0 of 150",
      text:
        "Runs on the 50 normal (control) questions, with the checks on, in which a check " +
        "repaired or rejected a number lookup.",
      note:
        "90.0% of these runs were answered correctly. This is a development set: the " +
        "fiscal-year check on searches was built after a dry run on these questions.",
    },
    {
      figure: "110 × 3",
      text: "Sealed held-out trap questions and runs each, scored by rules fixed in advance.",
    },
  ]);
});

test("the first tile's words follow the interval, not the hoped-for result", () => {
  const p = RESULTS.prompt_rules;
  const checksBetter = resultTiles({
    ...RESULTS,
    prompt_rules: { ...p, accuracy_difference: "+9.7" },
  });
  assert.match(checksBetter[0].text, /The server checks did better/);
  const unclear = resultTiles({ ...RESULTS, prompt_rules: { ...p, accuracy_clear: false } });
  assert.match(unclear[0].text, /No clear difference in accuracy/);
});

test("the control tile is the final report's own figures", () => {
  const repairs = /False repairs: (\d+) of (\d+) checks-on control runs/.exec(REPORT);
  assert.ok(repairs, "the report's false-repair line");
  assert.equal(CONTROL.falseRepairs, Number(repairs[1]));
  assert.equal(CONTROL.runs, Number(repairs[2]));
  const accuracy = /\| control \| accuracy, off → on \| (\d+) \| ([\d.]+%) \| ([\d.]+%) \|/.exec(
    REPORT,
  );
  assert.ok(accuracy, "the report's control accuracy row");
  assert.equal(CONTROL.questions, Number(accuracy[1]));
  assert.equal(CONTROL.accuracy, accuracy[3]);
});

test("the control tile's note is the decision record: the search check came from these questions", () => {
  const row = read("docs/decisions.md")
    .split("\n")
    .find((line) => line.startsWith("| 2026-11-12 | **A check added after the freeze"));
  assert.ok(row, "the Nov 12 decision row");
  assert.match(row, /fiscal-year check on `search_filings`/);
  assert.match(row, /Day 33 dry run/);
  assert.match(row, /text control questions/);
});

test("Data: 75 pinned filings from EDGAR, 25 companies, 3 fiscal years each, in 42,612 passages", () => {
  const { filings } = JSON.parse(read("data/manifest.json")) as {
    filings: { ticker: string; fiscal_year: number; accession: string }[];
  };
  assert.equal(INSIDE_FIGURES.reports, filings.length);
  assert.ok(filings.every((f) => /^\d{10}-\d{2}-\d{6}$/.test(f.accession)));
  const years = new Map<string, Set<number>>();
  for (const f of filings) years.set(f.ticker, (years.get(f.ticker) ?? new Set()).add(f.fiscal_year));
  assert.equal(INSIDE_FIGURES.companies, years.size);
  for (const [ticker, held] of years) assert.equal(held.size, INSIDE_FIGURES.years, ticker);
  const chunks = /\| Chunks \| ([\d,]+) \|/.exec(read("docs/data_report.md"));
  assert.ok(chunks, "the data report's chunk count");
  assert.equal(INSIDE_FIGURES.passages, Number(chunks[1].replaceAll(",", "")));
  // Downloaded from EDGAR: the filings client reads each document from the SEC's archive.
  assert.ok(read("filingcheck/ingest/filings.py").includes("https://www.sec.gov/Archives/edgar/data/"));
});

test("Numbers: the facts layer's 13 metrics and the companyfacts cross-check", () => {
  const metrics = [...read("filingcheck/facts/metrics.py").matchAll(/MetricSpec\(\s*"([a-z_]+)"/g)];
  assert.equal(INSIDE_FIGURES.metrics, metrics.length);
  const facts = read("docs/facts_report.md");
  const agree = /- Agreements: ([\d,]+)/.exec(facts);
  const disagree = /- Disagreements: ([\d,]+)/.exec(facts);
  assert.ok(agree && disagree, "the facts report's cross-check lines");
  assert.equal(INSIDE_FIGURES.agreements, Number(agree[1].replaceAll(",", "")));
  assert.equal(INSIDE_FIGURES.disagreements, Number(disagree[1].replaceAll(",", "")));
});

test("Agent and Checks: the tool registry and the report's check activity", () => {
  const tools = [...read("filingcheck/tools/__init__.py").matchAll(/Tool\(\s*"([a-z_]+)"/g)];
  assert.deepEqual(
    tools.map((m) => m[1]),
    ["search_filings", "get_financial_fact", "calculate"],
  );
  assert.equal(INSIDE_FIGURES.tools, tools.length);
  const pairs = new Set(
    [...REPORT.matchAll(/^\| [a-z_]+ \| [a-z_]+ \| (get_financial_fact|search_filings) \| ([a-z_]+) \|/gm)].map(
      (m) => `${m[1]} ${m[2]}`,
    ),
  );
  assert.equal(INSIDE_FIGURES.rules, pairs.size);
});

test("Evaluation: the committed final rows, one per answer, across five setups", () => {
  const files = readdirSync(repo("eval/results")).filter(
    (name) => name.startsWith("2026-11-14_") && name.endsWith("-final.jsonl"),
  );
  const rows = files
    .map((name) => read(`eval/results/${name}`).split("\n").filter((line) => line.trim()).length)
    .reduce((a, b) => a + b, 0);
  assert.equal(INSIDE_FIGURES.answers, rows);
  const setups = new Set(files.map((name) => name.replace(/-final\.jsonl$/, "").split("_").at(-1)));
  assert.equal(INSIDE_FIGURES.setups, setups.size);
});

test("Engineering: the CI workflow's jobs, the API's Docker deploy on Render, the database on Neon", () => {
  const ci = read(".github/workflows/ci.yml");
  const jobs = ci.slice(ci.indexOf("\njobs:\n"));
  const names = [...jobs.matchAll(/^ {2}([a-z_-]+):$/gm)].map((m) => m[1]);
  assert.deepEqual(names, ["checks", "reproduce", "integration", "web"]);
  assert.equal(INSIDE_FIGURES.ciJobs, names.length);
  assert.match(ci, /^on:\n {2}push:\n[\s\S]*?^ {2}pull_request:/m);
  assert.ok(read("filingcheck/app/api.py").includes("FastAPI("));
  assert.ok(read("Dockerfile").includes("uvicorn filingcheck.app.main:app"));
  const render = read("render.yaml");
  assert.ok(render.includes("runtime: docker") && render.includes("Neon"));
});

test("the Data and Engineering tiles are the plan's sentences", () => {
  const text = (name: string) => INSIDE.find((tile) => tile.name === name)?.text;
  assert.equal(
    text("Data"),
    "75 annual reports (10-Ks) from 25 companies, 3 years each, downloaded from SEC EDGAR, pinned " +
      "by accession number and split into 42,612 passages, searched by meaning and by keyword.",
  );
  assert.equal(
    text("Engineering"),
    "Unit and integration tests and 4 CI jobs on every push; a FastAPI service in Docker on " +
      "Render, Postgres + pgvector on Neon, the page on Vercel.",
  );
});

test("each tile has its icon", () => {
  const icons = read("web/components/Icons.tsx");
  const map = icons.slice(icons.indexOf("export const INSIDE_ICONS"));
  for (const tile of INSIDE) assert.match(map, new RegExp(`\\n  ${tile.name}: "[a-z]+",`), tile.name);
});

test("the six tiles say the checked figures, one per part of the system", () => {
  assert.deepEqual(
    INSIDE.map((tile) => tile.name),
    ["Data", "Numbers", "Agent", "Checks", "Evaluation", "Engineering"],
  );
  assert.deepEqual(insideTiles(INSIDE_FIGURES), INSIDE);
  const all = INSIDE.map((tile) => tile.text).join(" ");
  for (const figure of ["75 ", "25 ", "3 years", "42,612", "13 ", "1,123", "0 disagreements", "3 tools", "6 ", "3,855", "5 setups", "4 CI jobs"]) {
    assert.ok(all.includes(figure), figure);
  }
  // The tiles describe the parts; no tile claims an effect.
  assert.doesNotMatch(all, /cut|better|reduc|improv|fewer|accura/i);
});

test("the saved example shown on first load is the Nike answer, with a check at work", () => {
  const examples = JSON.parse(read("web/data/examples.json")) as Example[];
  const first = examples.find((e) => e.question === FIRST_EXAMPLE);
  assert.ok(first, "the saved Nike example");
  const { summary, lookups } = checkReport(first.answer);
  assert.equal(summary, "1 argument corrected.");
  assert.ok(lookups.flat().some((line) => line.startsWith("Year, corrected:")));
  assert.ok(first.answer.number_labels?.some((l) => l.label === "verified"));
});

test("how it works is three steps", () => {
  assert.deepEqual(STEPS, [
    "You ask a question",
    "The server checks each lookup the AI requests",
    "Every number is labeled against its source",
  ]);
});

test("the README's By the numbers table starts with the six tiles, word for word", () => {
  const readme = read("README.md");
  const start = readme.indexOf("\n**By the numbers**");
  assert.ok(start > 0, "the README's By the numbers table");
  const table = readme.slice(start, readme.indexOf("\n## ", start + 1));
  // A row may link its source (the Numbers row links the facts report); the words are the tile's.
  const unlinked = (text: string) => text.replace(/\[([^\]]+)\]\([^)]+\)/g, "$1");
  const rows = [...table.matchAll(/^\| ([^|]+?) \| (.+?) \|$/gm)]
    .map((m) => ({ name: m[1], text: unlinked(m[2]) }))
    .filter((row) => row.name !== "Part");
  assert.deepEqual(rows.slice(0, 6), INSIDE);
});

test("the example cards: five with their tags and full questions, then four behind More", () => {
  assert.deepEqual(
    EXAMPLE_CARDS.map((card) => [card.tag, card.question]),
    [
      ["Number lookup", "What was Costco's operating income in fiscal 2025?"],
      ["Calculation", "How much did NVIDIA's revenue grow from fiscal 2024 to fiscal 2025, in percent?"],
      ["Text search", "How much money does Citi have tied up in Argentina, and how does it handle the peso?"],
      ["Trap: a relative year", "How much revenue did Nike make last year?"],
      ["Trap: an ambiguous company name", "how much net revenue did morgan make in 2024"],
    ],
  );
  assert.deepEqual(
    MORE_CARDS.map((card) => card.tag),
    ["Text search", "Text search", "Text search", "Text search"],
  );
  assert.deepEqual(
    MORE_CARDS.map((card) => card.question.split(" ").find((w) => /^[A-Z][a-z]/.test(w) && w !== "How" && w !== "What")),
    ["Netflix", "UnitedHealth's", "Walmart's", "American"],
  );
});

test("each saved question has exactly one card, and the trap tags are the saved traps' sub-labels", () => {
  const examples = JSON.parse(read("web/data/examples.json")) as Example[];
  const traps = trapExamples(JSON.parse(read("web/data/trap_examples.json")) as TrapExample[], examples);
  const saved = new Set([...examples, ...traps].map((e) => e.question));
  const carded = [...EXAMPLE_CARDS, ...MORE_CARDS].map((card) => card.question);
  assert.deepEqual([...carded].sort(), [...saved].sort());
  for (const trap of traps) {
    const card = EXAMPLE_CARDS.find((c) => c.question === trap.question);
    assert.ok(card, trap.question);
    assert.equal(card.tag, `Trap: ${trap.trap[0].toLowerCase()}${trap.trap.slice(1)}`);
  }
});

test("the calculation example is the pipeline's saved answer, with the figures the plan names", () => {
  const examples = JSON.parse(read("web/data/examples.json")) as Example[];
  const calc = examples.find((e) => e.question === EXAMPLE_CARDS[1].question);
  assert.ok(calc, "the saved calculation example");
  assert.equal(calc.ticker, "NVDA");
  const answer = calc.answer;
  assert.equal(answer.mode, "agent");
  assert.equal(answer.checks, true);
  assert.deepEqual(
    (answer.tool_calls ?? []).map((c) => c.name),
    ["get_financial_fact", "get_financial_fact", "calculate"],
  );
  assert.deepEqual(
    // The stored fact keeps its value as filed; the page's type lists only what the page uses.
    ((answer.facts_used ?? []) as unknown as { fiscal_year: number; value: string }[]).map((f) => [
      f.fiscal_year,
      f.value,
    ]),
    [
      [2024, "60922000000"],
      [2025, "130497000000"],
    ],
  );
  const verified = (answer.number_labels ?? []).filter((l) => l.label === "verified").map((l) => l.figure);
  for (const figure of ["$60,922 million", "$130,497 million"]) assert.ok(verified.includes(figure), figure);
  assert.ok(verified.some((f) => f.startsWith("114.20")), "114.20 %");
  assert.ok((answer.overrides ?? []).every((o) => o.outcome === "pass"), "every check passed");
});

test("the headline and the line under it are the one sentence, split in two", () => {
  assert.equal(HEADLINE, "Ask about 25 companies' annual reports");
  assert.equal(`${HEADLINE}. ${SUBLINE}`, SENTENCE);
});

test("the footer names the builder with GitHub and LinkedIn, and no portfolio site", () => {
  const chrome = read("web/components/SiteChrome.tsx");
  assert.ok(chrome.includes("Built by Nazrul Huda Shanto"));
  assert.ok(chrome.includes("https://github.com/nazrulhuda"));
  assert.ok(chrome.includes("https://www.linkedin.com/in/mshanto/"));
  for (const path of ["web/components/SiteChrome.tsx", "web/app/page.tsx", "web/app/about/page.tsx"]) {
    assert.ok(!read(path).includes("nazrulhuda.com"), `${path}: no portfolio site`);
  }
});

test("both pages share the top bar and the footer", () => {
  for (const path of ["web/app/page.tsx", "web/app/about/page.tsx"]) {
    const page = read(path);
    assert.ok(page.includes("<TopBar />") && page.includes("<Footer />"), path);
  }
});

test("the home page's results strip: the trap line, the first two tiles, and the link to the rest", () => {
  const page = read("web/app/page.tsx");
  assert.ok(page.includes("resultTiles(RESULTS).slice(0, 2)"));
  assert.ok(page.includes("{TRAP_LINE}"));
  assert.ok(page.includes('href="/about#results"') && page.includes("All results and how they were measured"));
  assert.ok(page.includes('href="/about"') && page.includes("How it was built"));
  assert.ok(!page.includes("resultLines("), "the Details panel left the home page");
  assert.deepEqual(
    resultTiles(RESULTS).slice(0, 2).map((tile) => tile.figure),
    ["85.2% vs 75.5%", "18.5% → 10.6%"],
  );
});

test("the privacy note drops only its first sentence, which stays in What you can ask", () => {
  const page = read("web/app/page.tsx");
  assert.equal(
    PRIVACY_NOTE,
    "Questions are logged to improve the demo. Each question is sent to OpenAI to search the " +
      "filings, and through OpenRouter to Groq, or to Google if that is busy, to write the " +
      "answer; please don't enter personal information.",
  );
  assert.ok(page.includes("<li>Each question stands alone (no chat history).</li>"));
});

test("the page stays put only when the whole answer card is on screen", () => {
  assert.equal(answerInView(300, 700, 800), true, "the whole card shows");
  assert.equal(answerInView(0, 800, 800), true, "exactly the screen");
  assert.equal(answerInView(770, 1180, 800), false, "its top shows, its bottom does not");
  assert.equal(answerInView(120, 900, 800), false, "its top shows, its last 100 px do not");
  assert.equal(answerInView(-40, 300, 800), false, "its top is above the screen");
  assert.equal(answerInView(900, 1200, 800), false, "below the screen");
  assert.equal(scrollBehavior(true), "auto", "no animation with reduced motion");
  assert.equal(scrollBehavior(false), "smooth");
});

test("each card says what it is, in its strip, once", () => {
  assert.equal(cardLine("example", true), TRAP_NOTE, "a saved trap example");
  assert.equal(cardLine("example", false), "Saved example");
  assert.equal(cardLine("after-limit", true), TRAP_NOTE, "a saved trap answer served after the limit");
  assert.equal(cardLine("after-limit", false), "Saved example");
  assert.equal(cardLine("new", false), "Answer", "a live answer");
  assert.equal(cardLine("new", true), "Answer", "a live answer to a question like a trap");
  assert.equal(cardLine("working", false), "Answering…");
  const page = read("web/app/page.tsx");
  assert.ok(!page.includes("FIRST_EXAMPLE_LINE"), "the first-load line is the trap line now");
  assert.equal(page.split("{TRAP_NOTE}").length - 1, 0, "no second note at the bottom of the card");
});

test("Enter asks the question; Shift+Enter and composing do not", () => {
  assert.equal(enterAsks("Enter", false, false), true);
  assert.equal(enterAsks("Enter", true, false), false, "Shift+Enter starts a new line");
  assert.equal(enterAsks("Enter", false, true), false, "not while a character is being composed");
  assert.equal(enterAsks("a", false, false), false);
});

test("the top bar's links reach their targets from both pages, with no result figure", () => {
  assert.deepEqual(
    JUMP_LINKS.map((link) => [link.label, link.href]),
    [
      ["How it works", "/#how-it-works"],
      ["Results", "/about#results"],
      ["About", "/about"],
      ["GitHub", "https://github.com/nazrulhuda/filingcheck"],
    ],
  );
  const home = read("web/app/page.tsx");
  assert.ok(home.includes('id="how-it-works"'), "how-it-works");
  assert.ok(readmeSections(read("README.md")).some((s) => s.id === "results"), "/about#results");
  assert.doesNotMatch(JUMP_LINKS.map((l) => l.label).join(" "), /\d/);
});

test("the top bar shows the same four labels on every screen size", () => {
  for (const link of JUMP_LINKS) assert.ok(!("short" in link), link.label);
  const chrome = read("web/components/SiteChrome.tsx");
  assert.ok(!chrome.includes("sm:hidden") && !chrome.includes("link.short"));
  // What's inside stays on the home page, below How it works.
  assert.ok(read("web/app/page.tsx").includes('id="whats-inside"'));
});

test("the footer's Known limits goes to the About page's section", () => {
  const chrome = read("web/components/SiteChrome.tsx");
  assert.ok(chrome.includes('"/about#known-limits"'));
  assert.ok(!chrome.includes("#known-limits`"), "not the README on GitHub");
  assert.ok(readmeSections(read("README.md")).some((s) => s.id === "known-limits"));
});
