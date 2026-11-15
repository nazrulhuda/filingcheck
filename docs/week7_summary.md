# Week 7 summary

**What it did:** launched the measured version. Nothing in the answering, grading or scoring code changed: `make verify-measured` compares every path that could change an answer or a reported number with the tag `week6-measured` (and the final rows with the commit that merged them), in CI on every push. Every number on the page and in the README comes from the [full report](../eval/results/2026-11-14_final_report.md).

**Pinned and reproducible (Day 44):** a CI job recomputes the report, its CSVs, the charts' CSVs and the page's `web/data/results.json` from the committed rows, with no keys and no database, and fails on any difference. `/health` shows the commit the live API runs.

**The README (Day 45):** the result in three lines (the prompt-rules result first, as the pre-registration requires), a summary chart, the architecture as a Mermaid diagram checked box by box against the code, one saved question followed step by step, and [where each claim can be checked](evidence.md).

**The page (Day 46):** what it can and cannot answer; the three labels in the labeler's terms; the measured result read from `make report`'s output; a working checks switch; and two saved trap answers, said on the page to be chosen. Five development-trap candidates were asked once each and graded as the measurement was; two show a check acting and are right ("morgan" and Costco's calendar year). The page shows "morgan", with the saved Nike answer; the Costco answer is not shown, because the calendar-year rejects are among the report's failures caused by a check's own action.

**Launch checks (Day 47):** the deployed API runs the merged commit and passes `make smoke-live`; `make verify-measured` passes on it; all 84 links on 21 pages in the README and `docs/` resolve (`make check-links`); no stale status wording; the secret scan over the whole history (320 commits with changes) finds nothing.

**Cost:** under one cent of model calls (the key had $2.0993 left before the Day 46 runs and $2.0971 after Day 47's smoke test; the live page shares it).

**Not built:** the checks' gaps fixed, rules and checks together, a stronger model, questions by a person, search over tables. Each changes the measured system, so it needs new sealed questions and a new pre-registration.
