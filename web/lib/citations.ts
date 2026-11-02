// Citation markers in an answer, read with the same rule as the API's parser
// (filingcheck/answer/citations.py): [1], [1, 3], [1-3] and the lenticular 【1】 form.
// The API's `citations` list decides which passage each number points to; a marker
// whose numbers match no citation stays plain text. Both parsers are tested against
// tests/fixtures/citation_markers.json.

export type Citation = {
  number: number;
  chunk_id: number;
  ticker: string;
  fiscal_year: number;
  item: string;
  source_url: string;
  quote: string;
};

export type Segment =
  | { kind: "text"; text: string }
  | { kind: "cite"; raw: string; citations: Citation[] };

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
const CITATION = /\[\s*(\d+(?:\s*[,-]\s*\d+)*)\s*\]/g;

/** The text with the dashes, spaces and brackets models write mapped to plain ones. */
export function normalize(text: string): string {
  let out = "";
  for (let i = 0; i < text.length; i++) {
    out += NORMALIZE.get(text[i]) ?? text[i];
  }
  return out;
}

/** The passage numbers cited, in first-cited order, within 1..passages. */
export function citedNumbers(text: string, passages: number): number[] {
  const numbers: number[] = [];
  for (const match of normalize(text).matchAll(CITATION)) {
    for (const part of match[1].split(",")) {
      const bounds = part
        .trim()
        .split(/\s*-\s*/)
        .map(Number);
      const high = Math.min(Math.max(...bounds), passages);
      for (let n = Math.max(Math.min(...bounds), 1); n <= high; n++) {
        if (!numbers.includes(n)) numbers.push(n);
      }
    }
  }
  return numbers;
}

/** The answer split into plain text and citation chips, keeping the text exactly. */
export function segments(text: string, citations: Citation[]): Segment[] {
  const byNumber = new Map(citations.map((c) => [c.number, c]));
  const highest = Math.max(0, ...citations.map((c) => c.number));
  const parts: Segment[] = [];
  let plain = "";
  let last = 0;
  for (const match of normalize(text).matchAll(CITATION)) {
    const start = match.index;
    const end = start + match[0].length;
    const cited = citedNumbers(match[0], highest)
      .map((n) => byNumber.get(n))
      .filter((c): c is Citation => c !== undefined);
    if (cited.length === 0) continue;
    plain += text.slice(last, start);
    if (plain) parts.push({ kind: "text", text: plain });
    plain = "";
    parts.push({ kind: "cite", raw: text.slice(start, end), citations: cited });
    last = end;
  }
  plain += text.slice(last);
  if (plain) parts.push({ kind: "text", text: plain });
  return parts;
}
