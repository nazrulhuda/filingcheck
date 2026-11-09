# Evaluation: examples, agent, checks off, 3 run(s) per question

Graded by the deterministic number grader (`filingcheck/eval/grade.py`). Written by `make eval`; the rows are in `2026-11-09_examples_agent-checks-off.jsonl`.

Mode: agent, checks off; model openrouter:openai/gpt-oss-20b, temperature 0.6, reasoning effort low, max_tokens 700; retriever hybrid, k 8, question text only, no filters

| Question | Answers | Correct | Year not stated | Other year's number | Wrong number | No number | Asked when it should have answered | Answered when it should have asked | Abstained | Errors | Not graded | Cost | Mean time |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| trap-001 | 3 | 1 | 0 | 0 | 0 | 0 | 0 | 2 | 0 | 0 | 0 | $0.000590 | 0.9 s |
| trap-002 | 3 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | $0.000681 | 0.8 s |
| trap-003 | 3 | 0 | 0 | 2 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | $0.000553 | 0.7 s |
| trap-004 | 3 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | $0.000689 | 1.0 s |
| trap-005 | 3 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | $0.000324 | 0.4 s |
| control-001 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 3 | 0 | 0 | $0.000299 | 0.4 s |
| **All** | 18 | 10 | 0 | 2 | 0 | 0 | 1 | 2 | 3 | 0 | 0 | $0.003136 | 0.7 s |
