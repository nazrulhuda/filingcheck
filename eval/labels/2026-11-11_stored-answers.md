# Number labels on the stored answers

Written by `python -m filingcheck.labels.stored`; do not edit by hand. One line per figure is in the `.jsonl` file of the same name.

- **Answers labeled:** 406, from 16 files (agent rows with a final answer; baseline rows are not labeled).
- **Answers with at least one figure:** 254; **figures:** 304.
- **Figures whose facts were looked up again** from the recorded arguments, because the row did not record them: 145.

| Grade of the row | Verified, fact | Verified, other period | Verified, calculation | Verified, passage | Conflict | Unverified | Figures |
|---|---:|---:|---:|---:|---:|---:|---:|
| answered_when_should_ask | 6 | 0 | 0 | 0 | 0 | 0 | 6 |
| correct | 213 | 0 | 0 | 0 | 0 | 0 | 213 |
| other_year_number | 4 | 0 | 0 | 0 | 0 | 0 | 4 |
| not graded | 6 | 0 | 0 | 66 | 0 | 9 | 81 |
| **All** | 229 | 0 | 0 | 66 | 0 | 9 | 304 |

Verified means the figure is in a cited SEC source; it does not prove the sentence uses it correctly. The grade column is the deterministic grade stored with the row.

## Rows with something missing

- `eval/probes/2026-11-11_day26-examples-run2.jsonl:day26-examples-run2-ret-040:2`: passage markers [1] have no recorded passage
- `eval/probes/2026-11-11_day26-examples-run2.jsonl:day26-examples-run2-ret-010:2`: passage markers [1] have no recorded passage
- `eval/probes/2026-11-11_search-items-after.jsonl:after-page:UNH-3:3`: passage markers [1] have no recorded passage
- `eval/probes/2026-11-11_search-items-after.jsonl:after-fresh:JPM-1:1`: passage markers [1] have no recorded passage
- `eval/probes/2026-11-11_search-items-before.jsonl:before-page:C-3:3`: fact markers [F1, F4, F3] have no fact (the run has 0)
- `eval/probes/2026-11-11_search-items-before.jsonl:before-page:NFLX-2:2`: passage markers [1] have no recorded passage
- `eval/probes/2026-11-11_search-items-before.jsonl:before-fresh:JPM-2:2`: passage markers [1] have no recorded passage
- `eval/probes/2026-11-11_search-items-before.jsonl:before-fresh:JPM-3:3`: passage markers [1] have no recorded passage
- `eval/probes/2026-11-11_search-items-before.jsonl:before-fresh:GOOGL-1:1`: passage markers [1] have no recorded passage
