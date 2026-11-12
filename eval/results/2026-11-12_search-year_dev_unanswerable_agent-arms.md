# The two arms: dev_unanswerable, the agent with the checks off and on

Checks off: `2026-11-12_dev_unanswerable_agent-checks-off-search-year.jsonl`; checks on: `2026-11-12_dev_unanswerable_agent-checks-on-search-year.jsonl`; 3 run(s) per question. Graded by the deterministic number grader (`filingcheck/eval/grade.py`). Written by `make eval`.

**10 questions prove nothing about accuracy.** This page shows that the checks layer works and is logged; the measurement with intervals is Week 6's.

| Arm | Answers | Correct | Year not stated | Other year's number | Wrong number | No number | Asked when it should have answered | Answered when it should have asked | Asked about another thing | Abstained | Answered (unanswerable) | Errors | Not graded | Correct, lenient clarify rule | Cost | Mean time |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Checks off | 30 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 30 | 0 | 0 | 0 | 0 | $0.012301 | 1.5 s |
| Checks on | 30 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 25 | 5 | 0 | 0 | 0 | $0.012578 | 1.9 s |

## Each question

| Question | Checks off | Checks on | What the checks did | Outcomes differ |
|---|---|---|---|---|
| una-001 | Abstained x3 | Answered (unanswerable) x3 | fiscal_year repair x3 | yes |
| una-002 | Abstained x3 | Abstained x3 | fiscal_year reject + fiscal_year reject + fiscal_year reject x1, fiscal_year reject + fiscal_year reject x1, fiscal_year reject + fiscal_year reject + fiscal_year reject + fiscal_year reject + fiscal_year reject x1 | no |
| una-003 | Abstained x3 | Abstained x3 | no fact call x3 | no |
| una-004 | Abstained x3 | Abstained x3 | no fact call x2, pass x1 | no |
| una-005 | Abstained x3 | Abstained x3 | fiscal_year repair x1, no fact call x2 | no |
| una-006 | Abstained x3 | Abstained x3 | pass x2, fiscal_year repair x1 | no |
| una-007 | Abstained x3 | Abstained x3 | fiscal_year repair x3 | no |
| una-008 | Abstained x3 | Abstained x3 | fiscal_year repair x3 | no |
| una-009 | Abstained x3 | Abstained x1, Answered (unanswerable) x2 | fiscal_year repair x3 | yes |
| una-010 | Abstained x3 | Abstained x3 | fiscal_year repair x2, fiscal_year repair + fiscal_year repair x1 | no |

Outcomes can differ from model variance alone; a check changed an answer only where "What the checks did" shows a repair or a reject.
