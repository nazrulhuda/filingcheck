# Metrics demo: the Week 5 dry run's development rows

Development rows from the Week 5 dry run; a check of the code, not a result.

Rows: `eval/results/2026-11-12_<set>_<arm>-search-year.jsonl` with their `_llm.jsonl` grades; definitions: `eval/PREREGISTRATION.md`; code: `filingcheck/eval/metrics.py`, `filingcheck/eval/stats.py`. Per-run CSV: `eval/results/2026-11-12_dry-run_metrics-demo.csv`.
These rows were written before each call recorded the arguments as the model sent them, so the count of wrong-argument calls as sent is left out.

## Per set and arm

Rates are per question first, then the mean over the questions; questions marked not scored are left out. Error rows count in every rate: never correct, never confidently wrong.

| Set | Arm | Questions | Runs | Error rows | Accuracy | Partly (text runs) | Confidently wrong | without the labels | both graders | Wrong-argument calls per 100 runs | per 100 calls that ran | Abstain rate | p50 | p95 | Cost | Cost per 100 questions |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| dev_traps | agent-checks-off | 85 | 255 | 1 (0.4%) | 69.4% | - | 18.0% | 18.0% | 16.9% | 14.9 | 20.4 | 9.0% | 0.8 s | 2.3 s | $0.0771 | $0.0907 |
| dev_traps | agent-checks-on | 85 | 255 | 0 (0.0%) | 83.5% | - | 7.1% | 7.5% | 4.3% | 5.1 | 8.1 | 5.5% | 0.8 s | 2.6 s | $0.0814 | $0.0957 |
| dev_unanswerable | agent-checks-off | 10 | 30 | 0 (0.0%) | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0 | - | 100.0% | 1.3 s | 3.5 s | $0.0123 | $0.1230 |
| dev_unanswerable | agent-checks-on | 10 | 30 | 0 (0.0%) | 83.3% | 0.0% | 16.7% | 16.7% | 16.7% | 0.0 | - | 83.3% | 1.3 s | 6.2 s | $0.0126 | $0.1258 |
| control | agent-checks-off | 50 | 150 | 0 (0.0%) | 75.3% | 19.0% | 4.7% | 4.7% | 4.7% | 0.0 | 0.0 | 12.7% | 0.9 s | 2.3 s | $0.0511 | $0.1023 |
| control | agent-checks-on | 50 | 150 | 0 (0.0%) | 88.0% | 11.1% | 0.0% | 0.0% | 0.0% | 0.7 | 1.2 | 8.0% | 0.8 s | 2.6 s | $0.0603 | $0.1205 |

**The always-abstain floor** (the abstain sentence graded as the answer to every question by the same graders; its confidently-wrong rate is 0 by definition):

| Set | Questions | Accuracy |
|---|---:|---:|
| dev_traps | 85 | 29.4% |
| dev_unanswerable | 10 | 100.0% |
| control | 50 | 0.0% |

## Checks on against off

Paired by question: the difference is checks on minus checks off, with a 95% interval from a bootstrap over questions (10,000 resamples, seed 20261113); McNemar's exact test on each question's majority outcome (b: yes with the checks off and no with them on; c: the other way round). The wrong-argument rate falls partly by design: with the checks on, a stopped call never runs.

| Set | Metric | Checks off | Checks on | Difference | 95% interval | b | c | p |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| dev_traps | accuracy | 69.4% | 83.5% | +14.1 points | +6.3 to +22.0 | 1 | 16 | 0.0003 |
| dev_traps | confidently wrong | 18.0% | 7.1% | -11.0 points | -17.3 to -5.1 | 12 | 0 | 0.0005 |
| dev_traps | confidently wrong, both graders | 16.9% | 4.3% | -12.5 points | -19.2 to -6.3 | 13 | 0 | 0.0002 |
| dev_traps | confidently wrong, error rows counted as wrong | 18.4% | 7.1% | -11.4 points | -17.6 to -5.5 | 12 | 0 | 0.0005 |
| dev_traps | wrong-argument calls per 100 runs | 14.9 | 5.1 | -9.8 | -17.6 to -2.4 | - | - | - |
| dev_unanswerable | accuracy | 100.0% | 83.3% | -16.7 points | -40.0 to +0.0 | 2 | 0 | 0.5000 |
| dev_unanswerable | confidently wrong | 0.0% | 16.7% | +16.7 points | +0.0 to +40.0 | 0 | 2 | 0.5000 |
| dev_unanswerable | confidently wrong, both graders | 0.0% | 16.7% | +16.7 points | +0.0 to +40.0 | 0 | 2 | 0.5000 |
| dev_unanswerable | confidently wrong, error rows counted as wrong | 0.0% | 16.7% | +16.7 points | +0.0 to +40.0 | 0 | 2 | 0.5000 |
| dev_unanswerable | wrong-argument calls per 100 runs | 0.0 | 0.0 | +0.0 | +0.0 to +0.0 | - | - | - |
| control | accuracy | 75.3% | 88.0% | +12.7 points | +4.0 to +22.0 | 2 | 7 | 0.1797 |
| control | confidently wrong | 4.7% | 0.0% | -4.7 points | -10.7 to +0.0 | 2 | 0 | 0.5000 |
| control | confidently wrong, both graders | 4.7% | 0.0% | -4.7 points | -10.7 to +0.0 | 2 | 0 | 0.5000 |
| control | confidently wrong, error rows counted as wrong | 4.7% | 0.0% | -4.7 points | -10.7 to +0.0 | 2 | 0 | 0.5000 |
| control | wrong-argument calls per 100 runs | 0.0 | 0.7 | +0.7 | +0.0 to +2.0 | - | - | - |

## Segment refusals

Calls for the company and metric of a segment_vs_total refusal that ran, per 100 runs (not counted as wrong-argument calls).

| Set | Arm | Questions | Calls per 100 runs |
|---|---|---:|---:|
| dev_traps | agent-checks-off | 8 | 37.5 |
| dev_traps | agent-checks-on | 8 | 12.5 |

## False repairs on control questions

0 control run(s) of 300 in which a check repaired or rejected a get_financial_fact call. The fiscal-year check's repairs on search_filings, its design on a question that names no year, are counted apart: 65.

## Noise

The share of questions whose 3 runs do not all get the same outcome (the deciding grader's).

| Set | Arm | Questions | Not all the same |
|---|---|---:|---:|
| dev_traps | agent-checks-off | 85 | 22.4% |
| dev_traps | agent-checks-on | 85 | 17.6% |
| dev_unanswerable | agent-checks-off | 10 | 0.0% |
| dev_unanswerable | agent-checks-on | 10 | 10.0% |
| control | agent-checks-off | 50 | 16.0% |
| control | agent-checks-on | 50 | 12.0% |

## Stopped number-tool calls

Number-tool calls stored with status error: 40; stopped without a check's reject record: 0. Every stopped call is a check's reject.

## The graders

- Number-graded runs with an LLM second opinion: 134; where one grader passes the run and the other fails it: 10 (the deterministic grader passes and the LLM fails: 0; the deterministic grader fails and the LLM passes: 10). Rows graded before the final run have a second opinion only on failed runs, so only the second direction can show there.
- Text-graded runs with no usable LLM verdict: 0.
- Deciding outcomes seen: abstained, answered_when_should_ask, asked_about_another_thing, asked_when_should_answer, correct, error, no_number, other_year_number, partly, wrong, wrong_number.

Every pairing of the deterministic outcome and the LLM's second opinion:

| Deterministic | LLM | Runs |
|---|---|---:|
| abstained | abstained | 44 |
| answered_when_should_ask | wrong | 43 |
| other_year_number | wrong | 9 |
| answered_when_should_ask | correct | 9 |
| asked_when_should_answer | wrong | 7 |
| abstained | wrong | 6 |
| asked_about_another_thing | wrong | 4 |
| asked_when_should_answer | asked | 4 |
| wrong_number | wrong | 2 |
| abstained | asked | 2 |
| no_number | asked | 1 |
| answered_when_should_ask | asked | 1 |
| answered_when_should_ask | partly | 1 |
| asked_about_another_thing | correct | 1 |
