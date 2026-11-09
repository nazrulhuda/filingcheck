# Week 4 summary

The rest of this page comes with Days 24 to 27: the two graded rows with the checks off and on, the gate, the page switch and the costs. The limits below were written on Day 23, before the check rules were frozen.

## What the checks can and cannot do

The five checks compare the arguments the model sends to `get_financial_fact` with two things only: the words of the user's question and the SEC data the project holds (the company list, the pinned filings and their periods). They never read the model's reasoning and never guess at what the filings mean.

So they cannot act in three cases:
- **The question names no company.** "What was the revenue in 2025 for the company that makes the iPhone?" names no company, so the model's choice of company stands, right or wrong.
- **The model never calls the number tool.** A check runs on a tool call; when the model abstains or searches the text instead, as it did on Goldman's quarterly question in every run, the checks are not reached.
- **One sentence with two asks.** The metric and segment checks read the sentences about the call's metric; a single sentence that asks for a quarterly figure and an annual one is judged as one.

A repair rests on strong evidence only: a company named in the question, an explicit year, a date that is one of the company's fiscal year ends, a relative word ("last year"), or the page filter. A weak cue, such as a date after "compared to" or "reported on", changes nothing, because a wrong repair is a silent wrong answer while a missed one is not. A date that is no fiscal year end of the company ("the year ended December 31, 2025" for Walmart, "January 1 to June 30, 2025") is rejected with the company's real periods rather than moved to the nearest year.

The segment check knows the segment names each company reports. A phrase that is not one of them, such as "cloud revenue" for Microsoft or "ad revenue" for Amazon, passes, and the tool returns the company total under its own label.

**The rules were frozen on 2026-11-09, when Day 23 was merged**, like the agent's prompt on Day 18. A later change to a check means re-running both evaluation arms, with the checks off and on.
