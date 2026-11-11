// What a fact chip opens to: the printed line label, the value as filed, the period and the
// SEC document, kept here so it can be tested without rendering.

import type { FactCitation, FactUsed } from "./citations.ts";

export type FactDetail = {
  title: string;
  label: string;
  value: string;
  period: string;
  link: string;
};

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

/** "2026-01-25" as "Jan 25, 2026", read as written (no time zone); anything else unchanged. */
export function formatDate(iso: string): string {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(iso);
  if (!match) return iso;
  const [, year, month, day] = match;
  return `${MONTHS[Number(month) - 1]} ${Number(day)}, ${year}`;
}

const UNITS: Record<string, string> = { "USD/shares": "USD per share" };

/** The value as filed, digits grouped, decimals kept, with its unit in words. */
function formatValue(value: string, unit: string): string {
  const match = /^(-?)(\d+)(\.\d+)?$/.exec(value);
  const number = match
    ? `${match[1]}${match[2].replace(/\B(?=(\d{3})+(?!\d))/g, ",")}${match[3] ?? ""}`
    : value;
  return `${number} ${UNITS[unit] ?? unit}`;
}

/** The detail of fact [Fn]: its line label comes from the n-th fact the run looked up. */
export function factDetail(citation: FactCitation, factsUsed: FactUsed[]): FactDetail {
  const used = factsUsed[citation.number - 1];
  const matches = used !== undefined && used.concept === citation.concept;
  const period =
    citation.instant !== null
      ? `as of ${formatDate(citation.instant)}`
      : citation.period_start !== null && citation.period_end !== null
        ? `${formatDate(citation.period_start)} to ${formatDate(citation.period_end)}`
        : "";
  return {
    title: matches
      ? `[F${citation.number}] ${used.ticker}, fiscal year ${used.fiscal_year}`
      : `[F${citation.number}]`,
    label: matches ? used.line_label : citation.concept,
    value: formatValue(citation.value, citation.unit),
    period,
    link: citation.source_url,
  };
}
