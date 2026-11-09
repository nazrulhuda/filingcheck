# Evaluation runs

## `make eval`

```
make eval SET=examples MODE=agent CHECKS=on REPEATS=3
make eval SET=examples MODE=agent CHECKS=off REPEATS=3
make eval SET=examples MODE=baseline REPEATS=3
```

- **What it does:** runs `eval/questions/<SET>.jsonl` through the batch runner in one mode, asks each question `REPEATS` times (default 1), grades every answer with the deterministic number grader (`filingcheck/eval/grade.py`), and writes `eval/results/<date>_<SET>_<ARM>.jsonl` (every batch row with its `grade`) and a `.md` file next to it with a one-table summary.
- **Arms:** `<ARM>` is `baseline`, `agent-checks-on` or `agent-checks-off`. `CHECKS` applies to the agent only and is `on` by default, as in `make ask`, the batch command and the API. Day 20's `..._agent.jsonl` files predate the checks.
- **The two arms side by side:** after an agent run, when a finished file of the other arm exists (the newest one with a row for every question and repeat), `make eval` writes and prints `eval/results/<date>_<SET>_agent-arms.md`: the two arms as two rows one under the other (outcome counts, cost, mean time), then each question with both arms' outcomes, what the checks did in each run of the checks-on arm (the non-pass outcomes, `pass`, or `no fact call`) and whether the outcome counts changed. A few questions prove nothing about accuracy; the page shows that the layer works and is logged.
- **Resumable:** run the same command again and only the missing (question, repeat) pairs are asked; every row is graded again. Without `DATE`, the newest file of the same set and mode is resumed if it is unfinished (so a run resumed after midnight UTC goes on in its own file); otherwise the run gets today's date (UTC).
- **Stale rows:** a row whose question is no longer in the question file is kept in the results file with `grade: null` and left out of the summary, which says how many there are.
- **Grades:**
  - **A number question** (`expected_behavior: answer`):
    - `correct`: one number in the answer, in raw units, is within `tolerance_pct` of `gold_value`, and the fiscal year is stated;
    - `year_not_stated`: the number matches but the year is not stated;
    - `other_year_number`: the number matches the same metric for another pinned year of the company (`gold_other_years`), and `other_year` says which;
    - `wrong_number`: a number is given but matches nothing;
    - `no_number`: no amount is given, and the answer neither declines nor asks;
    - `asked_when_should_answer`: no amount, and the answer asks the user a question;
    - `abstained`: the abstain sentence, or a decline in other words with no amount.
  - **Matching:** a number goes to whichever value (the gold year's or another year's) it is closest to, because two years can be inside each other's tolerance. Coca-Cola's net income was 10,714 million in FY2023 and 10,631 million in FY2024, 0.8% apart.
  - **The fiscal year is stated** by an explicit phrase ("fiscal 2025", "fiscal year 2025", "FY2025", "FY25", "fiscal '25"), which wins. Without one, it is stated by a period-end date ("the year ended January 31, 2025", "as of June 30, 2025", "... to 2025-01-31") or a year standing on its own. A year inside any other date ("filed on February 25, 2026") counts for nothing. In all 75 pinned filings the fiscal year is the calendar year of the period end.
  - **A `clarify` or `refuse` question** is `correct` when the answer gives no amount and asks or declines (keyword rules), and `answered_when_should_ask` otherwise. Small counts ("3 months", "25 companies"), dates and footnote markers are not amounts; a currency sign, a scale, a percent sign, digit groups, decimals or a value of 1,000 or more make one.
  - **Numbers:** a minus sign attached to the number, an amount in parentheses, or a loss ("a net loss of $10.6 billion") makes a number negative; a dash with a space after it ("revenue - $681 billion", a subtraction) does not, and neither does the "(loss)" of a label. In a range ("$680.9-681.0 billion", "10-12%") both numbers are positive and take the second one's scale.
  - **Other outcomes:** `error` for a row with no answer; `not_graded` for a number question with no gold value.

## The batch runner

```
uv run python -m filingcheck.answer batch --mode agent --questions eval/questions/examples.jsonl --out eval/results/<name>.jsonl
uv run python -m filingcheck.answer batch --mode baseline --questions eval/questions/examples.jsonl --out eval/results/<name>.jsonl [--repeats 3]
```

- **Mode and input:** it runs every question of a question file through one mode (`baseline`: plain RAG; `agent`: the agent with its three tools) in **batch mode**. Batch mode means waiting out rate limits, never falling back to another model, and stopping on a provider failure.
- **Questions:** each is asked as its text only, with no company or year filter.
- **Output:** one JSON line per question.
- **Repeats:** with `--repeats N` each question is asked N times, one whole pass over the file after another; each row records its `repeat`.
- **Resumable:** a (question, repeat) pair already in the output file is skipped. A last line cut off by a crash (no line end) is dropped and that question is asked again. Any other line that is not a JSON object with an `id` stops the run with its line number, and the file is left as it is. Run the same command again to continue.
- **Failures:** a cut-off or empty answer is written with its error code and what the run spent up to it (see below). Any other provider failure stops the run, so no question is answered by another model.

## Output format (one JSON object per line)

| Field | What it holds |
|---|---|
| `id` | the question's id from the question file |
| `repeat` | which run of the question this is: 1, 2, ... (a row without it counts as 1) |
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
| `has_uncited_claims` | true when a sentence states a figure without a citation (a heuristic); a mark that points to no passage or fact, such as `[9]` among 4 passages or `[F3]` among 1 fact, is no citation |
| `model_calls` | how many model calls the answer took (1 for the baseline) |
| `stopped_by` | agent only: `model_calls` or `tool_calls` when a limit ended the run, else `null` |
| `checks` | agent only: whether the skeptical checks ran (`true` or `false`); `null` for the baseline |
| `overrides` | agent only: the checks' override log, one record per check per `get_financial_fact` call: `check`, `outcome` (`pass`, `repair` or `reject`), `argument`, `sent`, `used`, `reason`, `options` |
| `error` | `null`, or a short code such as `openrouter - incomplete_length` |

The baseline writes the same fields, with empty `fact_citations`, `tool_calls` and `facts_used`.

`make eval` adds a `grade` to each row: `outcome`, `numbers` (every number found, raw units, percentages ending in `%`), `matched` (the number that matched the gold value or another year's value), `year_stated` and `other_year`.

A row with an `error` has `answer: null` and no citations; `usage`, `cost_usd`, `latency_ms` and `model_calls` cover every model call the question made, the cut-off one included, and for the agent `tool_calls` and `facts_used` hold the calls made before it.

## Year conventions

- **A bare year** ("2025") means the fiscal year with that label: Walmart's 2025 is fiscal 2025, February 1, 2024 to January 31, 2025.
- **"Last year", "latest", "most recent"** mean the company's latest pinned fiscal year: for Nvidia, fiscal 2026 (January 27, 2025 to January 25, 2026).
- **A date** ("the year ended January 31, 2026", "as of June 30, 2025", or a range one year long) means the fiscal year ending within a week of it. A date that is no fiscal year end of the company ("the year ended December 31, 2025" for Walmart) or a range shorter or longer than a year is no fiscal year: the 10-K data has no figure for it, so the fiscal-year check rejects the call and the model should ask the user.
- **A calendar year** ("calendar 2025", "CY2025") is that fiscal year for a company whose year ends in December; for the others it overlaps two fiscal years, and the check asks the user which one.
- The question set's gold values follow these conventions (trap-002 is Walmart fiscal 2025; trap-003 is Nvidia fiscal 2026), the fiscal-year check uses them, and its reason always states the period dates, so a reader can see what was meant.

## Where the gold values come from

A number question's gold value is filled from the `facts` table through the same lookup the agent's `get_financial_fact` tool uses: the pinned filing's own XBRL fact for that company, fiscal year and metric (`python -m filingcheck.eval gold`, from Week 3 Day 20).
- **Hand-set values:** a value set by a person is marked `gold_source: "hand"` and is never overwritten.
- **Only number questions** (`expected_behavior: answer`) get a gold value; a clarify or refuse question has none.
- **Other years:** the same metric's value for each other pinned year of the company is recorded in `gold_other_years`, so the grader can tell another year's number from a wrong one.
- **Checking the facts:** the facts themselves are checked separately. Four golden facts were read by hand from the printed statements (`tests/golden_facts.yaml`), and every company total on a report's year-end date is compared with the SEC's companyfacts (`docs/facts_report.md`).

## What the evaluation therefore measures

Because the gold values come from the same facts the tool reads, the evaluation measures whether the system:
- picks the right filing, fiscal year and metric for the question,
- asks or declines when it should,
- reports the number correctly (value, unit and period).

It does not re-measure whether the XBRL facts are right; the separate checks above cover that.
