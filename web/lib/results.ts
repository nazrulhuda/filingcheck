// The results strip: the README's three lines, with every number from web/data/results.json,
// which `make report` writes from the committed rows (no number is typed here).

export type Results = {
  report: string;
  tag: string;
  held_out: { questions: number; runs: number };
  /** Confidently wrong, checks off → on; the difference is on minus off, in points. */
  headline: {
    checks_off: string;
    checks_on: string;
    difference: string;
    low: string;
    high: string;
    claimed: boolean;
  };
  /** The prompt-rules arm against the checks; each difference is checks minus prompt rules. */
  prompt_rules: {
    accuracy: string;
    accuracy_checks: string;
    accuracy_difference: string;
    accuracy_low: string;
    accuracy_high: string;
    accuracy_clear: boolean;
    confidently_wrong: string;
    confidently_wrong_checks: string;
    confidently_wrong_difference: string;
    confidently_wrong_low: string;
    confidently_wrong_high: string;
    confidently_wrong_clear: boolean;
    cost_per_100: string;
    cost_per_100_checks: string;
    cost_ratio: string;
  };
};

export type ResultLine = { lead: string; rest: string };

const negative = (signed: string) => signed.startsWith("-");

/** The three lines, worded by the intervals: "clear" means the interval leaves out zero. */
export function resultLines(r: Results): ResultLine[] {
  const p = r.prompt_rules;
  const lead = !p.accuracy_clear
    ? "The same rules written into the model's prompt and the server checks: no clear difference in accuracy."
    : negative(p.accuracy_difference)
      ? "The same rules written into the model's prompt were more accurate than the server checks."
      : "The server checks were more accurate than the same rules written into the model's prompt.";
  const both = `(${p.confidently_wrong} and ${p.confidently_wrong_checks})`;
  const wrong = !p.confidently_wrong_clear
    ? `no clear difference on confidently wrong answers ${both}`
    : negative(p.confidently_wrong_difference)
      ? `fewer confidently wrong answers with the checks ${both}`
      : `fewer confidently wrong answers with the rules in the prompt ${both}`;
  const h = r.headline;
  const interval = `(95% interval of the difference ${h.low} to ${h.high} points)`;
  return [
    {
      lead,
      rest:
        "The checks are six rules the server applies before a tool runs. Written into the " +
        `prompt instead, with no checks, the same rules scored ${p.accuracy} against ` +
        `${p.accuracy_checks} accuracy, at about ${p.cost_ratio} times the cost per question, ` +
        `with ${wrong}.`,
    },
    {
      lead: "The pre-registered headline:",
      rest: h.claimed
        ? `against no checks, the server checks cut confidently wrong answers from ${h.checks_off} to ${h.checks_on} ${interval}.`
        : `against no checks, confidently wrong answers went from ${h.checks_off} to ${h.checks_on} with the server checks ${interval}; no reduction is claimed.`,
    },
    {
      lead: "How it was measured:",
      rest:
        `once, on ${r.held_out.questions} sealed held-out trap questions (${r.held_out.runs} ` +
        `runs each), by rules fixed in advance, from the tagged commit ${r.tag}; reproducible ` +
        "with make report, with no API key and no database.",
    },
  ];
}
