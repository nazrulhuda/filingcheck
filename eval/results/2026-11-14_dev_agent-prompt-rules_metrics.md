# The prompt-rules arm on the development sets

Development rows: the prompt-rules arm (block version 1, 2026-11-14) next to the Week 5 search-year arms (2026-11-12). The checks were built on these questions; a check of the arm, not a result.

Rows: `eval/results/2026-11-12_<set>_agent-checks-off-search-year.jsonl`, `eval/results/2026-11-12_<set>_agent-checks-on-search-year.jsonl`, `eval/results/2026-11-14_<set>_agent-prompt-rules.jsonl`, with their `_llm.jsonl` grades; definitions: `eval/PREREGISTRATION.md`; code: `filingcheck/eval/metrics.py`, `filingcheck/eval/stats.py`. Per-run CSV: `eval/results/2026-11-14_dev_agent-prompt-rules_metrics.csv`.

## Per set and arm

Rates are per question first, then the mean over the questions; questions marked not scored are left out. Error rows count in every rate: never correct, never confidently wrong.

| Set | Arm | Questions | Runs | Error rows | Accuracy | Partly (text runs) | Confidently wrong | without the labels | both graders | Wrong-argument calls per 100 runs | per 100 calls that ran | Abstain rate | p50 | p95 | Cost | Cost per 100 questions |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| dev_traps | agent-checks-off | 85 | 255 | 1 (0.4%) | 69.4% | - | 18.0% | 18.0% | 16.9% | 14.9 | 20.4 | 9.0% | 0.8 s | 2.3 s | $0.0771 | $0.0907 |
| dev_traps | agent-checks-on | 85 | 255 | 0 (0.0%) | 83.5% | - | 7.1% | 7.5% | 4.3% | 5.1 | 8.1 | 5.5% | 0.8 s | 2.6 s | $0.0814 | $0.0957 |
| dev_traps | agent-prompt-rules | 85 | 255 | 0 (0.0%) | 78.4% | - | 13.3% | 14.1% | 7.1% | 2.7 | 4.6 | 4.3% | 0.6 s | 1.3 s | $0.1822 | $0.2144 |
| control | agent-checks-off | 50 | 150 | 0 (0.0%) | 75.3% | 19.0% | 4.7% | 4.7% | 4.7% | 0.0 | 0.0 | 12.7% | 0.9 s | 2.3 s | $0.0511 | $0.1023 |
| control | agent-checks-on | 50 | 150 | 0 (0.0%) | 88.0% | 11.1% | 0.0% | 0.0% | 0.0% | 0.7 | 1.2 | 8.0% | 0.8 s | 2.6 s | $0.0603 | $0.1205 |
| control | agent-prompt-rules | 50 | 150 | 0 (0.0%) | 81.3% | 23.8% | 2.7% | 2.7% | 2.7% | 0.0 | 0.0 | 5.3% | 0.9 s | 2.3 s | $0.1479 | $0.2959 |

## Checks on against off

Paired by question: the difference is checks on minus checks off, with a 95% interval from a bootstrap over questions (10,000 resamples, seed 20261113); McNemar's exact test on each question's majority outcome (b: yes with the checks off and no with them on; c: the other way round). The wrong-argument rate falls partly by design: with the checks on, a stopped call never runs.

| Set | Metric | Checks off | Checks on | Difference | 95% interval | b | c | p |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| dev_traps | accuracy | 69.4% | 83.5% | +14.1 points | +6.3 to +22.0 | 1 | 16 | 0.0003 |
| dev_traps | confidently wrong | 18.0% | 7.1% | -11.0 points | -17.3 to -5.1 | 12 | 0 | 0.0005 |
| dev_traps | confidently wrong, both graders | 16.9% | 4.3% | -12.5 points | -19.2 to -6.3 | 13 | 0 | 0.0002 |
| dev_traps | confidently wrong, error rows counted as wrong | 18.4% | 7.1% | -11.4 points | -17.6 to -5.5 | 12 | 0 | 0.0005 |
| dev_traps | wrong-argument calls per 100 runs | 14.9 | 5.1 | -9.8 | -17.6 to -2.4 | - | - | - |
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
| dev_traps | agent-prompt-rules | 8 | 8.3 |

## False repairs on control questions

0 control run(s) of 450 in which a check repaired or rejected a get_financial_fact call. The fiscal-year check's repairs on search_filings, its design on a question that names no year, are counted apart: 65.

## Noise

The share of questions whose 3 runs do not all get the same outcome (the deciding grader's).

| Set | Arm | Questions | Not all the same |
|---|---|---:|---:|
| dev_traps | agent-checks-off | 85 | 22.4% |
| dev_traps | agent-checks-on | 85 | 17.6% |
| dev_traps | agent-prompt-rules | 85 | 22.4% |
| control | agent-checks-off | 50 | 16.0% |
| control | agent-checks-on | 50 | 12.0% |
| control | agent-prompt-rules | 50 | 22.0% |

## Stopped number-tool calls

Number-tool calls stored with status error: 40; stopped without a check's reject record: 0. Every stopped call is a check's reject.

## The graders

- Number-graded runs with an LLM second opinion: 195; where one grader passes the run and the other fails it: 28 (the deterministic grader passes and the LLM fails: 0; the deterministic grader fails and the LLM passes: 28). Rows graded before the final run have a second opinion only on failed runs, so only the second direction can show there.
- Text-graded runs with no usable LLM verdict: 0.
- Deciding outcomes seen: abstained, answered_when_should_ask, asked_about_another_thing, asked_when_should_answer, correct, error, no_number, other_year_number, partly, wrong, wrong_number, year_not_stated.

Every pairing of the deterministic outcome and the LLM's second opinion:

| Deterministic | LLM | Runs |
|---|---|---:|
| abstained | abstained | 58 |
| answered_when_should_ask | wrong | 57 |
| answered_when_should_ask | correct | 24 |
| other_year_number | wrong | 13 |
| asked_when_should_answer | wrong | 8 |
| abstained | wrong | 8 |
| asked_when_should_answer | asked | 6 |
| asked_about_another_thing | wrong | 4 |
| wrong_number | wrong | 3 |
| answered_when_should_ask | asked | 3 |
| abstained | asked | 2 |
| asked_about_another_thing | correct | 2 |
| asked_about_another_thing | partly | 2 |
| year_not_stated | correct | 2 |
| no_number | asked | 1 |
| answered_when_should_ask | partly | 1 |
| no_number | wrong | 1 |
