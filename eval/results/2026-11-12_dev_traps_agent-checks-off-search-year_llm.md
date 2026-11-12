# LLM grades: 2026-11-12_dev_traps_agent-checks-off-search-year

Model openrouter:anthropic/claude-haiku-5.5, prompt version 2-8754c63e1ae3; 12 of 77 from the cache; new cost $0.016869.

| Use | Rows | correct | partly | wrong | abstained | asked | Errors |
|---|---:|---:|---:|---:|---:|---:|---:|
| text | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| also accept | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| second opinion | 77 | 2 | 0 | 50 | 18 | 7 | 0 |

Support on text answers:

| yes | partly | no | n/a |
|---:|---:|---:|---:|
| 0 | 0 | 0 | 0 |

## Disagreements

| Row | Deterministic | LLM | Reason |
|---|---|---|---|
| dev-016 #2 | answered_when_should_ask | correct | The answer flags that the December 31, 2025 period is not a Nike fiscal year and offers the real candidates, which is the clarification the question needed; its FY2025 revenue figure matches the looked-up value. |
| dev-016 #3 | answered_when_should_ask | correct | The answer correctly flags that Nike's May 31 fiscal year does not match a 12-month period ending December 31, 2025, and offers the fiscal year ending May 31, 2026 as the likely intent, which is the clarification the question calls for. |
