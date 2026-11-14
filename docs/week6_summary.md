# Week 6 summary

**What ran:** the pre-registered measurement, once, on 2026-11-14 from the tagged commit `week6-measured`: five arms (two baselines; the agent with the checks off, with the checks' rules written into its prompt, and with the checks on) over five question sets, 3 runs per question, 3,855 rows. The definitions (`eval/PREREGISTRATION.md`) were merged before the first final row. Every number is in the [full report](../eval/results/2026-11-14_final_report.md); details in the [week 6 notes](week6_notes.md).

**The prompt rules, first:** on the 110 held-out questions, the same rules written into the prompt were more accurate than the server-side checks (85.2% against 75.5%; -9.7 points, 95% interval -16.4 to -3.0) and level on confidently wrong answers (+3.3, -0.9 to +8.2), at about two and a half times the cost per question.

**The headline:** turning the checks on cut confidently wrong answers from 18.5% to 10.6% (-7.9 points, -12.7 to -3.6), so the pre-registered reduction is claimed; both held-out files point the same way. Development: -12.9 points (not pooled). Accuracy rose 4.2 points (-0.3 to +8.8). Control: no false repairs, accuracy +14.7.

**Before the run:** the held-out set grew to 112 questions (84 written by Gemini through its API); the prompt-rules arm was built from the checks' data (a reworded version 2 was withdrawn); the decline rule now reads the checks' own refusal wordings (re-grading every stored row changed 17 outcomes, none in the checks arms).

**The graders:** 30 text verdicts graded blind by Gemini and a reviewing AI session: 28 and 27 of 30 agree with the LLM grader. Of 90 failed checks-on runs read one by one, 20 came from gaps in the checks and 17 from a check's own action; the LLM grader wrongly failed five cited refusal answers.

**Changed after the results, marked:** the prompt-rules sentence judges accuracy as well as confidently wrong, as the pre-registration names both. The change goes against the checks.

**Known limits:** AI-written test questions; wide intervals; one model and one prompt; phrasings the checks miss; AI graders; tables not searchable.

**Cost:** about $2.09 billed for the week.
