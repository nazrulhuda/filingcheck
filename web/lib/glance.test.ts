// The page's first screen and its tiles: every figure is read from web/data/results.json or
// compared here with the file it comes from, so no number on the page is typed by hand.
import assert from "node:assert/strict";
import { readFileSync, readdirSync } from "node:fs";
import { test } from "node:test";

import { checkReport } from "./checks.ts";
import {
  CONTROL,
  FIRST_EXAMPLE,
  INSIDE,
  INSIDE_FIGURES,
  insideTiles,
  resultTiles,
  STEPS,
} from "./glance.ts";
import type { Results } from "./results.ts";
import type { Example } from "./traps.ts";

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

test("Data: 75 pinned filings, 25 companies, 3 fiscal years each", () => {
  const { filings } = JSON.parse(read("data/manifest.json")) as {
    filings: { ticker: string; fiscal_year: number; accession: string }[];
  };
  assert.equal(INSIDE_FIGURES.reports, filings.length);
  assert.ok(filings.every((f) => /^\d{10}-\d{2}-\d{6}$/.test(f.accession)));
  const years = new Map<string, Set<number>>();
  for (const f of filings) years.set(f.ticker, (years.get(f.ticker) ?? new Set()).add(f.fiscal_year));
  assert.equal(INSIDE_FIGURES.companies, years.size);
  for (const [ticker, held] of years) assert.equal(held.size, INSIDE_FIGURES.years, ticker);
});

test("Search: the data report's passage count, from Items 1, 1A, 7, 7A and 8", () => {
  const chunks = /\| Chunks \| ([\d,]+) \|/.exec(read("docs/data_report.md"));
  assert.ok(chunks, "the data report's chunk count");
  assert.equal(INSIDE_FIGURES.passages, Number(chunks[1].replaceAll(",", "")));
  const sections = Object.keys(JSON.parse(read("data/section_snapshot.json")) as object);
  const items = new Set(sections.map((name) => name.replace(/^\S+ FY\d{4} Item /, "")));
  // "1-7A" is where a filing's own index keeps Items together (Citigroup, JPMorgan).
  assert.deepEqual([...items].sort(), ["1", "1-7A", "1A", "7", "7A", "8"]);
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

test("Testing: the committed final rows, one per answer, across five setups", () => {
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

test("the six tiles say the checked figures, one per part of the system", () => {
  assert.deepEqual(
    INSIDE.map((tile) => tile.name),
    ["Data", "Search", "Numbers", "Agent", "Checks", "Testing"],
  );
  assert.deepEqual(insideTiles(INSIDE_FIGURES), INSIDE);
  const all = INSIDE.map((tile) => tile.text).join(" ");
  for (const figure of ["75 ", "25 ", "3 years", "42,612", "13 ", "1,123", "0 disagreements", "3 tools", "6 ", "3,855", "5 setups"]) {
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
  const table = readme.slice(start, readme.indexOf("\n**", start + 1));
  const rows = [...table.matchAll(/^\| ([^|]+?) \| (.+?) \|$/gm)]
    .map((m) => ({ name: m[1], text: m[2] }))
    .filter((row) => row.name !== "Part");
  assert.deepEqual(rows.slice(0, 6), INSIDE);
});
