// Number labels on the page: a small badge after each labeled figure, what it says on hover or
// tap, and the one-line key under the answer. The labels come with the answer from the API
// (filingcheck/labels); the page only shows them.

import type { Answer } from "./api.ts";
import type { FactCitation, Segment } from "./citations.ts";

/** One figure's label, as the API sends it. `end` is where the figure ends in the answer text. */
export type NumberLabel = {
  figure: string;
  value: string;
  percent: boolean;
  label: "verified" | "conflict" | "unverified";
  basis: "fact" | "fact_other_period" | "calculation" | "passage" | null;
  fact: number | null;
  concept: string | null;
  period: string | null;
  fiscal_year: number | null;
  passage: number | null;
  calculation: string | null;
  cited_value: string | null;
  source: string | null;
  inputs?: string[];
  end: number | null;
};

/** The answer's pieces with the badges put in. */
export type BadgedSegment = Segment | { kind: "badge"; label: NumberLabel };

/** The symbol and name of each label; the symbols differ in shape, not only in colour. */
export const BADGES: Record<
  NumberLabel["label"],
  { symbol: string; name: string }
> = {
  verified: { symbol: "✓", name: "Verified" },
  unverified: { symbol: "?", name: "Unverified" },
  conflict: { symbol: "⚠︎", name: "Conflict" },
};

export const LABEL_KEY =
  "✓ Verified: in the SEC data this answer used · ? Unverified: not found in its sources · " +
  "⚠︎ Conflict: differs from the cited fact. Verified means the number is in a cited source, " +
  "not that the sentence is right.";

function grouped(value: string): string {
  const match = /^(-?)(\d+)(\.\d+)?$/.exec(value);
  if (!match) return value;
  return `${match[1]}${match[2].replace(/\B(?=(\d{3})+(?!\d))/g, ",")}${match[3] ?? ""}`;
}

/** A cited fact's value in its unit: "$680,985,000,000", "$6.43 per share", "15,204 shares". */
function inUnit(value: string, unit: string | undefined): string {
  const number = grouped(value);
  const sign = number.startsWith("-") ? "-" : "";
  const digits = number.replace(/^-/, "");
  if (unit === "USD") return `${sign}$${digits}`;
  if (unit === "USD/shares") return `${sign}$${digits} per share`;
  if (unit === "shares") return `${number} shares`;
  return number;
}

function list(names: string[]): string {
  if (names.length < 2) return names.join("");
  return `${names.slice(0, -1).join(", ")} and ${names[names.length - 1]}`;
}

/** What a badge says on hover or tap. */
export function badgeText(label: NumberLabel, facts: FactCitation[]): string {
  if (label.label === "conflict") {
    const unit = facts.find((f) => f.number === label.fact)?.unit;
    return `The source says ${inUnit(label.cited_value ?? "", unit)}`;
  }
  if (label.label === "unverified")
    return "Not found in the sources this answer used";
  switch (label.basis) {
    case "fact":
      return `In the SEC data: fact F${label.fact}, ${label.concept}, FY${label.fiscal_year}`;
    case "fact_other_period":
      return `In the SEC data for fiscal ${label.fiscal_year} (another period in the same filing)`;
    case "passage":
      return `In cited passage ${label.passage}`;
    case "calculation": {
      const inputs = label.inputs ?? [];
      return inputs.length
        ? `From a calculation of ${list(inputs)}`
        : "From a calculation in this answer";
    }
    default:
      return "In the SEC data this answer used";
  }
}

/** Whether the answer shows at least one badge, so the key goes under it. */
export function hasBadges(answer: Answer): boolean {
  return (answer.number_labels ?? []).some((label) => label.end !== null);
}

/**
 * The answer's pieces with a badge right after each labeled figure. A figure in **bold** gets its
 * badge after the closing asterisks. Offsets count UTF-16 units, as JavaScript strings do; a
 * label with no place gets no badge.
 */
export function withBadges(
  parts: Segment[],
  labels: NumberLabel[],
): BadgedSegment[] {
  const placed = labels
    .filter(
      (label): label is NumberLabel & { end: number } => label.end !== null,
    )
    .sort((a, b) => a.end - b.end);
  const out: BadgedSegment[] = [];
  let offset = 0;
  let next = 0;
  for (const part of parts) {
    if (part.kind === "cite") {
      out.push(part);
      offset += part.raw.length;
      continue;
    }
    const text = part.text;
    let cut = 0;
    while (next < placed.length && placed[next].end <= offset + text.length) {
      let at = Math.max(placed[next].end - offset, cut);
      while (text.startsWith("**", at)) at += 2;
      at = Math.min(at, text.length);
      if (at > cut) out.push({ kind: "text", text: text.slice(cut, at) });
      out.push({ kind: "badge", label: placed[next] });
      cut = at;
      next += 1;
    }
    if (cut < text.length) out.push({ kind: "text", text: text.slice(cut) });
    offset += text.length;
  }
  for (; next < placed.length; next += 1)
    out.push({ kind: "badge", label: placed[next] });
  return out;
}
