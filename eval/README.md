# Evaluation runs

## The batch runner

```
uv run python -m filingcheck.answer batch --mode agent --questions eval/questions/examples.jsonl --out eval/results/<name>.jsonl
uv run python -m filingcheck.answer batch --mode baseline --questions eval/questions/examples.jsonl --out eval/results/<name>.jsonl
```

- **Mode and input:** it runs every question of a question file through one mode (`baseline`: plain RAG; `agent`: the agent with its three tools) in **batch mode**. Batch mode means waiting out rate limits, never falling back to another model, and stopping on a provider failure.
- **Questions:** each is asked as its text only, with no company or year filter.
- **Output:** one JSON line per question.
- **Resumable:** a question whose `id` is already in the output file is skipped. A last line cut off by a crash is dropped and that question is asked again. Run the same command again to continue.
- **Failures:** a cut-off or empty answer is written with its error code. Any other provider failure stops the run, so no question is answered by another model.

## Output format (one JSON object per line)

| Field | What it holds |
|---|---|
| `id` | the question's id from the question file |
| `mode` | `baseline` or `agent` |
| `question` | the question text as asked |
| `model` | the model that answered, `provider:model` |
| `settings` | the model and retrieval settings of the run (temperature, reasoning effort, token limit, retriever, k, filters) |
| `answer` | the answer text, or `null` when `error` is set |
| `citations` | the passages the answer cites as `[n]`: `number`, `chunk_id`, `ticker`, `fiscal_year`, `item`, `source_url`, `quote` |
| `fact_citations` | agent only: the numbers cited as `[Fn]`, with `concept`, `value`, `unit`, period, `accession`, `source_url` |
| `tool_calls` | agent only: every tool call, with `name`, `arguments` as run, `defaults_applied`, `status` (`ok`, `error` or `skipped`), `result_summary` and `duration_ms` |
| `facts_used` | agent only: every fact `get_financial_fact` returned, with its exact `value` as a decimal string, `unit`, period, `concept`, `accession`, `source_url`, `decimals` and `line_label` |
| `usage` | `prompt_tokens` and `completion_tokens`, summed over the agent's model calls |
| `cost_usd` | the question's cost in dollars, summed over its model calls |
| `latency_ms` | the time the question took |
| `finish_reason` | the last model call's finish reason |
| `abstained` | true when the answer is the abstain sentence |
| `has_uncited_claims` | true when a sentence states a figure without a citation (a heuristic) |
| `model_calls` | how many model calls the answer took (1 for the baseline) |
| `stopped_by` | agent only: `model_calls` or `tool_calls` when a limit ended the run, else `null` |
| `error` | `null`, or a short code such as `openrouter - incomplete_length` |

The baseline writes the same fields, with empty `fact_citations`, `tool_calls` and `facts_used`.

## Where the gold values come from

A number question's gold value is filled from the `facts` table through the same lookup the agent's `get_financial_fact` tool uses: the pinned filing's own XBRL fact for that company, fiscal year and metric (`python -m filingcheck.eval gold`, from Week 3 Day 20).
- **Hand-set values:** a value set by a person is marked `gold_source: "hand"` and is never overwritten.
- **Checking the facts:** the facts themselves are checked separately. Four golden facts were read by hand from the printed statements (`tests/golden_facts.yaml`), and every company total on a report's year-end date is compared with the SEC's companyfacts (`docs/facts_report.md`).

## What the evaluation therefore measures

Because the gold values come from the same facts the tool reads, the evaluation measures whether the system:
- picks the right filing, fiscal year and metric for the question,
- asks or declines when it should,
- reports the number correctly (value, unit and period).

It does not re-measure whether the XBRL facts are right; the separate checks above cover that.
