# Evaluation: dev_unanswerable, agent, checks off, 3 run(s) per question

Graded by the deterministic number grader (`filingcheck/eval/grade.py`). Written by `make eval`; the rows are in `2026-11-12_dev_unanswerable_agent-checks-off-search-year.jsonl`.

Mode: agent, checks off; model openrouter:openai/gpt-oss-20b, temperature 0.6, reasoning effort low, max_tokens 700; retriever hybrid, k 8, question text only, no filters

| Question | Answers | Correct | Year not stated | Other year's number | Wrong number | No number | Asked when it should have answered | Answered when it should have asked | Asked about another thing | Abstained | Answered (unanswerable) | Errors | Not graded | Correct, lenient clarify rule | Cost | Mean time |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| una-001 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 3 | 0 | 0 | 0 | 0 | $0.000770 | 1.7 s |
| una-002 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 3 | 0 | 0 | 0 | 0 | $0.001809 | 1.6 s |
| una-003 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 3 | 0 | 0 | 0 | 0 | $0.000378 | 0.4 s |
| una-004 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 3 | 0 | 0 | 0 | 0 | $0.002004 | 1.9 s |
| una-005 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 3 | 0 | 0 | 0 | 0 | $0.000748 | 0.9 s |
| una-006 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 3 | 0 | 0 | 0 | 0 | $0.001454 | 1.6 s |
| una-007 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 3 | 0 | 0 | 0 | 0 | $0.000754 | 1.4 s |
| una-008 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 3 | 0 | 0 | 0 | 0 | $0.001476 | 1.5 s |
| una-009 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 3 | 0 | 0 | 0 | 0 | $0.001784 | 2.6 s |
| una-010 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 3 | 0 | 0 | 0 | 0 | $0.001124 | 1.4 s |
| **All** | 30 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 30 | 0 | 0 | 0 | 0 | $0.012301 | 1.5 s |
