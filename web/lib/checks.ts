// The "What was checked" panel: the agent's override log in plain words. Each record is one
// check's result on one get_financial_fact call (filingcheck/checks/base.py); the reasons are
// written for the model, so the instructions to it are dropped here.

export type Override = {
  check: string;
  outcome: "pass" | "repair" | "reject";
  argument: string | null;
  sent: unknown;
  used: unknown;
  reason: string;
  options: string[];
};

const NAMES: Record<string, string> = {
  company: "Company",
  fiscal_year: "Year",
  metric: "Metric",
  units: "Units",
  segment: "Segment",
};

// Endings that tell the model what to do next; the visitor sees the reason without them.
const FOR_THE_MODEL = [
  /; ask the user which (?:one|fiscal year)$/,
  /; use search_filings for the text or say so$/,
  /; the supported metrics are listed$/,
];

function nameOf(check: string): string {
  const words = check.replace(/_/g, " ");
  return NAMES[check] ?? words.charAt(0).toUpperCase() + words.slice(1);
}

function sentence(text: string): string {
  return text.endsWith(".") ? text : `${text}.`;
}

/** One override record as a sentence. */
export function checkLine(override: Override): string {
  const name = nameOf(override.check);
  let reason = override.reason;
  if (override.check === "retry") {
    return "Rejected: the one retry was already used, so this lookup did not run.";
  }
  if (override.outcome === "reject") {
    for (const ending of FOR_THE_MODEL) reason = reason.replace(ending, "");
    return sentence(`Rejected, ${name.toLowerCase()}: ${reason}`);
  }
  if (override.outcome === "repair") {
    reason = reason.replace("; used ", ", used ");
    if (!reason.includes(", used ") && override.used !== null && override.used !== undefined) {
      reason += `, used ${String(override.used)}`;
    }
    return sentence(`${name}, corrected: ${reason}`);
  }
  reason = reason
    .replace(/; the model sent \d+: /, ", used ")
    .replace(/; the model sent ([A-Z][A-Z.-]*|\d+)(?=;|$)/, ", used $1");
  return sentence(`${name}: ${reason}`);
}

function count(n: number, one: string, many: string): string {
  return `${n} ${n === 1 ? one : many}`;
}

/** A one-line summary, and the log's sentences grouped by lookup. */
export function checkSummary(overrides: Override[]): { summary: string; lookups: string[][] } {
  if (overrides.length === 0) {
    return { summary: "No number was looked up, so there was nothing to check.", lookups: [] };
  }
  // A lookup's records start with the company check (or the retry refusal, which has no other).
  const lookups: string[][] = [];
  for (const override of overrides) {
    if (lookups.length === 0 || override.check === "company" || override.check === "retry") {
      lookups.push([]);
    }
    lookups[lookups.length - 1].push(checkLine(override));
  }
  const rejects = overrides.filter((o) => o.outcome === "reject").length;
  const repairs = overrides.filter((o) => o.outcome === "repair").length;
  const changes = [
    ...(rejects ? [count(rejects, "lookup sent back to the model", "lookups sent back to the model")] : []),
    ...(repairs ? [count(repairs, "argument corrected", "arguments corrected")] : []),
  ];
  const summary = changes.length ? `${changes.join("; ")}.` : "All arguments passed the checks.";
  return { summary, lookups };
}
