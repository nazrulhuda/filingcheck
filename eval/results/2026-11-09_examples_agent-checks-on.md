# Evaluation: examples, agent, checks on, 3 run(s) per question

Graded by the deterministic number grader (`filingcheck/eval/grade.py`). Written by `make eval`; the rows are in `2026-11-09_examples_agent-checks-on.jsonl`.

Mode: agent, checks on; model openrouter:openai/gpt-oss-20b, temperature 0.6, reasoning effort low, max_tokens 700; retriever hybrid, k 8, question text only, no filters

| Question | Answers | Correct | Year not stated | Other year's number | Wrong number | No number | Asked when it should have answered | Answered when it should have asked | Abstained | Errors | Not graded | Cost | Mean time |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| trap-001 | 3 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | $0.000556 | 0.8 s |
| trap-002 | 3 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | $0.000684 | 1.0 s |
| trap-003 | 3 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | $0.000705 | 1.3 s |
| trap-004 | 3 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | $0.000679 | 0.9 s |
| trap-005 | 3 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | $0.000858 | 1.3 s |
| control-001 | 3 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 0 | 0 | $0.000431 | 0.9 s |
| **All** | 18 | 16 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 0 | 0 | $0.003913 | 1.0 s |
