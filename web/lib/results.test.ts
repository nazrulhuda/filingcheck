// The results strip: the README's three lines, every number from web/data/results.json,
// which `make report` writes from the committed rows.
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";

import { type Results, resultLines } from "./results.ts";

const RESULTS = JSON.parse(
  readFileSync(new URL("../data/results.json", import.meta.url), "utf8"),
) as Results;

const text = (r: Results) => resultLines(r).map((l) => `${l.lead} ${l.rest}`);

test("the strip says the README's three lines with the report's numbers", () => {
  assert.deepEqual(text(RESULTS), [
    "The same rules written into the model's prompt were more accurate than the server checks. " +
      "The checks are six rules the server applies before a tool runs. Written into the prompt " +
      "instead, with no checks, the same rules scored 85.2% against 75.5% accuracy, at about " +
      "2.5 times the cost per question, with no clear difference on confidently wrong answers " +
      "(7.3% and 10.6%).",
    "The pre-registered headline: against no checks, the server checks cut confidently wrong " +
      "answers from 18.5% to 10.6% (95% interval of the difference -12.7 to -3.6 points).",
    "How it was measured: once, on 110 sealed held-out trap questions (3 runs each), by rules " +
      "fixed in advance, from the tagged commit week6-measured; reproducible with make report, " +
      "with no API key and no database.",
  ]);
});

test("the words follow the intervals, not the hoped-for result", () => {
  const p = RESULTS.prompt_rules;
  const fewerWithRules = text({
    ...RESULTS,
    prompt_rules: { ...p, confidently_wrong_clear: true, confidently_wrong_difference: "+3.3" },
  });
  assert.match(fewerWithRules[0], /fewer confidently wrong answers with the rules in the prompt/);
  const fewerWithChecks = text({
    ...RESULTS,
    prompt_rules: { ...p, confidently_wrong_clear: true, confidently_wrong_difference: "-3.3" },
  });
  assert.match(fewerWithChecks[0], /fewer confidently wrong answers with the checks/);
  const checksBetter = text({
    ...RESULTS,
    prompt_rules: { ...p, accuracy_difference: "+9.7" },
  });
  assert.match(checksBetter[0], /^The server checks were more accurate than the same rules/);
  const unclear = text({ ...RESULTS, prompt_rules: { ...p, accuracy_clear: false } });
  assert.match(unclear[0], /no clear difference in accuracy/);
  const notClaimed = text({ ...RESULTS, headline: { ...RESULTS.headline, claimed: false } });
  assert.match(notClaimed[1], /no reduction is claimed/);
});
