# LLM grades: 2026-11-14_dev_traps_agent-prompt-rules-v2

Model openrouter:anthropic/claude-haiku-5.5, prompt version 2-8754c63e1ae3; 13 of 52 from the cache; new cost $0.010375.

| Use | Rows | correct | partly | wrong | abstained | asked | Errors |
|---|---:|---:|---:|---:|---:|---:|---:|
| text | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| also accept | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| second opinion | 52 | 11 | 0 | 32 | 7 | 2 | 0 |

Support on text answers:

| yes | partly | no | n/a |
|---:|---:|---:|---:|
| 0 | 0 | 0 | 0 |

## Disagreements

| Row | Deterministic | LLM | Reason |
|---|---|---|---|
| dev-004 #1 | answered_when_should_ask | correct | The question expects a refusal because Capital Group is not in the dataset, and the answer declines by stating it is not among the companies in the dataset. |
| dev-050 #1 | answered_when_should_ask | correct | The answer declines to give a dollar figure for AWS sales, as the question expects, and notes only the 20% increase that the note says the text contains; it does not substitute Amazon's total. However, it cites no passages, so its claim about the 20% increase is not backed by any shown source. |
| dev-065 #1 | answered_when_should_ask | correct | The question expects a refusal because EBITDA is not a reported GAAP line or one of the 13 metrics, and the answer declines by saying EBITDA is not among the available metrics; its list of metrics is a statement about the tool, not a filing fact requiring citation. |
| dev-073 #1 | answered_when_should_ask | correct | The question expects a refusal because free cash flow is not a reported line item, and the answer declines by saying it is not among the available metrics, stating no figures. |
| dev-052 #2 | answered_when_should_ask | correct | The answer declines to give Azure revenue, which the question expects, and its total-revenue figure matches the looked-up value F1, but its claim that segment revenue is not reported in the XBRL facts is not shown in the sources. |
| dev-068 #2 | answered_when_should_ask | correct | The question expects a refusal because Visa is not among the 25 companies, and the answer declines on that basis without giving any figure. |
| dev-069 #2 | answered_when_should_ask | correct | The question expects a refusal since market cap is not in the dataset, and the answer declines, stating only that the metric is not in the filings. |
| dev-003 #3 | answered_when_should_ask | correct | The answer declines because Citizens is not among the 25 companies, which matches the expected refusal and the note, and it does not substitute Citigroup. |
| dev-004 #3 | answered_when_should_ask | correct | The question expects a refusal because Capital Group is not in the dataset, and the answer declines by stating it is not among the companies in the dataset. |
| dev-066 #3 | answered_when_should_ask | correct | The question expects a refusal because EBITDA is not reported, and the answer declines to give an EBITDA figure, stating only that it is not available in the data set. |
| dev-068 #3 | answered_when_should_ask | correct | The question expects a refusal because Visa is not among the 25 companies, and the answer declines on that basis without giving any figure. |
