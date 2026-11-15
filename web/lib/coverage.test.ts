// "What you can ask": the metrics are the facts layer's own 13, in its order.
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";

import { CANNOT, METRICS } from "./coverage.ts";

const metricsPy = readFileSync(
  new URL("../../filingcheck/facts/metrics.py", import.meta.url),
  "utf8",
);

test("the page lists the 13 metrics of the facts layer, in its order", () => {
  const keys = [...metricsPy.matchAll(/MetricSpec\(\s*"([a-z_]+)"/g)].map((m) => m[1]);
  assert.equal(keys.length, 13);
  assert.deepEqual(
    METRICS.map(([key]) => key),
    keys,
  );
  for (const [, name] of METRICS) assert.ok(name.length > 2);
});

test("the page says what it cannot answer", () => {
  const all = CANNOT.join(" ");
  for (const word of ["quarter", "forecast", "outside the 25", "part of a company"]) {
    assert.ok(all.includes(word), word);
  }
});
