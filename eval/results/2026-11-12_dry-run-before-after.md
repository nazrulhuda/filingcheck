# The search-year check: before and after

The Day 33 dry run (`*_agent-checks-off.jsonl`, `*_agent-checks-on.jsonl`) against its re-run with the fiscal-year check on `search_filings` (`*-search-year.jsonl`), same sets, both arms, 3 runs per question. The checks-off arm has no search-year check in either run, so its differences are the model's own variation between two runs. Computed from the rows with `filingcheck/eval/dryrun.py`; no claim is attached.

## Abstains and correct answers

| Set | Arm | Before: runs | abstained | correct | After: runs | abstained | correct |
|---|---|---:|---:|---:|---:|---:|---:|
| dev_traps | checks off | 255 | 20 | 182 | 255 | 23 | 177 |
| dev_traps | checks on | 255 | 10 | 219 | 255 | 14 | 213 |
| dev_unanswerable | checks off | 30 | 28 | 0 | 30 | 30 | 0 |
| dev_unanswerable | checks on | 30 | 29 | 0 | 30 | 25 | 0 |
| control | checks off | 150 | 19 | 79 | 150 | 19 | 80 |
| control | checks on | 150 | 21 | 80 | 150 | 12 | 79 |

## Text support (the LLM grader's `supported` on text answers)

| Set | Arm | Before: text answers | no | partly | unsupported share | After: text answers | no | partly | unsupported share |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| dev_unanswerable | checks off | 30 | 0 | 1 | 3% | 30 | 0 | 0 | 0% |
| dev_unanswerable | checks on | 30 | 0 | 0 | 0% | 30 | 1 | 3 | 13% |
| control | checks off | 63 | 3 | 24 | 43% | 63 | 6 | 20 | 41% |
| control | checks on | 63 | 2 | 19 | 33% | 63 | 2 | 21 | 37% |

## Search years on text questions

| Set | Arm | Run | Search calls | Latest pinned year | An earlier pinned year | A year the company does not hold | No year |
|---|---|---|---:|---:|---:|---:|---:|
| dev_unanswerable | checks off | before | 30 | 6 | 16 | 5 | 3 |
| dev_unanswerable | checks off | after | 34 | 7 | 18 | 8 | 1 |
| dev_unanswerable | checks on | before | 32 | 8 | 15 | 9 | 0 |
| dev_unanswerable | checks on | after | 36 | 35 | 1 | 0 | 0 |
| control | checks off | before | 76 | 3 | 45 | 15 | 13 |
| control | checks off | after | 74 | 2 | 49 | 11 | 12 |
| control | checks on | before | 83 | 3 | 58 | 17 | 5 |
| control | checks on | after | 79 | 79 | 0 | 0 | 0 |

## The LLM grader's verdicts on text answers

The LLM grade is the main grade for text questions (`control` has 21, 63 answers per arm; `dev_unanswerable` has 10, 30 per arm).

| Set | Arm | Before: correct | partly | wrong | abstained | After: correct | partly | wrong | abstained |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| dev_unanswerable | checks off | 28 | 0 | 2 | 0 | 30 | 0 | 0 | 0 |
| dev_unanswerable | checks on | 29 | 0 | 1 | 0 | 25 | 0 | 5 | 0 |
| control | checks off | 30 | 13 | 8 | 12 | 33 | 12 | 7 | 11 |
| control | checks on | 27 | 15 | 7 | 14 | 53 | 7 | 0 | 3 |

## Reading

- With the check on, every search on a control text question went to the company's latest filing (79 of 79; before, 3 of 83, and 17 to a year the company does not hold), and control abstains fell from 21 to 12. The checks-off arm, which has no search-year check in either run, moved only within the model's own variation.
- The LLM grader's verdicts on control text answers improved with the check on; their `supported` share did not: answers from the right filing still say more than their cited passages support. That is the Goldman and Walmart pattern, untouched by any check.
- The unanswerable set got worse with the check on: searched in the latest filing, the model answered 5 of 30 questions the filings do not answer (before: 1). The check gives it passages to read where before it mostly found nothing.
- dev_traps moved in both arms between the two runs (checks off 182 to 177 correct, checks on 219 to 213): number questions make few search calls, so this is the model's variation, not the check. No claim is attached to any of these numbers; the measurement is Week 6.
