# The two arms: dev_unanswerable, the agent with the checks off and on

Checks off: `2026-11-12_dev_unanswerable_agent-checks-off.jsonl`; checks on: `2026-11-12_dev_unanswerable_agent-checks-on.jsonl`; 3 run(s) per question. Graded by the deterministic number grader (`filingcheck/eval/grade.py`). Written by `make eval`.

**10 questions prove nothing about accuracy.** This page shows that the checks layer works and is logged; the measurement with intervals is Week 6's.

| Arm | Answers | Correct | Year not stated | Other year's number | Wrong number | No number | Asked when it should have answered | Answered when it should have asked | Asked about another thing | Abstained | Answered (unanswerable) | Errors | Not graded | Correct, lenient clarify rule | Cost | Mean time |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Checks off | 30 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 28 | 2 | 0 | 0 | 0 | $0.011557 | 1.5 s |
| Checks on | 30 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 29 | 1 | 0 | 0 | 0 | $0.011931 | 2.0 s |

## Each question

| Question | Checks off | Checks on | What the checks did | Outcomes differ |
|---|---|---|---|---|
| una-001 | Abstained x2, Answered (unanswerable) x1 | Abstained x3 | no fact call x3 | yes |
| una-002 | Abstained x3 | Abstained x3 | no fact call x3 | no |
| una-003 | Abstained x3 | Abstained x3 | no fact call x3 | no |
| una-004 | Abstained x3 | Abstained x3 | no fact call x3 | no |
| una-005 | Abstained x3 | Abstained x3 | no fact call x3 | no |
| una-006 | Abstained x3 | Abstained x3 | no fact call x3 | no |
| una-007 | Abstained x3 | Abstained x3 | no fact call x3 | no |
| una-008 | Abstained x3 | Abstained x3 | no fact call x3 | no |
| una-009 | Abstained x2, Answered (unanswerable) x1 | Abstained x2, Answered (unanswerable) x1 | no fact call x3 | no |
| una-010 | Abstained x3 | Abstained x3 | no fact call x3 | no |

Outcomes can differ from model variance alone; a check changed an answer only where "What the checks did" shows a repair or a reject.
