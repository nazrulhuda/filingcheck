# Week 6 notes

The detail behind the [week 6 summary](week6_summary.md). Every number is from the committed rows ([full report](../eval/results/2026-11-14_final_report.md)); every choice has a row in [decisions](decisions.md).

## The days

| Day | Pull request | What |
|---|---|---|
| 36 | #75 | Small fixes before the measurement: what each run records (the arguments as sent, a fixed error-kind list, the commit, a clean tree, the question file's SHA-256), the vector baseline, README fixes. The step-cap change (send no tools after the cap) did not stop the provider's "tool choice is none" error and was reverted. |
| 37 | #76 | The second held-out file: 84 questions written by Google Gemini through its API, outside the project; gold from the facts table, all cross-checked against companyfacts; refusal notes on questions whose figure the filing states; two questions marked not scored; both files sealed. |
| 38 | #77 | The pre-registration (definitions written by a reviewing AI session before any held-out answer existed), the metrics and statistics code, and a demo on development rows. |
| 39 | #78 | The prompt-rules arm (the block built by code from the checks' data), its development runs; the decline rule widened to the checks' own refusal wordings and every stored row re-graded; the tag `week6-measured`, the deploy and the live smoke check. |
| 40 | #79 | The final run: 3,855 rows and their grades, unedited, with the run record. |
| 41 | #80 | The report, the charts, the error analysis and the blind check of the text verdicts. |

## Before the final run

- **The held-out set grew from 28 to 112 questions** before anything was run (a simulation on development rows gave about 1 in 10 for 28 questions to show a clear difference, about 8 in 10 for 112).
- **The prompt-rules block is version 1**, as the code built it. A version 2 that reworded one line was run on the development sets and withdrawn at review because its reason was wrong; its rows are kept.
- **The decline rule reads the checks' own refusal wordings.** A refusal in the company check's words ("X is not one of the 25 companies in the dataset") was graded as an answer. Every reject reason in the checks was listed and marked refusal, ask or retry; the refusal wordings were added; every stored row was re-graded before and after: 17 outcomes changed, all in the prompt-rules development files, none in the checks arms.

## The final run

- One commit throughout (`da7a451`), a clean tree, both seals and the pre-registration's hash checked before the run. The arms ran one after another, none at the same time. 4 error rows of 3,855 (three `tool_choice_none`, one `cut_off`), at most 3.3% in any set and arm.
- **The PC slept from 07:58 to 17:53 UTC during the baseline arm.** One run (control-117, run 1) was in flight; it finished normally, and its time includes the sleep. Latency is reported as pre-registered, with one line, marked added after the results, without that run.
- Grading ran after every arm had ended, with the LLM's second opinion on every number-graded run (3,851 grades, no grader errors).

## The report

- `make report` computes every section from the committed rows. The comparisons are paired by question with a bootstrap interval (seed 20261113, 10,000 resamples); accuracy and confidently wrong also get McNemar's exact test.
- **Changed after the results, marked in the report:** the prompt-rules sentence was first coded on confidently wrong alone; the pre-registration's S1 names confidently wrong and accuracy, so it now judges both. The change goes against the checks.
- **The blind check:** 30 text-graded checks-on runs drawn by seed 20261141, graded blind by Gemini (the newest Pro hit the free tier's quota and the newest Flash was overloaded several times before it replied; every attempt is committed) and by a reviewing AI session, whose grades were hashed before the reveal. Agreement with the LLM grader: 28 and 27 of 30.
- **The error analysis** read 90 failed checks-on runs (60 held-out drawn by seed, 30 development): 36 asked or abstained when they should have answered, 22 used a wrong argument no check caught, 13 other (mostly a check misreading the question), 8 grader errors. In the review's two groups: 23 from gaps in the checks, 17 from a check's own action, 50 in neither.

## Open for Week 7

- **The checks' gaps found in the error analysis:** the number tool keeps a year the model chose when the question names none (the search tool already uses the latest); "last yr", "morgans", one-candidate names ("american", "united"), "standard and poors" and "Citizens" are not read; `search_filings` has no company check; "through <date>" is not read as a period end; "the year before last" is read one year earlier than one question's writer meant; the company check rejects "morgan" as ambiguous even when the page filter names Morgan Stanley.
- **The LLM grader** failed five held-out answers that gave a figure the filing states with a citation, although the question's note accepts that.
- **The prompt-rules result:** the rules in the prompt were more accurate than the checks on held-out. Worth understanding before changing either: part of it is the block's year table (each company's latest fiscal year marked), which covers the no-year gap above.
- The page polish (the metric's line name on chips, company line labels), the MCP wrapper, the architecture picture and the video.
- A stronger-model row on the tagged commit, only if the key's limit is raised first (about $10 to $15).

## Costs

| | Billed by the key |
|---|---:|
| Days 36 to 39 (mostly Day 39's two development runs of the prompt-rules arm) | $0.45 |
| Day 40, the final run and its grading ($2.06 as recorded from the price table) | $1.64 |
| Day 41 (Gemini on the free tier; the floor's grades from the cache) | $0.00 |
| **Week 6** | **$2.09** |

The key's usage rose from $0.81 at the start of the week to $2.90; $2.10 of its $5 limit is left.
