# The two arms: dev_traps, the agent with the checks off and on

Checks off: `2026-11-12_dev_traps_agent-checks-off-search-year.jsonl`; checks on: `2026-11-12_dev_traps_agent-checks-on-search-year.jsonl`; 3 run(s) per question. Graded by the deterministic number grader (`filingcheck/eval/grade.py`). Written by `make eval`.

**85 questions prove nothing about accuracy.** This page shows that the checks layer works and is logged; the measurement with intervals is Week 6's.

| Arm | Answers | Correct | Year not stated | Other year's number | Wrong number | No number | Asked when it should have answered | Answered when it should have asked | Asked about another thing | Abstained | Answered (unanswerable) | Errors | Not graded | Correct, lenient clarify rule | Cost | Mean time |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Checks off | 255 | 177 | 0 | 8 | 1 | 1 | 6 | 37 | 1 | 23 | 0 | 1 | 0 | 178 | $0.077100 | 16.7 s |
| Checks on | 255 | 213 | 0 | 1 | 1 | 0 | 5 | 17 | 4 | 14 | 0 | 0 | 0 | 217 | $0.081351 | 16.7 s |

## Each question

| Question | Checks off | Checks on | What the checks did | Outcomes differ |
|---|---|---|---|---|
| dev-001 | Answered when it should have asked x3 | Correct x3 | company reject x3 | yes |
| dev-002 | Correct x3 | Correct x3 | pass x3 | no |
| dev-003 | Answered when it should have asked x3 | Answered when it should have asked x3 | pass x3 | no |
| dev-004 | Correct x2, Answered when it should have asked x1 | Correct x2, Answered when it should have asked x1 | no fact call x3 | no |
| dev-005 | Correct x3 | Correct x3 | pass x3 | no |
| dev-006 | Correct x3 | Correct x3 | pass x3 | no |
| dev-007 | Correct x1, Answered when it should have asked x2 | Answered when it should have asked x3 | fiscal_year repair x3 | yes |
| dev-008 | Correct x3 | Correct x3 | pass x3 | no |
| dev-009 | Correct x3 | Correct x3 | pass x3 | no |
| dev-010 | Correct x3 | Asked when it should have answered x3 | company reject x2, company reject + company reject x1 | yes |
| dev-011 | Answered when it should have asked x3 | Asked about another thing x3 | company repair + company repair x1, company repair x1, company repair + fiscal_year repair + company repair x1 | yes |
| dev-012 | Correct x3 | Correct x3 | pass x3 | no |
| dev-013 | Correct x3 | Correct x3 | pass x3 | no |
| dev-014 | Answered when it should have asked x2, Asked about another thing x1 | Correct x2, Answered when it should have asked x1 | fiscal_year reject x3 | yes |
| dev-015 | Correct x3 | Correct x3 | pass x3 | no |
| dev-016 | Answered when it should have asked x3 | Answered when it should have asked x3 | pass x3 | no |
| dev-017 | Correct x3 | Correct x3 | pass x3 | no |
| dev-018 | Answered when it should have asked x3 | Correct x2, Answered when it should have asked x1 | fiscal_year reject x3 | yes |
| dev-019 | Correct x2, Wrong number x1 | Correct x2, Wrong number x1 | pass x3 | no |
| dev-020 | Correct x3 | Correct x3 | pass x3 | no |
| dev-021 | Correct x3 | Correct x3 | pass x3 | no |
| dev-022 | Answered when it should have asked x3 | Answered when it should have asked x2, Asked about another thing x1 | pass x3 | yes |
| dev-023 | Correct x3 | Correct x3 | pass x3 | no |
| dev-024 | Correct x3 | Correct x3 | pass x3 | no |
| dev-025 | Correct x1, Answered when it should have asked x2 | Correct x2, Answered when it should have asked x1 | no fact call x2, fiscal_year reject x1 | yes |
| dev-026 | Correct x1, Other year's number x2 | Correct x3 | fiscal_year repair x2, pass x1 | yes |
| dev-027 | Correct x2, Other year's number x1 | Correct x3 | pass x3 | yes |
| dev-028 | Correct x3 | Correct x3 | pass x1, fiscal_year repair x2 | no |
| dev-029 | Asked when it should have answered x1, Abstained x2 | Correct x3 | fiscal_year repair x3 | yes |
| dev-030 | Asked when it should have answered x3 | Asked when it should have answered x1, Abstained x2 | fiscal_year repair x1, fiscal_year repair + fiscal_year repair + fiscal_year repair + fiscal_year repair x1, no fact call x1 | yes |
| dev-031 | No number x1, Abstained x2 | Other year's number x1, Abstained x2 | fiscal_year repair + fiscal_year repair + fiscal_year repair + fiscal_year repair + fiscal_year repair x1, fiscal_year repair + fiscal_year repair + fiscal_year repair x1, fiscal_year repair x1 | yes |
| dev-032 | Correct x3 | Correct x3 | fiscal_year repair x2, pass x1 | no |
| dev-033 | Correct x1, Other year's number x2 | Correct x3 | pass x2, fiscal_year repair x1 | yes |
| dev-034 | Other year's number x2, Abstained x1 | Correct x3 | fiscal_year repair x3 | yes |
| dev-035 | Other year's number x1, Abstained x2 | Correct x3 | fiscal_year repair x3 | yes |
| dev-036 | Asked when it should have answered x2, Abstained x1 | Correct x1, Asked when it should have answered x1, Abstained x1 | fiscal_year repair + fiscal_year repair + fiscal_year repair + fiscal_year repair x1, fiscal_year repair x1, no fact call x1 | yes |
| dev-037 | Abstained x3 | Correct x3 | fiscal_year repair x3 | yes |
| dev-038 | Answered when it should have asked x3 | Correct x3 | fiscal_year reject x3 | yes |
| dev-039 | Correct x3 | Correct x3 | pass x3 | no |
| dev-040 | Correct x2, Errors x1 | Correct x3 | pass x3 | yes |
| dev-041 | Correct x3 | Correct x3 | pass x3 | no |
| dev-042 | Correct x3 | Correct x3 | pass x3 | no |
| dev-043 | Correct x3 | Correct x3 | pass x3 | no |
| dev-044 | Correct x3 | Correct x3 | pass x3 | no |
| dev-045 | Correct x3 | Correct x3 | pass x3 | no |
| dev-046 | Correct x3 | Correct x3 | pass x3 | no |
| dev-047 | Correct x3 | Correct x3 | pass x3 | no |
| dev-048 | Correct x3 | Correct x3 | pass x3 | no |
| dev-049 | Correct x3 | Correct x3 | pass x3 | no |
| dev-050 | Correct x3 | Correct x3 | no fact call x1, segment reject x2 | no |
| dev-051 | Correct x1, Answered when it should have asked x2 | Correct x3 | pass x1, segment reject x2 | yes |
| dev-052 | Correct x3 | Correct x3 | no fact call x2, segment reject x1 | no |
| dev-053 | Correct x3 | Correct x3 | pass x3 | no |
| dev-054 | Correct x3 | Correct x3 | no fact call x2, segment reject x1 | no |
| dev-055 | Correct x3 | Correct x3 | pass x3 | no |
| dev-056 | Correct x1, Abstained x2 | Correct x1, Abstained x2 | no fact call x2, pass x1 | no |
| dev-057 | Abstained x3 | Abstained x3 | no fact call x2, company repair + segment reject x1 | no |
| dev-058 | Correct x3 | Correct x2, Abstained x1 | no fact call x1, pass x2 | yes |
| dev-059 | Correct x3 | Correct x3 | pass x3 | no |
| dev-060 | Correct x3 | Correct x3 | pass x3 | no |
| dev-061 | Correct x3 | Correct x3 | pass x3 | no |
| dev-062 | Correct x3 | Correct x3 | segment reject x3 | no |
| dev-063 | Correct x3 | Correct x3 | pass x1, metric reject x1, no fact call x1 | no |
| dev-064 | Correct x3 | Correct x3 | no fact call x2, metric reject x1 | no |
| dev-065 | Correct x3 | Correct x3 | pass x1, no fact call x2 | no |
| dev-066 | Correct x3 | Correct x3 | fiscal_year repair + fiscal_year repair x1, no fact call x2 | no |
| dev-067 | Correct x3 | Correct x3 | no fact call x3 | no |
| dev-068 | Correct x3 | Correct x3 | no fact call x3 | no |
| dev-069 | Correct x3 | Correct x3 | no fact call x3 | no |
| dev-070 | Correct x3 | Correct x3 | no fact call x2, pass x1 | no |
| dev-071 | Correct x3 | Correct x3 | fiscal_year repair x2, pass x1 | no |
| dev-072 | Correct x3 | Correct x2, Answered when it should have asked x1 | fiscal_year repair x1, no fact call x2 | yes |
| dev-073 | Correct x3 | Correct x3 | no fact call x2, metric reject + metric reject + retry reject + retry reject x1 | no |
| dev-074 | Correct x3 | Correct x3 | pass x2, no fact call x1 | no |
| dev-075 | Correct x3 | Correct x3 | no fact call x2, pass x1 | no |
| dev-076 | Correct x1, Abstained x2 | Correct x2, Abstained x1 | pass x2, no fact call x1 | yes |
| dev-077 | Answered when it should have asked x3 | Correct x3 | company reject x3 | yes |
| dev-078 | Correct x1, Abstained x2 | Correct x1, Abstained x2 | pass x2, no fact call x1 | no |
| dev-079 | Correct x3 | Correct x3 | pass x3 | no |
| dev-080 | Abstained x3 | Correct x3 | pass x3 | yes |
| dev-081 | Correct x2, Answered when it should have asked x1 | Correct x2, Answered when it should have asked x1 | no fact call x3 | no |
| dev-082 | Correct x3 | Correct x3 | no fact call x2, fiscal_year reject x1 | no |
| dev-083 | Correct x3 | Correct x3 | pass x3 | no |
| dev-084 | Correct x3 | Correct x3 | pass x3 | no |
| dev-085 | Answered when it should have asked x3 | Correct x3 | company reject x3 | yes |

Outcomes can differ from model variance alone; a check changed an answer only where "What the checks did" shows a repair or a reject.
