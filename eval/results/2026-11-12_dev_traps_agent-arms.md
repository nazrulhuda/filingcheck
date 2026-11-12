# The two arms: dev_traps, the agent with the checks off and on

Checks off: `2026-11-12_dev_traps_agent-checks-off.jsonl`; checks on: `2026-11-12_dev_traps_agent-checks-on.jsonl`; 3 run(s) per question. Graded by the deterministic number grader (`filingcheck/eval/grade.py`). Written by `make eval`.

**85 questions prove nothing about accuracy.** This page shows that the checks layer works and is logged; the measurement with intervals is Week 6's.

| Arm | Answers | Correct | Year not stated | Other year's number | Wrong number | No number | Asked when it should have answered | Answered when it should have asked | Asked about another thing | Abstained | Answered (unanswerable) | Errors | Not graded | Correct, lenient clarify rule | Cost | Mean time |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Checks off | 255 | 182 | 0 | 8 | 0 | 0 | 6 | 36 | 3 | 20 | 0 | 0 | 0 | 185 | $0.084365 | 1.1 s |
| Checks on | 255 | 219 | 0 | 1 | 1 | 0 | 8 | 13 | 3 | 10 | 0 | 0 | 0 | 222 | $0.079843 | 1.0 s |

## Each question

| Question | Checks off | Checks on | What the checks did | Outcomes differ |
|---|---|---|---|---|
| dev-001 | Answered when it should have asked x3 | Correct x3 | company reject x3 | yes |
| dev-002 | Correct x3 | Correct x3 | pass x3 | no |
| dev-003 | Answered when it should have asked x3 | Answered when it should have asked x3 | pass x3 | no |
| dev-004 | Correct x3 | Correct x1, Answered when it should have asked x2 | no fact call x1, pass x2 | yes |
| dev-005 | Correct x3 | Correct x3 | pass x3 | no |
| dev-006 | Correct x3 | Correct x3 | pass x3 | no |
| dev-007 | Answered when it should have asked x2, Asked about another thing x1 | Correct x1, Answered when it should have asked x2 | no fact call x1, fiscal_year repair x2 | yes |
| dev-008 | Correct x3 | Correct x3 | pass x3 | no |
| dev-009 | Correct x3 | Correct x3 | pass x3 | no |
| dev-010 | Correct x3 | Asked when it should have answered x3 | company reject x3 | yes |
| dev-011 | Answered when it should have asked x2, Asked about another thing x1 | Asked about another thing x3 | company repair x2, company repair + company repair x1 | yes |
| dev-012 | Correct x3 | Correct x3 | pass x3 | no |
| dev-013 | Correct x3 | Correct x3 | pass x3 | no |
| dev-014 | Answered when it should have asked x2, Asked about another thing x1 | Correct x3 | fiscal_year reject x3 | yes |
| dev-015 | Correct x3 | Correct x3 | pass x3 | no |
| dev-016 | Answered when it should have asked x3 | Answered when it should have asked x3 | pass x3 | no |
| dev-017 | Correct x3 | Correct x3 | pass x3 | no |
| dev-018 | Answered when it should have asked x3 | Correct x3 | fiscal_year reject x3 | yes |
| dev-019 | Correct x3 | Correct x1, Wrong number x1, Asked when it should have answered x1 | pass x2, no fact call x1 | yes |
| dev-020 | Correct x3 | Correct x3 | pass x3 | no |
| dev-021 | Correct x3 | Correct x3 | pass x3 | no |
| dev-022 | Answered when it should have asked x3 | Answered when it should have asked x3 | pass x3 | no |
| dev-023 | Correct x3 | Correct x3 | pass x3 | no |
| dev-024 | Correct x3 | Correct x3 | pass x3 | no |
| dev-025 | Correct x2, Answered when it should have asked x1 | Correct x3 | fiscal_year reject x3 | yes |
| dev-026 | Correct x2, Other year's number x1 | Correct x3 | pass x2, fiscal_year repair x1 | yes |
| dev-027 | Correct x2, Other year's number x1 | Correct x3 | fiscal_year repair x2, pass x1 | yes |
| dev-028 | Correct x2, Other year's number x1 | Correct x3 | fiscal_year repair x2, pass x1 | yes |
| dev-029 | Asked when it should have answered x1, Abstained x2 | Correct x3 | fiscal_year repair x3 | yes |
| dev-030 | Asked when it should have answered x1, Abstained x2 | Asked when it should have answered x1, Abstained x2 | fiscal_year repair + fiscal_year repair + fiscal_year repair x1, fiscal_year repair + fiscal_year repair x1, no fact call x1 | no |
| dev-031 | Other year's number x1, Abstained x2 | Other year's number x1, Asked when it should have answered x1, Abstained x1 | fiscal_year repair + fiscal_year repair + fiscal_year repair x1, fiscal_year repair + fiscal_year repair + fiscal_year repair + fiscal_year repair x1, no fact call x1 | yes |
| dev-032 | Correct x3 | Correct x3 | pass x1, fiscal_year repair x2 | no |
| dev-033 | Correct x1, Other year's number x2 | Correct x3 | fiscal_year repair x1, pass x2 | yes |
| dev-034 | Other year's number x1, Asked when it should have answered x1, Abstained x1 | Correct x2, Asked when it should have answered x1 | fiscal_year repair x2, no fact call x1 | yes |
| dev-035 | Other year's number x1, Asked when it should have answered x1, Abstained x1 | Correct x3 | pass x1, fiscal_year repair x2 | yes |
| dev-036 | Asked when it should have answered x1, Abstained x2 | Correct x1, Asked when it should have answered x1, Abstained x1 | no fact call x1, fiscal_year repair x1, fiscal_year repair + fiscal_year repair x1 | yes |
| dev-037 | Asked when it should have answered x1, Abstained x2 | Correct x3 | fiscal_year repair x3 | yes |
| dev-038 | Answered when it should have asked x3 | Correct x3 | fiscal_year reject x3 | yes |
| dev-039 | Correct x3 | Correct x3 | pass x3 | no |
| dev-040 | Correct x3 | Correct x3 | pass x3 | no |
| dev-041 | Correct x3 | Correct x3 | pass x3 | no |
| dev-042 | Correct x3 | Correct x3 | pass x3 | no |
| dev-043 | Correct x3 | Correct x3 | pass x3 | no |
| dev-044 | Correct x3 | Correct x3 | pass x3 | no |
| dev-045 | Correct x3 | Correct x3 | pass x3 | no |
| dev-046 | Correct x3 | Correct x3 | pass x3 | no |
| dev-047 | Correct x3 | Correct x3 | pass x3 | no |
| dev-048 | Correct x3 | Correct x3 | pass x3 | no |
| dev-049 | Correct x3 | Correct x3 | pass x3 | no |
| dev-050 | Correct x2, Answered when it should have asked x1 | Correct x3 | no fact call x2, segment reject x1 | yes |
| dev-051 | Correct x3 | Correct x3 | no fact call x2, segment reject x1 | no |
| dev-052 | Correct x3 | Correct x3 | segment reject x3 | no |
| dev-053 | Correct x3 | Correct x3 | pass x3 | no |
| dev-054 | Correct x1, Answered when it should have asked x2 | Correct x3 | segment reject x1, no fact call x2 | yes |
| dev-055 | Correct x3 | Correct x3 | pass x1, no fact call x2 | no |
| dev-056 | Correct x2, Abstained x1 | Correct x3 | no fact call x3 | yes |
| dev-057 | Correct x1, Abstained x2 | Abstained x3 | no fact call x1, segment reject x2 | yes |
| dev-058 | Correct x2, Abstained x1 | Correct x2, Abstained x1 | no fact call x2, segment reject x1 | no |
| dev-059 | Correct x3 | Correct x3 | pass x3 | no |
| dev-060 | Correct x3 | Correct x3 | pass x3 | no |
| dev-061 | Correct x3 | Correct x3 | no fact call x3 | no |
| dev-062 | Correct x3 | Correct x3 | no fact call x2, segment reject x1 | no |
| dev-063 | Correct x3 | Correct x3 | metric reject x1, no fact call x2 | no |
| dev-064 | Correct x3 | Correct x3 | no fact call x3 | no |
| dev-065 | Correct x3 | Correct x3 | no fact call x1, metric reject x2 | no |
| dev-066 | Correct x3 | Correct x3 | no fact call x3 | no |
| dev-067 | Correct x3 | Correct x3 | no fact call x3 | no |
| dev-068 | Correct x3 | Correct x3 | no fact call x3 | no |
| dev-069 | Correct x3 | Correct x3 | no fact call x3 | no |
| dev-070 | Correct x3 | Correct x3 | no fact call x3 | no |
| dev-071 | Correct x3 | Correct x3 | no fact call x3 | no |
| dev-072 | Correct x2, Answered when it should have asked x1 | Correct x3 | no fact call x3 | yes |
| dev-073 | Correct x2, Answered when it should have asked x1 | Correct x3 | no fact call x3 | yes |
| dev-074 | Correct x3 | Correct x3 | no fact call x3 | no |
| dev-075 | Correct x3 | Correct x3 | no fact call x3 | no |
| dev-076 | Correct x3 | Correct x3 | pass x3 | no |
| dev-077 | Answered when it should have asked x3 | Correct x3 | company reject x3 | yes |
| dev-078 | Correct x1, Abstained x2 | Correct x1, Abstained x2 | pass x3 | no |
| dev-079 | Correct x2, Abstained x1 | Correct x3 | pass x3 | yes |
| dev-080 | Correct x2, Abstained x1 | Correct x3 | pass x3 | yes |
| dev-081 | Correct x3 | Correct x3 | metric reject x1, no fact call x2 | no |
| dev-082 | Correct x3 | Correct x3 | no fact call x2, fiscal_year reject x1 | no |
| dev-083 | Correct x3 | Correct x3 | pass x3 | no |
| dev-084 | Correct x3 | Correct x3 | pass x3 | no |
| dev-085 | Answered when it should have asked x3 | Correct x3 | company reject x3 | yes |

Outcomes can differ from model variance alone; a check changed an answer only where "What the checks did" shows a repair or a reject.
