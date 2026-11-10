// A fact chip's detail: the printed line label, the value as filed, the period and the link.
import assert from "node:assert/strict";
import { test } from "node:test";

import type { FactCitation, FactUsed } from "./citations.ts";
import { factDetail, formatDate } from "./facts.ts";

const KO: FactCitation = {
  number: 1,
  concept: "us-gaap:NetIncomeLoss",
  value: "10631000000",
  unit: "USD",
  period_start: "2024-01-01",
  period_end: "2024-12-31",
  instant: null,
  accession: "0000021344-25-000011",
  source_url: "https://www.sec.gov/Archives/edgar/data/21344/000002134425000011/ko-20241231.htm",
};

function used(fields: Partial<FactUsed>): FactUsed {
  return {
    ticker: "KO",
    fiscal_year: 2024,
    metric: "net_income",
    concept: "us-gaap:NetIncomeLoss",
    line_label: "Net income attributable to shareowners of The Coca-Cola Company",
    ...fields,
  };
}

test("a duration fact shows its line label, value as filed, period and link", () => {
  assert.deepEqual(factDetail(KO, [used({})]), {
    title: "[F1] KO, fiscal year 2024",
    label: "Net income attributable to shareowners of The Coca-Cola Company",
    value: "10,631,000,000 USD",
    period: "Jan 1, 2024 to Dec 31, 2024",
    link: KO.source_url,
  });
});

test("an instant fact shows the date it is as of", () => {
  const assets: FactCitation = {
    ...KO,
    concept: "us-gaap:Assets",
    value: "512163000000",
    period_start: null,
    period_end: null,
    instant: "2025-06-30",
  };
  const detail = factDetail(assets, [used({ concept: "us-gaap:Assets", line_label: "Total assets", ticker: "MSFT", fiscal_year: 2025 })]);
  assert.equal(detail.period, "as of Jun 30, 2025");
  assert.equal(detail.label, "Total assets");
  assert.equal(detail.title, "[F1] MSFT, fiscal year 2025");
});

test("per-share and share values keep their decimals and say their unit", () => {
  const eps = { ...KO, value: "2.46", unit: "USD/shares" };
  assert.equal(factDetail(eps, [used({})]).value, "2.46 USD per share");
  const shares = { ...KO, value: "4307000000", unit: "shares" };
  assert.equal(factDetail(shares, [used({})]).value, "4,307,000,000 shares");
  const negative = { ...KO, value: "-1234567.50" };
  assert.equal(factDetail(negative, [used({})]).value, "-1,234,567.50 USD");
});

test("without the matching fact the concept stands in for the label", () => {
  const detail = factDetail(KO, []);
  assert.equal(detail.label, "us-gaap:NetIncomeLoss");
  assert.equal(detail.title, "[F1]");
  // A fact used under another number is not borrowed.
  assert.equal(factDetail(KO, [used({ concept: "us-gaap:Assets" })]).label, "us-gaap:NetIncomeLoss");
});

test("dates are written out without a time zone shift", () => {
  assert.equal(formatDate("2026-01-25"), "Jan 25, 2026");
  assert.equal(formatDate("2025-12-01"), "Dec 1, 2025");
  assert.equal(formatDate("not a date"), "not a date");
});
