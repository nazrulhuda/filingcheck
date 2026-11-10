// The saved examples the page builds in (web/data/examples.json, from `make examples-export`).
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";

import type { Answer } from "./api.ts";
import { citedFacts, citedNumbers } from "./citations.ts";

type Example = { question: string; ticker: string | null; fiscal_year: number | null; answer: Answer };

const examples = JSON.parse(
  readFileSync(new URL("../data/examples.json", import.meta.url), "utf8"),
) as Example[];
const pageQuestions = readFileSync(
  new URL("../../eval/questions/page_examples.jsonl", import.meta.url),
  "utf8",
)
  .split("\n")
  .filter((line) => line.trim())
  .map((line) => JSON.parse(line) as { question: string; ticker: string; fiscal_year: number });

test("the examples are the page's five questions, with their company and year", () => {
  assert.deepEqual(
    examples.map((e) => [e.question, e.ticker, e.fiscal_year]),
    pageQuestions.map((q) => [q.question, q.ticker, q.fiscal_year]),
  );
});

test("every example was answered by the agent with the checks on", () => {
  for (const { question, answer } of examples) {
    assert.equal(answer.mode, "agent", question);
    assert.equal(answer.checks, true, question);
    assert.ok(Array.isArray(answer.overrides), question);
    assert.ok(Array.isArray(answer.tool_calls) && answer.tool_calls.length > 0, question);
    assert.equal(answer.abstained, false, question);
    assert.equal(answer.degraded, false, question);
    assert.equal(answer.finish_reason, "stop", question);
  }
});

test("every marker in an example opens a passage or a fact", () => {
  for (const { question, answer } of examples) {
    const passages = new Set(answer.citations.map((c) => c.number));
    const facts = answer.fact_citations ?? [];
    const factNumbers = new Set(facts.map((f) => f.number));
    const cited = citedNumbers(answer.text, Math.max(0, ...passages));
    const citedFact = citedFacts(answer.text, Math.max(0, ...factNumbers));
    assert.ok(cited.length + citedFact.length > 0, `${question}: no citation`);
    assert.deepEqual([...passages].sort(), [...cited].sort(), question);
    assert.deepEqual([...factNumbers].sort(), [...citedFact].sort(), question);
    for (const f of facts) {
      // [Fn] is the n-th fact the run looked up; its printed line label comes from there.
      assert.equal(answer.facts_used?.[f.number - 1]?.concept, f.concept, question);
    }
  }
});
