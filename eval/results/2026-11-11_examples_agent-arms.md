# The two arms: examples, the agent with the checks off and on

Checks off: `2026-11-11_examples_agent-checks-off.jsonl`; checks on: `2026-11-11_examples_agent-checks-on.jsonl`; 3 run(s) per question. Graded by the deterministic number grader (`filingcheck/eval/grade.py`). Written by `make eval`.

**6 questions prove nothing about accuracy.** This page shows that the checks layer works and is logged; the measurement with intervals is Week 6's.

| Arm | Answers | Correct | Year not stated | Other year's number | Wrong number | No number | Asked when it should have answered | Answered when it should have asked | Abstained | Errors | Not graded | Cost | Mean time |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Checks off | 18 | 13 | 0 | 0 | 0 | 0 | 1 | 2 | 2 | 0 | 0 | $0.004217 | 0.7 s |
| Checks on | 18 | 16 | 0 | 0 | 0 | 1 | 1 | 0 | 0 | 0 | 0 | $0.003997 | 0.9 s |

## Each question

| Question | Checks off | Checks on | What the checks did | Outcomes differ |
|---|---|---|---|---|
| trap-001 | Correct x1, Answered when it should have asked x2 | Correct x3 | no fact call x2, company reject x1 | yes |
| trap-002 | Correct x3 | Correct x3 | pass x3 | no |
| trap-003 | Asked when it should have answered x1, Abstained x2 | Correct x2, Asked when it should have answered x1 | fiscal_year repair x2, no fact call x1 | yes |
| trap-004 | Correct x3 | Correct x2, No number x1 | no fact call x1, pass x2 | yes |
| trap-005 | Correct x3 | Correct x3 | no fact call x3 | no |
| control-001 | Correct x3 | Correct x3 | pass x3 | no |

Outcomes can differ from model variance alone; a check changed an answer only where "What the checks did" shows a repair or a reject.
