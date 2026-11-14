# Probe: refusals failed for their wording only (Day 39, development rows)

Written by `uv run python eval/probes/2026-11-14_decline-wording.py`. The prompt-rules block (version 1) tells the model to reply in the checks' reason words ("say it is not one of the 25 companies in the dataset"; "each is not one of the 13 metrics the data holds; say so"). The deterministic grader's decline phrases (`DECLINE_RE`, frozen) do not include "is not one of the", so such a refusal with no amount is graded `answered_when_should_ask`, which counts as confidently wrong. The what-if columns count those runs correct and not confidently wrong; **the grader does not change, and the what-if is not a result.**

| Set | Arm | Refuse runs failed for the wording only | By question |
|---|---|---:|---|
| dev_traps | agent-checks-off | 0 | - |
| dev_traps | agent-checks-on | 0 | - |
| dev_traps | agent-prompt-rules | 12 | dev-003 x1, dev-004 x3, dev-066 x1, dev-067 x3, dev-068 x3, dev-069 x1 |
| control | agent-checks-off | 0 | - |
| control | agent-checks-on | 0 | - |
| control | agent-prompt-rules | 0 | - |

Of the 12 runs, counted confidently wrong as graded: 12.

| Set | Arm | Accuracy, as graded | Confidently wrong, as graded | Accuracy, what-if | Confidently wrong, what-if |
|---|---|---:|---:|---:|---:|
| dev_traps | agent-checks-off | 69.4% | 18.0% | 69.4% | 18.0% |
| dev_traps | agent-checks-on | 83.5% | 7.1% | 83.5% | 7.1% |
| dev_traps | agent-prompt-rules | 78.4% | 13.3% | 83.1% | 8.6% |
| control | agent-checks-off | 75.3% | 4.7% | 75.3% | 4.7% |
| control | agent-checks-on | 88.0% | 0.0% | 88.0% | 0.0% |
| control | agent-prompt-rules | 81.3% | 2.7% | 81.3% | 2.7% |
