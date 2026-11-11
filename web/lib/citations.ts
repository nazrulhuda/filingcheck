// Citation markers in an answer, read with the same rule as the API's parser
// (filingcheck/answer/citations.py): passages as [1], [1, 3], [1-3] and the lenticular 【1】
// form (with or without a dagger note, 【1†number=1】), and the agent's facts from get_financial_fact as [F1] or [F1, F2]; one bracket may
// hold both ([1, F2]). The API's `citations` and `fact_citations` lists decide what each
// number points to; a marker whose numbers match nothing stays plain text. Both parsers are
// tested against tests/fixtures/citation_markers.json and tests/fixtures/fact_markers.json.

export type Citation = {
  number: number;
  chunk_id: number;
  ticker: string;
  fiscal_year: number;
  item: string;
  source_url: string;
  quote: string;
  /** The whole passage, for the chip; absent in answers saved before it was sent. */
  text?: string;
};

/** A number from get_financial_fact, cited as [Fn]; the value is a string as filed. */
export type FactCitation = {
  number: number;
  concept: string;
  value: string;
  unit: string;
  period_start: string | null;
  period_end: string | null;
  instant: string | null;
  accession: string;
  source_url: string;
  /** True when the line label is the metric's standard name, not the company's own wording. */
  standard_label?: boolean;
};

/** A fact the run looked up: [Fn] is the n-th one. Only the fields the page reads. */
export type FactUsed = {
  ticker: string;
  fiscal_year: number;
  metric: string;
  concept: string;
  line_label: string;
};

export type Segment =
  | { kind: "text"; text: string }
  | { kind: "cite"; raw: string; citations: Citation[]; facts: FactCitation[] };

// Each mapping is one character to one character, so positions in the normalized copy
// are positions in the original text.
const NORMALIZE = new Map<string, string>([
  ...[0x2010, 0x2011, 0x2012, 0x2013, 0x2212].map((c): [string, string] => [
    String.fromCharCode(c),
    "-",
  ]),
  ...[0x2014, 0x00a0, 0x2007, 0x2009, 0x202f].map((c): [string, string] => [
    String.fromCharCode(c),
    " ",
  ]),
  [String.fromCharCode(0x3010), "["],
  [String.fromCharCode(0x3011), "]"],
]);
// One part is a passage (2), a passage range (1-3), a fact (F2) or a fact range (F1-3).
// gpt-oss sometimes adds a dagger and a note after the numbers (【1†number=1】, 【3†L3-L5】);
// the note is read past, so those cite passage 1 and passage 3.
const PART = String.raw`F?\d+(?:\s*-\s*\d+)?`;
const CITATION = new RegExp(
  String.raw`\[\s*(${PART}(?:\s*,\s*${PART})*)\s*(?:\u2020[^\[\]]*)?\]`,
  "g",
);

/** The text with the dashes, spaces and brackets models write mapped to plain ones. */
export function normalize(text: string): string {
  let out = "";
  for (let i = 0; i < text.length; i++) {
    out += NORMALIZE.get(text[i]) ?? text[i];
  }
  return out;
}

/** The numbers cited, in first-cited order, within 1..highest: fact parts or passage parts. */
function cited(text: string, highest: number, facts: boolean): number[] {
  const numbers: number[] = [];
  for (const match of normalize(text).matchAll(CITATION)) {
    for (const raw of match[1].split(",")) {
      const part = raw.trim();
      if (part.startsWith("F") !== facts) continue;
      const bounds = part
        .replace(/^F/, "")
        .split(/\s*-\s*/)
        .map(Number);
      const high = Math.min(Math.max(...bounds), highest);
      for (let n = Math.max(Math.min(...bounds), 1); n <= high; n++) {
        if (!numbers.includes(n)) numbers.push(n);
      }
    }
  }
  return numbers;
}

/** The passage numbers cited, in first-cited order, within 1..passages. */
export function citedNumbers(text: string, passages: number): number[] {
  return cited(text, passages, false);
}

/** The fact numbers cited as [Fn], in first-cited order, within 1..facts. */
export function citedFacts(text: string, facts: number): number[] {
  return cited(text, facts, true);
}

/** The answer split into plain text and citation chips, keeping the text exactly. */
export function segments(
  text: string,
  citations: Citation[],
  facts: FactCitation[] = [],
): Segment[] {
  const byNumber = new Map(citations.map((c) => [c.number, c]));
  const factByNumber = new Map(facts.map((f) => [f.number, f]));
  const highest = Math.max(0, ...citations.map((c) => c.number));
  const highestFact = Math.max(0, ...facts.map((f) => f.number));
  const parts: Segment[] = [];
  let plain = "";
  let last = 0;
  for (const match of normalize(text).matchAll(CITATION)) {
    const start = match.index;
    const end = start + match[0].length;
    const passages = citedNumbers(match[0], highest)
      .map((n) => byNumber.get(n))
      .filter((c): c is Citation => c !== undefined);
    const factsCited = citedFacts(match[0], highestFact)
      .map((n) => factByNumber.get(n))
      .filter((f): f is FactCitation => f !== undefined);
    if (passages.length === 0 && factsCited.length === 0) continue;
    plain += text.slice(last, start);
    if (plain) parts.push({ kind: "text", text: plain });
    plain = "";
    parts.push({
      kind: "cite",
      raw: text.slice(start, end),
      citations: passages,
      facts: factsCited,
    });
    last = end;
  }
  plain += text.slice(last);
  if (plain) parts.push({ kind: "text", text: plain });
  return parts;
}
