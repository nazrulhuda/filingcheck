# The step-cap change, checked live (2026-11-13)

The 8 runs of the Week 5 search-year re-run that stopped at the model-call cap (7 with the checks on), each question asked 3 more times in the same arm with the change then on the branch: past the cap, the final request carried no tools instead of `tool_choice: none`. The change was reverted after this check (docs/decisions.md, 2026-11-13). Rows: `eval/probes/2026-11-13_step-cap-check_*.jsonl`. Written by `eval/step_cap_check.py`.

## The old runs

| Arm | Question | Run | Ended by | Error | Deterministic | Answer |
|---|---|---:|---|---|---|---|
| agent-checks-on | dev-031 | 1 | model_calls | none | abstained | I can't find this in the filings I have. |
| agent-checks-on | dev-053 | 2 | model_calls | none | correct | I can't find this in the filings I have. |
| agent-checks-on | dev-073 | 3 | model_calls | none | correct | I can’t find free cash flow in the filings I have. |
| agent-checks-on | una-002 | 3 | model_calls | none | abstained | I can't find this in the filings I have. |
| agent-checks-off | control-139 | 3 | model_calls | none | not_graded | Capital One closed its deal for Discover on **February 19, 2024**【2†L2-L4】. |
| agent-checks-on | control-131 | 1 | model_calls | none | not_graded | Nike’s corporate headquarters is located at One Bowerman Drive, Beaverton, Oregon 97005‑6453【12】. |
| agent-checks-on | control-131 | 2 | model_calls | none | not_graded | Nike, Inc. is headquartered in Beaverton, Oregon, United States【13】. |
| agent-checks-on | control-134 | 2 | model_calls | none | abstained | I can't find this in the filings I have. |

## The new runs

| Arm | Question | Run | Ended by | Error | Deterministic | LLM (text) | Answer |
|---|---|---:|---|---|---|---|---|
| agent-checks-off | control-139 | 1 | answer | none | abstained | abstained | I can’t find a specific closing date for the Capital One – Discover transaction in the filings I have. |
| agent-checks-off | control-139 | 2 | answer | none | abstained | abstained | I can't find this in the filings I have. |
| agent-checks-off | control-139 | 3 | answer | none | not_graded | correct | Capital One closed its acquisition of Discover on **May 18, 2025**【1†number=1】. |
| agent-checks-on | dev-031 | 1 | answer | none | asked_when_should_answer | - | I’m not sure which fiscal year you’re referring to as “the year before last.” Could you specify the exact fiscal year (e.g., 2022, 2023, etc.)? |
| agent-checks-on | dev-053 | 1 | answer | none | correct | - | I can’t find the exact dollar amount for Nvidia’s Data Center segment revenue in the filings I have. |
| agent-checks-on | dev-073 | 1 | answer | none | correct | - | I can't find this in the filings I have. |
| agent-checks-on | una-002 | 1 | answer | none | abstained | correct | I can’t find any guidance for Nvidia’s fiscal 2027 revenue in the 10‑K filings that are available in the dataset. |
| agent-checks-on | control-131 | 1 | provider error at the capped final request | openrouter 200 502 | error | - |  |
| agent-checks-on | control-134 | 1 | model_calls | none | abstained | - | I can't find this in the filings I have. |
| agent-checks-on | dev-031 | 2 | answer | none | abstained | - | I can’t find the revenue figure for S&P Global’s fiscal year 2022 in the filings I have. |
| agent-checks-on | dev-053 | 2 | answer | none | correct | - | I can’t find a specific figure for Nvidia’s Data Center segment revenue in the filings I have. |
| agent-checks-on | dev-073 | 2 | answer | none | correct | - | I can’t find this in the filings I have. |
| agent-checks-on | una-002 | 2 | answer | none | abstained | correct | I can't find this in the filings I have. |
| agent-checks-on | control-131 | 2 | answer | none | not_graded | correct | Nike is headquartered in Beaverton, Oregon. [1] |
| agent-checks-on | control-134 | 2 | answer | none | abstained | - | I can’t find the specific amount an ordinary Costco member pays each year to upgrade to an Executive membership in the filings I have. |
| agent-checks-on | dev-031 | 3 | answer | none | asked_when_should_answer | - | I’m not sure which fiscal year you’re referring to—“the year before last” could mean 2024 if you’re looking at 2025 data, or 2023 if you’re looking at 2024 data |
| agent-checks-on | dev-053 | 3 | answer | none | answered_when_should_ask | - | Nvidia’s Data Center segment generated **$147.3 billion** in revenue during fiscal 2026. This figure is reported in the company’s 10‑K summary: “Data Center rev |
| agent-checks-on | dev-073 | 3 | answer | none | correct | - | I can't find this in the filings I have. |
| agent-checks-on | una-002 | 3 | answer | none | abstained | correct | I can't find this in the filings I have. |
| agent-checks-on | control-131 | 3 | answer | none | not_graded | correct | Nike is headquartered at One Bowerman Drive, Beaverton, Oregon 97005‑6453【7】. |
| agent-checks-on | control-134 | 3 | answer | none | abstained | - | I can't find this in the filings I have. |

21 new runs: 1 with a provider error. 2 reached the step cap, so their final request carried no tools; 1 of those ended in a provider error. The other runs answered before the cap.
