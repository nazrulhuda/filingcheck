# Re-grade after the decline fix (Day 39 review)

Every stored row in `eval/results/` graded with the current question files, by the deterministic grader with the decline rule before the fix and after it (`filingcheck/eval/regrade.py`); the new grades are in this folder, one file per results file. No stored row is edited.

17 outcome(s) change, in 17 of 2694 row(s), 24 file(s). Rows whose question is no longer in its file: 0. Stored grades that differ from the grade before the fix (older grader or question changes, not this fix): 10.

| File | Question | Run | Before | After | Answer |
|---|---|---:|---|---|---|
| 2026-11-14_control_agent-prompt-rules.jsonl | control-122 | 2 | no_number | abstained | I’m sorry, but “revenue net of interest expense” is not one of the 13 metrics that the 10‑K data holds. The available metrics are revenue, n |
| 2026-11-14_dev_traps_agent-prompt-rules-v2.jsonl | dev-004 | 1 | answered_when_should_ask | correct | I’m sorry, but Capital Group is not one of the 25 companies in the dataset. |
| 2026-11-14_dev_traps_agent-prompt-rules-v2.jsonl | dev-065 | 1 | answered_when_should_ask | correct | I’m sorry, but EBITDA is not one of the 13 metrics available in the 10‑K data set. The tool can only provide figures for revenue, net income |
| 2026-11-14_dev_traps_agent-prompt-rules-v2.jsonl | dev-068 | 2 | answered_when_should_ask | correct | I’m sorry, but Visa is not one of the 25 companies in the dataset. |
| 2026-11-14_dev_traps_agent-prompt-rules-v2.jsonl | dev-003 | 3 | answered_when_should_ask | correct | I’m sorry, but Citizens is not one of the 25 companies in the dataset I have. |
| 2026-11-14_dev_traps_agent-prompt-rules-v2.jsonl | dev-004 | 3 | answered_when_should_ask | correct | I’m sorry, but Capital Group is not one of the 25 companies in the dataset. |
| 2026-11-14_dev_traps_agent-prompt-rules-v2.jsonl | dev-068 | 3 | answered_when_should_ask | correct | I’m sorry, but Visa is not one of the 25 companies in the dataset. |
| 2026-11-14_dev_traps_agent-prompt-rules.jsonl | dev-004 | 1 | answered_when_should_ask | correct | Capital Group is not one of the 25 companies in the dataset. |
| 2026-11-14_dev_traps_agent-prompt-rules.jsonl | dev-067 | 1 | answered_when_should_ask | correct | I’m sorry, but Tesla is not one of the 25 companies in the dataset. |
| 2026-11-14_dev_traps_agent-prompt-rules.jsonl | dev-068 | 1 | answered_when_should_ask | correct | I’m sorry, but Visa is not one of the 25 companies in the dataset. |
| 2026-11-14_dev_traps_agent-prompt-rules.jsonl | dev-003 | 2 | answered_when_should_ask | correct | I’m sorry, but Citizens is not one of the 25 companies in the dataset. |
| 2026-11-14_dev_traps_agent-prompt-rules.jsonl | dev-004 | 2 | answered_when_should_ask | correct | I’m sorry, but Capital Group is not one of the 25 companies in the dataset. |
| 2026-11-14_dev_traps_agent-prompt-rules.jsonl | dev-067 | 2 | answered_when_should_ask | correct | I’m sorry, but Tesla is not one of the 25 companies in the dataset. |
| 2026-11-14_dev_traps_agent-prompt-rules.jsonl | dev-068 | 2 | answered_when_should_ask | correct | Visa is not one of the 25 companies in the dataset. |
| 2026-11-14_dev_traps_agent-prompt-rules.jsonl | dev-004 | 3 | answered_when_should_ask | correct | I’m sorry, but Capital Group is not one of the 25 companies in the dataset. |
| 2026-11-14_dev_traps_agent-prompt-rules.jsonl | dev-067 | 3 | answered_when_should_ask | correct | I’m sorry, but Tesla is not one of the 25 companies in the dataset. |
| 2026-11-14_dev_traps_agent-prompt-rules.jsonl | dev-068 | 3 | answered_when_should_ask | correct | Visa is not one of the 25 companies in the dataset. |
