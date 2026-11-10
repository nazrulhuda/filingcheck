// The "What was checked" panel: the override log in plain words.
import assert from "node:assert/strict";
import { test } from "node:test";

import { type Override, checkLine, checkSummary } from "./checks.ts";

function record(fields: Partial<Override>): Override {
  return {
    check: "company",
    outcome: "pass",
    argument: "ticker",
    sent: "WMT",
    used: "WMT",
    reason: "",
    options: [],
    ...fields,
  };
}

// Reasons copied from real override logs (eval/results/2026-11-10_examples_agent-checks-on.jsonl)
// and from the reason templates in filingcheck/checks/.
const COMPANY_PASS = record({ reason: "the question names Walmart Inc. (WMT); the model sent WMT" });
const YEAR_PASS = record({
  check: "fiscal_year",
  argument: "fiscal_year",
  sent: 2025,
  used: 2025,
  reason: "the question says fiscal 2025; the model sent 2025: fiscal 2025 (Jul 1, 2024 to Jun 30, 2025)",
});
const YEAR_REPAIR = record({
  check: "fiscal_year",
  outcome: "repair",
  argument: "fiscal_year",
  sent: 2023,
  used: 2026,
  reason:
    "'last year' read as the latest annual report; the model sent 2023; used fiscal 2026 (Jan 27, 2025 to Jan 25, 2026)",
});
const COMPANY_REJECT = record({
  outcome: "reject",
  sent: "MS",
  used: null,
  reason:
    "the question's company is ambiguous: JPMorgan Chase & Co. (JPM) or Morgan Stanley (MS); ask the user which one",
  options: ["JPM", "MS"],
});
const METRIC_PASS = record({
  check: "metric",
  argument: "metric",
  sent: "revenue",
  used: "revenue",
  reason: "an annual metric the data holds (revenue)",
});
const UNITS_PASS = record({ check: "units", argument: null, sent: null, used: null, reason: "no scale asked for" });
const SEGMENT_PASS = record({
  check: "segment",
  argument: null,
  sent: null,
  used: null,
  reason: "no segment tied to the number",
});

test("a company that passed says what the question names and what was used", () => {
  assert.equal(checkLine(COMPANY_PASS), "Company: the question names Walmart Inc. (WMT), used WMT.");
});

test("a year that passed says how the question was read and the period used", () => {
  assert.equal(
    checkLine(YEAR_PASS),
    "Year: the question says fiscal 2025, used fiscal 2025 (Jul 1, 2024 to Jun 30, 2025).",
  );
});

test("a repaired year says what the model sent and what was used instead", () => {
  assert.equal(
    checkLine(YEAR_REPAIR),
    "Year, corrected: 'last year' read as the latest annual report; the model sent 2023, used fiscal 2026 (Jan 27, 2025 to Jan 25, 2026).",
  );
});

test("a repaired company names the ticker used", () => {
  const repaired = record({
    outcome: "repair",
    sent: "MSFT",
    used: "AAPL",
    reason: "the question names Apple Inc. (AAPL); the model sent MSFT",
  });
  assert.equal(
    checkLine(repaired),
    "Company, corrected: the question names Apple Inc. (AAPL); the model sent MSFT, used AAPL.",
  );
});

test("a reject gives the reason without the instruction meant for the model", () => {
  assert.equal(
    checkLine(COMPANY_REJECT),
    "Rejected, company: the question's company is ambiguous: JPMorgan Chase & Co. (JPM) or Morgan Stanley (MS).",
  );
  const quarter = record({
    check: "metric",
    outcome: "reject",
    argument: "metric",
    reason: "the dataset has annual figures only (10-K); no quarterly periods ('Q3' in the question)",
  });
  assert.equal(
    checkLine(quarter),
    "Rejected, metric: the dataset has annual figures only (10-K); no quarterly periods ('Q3' in the question).",
  );
  const segment = record({
    check: "segment",
    outcome: "reject",
    argument: null,
    reason:
      "the fact tool returns company totals only; segment figures (AWS) are not supported; use search_filings for the text or say so",
  });
  assert.equal(
    checkLine(segment),
    "Rejected, segment: the fact tool returns company totals only; segment figures (AWS) are not supported.",
  );
  const year = record({
    check: "fiscal_year",
    outcome: "reject",
    argument: "fiscal_year",
    reason:
      "calendar 2024 is not one of WMT's fiscal years, which end in January; it overlaps fiscal 2024 and fiscal 2025; ask the user which fiscal year",
  });
  assert.equal(
    checkLine(year),
    "Rejected, year: calendar 2024 is not one of WMT's fiscal years, which end in January; it overlaps fiscal 2024 and fiscal 2025.",
  );
});

test("a call refused because the retry was used up says so in plain words", () => {
  const blocked = record({
    check: "retry",
    outcome: "reject",
    argument: null,
    sent: null,
    used: null,
    reason: "no further attempts; answer with what you have, ask the user, or say you can't find it",
  });
  assert.equal(checkLine(blocked), "Rejected: the one retry was already used, so this lookup did not run.");
});

test("the other passes read as plain sentences", () => {
  assert.equal(checkLine(METRIC_PASS), "Metric: an annual metric the data holds (revenue).");
  assert.equal(checkLine(UNITS_PASS), "Units: no scale asked for.");
  assert.equal(checkLine(SEGMENT_PASS), "Segment: no segment tied to the number.");
});

test("an unknown check still shows its name and reason", () => {
  assert.equal(checkLine(record({ check: "new_rule", reason: "fine" })), "New rule: fine.");
});

test("the summary: nothing looked up, all passed, or what changed", () => {
  assert.deepEqual(checkSummary([]), {
    summary: "No number was looked up, so there was nothing to check.",
    lookups: [],
  });
  const passed = [COMPANY_PASS, YEAR_PASS, METRIC_PASS, UNITS_PASS, SEGMENT_PASS];
  const all = checkSummary(passed);
  assert.equal(all.summary, "All arguments passed the checks.");
  assert.equal(all.lookups.length, 1);
  assert.equal(all.lookups[0].length, 5);
  const mixed = checkSummary([COMPANY_REJECT, COMPANY_PASS, YEAR_REPAIR, METRIC_PASS]);
  assert.equal(mixed.summary, "1 lookup sent back to the model; 1 argument corrected.");
  // Each lookup's records start with the company check.
  assert.deepEqual(
    mixed.lookups.map((lines) => lines.length),
    [1, 3],
  );
  const two = checkSummary([COMPANY_PASS, YEAR_REPAIR, COMPANY_PASS, YEAR_REPAIR]);
  assert.equal(two.summary, "2 arguments corrected.");
  assert.equal(two.lookups.length, 2);
});
