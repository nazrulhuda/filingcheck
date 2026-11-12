# The two arms: control, the agent with the checks off and on

Checks off: `2026-11-12_control_agent-checks-off.jsonl`; checks on: `2026-11-12_control_agent-checks-on.jsonl`; 3 run(s) per question. Graded by the deterministic number grader (`filingcheck/eval/grade.py`). Written by `make eval`.

**50 questions prove nothing about accuracy.** This page shows that the checks layer works and is logged; the measurement with intervals is Week 6's.

| Arm | Answers | Correct | Year not stated | Other year's number | Wrong number | No number | Asked when it should have answered | Answered when it should have asked | Asked about another thing | Abstained | Answered (unanswerable) | Errors | Not graded | Correct, lenient clarify rule | Cost | Mean time |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Checks off | 150 | 79 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 19 | 0 | 0 | 51 | 79 | $0.050393 | 1.1 s |
| Checks on | 150 | 80 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 21 | 0 | 0 | 48 | 80 | $0.054110 | 1.2 s |

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
| control-121 | Correct x1, Abstained x2 | Correct x2, Abstained x1 | pass x2, no fact call x1 | yes |
| control-122 | Abstained x3 | Abstained x3 | no fact call x3 | no |
| control-123 | Correct x3 | Correct x3 | pass x3 | no |
| control-124 | Correct x3 | Correct x3 | pass x3 | no |
| control-125 | Correct x3 | Correct x3 | pass x3 | no |
| control-126 | Correct x3 | Correct x3 | pass x3 | no |
| control-127 | Correct x3 | Correct x3 | pass x3 | no |
| control-128 | Correct x3 | Correct x3 | pass x3 | no |
| control-129 | Not graded x3 | Not graded x3 | no fact call x3 | no |
| control-130 | Not graded x3 | Not graded x3 | no fact call x3 | no |
| control-131 | Abstained x3 | Abstained x3 | no fact call x3 | no |
| control-132 | Not graded x3 | Not graded x3 | no fact call x3 | no |
| control-133 | Not graded x3 | Not graded x3 | no fact call x3 | no |
| control-134 | Wrong number x1, Abstained x2 | Wrong number x1, Abstained x2 | no fact call x3 | no |
| control-135 | Not graded x3 | Not graded x3 | no fact call x3 | no |
| control-136 | Not graded x3 | Not graded x3 | no fact call x3 | no |
| control-137 | Abstained x2, Not graded x1 | Abstained x2, Not graded x1 | no fact call x3 | no |
| control-138 | Not graded x3 | Not graded x3 | no fact call x3 | no |
| control-139 | Abstained x2, Not graded x1 | Abstained x2, Not graded x1 | no fact call x3 | no |
| control-140 | Not graded x3 | Not graded x3 | no fact call x3 | no |
| control-141 | Abstained x3 | Abstained x3 | no fact call x3 | no |
| control-142 | Abstained x2, Not graded x1 | Abstained x3 | no fact call x3 | yes |
| control-143 | Not graded x3 | Not graded x3 | no fact call x3 | no |
| control-144 | Not graded x3 | Not graded x3 | no fact call x3 | no |
| control-145 | Not graded x3 | Not graded x3 | no fact call x3 | no |
| control-146 | Not graded x3 | Not graded x3 | no fact call x3 | no |
| control-147 | Not graded x3 | Not graded x3 | no fact call x3 | no |
| control-148 | Not graded x3 | Not graded x3 | no fact call x3 | no |
| control-149 | Not graded x3 | Not graded x3 | no fact call x3 | no |
| control-150 | Not graded x3 | Abstained x2, Not graded x1 | no fact call x3 | yes |

Outcomes can differ from model variance alone; a check changed an answer only where "What the checks did" shows a repair or a reject.
