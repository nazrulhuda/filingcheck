// Review notes the page shows under a saved example, next to the answer they qualify.
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";

import type { Answer } from "./api.ts";
import { normalize } from "./citations.ts";
import { REVIEW_NOTES, reviewNote } from "./notes.ts";

type Example = { question: string; answer: Answer };

const examples = JSON.parse(
  readFileSync(new URL("../data/examples.json", import.meta.url), "utf8"),
) as Example[];

const WALMART =
  "How much would Walmart's currency swaps change in value if the dollar weakened by ten percent?";

test("the Walmart example carries the review note on its wording", () => {
  assert.equal(
    reviewNote(WALMART),
    "Review note: the $0.7 billion is from the filing; the words '10-year-old' are not. " +
      "FilingCheck checks numbers, not wording, yet.",
  );
});

test("an example without a note has none", () => {
  assert.equal(reviewNote("How much revenue did Nike make last year?"), null);
});

test("every note belongs to a saved example whose answer still has what the note is about", () => {
  // A refresh that drops the example or rewrites its answer must drop or update the note.
  const quoted: Record<string, string> = { [WALMART]: "10-year-old" };
  for (const question of Object.keys(REVIEW_NOTES)) {
    const example = examples.find((e) => e.question === question);
    assert.ok(example, `no saved example for the note on: ${question}`);
    assert.ok(quoted[question], `no wording recorded for the note on: ${question}`);
    assert.ok(normalize(example.answer.text).includes(quoted[question]), question);
  }
});
