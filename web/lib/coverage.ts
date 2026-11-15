// "What you can ask": what the data holds and what it cannot answer.

/** The facts layer's 13 metrics (filingcheck/facts/metrics.py), in its order, in words. */
export const METRICS: [key: string, name: string][] = [
  ["revenue", "revenue"],
  ["net_income", "net income"],
  ["diluted_eps", "diluted earnings per share"],
  ["operating_income", "operating income"],
  ["pretax_income", "pretax income"],
  ["total_assets", "total assets"],
  ["total_liabilities", "total liabilities"],
  ["stockholders_equity", "stockholders' equity"],
  ["operating_cash_flow", "operating cash flow"],
  ["capital_expenditures", "capital expenditures"],
  ["cash_and_equivalents", "cash and equivalents"],
  ["long_term_debt", "long-term debt"],
  ["shares_outstanding", "shares outstanding"],
];

export const CANNOT = [
  "quarterly figures (only the annual 10-K filings are loaded)",
  "forecasts",
  "companies outside the 25",
  "a part of a company (a segment, a product, a region) unless the filing's text states it",
];
