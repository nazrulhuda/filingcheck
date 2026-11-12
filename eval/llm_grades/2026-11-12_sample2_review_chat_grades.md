# Day 32 sample 2: hand grades by the review chat (2026-11-12)

Graded from `eval/llm_grades/2026-11-12_sample2_hidden.md` (PR #71, head 1ba0dc8) by the rules in `eval/grader_prompt.md` version 2, before seeing any LLM verdict for sample 2 (its key is not in the repo) and before any other grader's sample 2 grades existed.

| Row | Verdict | Supported | Note |
|---:|---|---|---|
| 1 | correct | yes | |
| 2 | correct | partly | the AOCI / reclassification detail is not in the cited passages shown |
| 3 | wrong | yes | owner row; FY2025 figure for "last year" (FY2026) |
| 4 | correct | yes | |
| 5 | abstained | n/a | |
| 6 | abstained | n/a | |
| 7 | correct | yes | |
| 8 | correct | yes | |
| 9 | correct | no | no passages are shown (the dagger marker was unread when the row was stored), so its claims cite nothing |
| 10 | abstained | n/a | |
| 11 | correct | yes | |
| 12 | wrong | yes | FY2025 figure for "last year" |
| 13 | wrong | n/a | owner row; asks which year, not which Morgan |
| 14 | correct | yes | owner row |
| 15 | correct | yes | owner row |
| 16 | correct | yes | |
| 17 | correct | yes | owner row |
| 18 | abstained | n/a | a discarded typo row ("Moody's's") |
| 19 | wrong | yes | owner row; answered Morgan Stanley instead of asking |
| 20 | abstained | n/a | discarded typo row |
| 21 | correct | no | same as row 9: no passages shown |
| 22 | abstained | n/a | |
| 23 | correct | yes | |
| 24 | correct | yes | |
| 25 | correct | yes | the question asks what it saves; the realignment purpose is a side detail |
| 26 | abstained | n/a | owner row; discarded typo row |
| 27 | wrong | partly | owner row; gives a reason the filing doesn't give; the regulation quotes are in the source, the causal claim is not |
| 28 | wrong | n/a | asks which year, not which Morgan |
| 29 | abstained | n/a | discarded typo row |
| 30 | correct | yes | |
| 31 | correct | yes | |
| 32 | correct | yes | the last sentence is a summary that follows from the passage |
| 33 | wrong | partly | gives a reason; "approved by the Federal Reserve Board and the NYDFS" is not in the passage |
| 34 | correct | yes | |
| 35 | partly | partly | says Nvidia itself "design[s]-out" U.S. semiconductors (the filing says customers do), and that is not in the cited passages |
| 36 | wrong | partly | owner row; same pattern as row 27 |
| 37 | wrong | yes | answered Morgan Stanley instead of asking |
| 38 | abstained | n/a | |
| 39 | correct | yes | owner row |
| 40 | correct | yes | |

Hardest calls: rows 2 and 35 (support), 9 and 21 (no passages shown because of the old parser), 25 and 32 (side detail vs summary), 27, 33 and 36 (partly vs no).
Note: sample 2 is again easy-heavy (6 Coca-Cola rows, 4 discarded "Moody's's" abstains, 5 Morgan rows), so the 15 text rows matter most.
