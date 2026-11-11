# Evaluation: examples, agent, checks off, 3 run(s) per question

Graded by the deterministic number grader (`filingcheck/eval/grade.py`). Written by `make eval`; the rows are in `2026-11-11_examples_agent-checks-off.jsonl`.

Mode: agent, checks off; model openrouter:openai/gpt-oss-20b, temperature 0.6, reasoning effort low, max_tokens 700; retriever hybrid, k 8, question text only, no filters

| Question | Answers | Correct | Year not stated | Other year's number | Wrong number | No number | Asked when it should have answered | Answered when it should have asked | Abstained | Errors | Not graded | Cost | Mean time |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| trap-001 | 3 | 1 | 0 | 0 | 0 | 0 | 0 | 2 | 0 | 0 | 0 | $0.000701 | 0.8 s |
| trap-002 | 3 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | $0.000817 | 0.8 s |
| trap-003 | 3 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 2 | 0 | 0 | $0.000632 | 0.4 s |
| trap-004 | 3 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | $0.000844 | 1.0 s |
| trap-005 | 3 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | $0.000400 | 0.4 s |
| control-001 | 3 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | $0.000823 | 0.8 s |
| **All** | 18 | 13 | 0 | 0 | 0 | 0 | 1 | 2 | 2 | 0 | 0 | $0.004217 | 0.7 s |
