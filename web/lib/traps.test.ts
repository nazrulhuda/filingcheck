// "Try a trap question": saved answers from the development traps only, each showing a check
// at work, plus the saved Nike answer the page already held; the seven stay as they were.
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";

import {
  type Example,
  TRAP_NOTE,
  type TrapExample,
  plainExamples,
  trapExamples,
} from "./traps.ts";

const read = (path: string) => readFileSync(new URL(path, import.meta.url), "utf8");
const examples = JSON.parse(read("../data/examples.json")) as Example[];
const picked = JSON.parse(read("../data/trap_examples.json")) as TrapExample[];
const questions = (path: string) =>
  read(path)
    .split("\n")
    .filter((line) => line.trim())
    .map((line) => JSON.parse(line) as { id: string; question: string });
const devTraps = new Map(questions("../../eval/questions/dev_traps.jsonl").map((q) => [q.id, q]));
const heldOut = [
  ...questions("../../eval/questions/heldout_traps.jsonl"),
  ...questions("../../eval/questions/heldout_traps_2.jsonl"),
].map((q) => q.question);

test("the saved trap answers come from the development traps, word for word", () => {
  // The review's pick: morgan only (Costco's calendar-year ask is one of the report's failures
  // caused by a check's own action, so it is not shown as a check working).
  assert.deepEqual(
    picked.map((t) => t.id),
    ["dev-001"],
  );
  for (const t of picked) {
    assert.ok(t.id.startsWith("dev-"), t.id);
    assert.equal(t.question, devTraps.get(t.id)?.question, t.id);
    assert.ok(!heldOut.includes(t.question), t.id);
  }
});

test("each trap example shows a check acting, with the checks on", () => {
  for (const t of trapExamples(picked, examples)) {
    assert.equal(t.answer.mode, "agent", t.id);
    assert.equal(t.answer.checks, true, t.id);
    const acted = (t.answer.overrides ?? []).filter((o) => o.outcome !== "pass");
    assert.ok(acted.length > 0, `${t.id}: no check repaired or rejected anything`);
  }
});

test("the Nike answer is the saved example itself, and the list follows the plan's order", () => {
  const traps = trapExamples(picked, examples);
  assert.deepEqual(
    traps.map((t) => t.id),
    ["dev-001", "fact-002"],
  );
  const nike = traps.find((t) => t.id === "fact-002");
  const saved = examples.find((e) => e.question === "How much revenue did Nike make last year?");
  assert.equal(nike?.answer, saved?.answer);
  assert.equal(nike?.trap, "A relative year");
});

test("an example shown as a trap is not shown twice", () => {
  const plain = plainExamples(examples, trapExamples(picked, examples));
  assert.equal(plain.length, 6);
  assert.ok(!plain.some((e) => e.question.includes("Nike")));
});

test("the page says the trap examples were chosen", () => {
  assert.equal(
    TRAP_NOTE,
    "Saved examples, chosen to show a check at work. How often the checks work is in the results.",
  );
});
