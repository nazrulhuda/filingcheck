# Development probes

**These are development probes, not evaluation rows.** They were run to find out why the agent abstained on Coca-Cola's control question and to check the fix, the company names in both tools' ticker descriptions (`docs/decisions.md`, 2026-11-10). No probe question is in an evaluation set, and the eval runner never reads this folder.

All runs are from 2026-11-09:
- Model `openrouter:openai/gpt-oss-20b`, temperature 0.6, reasoning effort low unless the row says otherwise.
- max_tokens 700, batch router, question text only, checks on.
- `tool_schema` says whether the run saw the tickers alone (before the change) or the tickers with company names (after it).

## Files

| File | Rows | What |
|---|---:|---|
| `2026-11-09_coca-cola-diagnosis.jsonl` | 70 | 55 full agent runs on Coca-Cola's control question and variants, including 10 at reasoning effort medium; then 15 runs of the agent's first model call only, with the model's reasoning text returned and no tool run |
| `2026-11-09_names-before.jsonl` | 45 | Nine more companies, 5 runs each, before the change |
| `2026-11-09_names-after.jsonl` | 65 | The same nine companies plus three Coca-Cola questions, after the change |
| `2026-11-09_names-before_discarded.jsonl` | 5 | Moody's runs whose question text had a typo ("Moody's's"); re-run with the right text, and not counted below |

## Results

Fiscal 2024 net income unless noted.

| Question | Runs | No tool call before | No tool call after | Correct before | Correct after |
|---|---:|---:|---:|---:|---:|
| American Express | 5 | 0 | 0 | 5 | 5 |
| Citigroup | 5 | 0 | 0 | 5 | 5 |
| Capital One | 5 | 0 | 0 | 5 | 5 |
| Mastercard | 5 | 3 | 0 | 2 | 5 |
| Moody's | 5 | 5 | 0 | 0 | 5 |
| S&P Global | 5 | 1 | 0 | 4 | 5 |
| UnitedHealth | 5 | 0 | 0 | 5 | 5 |
| Verizon | 5 | 5 | 0 | 0 | 5 |
| Alphabet | 5 | 0 | 0 | 5 | 5 |
| Coca-Cola, "in fiscal 2024" (control-001's text) | 10 | 4 | 0 | 6 | 10 |
| Coca-Cola, "in 2024" | 5 | 4 | 0 | 1 | 5 |
| Coca-Cola revenue | 5 | 3 | 0 | 2 | 5 |

The Coca-Cola "before" rows are from the diagnosis file. The diagnosis's other full agent runs, all before the change:

| Question | Runs | No tool call | Correct |
|---|---:|---:|---:|
| "The Coca-Cola Company's" | 5 | 1 | 4 |
| "KO's" | 5 | 0 | 5 |
| "Coca Cola's" (no hyphen) | 5 | 0 | 5 |
| Apple | 5 | 0 | 5 |
| Nike | 5 | 0 | 5 |
| Coca-Cola, control-001's text, reasoning effort medium | 10 | 0 | 10 |

In the first-call runs, the model made no tool call in 5 of the 10 runs that asked control-001's question, and in none of the 5 that named KO.

Cost: the diagnosis was $0.0127, the nine-company baseline $0.0085 (plus $0.0005 for the discarded runs) and the after runs $0.0187.

## Row fields

The rows follow the shape of `eval/results` where the probe recorded the field, and they carry `batch`, `label` and `tool_schema` as well.
- **`grade`:** the project's deterministic grader, against the facts table's fiscal 2024 value in `gold`.
  - The baseline and after rows were graded at run time and graded again when the rows were converted to this format, with the same outcome for every row.
  - The diagnosis's agent rows were graded at conversion.
  - The first-call rows have no final answer and are not graded.
- **Fields the probe did not record are `null`.**
  - The baseline and after rows have no `facts_used`, `overrides`, `finish_reason` or `completion_tokens`.
  - The first-call rows have no `facts_used`, `overrides` or `abstained`.
  - Those rows record each tool call's arguments and status, and the answer text.
- **`finish_reason` and `completion_tokens`** are lists with one entry per model call, where they were recorded.
