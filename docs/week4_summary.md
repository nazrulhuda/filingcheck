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

**The prompt and the tool schemas are frozen until Week 6**, unless there is strong evidence of a problem. The prompt has not changed since Day 18. The tool schemas changed three times after it:
- The calculator's comma rule (#55).
- On 2026-11-10, both tools' ticker descriptions gained the company names, with dev probes and both arms re-run.
- On 2026-11-11, `search_filings` lost its `items` filter, with dev probes and both arms re-run.

## Open for the Week 5 grader round

`is_abstain` misses two wordings of "I can't find it": "I can't find this information…" and "I can't find any information in…". An answer worded that way is stored with `abstained: false`.
- The grader does not depend on it. For number questions it also uses its own decline rule, and for clarify and refuse questions it uses ask-or-decline. So it changed no Day 24 grade.
- Of the 144 stored rows of the example question sets, 2 have such an answer. Both are trap-005, the quarterly question, where declining is correct, and both were graded correct.

Three more findings from the 2026-11-11 search probes (`eval/probes/`), noted here and not fixed:
- **A text answer can be confidently unsupported, and no check covers it.** On "Why did Goldman narrow its focus in consumer banking?" the stored FY2023 filing mentions the narrowing but gives no reason, and the agent gave a reason (regulation, the Community Reinvestment Act) in all 6 runs, before and after the schema change. The checks only act on the arguments of `get_financial_fact`; nothing compares a text claim with the cited passage. The Day 26 page examples show the same thing on a smaller scale: Walmart's saved answer calls the swaps "10-year-old", which the filing does not say, next to a number that is right.
- **Giving up without searching.** 1 run before and 3 after (Walmart twice, UnitedHealth once) said they couldn't find the information and made no tool call at all.
- **A text question answered from the fact tool.** On "How did Converse revenues change?" some runs called `get_financial_fact` five times and never searched (2 before, 1 after).
- **A citation marker form the parser does not read.** In the Day 26 example refresh, 2 of 14 agent answers marked their source as `【1†number=1】` instead of `[1]`. The parser read `[1]` and `【1】` only, so both answers were stored with no citation at all, although the right passage had been retrieved. **Fixed in the Day 26 PR:** both parsers (API and page) now read past a dagger note, so `【1†number=1】` cites passage 1. No stored eval row has the marker, so no grade changes. The run 2 rows are in `eval/probes/`.

## Day 24: the two arms on the 6 example questions (current run: 2026-11-11)

**Six questions prove nothing about accuracy.** These runs show that the checks layer works and is logged; the measurement with intervals is Week 6's, on the full question sets.

**This is the current run.** Both arms were re-run on 2026-11-11, 3 runs per question, after `search_filings` lost its `items` filter (decisions, 2026-11-11). Same model, settings and frozen prompt as below. The page is `eval/results/2026-11-11_examples_agent-arms.md`.

| Arm | Answers | Correct | No number | Asked when it should have answered | Answered when it should have asked | Abstained | Cost | Mean time |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Checks off | 18 | 13 | 0 | 1 | 2 | 2 | $0.004217 | 0.7 s |
| Checks on | 18 | 16 | 1 | 1 | 0 | 0 | $0.003997 | 0.9 s |

| Question | Checks off | Checks on | What the checks did (3 runs) | Changed by a check? |
|---|---|---|---|---|
| trap-001 "How much net revenue did Morgan report last year?" | 1 correct under the lenient rule (it asked only which year), 2 answered with Morgan Stanley's figure | 3 correct: 1 asked which Morgan after a company reject, 2 correct under the lenient rule (they asked only which year, with no fact call) | company reject x1; 2 runs with no fact call | yes, in 1 run |
| trap-002 "What was Walmart's revenue for 2025?" | 3 correct | 3 correct | pass x3 | no |
| trap-003 "What was Nvidia's net income last year?" | 2 abstained after fetching fiscal 2023, which has no 10-K in the dataset; 1 asked which year | 2 correct; 1 asked which year, with no fact call | fiscal-year repair x2 (sent 2025 and 2023; used 2026); 1 run with no fact call | yes, in 2 runs |
| trap-004 "Give Microsoft's FY2025 total assets in millions." | 3 correct | 2 correct; 1 no number: with no fact call it said there was no FY2025 filing, which is wrong | pass x2; 1 run with no fact call | no |
| trap-005 "What was Goldman Sachs's quarterly net revenue in Q3 2025?" | 3 correct (declined) | 3 correct (declined) | not reached: no fact call | no |
| control-001 "What was Coca-Cola's net income in fiscal 2024?" | 3 correct | 3 correct | pass x3 | no |

**The gain from the checks shrank from five to three, and the checks did not cause the drop.** The checks-off arm is 13 of 18 again.
- The checks-on arm lost two answers in runs with no fact call: a question back about the year on trap-003, and on trap-004 a wrong claim that there is no FY2025 filing. A check cannot act when the model makes no call, the limit stated above.
- The three extra correct answers with the checks on all follow from a check's action: one company reject on trap-001 and two year repairs on trap-003.
- With the strict clarify rule, which does not count an answer that asks only which year, the count is 12 against 14.
- None of the six questions needs a text search. Eighteen runs per arm cannot tell whether the shorter search schema moved these two runs or whether it was the model's variance (temperature 0.6).

**Cost per question:** about $0.00023 with the checks off and $0.00022 with them on.

## Day 24, second run (2026-11-10, superseded)

Kept for the record; superseded by the 2026-11-11 run above because the search tool's schema changed.

Both arms were re-run on 2026-11-10, 3 runs per question, after one change to the tool schemas: both tools' ticker descriptions now list each ticker with its company's official name (decisions, 2026-11-10). Before it, the model often failed to find Coca-Cola among the bare tickers and abstained without a tool call, which handicapped both arms. The first run, of 2026-11-09, is kept below and in its files. Same model and settings (`openrouter:openai/gpt-oss-20b`, temperature 0.6, reasoning effort low, batch mode, question text only) and the same frozen prompt. The page is `eval/results/2026-11-10_examples_agent-arms.md`.

| Arm | Answers | Correct | Asked when it should have answered | Answered when it should have asked | Abstained | Cost | Mean time |
|---|---:|---:|---:|---:|---:|---:|---:|
| Checks off | 18 | 13 | 1 | 2 | 2 | $0.005199 | 2.2 s |
| Checks on | 18 | 18 | 0 | 0 | 0 | $0.005453 | 1.6 s |

| Question | Checks off | Checks on | What the checks did (3 runs) | Changed by a check? |
|---|---|---|---|---|
| trap-001 "How much net revenue did Morgan report last year?" | 1 correct under the lenient rule (it asked only which year), 2 answered with Morgan Stanley's figure | 3 correct: 2 asked which Morgan, 1 correct under the lenient rule (it asked only which year) | company reject x2 (the model then asked which Morgan); 1 run with no fact call | yes, in 2 runs |
| trap-002 "What was Walmart's revenue for 2025?" | 3 correct | 3 correct | pass x3 | no |
| trap-003 "What was Nvidia's net income last year?" | 2 abstained after fetching fiscal 2023, which has no 10-K in the dataset; 1 asked which year | 3 correct | fiscal-year repair x3 (sent 2023, 2023 and 2024; used 2026) | yes, in 3 runs |
| trap-004 "Give Microsoft's FY2025 total assets in millions." | 3 correct | 3 correct | pass x3 | no |
| trap-005 "What was Goldman Sachs's quarterly net revenue in Q3 2025?" | 3 correct (declined) | 3 correct (declined) | not reached: no fact call | no |
| control-001 "What was Coca-Cola's net income in fiscal 2024?" | 3 correct | 3 correct | pass x3 | no |

**The checks-off arm got better, and the gain from the checks shrank.** Coca-Cola's control question went from 0 of 3 to 3 of 3 with the checks off, because the model now finds KO; the checks had nothing to do with it. The five extra correct answers with the checks on all follow from a check's action: two company rejects on trap-001 and three year repairs on trap-003. With the strict clarify rule, which does not count an answer that asks only which year, the count is 12 against 17, the same gap of five. On the first run the gap was six, one of which was the control question's variance.

**Cost and time per arm**, for Week 6: about $0.00029 per question with the checks off and $0.00030 with them on, about $0.0001 more than on 2026-11-09 because the tool descriptions are longer (394 more prompt tokens per model call). The mean times, 2.2 s and 1.6 s against 0.7 s and 1.0 s on the first run, moved with the provider's load and are not a measure of the checks.

## Day 24, first run (2026-11-09, superseded)

Kept for the record; superseded by the 2026-11-10 and 2026-11-11 runs above because the tool schemas changed. **Six questions prove nothing about accuracy.**

Both arms were run fresh on 2026-11-09, 3 runs per question, with the same model and settings (`openrouter:openai/gpt-oss-20b`, temperature 0.6, batch mode, question text only), the same frozen prompt and the same tool schemas. Day 20's rows were not reused: the fact tool's results and the calculator's description have changed since then. The pages are `eval/results/2026-11-09_examples_agent-arms.md` and the two files it names.

| Arm | Answers | Correct | Other year's number | Asked when it should have answered | Answered when it should have asked | Abstained | Cost | Mean time |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Checks off | 18 | 10 | 2 | 1 | 2 | 3 | $0.003136 | 0.7 s |
| Checks on | 18 | 16 | 0 | 0 | 0 | 2 | $0.003913 | 1.0 s |

| Question | Checks off | Checks on | What the checks did (3 runs) | Changed by a check? |
|---|---|---|---|---|
| trap-001 "How much net revenue did Morgan report last year?" | 1 correct under the lenient rule (it asked only which year, not which Morgan), 2 answered with Morgan Stanley's figure | 3 correct: 2 asked which Morgan, 1 correct under the lenient rule (the abstain sentence) | company reject x2 (the model then asked which Morgan); 1 run with no fact call | yes, in 2 runs |
| trap-002 "What was Walmart's revenue for 2025?" | 3 correct | 3 correct | pass x3 | no |
| trap-003 "What was Nvidia's net income last year?" | 2 fiscal 2025's figure, 1 asked | 3 correct | fiscal-year repair x3 (sent 2025, 2025 and 2023; used 2026) | yes, in 3 runs |
| trap-004 "Give Microsoft's FY2025 total assets in millions." | 3 correct | 3 correct | pass x3 | no |
| trap-005 "What was Goldman Sachs's quarterly net revenue in Q3 2025?" | 3 correct (declined) | 3 correct (declined) | not reached: no fact call | no |
| control-001 "What was Coca-Cola's net income in fiscal 2024?" | 3 abstained, no tool call | 1 correct, 2 abstained | pass x1; 2 runs with no tool call | no: model variance |

Two of trap-001's correct runs, one in each arm, count as correct only under the lenient rule for clarify questions (decisions, 2026-11-04): an answer that asks only which year is meant, or gives the abstain sentence, is correct. With a strict rule, where a clarify answer must ask about the ambiguous thing (here, which Morgan), the count is 9 against 15, the same gap.

Of the six more correct answers, five follow from a check's action (two company rejects, three year repairs). The sixth is control-001, where no check acted: the model called the fact tool in one run and not in the others, as it did on Day 20 (1 of 3 correct). Every override is in the rows' `overrides` field.

**Cost and time per arm**, for Week 6: about $0.00017 per question with the checks off and $0.00022 with them on, and a mean of 0.7 s against 1.0 s. A reject costs one more model call, when the model reads the reason and answers.
