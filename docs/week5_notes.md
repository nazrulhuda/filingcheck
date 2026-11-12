# Week 5 notes

Details behind the Week 5 work, and what is left for Week 6.

## Day 33

**A fresh text sample after the dry run.** Both hand-graded samples of Day 32 hold many easy rows (identical "I can't find this" answers, clean numbers). After the dry run, draw 20 text answers from the dry-run rows by seed, with the LLM verdicts hidden, for a hand grader, and report the agreement on them.

## Open for Week 6

**An always-abstain baseline next to the arms.** The Week 6 report should show what an answerer that says "I can't find this in the filings I have." to every question would score, graded by the same graders, beside the checks-off and checks-on arms. A trap set where many questions expect a refusal or a question back rewards declining, so the arms' scores mean more next to that floor. Not built in Week 5.

**The graders in the Week 6 report.**

- The deterministic grade stays the main grade for number questions; the LLM grade is a second opinion on them, and the main grade only for text questions and for rows marked `llm_decides`.
- List every row where the LLM grader's reason contradicts its own verdict (in sample 2, rows 19 and 40: the schema asks for the verdict before the reason).
- The review chat hand-checks a fresh sample of the LLM's text verdicts from the Week 6 run.
- The existing decline rule does not recognise every refusal ("I won't make up a figure for that" is not read as declining); the LLM second opinion covers such rows, and the report should list them.

**A known disagreement between the frozen rule and the held-out writer (held-006).** The writer's note for "walmart net income for calendar year 2024" accepts Walmart's fiscal 2025 (February 2024 to January 2025) as the nearest year, so the gold is FY2025. The frozen fiscal-year check reads "calendar year" for a non-December company as ambiguous and sends the call back, so the checks-on arm will likely ask instead of answering and be graded `asked_when_should_answer`. Left as the writer wrote it, with no `also_accept`; the Week 6 report states this row openly.

## Day 33: the dry run

**A provider error that stopped the run twice.** With the checks on, dev-031 ("S&P Global revenue the year before last"), run 2, failed eight times over two resumes with the same upstream error from Groq, "Tool choice is none, but model called a tool": after the agent's step cap the model is asked to answer with `tool_choice: none`, and gpt-oss-20b kept emitting a tool call instead. The batch runner then stopped the whole run (its rule at the time), so the rule changed: a provider failure on one row is written as an error row and the run goes on; three in a row stop it. On the third resume the same row succeeded (temperature 0.6). For Week 6, when the prompt and the agent are open again: when the step cap stops the agent, send the request with no tools at all instead of `tool_choice: none`, so the provider cannot reject the reply.

**The search-year finding, and a check added after the freeze.** The review chat read the dry run's rows and found that on text questions that name no year the agent passed fiscal 2023 to `search_filings` in 124 of 159 calls, and the question's latest year in only 6. Verified from the rows and added to the report (the search-year table). The six non-December companies hold no 2023, which explains the Walmart, Copilot and CUDA abstains; other answers were two years stale. The fiscal-year check now runs on `search_filings` in the checks-on arm (no year named: the latest pinned year, as a repair), developed on the development sets only; the held-out set is untouched and unrun. The dry run was re-run with it, and the re-run's report is `eval/results/2026-11-12_dry-run-search-year.md` and the before and after are in `eval/results/2026-11-12_dry-run-before-after.md`.
