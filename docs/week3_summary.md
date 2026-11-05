# Week 3 summary

## The first graded rows

The 6 example questions (`eval/questions/examples.jsonl`), each asked 3 times in each mode:
- **How they were run:** batch mode, question text only, with no filters, on `openrouter:openai/gpt-oss-20b` (temperature 0.6, reasoning effort low, max_tokens 700).
- **How they were graded:** by the deterministic number grader (`filingcheck/eval/grade.py`).
- **Gold values:** the 4 number questions have one, filled from the facts table by `python -m filingcheck.eval gold`. The clarify question (trap-001) and the refuse question (trap-005) have none.

| Mode | Answers | Correct | Year not stated | Other year's number | Wrong number | Asked when it should have answered | Answered when it should have asked | Abstained | Errors | Cost |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| baseline (RAG) | 18 | 6 | 0 | 0 | 1 | 0 | 3 | 8 | 0 | $0.003137 |
| agent, no checks | 18 | 13 | 0 | 2 | 0 | 1 | 0 | 2 | 0 | $0.003583 |

**Six questions prove nothing.** These rows show only that the pipeline works end to end: questions, the batch runner, both modes, the grader and the summary.

**The agent's misses:**
- **"Last year" for Nvidia (trap-003):** twice it gave FY2025's net income, $72,880M, instead of FY2026's $120,067M. Once it asked which year was meant.
- **Coca-Cola (control-001):** it abstained twice without calling a tool.

**Why the agent's trap-001 counts as correct:** the keyword rules count an answer as correct when it asks or declines and gives no amount. In two of its three runs the agent gave the abstain sentence. In the third it asked which year was meant, assuming Morgan Stanley. The LLM grader in Week 5 judges what an answer asks.

**Sources:**
- the rows: `eval/results/2026-11-05_examples_baseline.jsonl` and `eval/results/2026-11-05_examples_agent.jsonl`;
- the tables: the `.md` files next to them.
- The rows were graded again after the grader fixes, with no new model calls.
