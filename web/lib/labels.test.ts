// Number labels on the page: each badge's text, where it goes, and the key under the answer.
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";

import type { Answer } from "./api.ts";
import { type Citation, type FactCitation, segments } from "./citations.ts";
import { lineHeading } from "./facts.ts";
import {
  LABEL_KEY,
  type NumberLabel,
  badgeText,
  hasBadges,
  withBadges,
} from "./labels.ts";

function label(fields: Partial<NumberLabel>): NumberLabel {
  return {
    figure: "$1",
    value: "1",
    percent: false,
    label: "unverified",
    basis: null,
    fact: null,
    concept: null,
    period: null,
    fiscal_year: null,
    passage: null,
    calculation: null,
    cited_value: null,
    source: null,
    inputs: [],
    end: null,
    ...fields,
  };
}

const REVENUE: FactCitation = {
  number: 1,
  concept: "us-gaap:Revenues",
  value: "680985000000",
  unit: "USD",
  period_start: "2024-02-01",
  period_end: "2025-01-31",
  instant: null,
  accession: "a",
  source_url: "u",
};
const EPS: FactCitation = {
  ...REVENUE,
  number: 2,
  concept: "us-gaap:EarningsPerShareDiluted",
  value: "6.43",
  unit: "USD/shares",
};
const SHARES: FactCitation = {
  ...REVENUE,
  number: 3,
  concept: "us-gaap:CommonStockSharesOutstanding",
  value: "15204137000",
  unit: "shares",
};

test("each label says in words what it found", () => {
  assert.equal(
    badgeText(
      label({
        label: "verified",
        basis: "fact",
        fact: 1,
        concept: "us-gaap:Revenues",
        fiscal_year: 2024,
      }),
      [],
    ),
    "In the SEC data: fact F1, us-gaap:Revenues, FY2024",
  );
  assert.equal(
    badgeText(
      label({
        label: "verified",
        basis: "fact_other_period",
        fact: 1,
        fiscal_year: 2023,
      }),
      [],
    ),
    "In the SEC data for fiscal 2023 (another period in the same filing)",
  );
  assert.equal(
    badgeText(label({ label: "verified", basis: "passage", passage: 2 }), []),
    "In cited passage 2",
  );
  assert.equal(
    badgeText(
      label({ label: "verified", basis: "calculation", inputs: ["F1", "F2"] }),
      [],
    ),
    "From a calculation of F1 and F2",
  );
  assert.equal(
    badgeText(
      label({
        label: "verified",
        basis: "calculation",
        inputs: ["F1", "F2", "passage 3"],
      }),
      [],
    ),
    "From a calculation of F1, F2 and passage 3",
  );
  assert.equal(
    badgeText(label({}), []),
    "Not found in the sources this answer used",
  );
});

test("a Conflict says what the cited source says, in the fact's unit", () => {
  const facts = [REVENUE, EPS, SHARES];
  assert.equal(
    badgeText(
      label({ label: "conflict", fact: 1, cited_value: "680985000000" }),
      facts,
    ),
    "The source says $680,985,000,000",
  );
  assert.equal(
    badgeText(
      label({ label: "conflict", fact: 2, cited_value: "6.43" }),
      facts,
    ),
    "The source says $6.43 per share",
  );
  assert.equal(
    badgeText(
      label({ label: "conflict", fact: 3, cited_value: "15204137000" }),
      facts,
    ),
    "The source says 15,204,137,000 shares",
  );
});

function citation(number: number): Citation {
  return {
    number,
    chunk_id: number,
    ticker: "WMT",
    fiscal_year: 2024,
    item: "7A",
    source_url: "u",
    quote: "q",
  };
}

function shape(
  text: string,
  labels: NumberLabel[],
  cites: Citation[] = [],
): string[] {
  return withBadges(segments(text, cites), labels).map((p) =>
    p.kind === "text"
      ? p.text
      : p.kind === "cite"
        ? `[cite ${p.raw}]`
        : `[${p.label.label}]`,
  );
}

test("a badge goes right after its figure, before the citation chip", () => {
  const text = "Swaps would change by $0.7 billion [1].";
  const end = text.indexOf(" [1]");
  assert.deepEqual(
    shape(text, [label({ label: "verified", end })], [citation(1)]),
    [
      "Swaps would change by $0.7 billion",
      "[verified]",
      " ",
      "[cite [1]]",
      ".",
    ],
  );
});

test("a badge after a bold figure goes after the closing asterisks", () => {
  const text = "It was **$44 billion** of debt.";
  const end = text.indexOf("**", 8);
  assert.deepEqual(shape(text, [label({ end })]), [
    "It was **$44 billion**",
    "[unverified]",
    " of debt.",
  ]);
});

test("two badges in one run of text split it twice; a label with no place gets no badge", () => {
  const text = "From $1 to $2 and $3.";
  const labels = [
    label({ end: 7 }),
    label({ end: 13, label: "conflict" }),
    label({ end: null }),
  ];
  assert.deepEqual(shape(text, labels), [
    "From $1",
    "[unverified]",
    " to $2",
    "[conflict]",
    " and $3.",
  ]);
});

test("putting the pieces back together gives the text exactly", () => {
  const text = "Revenue was $680,985 million【F1】, up 4.7% [1].";
  const labels = [
    label({ end: text.indexOf("【") }),
    label({ end: text.indexOf("% ") + 1 }),
  ];
  const parts = withBadges(segments(text, [citation(1)], [REVENUE]), labels);
  assert.equal(
    parts
      .map((p) => (p.kind === "text" ? p.text : p.kind === "cite" ? p.raw : ""))
      .join(""),
    text,
  );
});

test("the key under an answer explains the three badges and what Verified means", () => {
  assert.match(LABEL_KEY, /Verified/);
  assert.match(LABEL_KEY, /not that the sentence is right/);
  assert.equal(
    hasBadges({ number_labels: [label({ end: 3 })] } as Answer),
    true,
  );
  assert.equal(
    hasBadges({ number_labels: [label({ end: null })] } as Answer),
    false,
  );
  assert.equal(hasBadges({} as Answer), false);
});

test("the fact chip names a standard line label as such", () => {
  assert.equal(
    lineHeading({ ...REVENUE, standard_label: true }),
    "Standard name",
  );
  assert.equal(lineHeading({ ...REVENUE, standard_label: false }), "Line");
  assert.equal(lineHeading(REVENUE), "Line");
});

type Example = { question: string; answer: Answer };
const examples = JSON.parse(
  readFileSync(new URL("../data/examples.json", import.meta.url), "utf8"),
) as Example[];

test("every saved example carries its labels, each badge placed right after its figure", () => {
  for (const { question, answer } of examples) {
    assert.ok(Array.isArray(answer.number_labels), question);
    for (const lab of answer.number_labels ?? []) {
      assert.ok(lab.end !== null, `${question}: ${lab.figure}`);
      const before = answer.text.slice(0, lab.end ?? 0).replace(/[   ]/g, " ");
      const digits = lab.figure.replace(/[^\d]/g, "");
      assert.ok(
        before.replace(/[^\d]/g, "").endsWith(digits),
        `${question}: ${lab.figure}`,
      );
    }
  }
});

test("the passage chips of the saved examples carry their whole passage", () => {
  for (const { question, answer } of examples) {
    for (const c of answer.citations) {
      assert.ok(
        (c.text ?? "").length > c.quote.length,
        `${question}: passage ${c.number}`,
      );
    }
  }
});
