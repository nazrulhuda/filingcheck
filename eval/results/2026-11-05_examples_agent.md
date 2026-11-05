# Evaluation: examples, agent, 3 run(s) per question

Graded by the deterministic number grader (`filingcheck/eval/grade.py`). Written by `make eval`; the rows are in `2026-11-05_examples_agent.jsonl`.

Mode: agent; model openrouter:openai/gpt-oss-20b, temperature 0.6, reasoning effort low, max_tokens 700; retriever hybrid, k 8, question text only, no filters

| Question | Answers | Correct | Year not stated | Other year's number | Wrong number | No number | Asked when it should have answered | Answered when it should have asked | Abstained | Errors | Not graded | Cost | Mean time |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| trap-001 | 3 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | $0.000311 | 0.7 s |
| trap-002 | 3 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | $0.000688 | 1.8 s |
| trap-003 | 3 | 0 | 0 | 2 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | $0.000564 | 1.2 s |
| trap-004 | 3 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | $0.000699 | 2.1 s |
| trap-005 | 3 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | $0.000886 | 2.0 s |
| control-001 | 3 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 0 | 0 | $0.000434 | 1.0 s |
| **All** | 18 | 13 | 0 | 2 | 0 | 0 | 1 | 0 | 2 | 0 | 0 | $0.003583 | 1.4 s |
