// The page's citation parser must give the same numbers as the API's
// (filingcheck/answer/citations.py); both are tested against the same cases.
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";

import { type Citation, citedNumbers, normalize, segments } from "./citations.ts";

const fixture = JSON.parse(
  readFileSync(new URL("../../tests/fixtures/citation_markers.json", import.meta.url), "utf8"),
) as { cases: { text: string; passages: number; numbers: number[] }[] };

for (const c of fixture.cases) {
  test(`shared case: ${c.text}`, () => {
    assert.deepEqual(citedNumbers(c.text, c.passages), c.numbers);
  });
}

function citation(number: number): Citation {
  return {
    number,
    chunk_id: 100 + number,
    ticker: "WMT",
    fiscal_year: 2025,
    item: "1A",
    source_url: `https://www.sec.gov/doc${number}.htm`,
    quote: `Passage ${number}`,
  };
}

test("normalizing keeps every character's position", () => {
  const text = `a‑b—c d【e】`;
  assert.equal(normalize(text), "a-b c d[e]");
  assert.equal(normalize(text).length, text.length);
});

test("markers become chips pointing at the citations with those numbers", () => {
  const parts = segments("Peso risk [1] and tariffs [2, 3].", [citation(1), citation(3)]);
  assert.deepEqual(
    parts.map((p) => (p.kind === "text" ? p.text : p.citations.map((c) => c.number))),
    ["Peso risk ", [1], " and tariffs ", [3], "."],
  );
});

test("lenticular markers become chips and keep their own characters", () => {
  const text = `Swaps change by $0.7 billion【1】`;
  const parts = segments(text, [citation(1)]);
  assert.equal(parts.length, 2);
  const chip = parts[1];
  assert.ok(chip.kind === "cite");
  assert.equal(chip.raw, "【1】");
  assert.deepEqual(chip.citations.map((c) => c.chunk_id), [101]);
});

test("a marker that points to no citation stays as text", () => {
  const parts = segments("Unknown [9] passage.", [citation(1)]);
  assert.deepEqual(parts, [{ kind: "text", text: "Unknown [9] passage." }]);
});

test("the segments put together give back the text exactly", () => {
  const text = `A [1]【2】 b [1‑2] c [7] d.`;
  const parts = segments(text, [citation(1), citation(2)]);
  assert.equal(parts.map((p) => (p.kind === "text" ? p.text : p.raw)).join(""), text);
});

test("a range is never expanded past the highest citation number", () => {
  const parts = segments("Huge [1-1000000000].", [citation(1), citation(2)]);
  const chip = parts.find((p) => p.kind === "cite");
  assert.ok(chip && chip.kind === "cite");
  assert.deepEqual(chip.citations.map((c) => c.number), [1, 2]);
});
