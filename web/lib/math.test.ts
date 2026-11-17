// The model's LaTeX working, shown cleanly in the answer view only (the stored text, the labels
// and the checks do not change).
import assert from "node:assert/strict";
import { test } from "node:test";

import { mathText } from "./math.ts";

test("the review's line: the delimiters go, times and percent become symbols", () => {
  assert.equal(
    mathText("Calculation: \\((130,497 M - 60,922 M) / 60,922 M \\times 100 = 114.20\\%\\)."),
    "Calculation: (130,497 M - 60,922 M) / 60,922 M × 100 = 114.20%.",
  );
});

test("the saved calculation example's line", () => {
  assert.equal(
    mathText("Growth calculation: \\((130,497 - 60,922)/60,922 × 100 = 114.20\\%\\)."),
    "Growth calculation: (130,497 - 60,922)/60,922 × 100 = 114.20%.",
  );
});

test("a thin space for \\, and nothing else touched", () => {
  assert.equal(mathText("130\\,497"), "130\u2009497");
  const plain = "Nike’s revenue was **$46,398 million**【F1】 (a 5% fall; see [2]).";
  assert.equal(mathText(plain), plain);
});
