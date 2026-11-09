# Week 4 summary

The rest of this page comes with Days 25 to 27: the gate, the page switch and the costs. The limits below were written on Day 23, before the check rules were frozen.

## What the checks can and cannot do

The five checks compare the arguments the model sends to `get_financial_fact` with two things only: the words of the user's question and the SEC data the project holds (the company list, the pinned filings and their periods). They never read the model's reasoning and never guess at what the filings mean.

So they cannot act in three cases:
- **The question names no company.** "What was the revenue in 2025 for the company that makes the iPhone?" names no company, so the model's choice of company stands, right or wrong.
- **The model never calls the number tool.** A check runs on a tool call; when the model abstains or searches the text instead, as it did on Goldman's quarterly question in every run, the checks are not reached.
- **One sentence with two asks.** The metric and segment checks read the sentences about the call's metric; a single sentence that asks for a quarterly figure and an annual one is judged as one.

A repair rests on strong evidence only: a company named in the question, an explicit year, a date that is one of the company's fiscal year ends, a relative word ("last year"), or the page filter. A weak cue, such as a date after "compared to" or "reported on", changes nothing, because a wrong repair is a silent wrong answer while a missed one is not. A date that is no fiscal year end of the company ("the year ended December 31, 2025" for Walmart, "January 1 to June 30, 2025") is rejected with the company's real periods rather than moved to the nearest year.

The segment check knows the segment names each company reports. A phrase that is not one of them, such as "cloud revenue" for Microsoft or "ad revenue" for Amazon, passes, and the tool returns the company total under its own label.

**The rules were frozen on 2026-11-09, when Day 23 was merged**, like the agent's prompt on Day 18. A later change to a check means re-running both evaluation arms, with the checks off and on.

## Day 24: the two arms on the 6 example questions

**Six questions prove nothing about accuracy.** These runs show that the checks layer works and is logged; the measurement with intervals is Week 6's, on the full question sets.

Both arms were run fresh on 2026-11-09, 3 runs per question, with the same model and settings (`openrouter:openai/gpt-oss-20b`, temperature 0.6, batch mode, question text only), the same frozen prompt and the same tool schemas. Day 20's rows were not reused: the fact tool's results and the calculator's description have changed since then. The pages are `eval/results/2026-11-09_examples_agent-arms.md` and the two files it names.

| Arm | Answers | Correct | Other year's number | Asked when it should have answered | Answered when it should have asked | Abstained | Cost | Mean time |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Checks off | 18 | 10 | 2 | 1 | 2 | 3 | $0.003136 | 0.7 s |
| Checks on | 18 | 16 | 0 | 0 | 0 | 2 | $0.003913 | 1.0 s |

| Question | Checks off | Checks on | What the checks did (3 runs) | Changed by the checks? |
|---|---|---|---|---|
| trap-001 "How much net revenue did Morgan report last year?" | 1 correct (asked), 2 answered with Morgan Stanley's figure | 3 correct | company reject x2 (the model then asked which Morgan); 1 run with no fact call (declined) | yes, in 2 runs |
| trap-002 "What was Walmart's revenue for 2025?" | 3 correct | 3 correct | pass x3 | no |
| trap-003 "What was Nvidia's net income last year?" | 2 fiscal 2025's figure, 1 asked | 3 correct | fiscal-year repair x3 (sent 2025, 2025 and 2023; used 2026) | yes, in 3 runs |
| trap-004 "Give Microsoft's FY2025 total assets in millions." | 3 correct | 3 correct | pass x3 | no |
| trap-005 "What was Goldman Sachs's quarterly net revenue in Q3 2025?" | 3 correct (declined) | 3 correct (declined) | not reached: no fact call | no |
| control-001 "What was Coca-Cola's net income in fiscal 2024?" | 3 abstained, no tool call | 1 correct, 2 abstained | pass x1; 2 runs with no tool call | no: model variance |

Of the six more correct answers, five follow from a check's action (two company rejects, three year repairs). The sixth is control-001, where no check acted: the model called the fact tool in one run and not in the others, as it did on Day 20 (1 of 3 correct). Every override is in the rows' `overrides` field.

**Cost and time per arm**, for Week 6: about $0.00017 per question with the checks off and $0.00022 with them on, and a mean of 0.7 s against 1.0 s. A reject costs one more model call, when the model reads the reason and answers.
