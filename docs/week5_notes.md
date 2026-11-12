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
