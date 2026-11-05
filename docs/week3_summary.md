# Week 3 summary

## The first graded rows

The 6 example questions (`eval/questions/examples.jsonl`), each asked 3 times in each mode:
- **How they were run:** batch mode, question text only, with no filters, on `openrouter:openai/gpt-oss-20b` (temperature 0.6, reasoning effort low, max_tokens 700).
- **How they were graded:** by the deterministic number grader (`filingcheck/eval/grade.py`).
- **Gold values:** 5 of the 6 questions have one, filled from the facts table by `python -m filingcheck.eval gold`. trap-001 is ambiguous on purpose and has none.

| Mode | Answers | Correct | Wrong number | Wrong year | Answered when it should have asked | Abstained | Errors | Cost |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| baseline (RAG) | 18 | 6 | 1 | 0 | 3 | 8 | 0 | $0.003137 |
| agent, no checks | 18 | 13 | 3 | 0 | 0 | 2 | 0 | $0.003583 |

**Six questions prove nothing.** These rows show only that the pipeline works end to end: questions, the batch runner, both modes, the grader and the summary.

**Why the agent's trap-001 counts as correct:** the keyword rules count an answer as correct when it asks or declines and gives no number. In two of its three runs the agent gave the abstain sentence. In the third it asked which year was meant, assuming Morgan Stanley. The LLM grader in Week 5 judges what an answer asks.

**Sources:**
- the rows: `eval/results/2026-11-05_examples_baseline.jsonl` and `eval/results/2026-11-05_examples_agent.jsonl`;
- the tables: the `.md` files next to them.
