# The two arms: control, the agent with the checks off and on

Checks off: `2026-11-12_control_agent-checks-off-search-year.jsonl`; checks on: `2026-11-12_control_agent-checks-on-search-year.jsonl`; 3 run(s) per question. Graded by the deterministic number grader (`filingcheck/eval/grade.py`). Written by `make eval`.

**50 questions prove nothing about accuracy.** This page shows that the checks layer works and is logged; the measurement with intervals is Week 6's.

| Arm | Answers | Correct | Year not stated | Other year's number | Wrong number | No number | Asked when it should have answered | Answered when it should have asked | Asked about another thing | Abstained | Answered (unanswerable) | Errors | Not graded | Correct, lenient clarify rule | Cost | Mean time |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Checks off | 150 | 80 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 19 | 0 | 0 | 51 | 80 | $0.051142 | 1.1 s |
| Checks on | 150 | 79 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 12 | 0 | 0 | 59 | 79 | $0.060253 | 1.1 s |

## Each question

| Question | Checks off | Checks on | What the checks did | Outcomes differ |
|---|---|---|---|---|
| control-101 | Correct x3 | Correct x3 | pass x3 | no |
| control-102 | Correct x3 | Correct x3 | pass x3 | no |
| control-103 | Correct x3 | Correct x3 | pass x3 | no |
| control-104 | Correct x3 | Correct x3 | pass x3 | no |
| control-105 | Correct x3 | Correct x3 | pass x3 | no |
| control-106 | Correct x3 | Correct x3 | pass x3 | no |
| control-107 | Correct x3 | Correct x3 | pass x3 | no |
| control-108 | Correct x3 | Correct x3 | pass x3 | no |
| control-109 | Correct x3 | Correct x3 | pass x3 | no |
| control-110 | Correct x3 | Correct x3 | pass x3 | no |
| control-111 | Correct x3 | Correct x3 | pass x3 | no |
| control-112 | Correct x3 | Correct x3 | pass x3 | no |
| control-113 | Correct x3 | Correct x3 | pass x3 | no |
| control-114 | Correct x3 | Correct x3 | pass x3 | no |
| control-115 | Correct x3 | Correct x3 | pass x3 | no |
| control-116 | Correct x3 | Correct x3 | pass x3 | no |
| control-117 | Correct x3 | Correct x3 | pass x3 | no |
| control-118 | Correct x3 | Correct x3 | pass x3 | no |
| control-119 | Correct x3 | Correct x3 | pass x3 | no |
| control-120 | Correct x3 | Correct x3 | pass x3 | no |
| control-121 | Correct x2, Abstained x1 | Correct x1, Abstained x2 | pass x1, no fact call x2 | yes |
| control-122 | Abstained x3 | Abstained x3 | no fact call x3 | no |
| control-123 | Correct x3 | Correct x3 | pass x3 | no |
| control-124 | Correct x3 | Correct x3 | pass x3 | no |
| control-125 | Correct x3 | Correct x3 | pass x3 | no |
| control-126 | Correct x3 | Correct x3 | pass x3 | no |
| control-127 | Correct x3 | Correct x3 | pass x3 | no |
| control-128 | Correct x3 | Correct x3 | pass x3 | no |
| control-129 | Not graded x3 | Not graded x3 | fiscal_year repair x3 | no |
| control-130 | Not graded x3 | Not graded x3 | fiscal_year repair + fiscal_year repair + fiscal_year repair x1, fiscal_year repair x2 | no |
| control-131 | Abstained x3 | Abstained x1, Not graded x2 | fiscal_year repair x3 | yes |
| control-132 | Not graded x3 | Not graded x3 | fiscal_year repair x3 | no |
| control-133 | Not graded x3 | Not graded x3 | fiscal_year repair x3 | no |
| control-134 | Abstained x3 | Abstained x3 | fiscal_year repair x3 | no |
| control-135 | Not graded x3 | Not graded x3 | fiscal_year repair x3 | no |
| control-136 | Not graded x3 | Not graded x3 | fiscal_year repair x3 | no |
| control-137 | Abstained x2, Not graded x1 | Abstained x1, Not graded x2 | fiscal_year repair x3 | yes |
| control-138 | Not graded x3 | Not graded x3 | fiscal_year repair x3 | no |
| control-139 | Abstained x1, Not graded x2 | Not graded x3 | fiscal_year repair x3 | yes |
| control-140 | Not graded x3 | Not graded x3 | fiscal_year repair x3 | no |
| control-141 | Abstained x2, Not graded x1 | Not graded x3 | fiscal_year repair x3 | yes |
| control-142 | Abstained x3 | Not graded x3 | fiscal_year repair x3 | yes |
| control-143 | Not graded x3 | Not graded x3 | fiscal_year repair x3 | no |
| control-144 | Not graded x3 | Abstained x2, Not graded x1 | fiscal_year repair x3 | yes |
| control-145 | Not graded x3 | Not graded x3 | fiscal_year repair x3 | no |
| control-146 | Abstained x1, Not graded x2 | Not graded x3 | pass x3 | yes |
| control-147 | Not graded x3 | Not graded x3 | fiscal_year repair x3 | no |
| control-148 | Not graded x3 | Not graded x3 | fiscal_year repair x3 | no |
| control-149 | Not graded x3 | Not graded x3 | fiscal_year repair x3 | no |
| control-150 | Not graded x3 | Not graded x3 | fiscal_year repair x3 | no |

Outcomes can differ from model variance alone; a check changed an answer only where "What the checks did" shows a repair or a reject.
