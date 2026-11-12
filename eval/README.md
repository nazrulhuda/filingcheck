# Evaluation runs

## `make eval`

```
make eval SET=examples MODE=agent CHECKS=on REPEATS=3
make eval SET=examples MODE=agent CHECKS=off REPEATS=3
make eval SET=examples MODE=baseline REPEATS=3
make eval SET=dev_traps,dev_unanswerable,control MODE=agent CHECKS=on REPEATS=3   # several sets, one after another, one file each
```

- **What it does:** runs `eval/questions/<SET>.jsonl` through the batch runner in one mode, asks each question `REPEATS` times (default 1), grades every answer with the deterministic number grader (`filingcheck/eval/grade.py`), and writes `eval/results/<date>_<SET>_<ARM>.jsonl` (every batch row with its `grade`) and a `.md` file next to it with a one-table summary.
- **Arms:** `<ARM>` is `baseline`, `agent-checks-on` or `agent-checks-off`. `CHECKS` applies to the agent only and is `on` by default, as in `make ask`, the batch command and the API. Day 20's `..._agent.jsonl` files predate the checks.
- **The two arms side by side:** after an agent run, when a finished file of the other arm exists (the newest one with a row for every question and repeat), `make eval` writes and prints `eval/results/<date>_<SET>_agent-arms.md`: the two arms as two rows one under the other (outcome counts, cost, mean time), then each question with both arms' outcomes, what the checks did in each run of the checks-on arm (the non-pass outcomes, `pass`, or `no fact call`) and whether the outcome counts differ. Outcomes can differ from model variance alone; a check changed an answer only where the page shows a repair or a reject. A few questions prove nothing about accuracy; the page shows that the layer works and is logged.
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

## `make dry-run`: the Day 33 report

`make dry-run [DATE=YYYY-MM-DD] [KEY=<file outside the repo>]` reads the day's result files for `dev_traps`, `dev_unanswerable` and `control`, both arms, with their `_llm.jsonl` grades, and writes `eval/results/<date>_dry-run.md` ("Dry run: pipeline check, not results"): per set and arm the outcomes, the lenient-rule count, the LLM verdicts, abstain rate, cost and p50/p95 latency; check activity per category; false repairs on control questions; label shares in correct and wrong-number answers; text support; every grader disagreement; and the relative_year runs with no tool call. With `KEY`, it also draws the third hand-graded sample: 20 text answers from the dry run's rows (seed 20261133), written to `eval/llm_grades/<date>_sample3_hidden.md` with the verdicts hidden and the key at `KEY`. No model call.

## `make eval-smoke`: the deterministic gate

```
make eval-smoke
uv run python -m filingcheck.eval gate-fixture   # after the facts change: rewrite the fixture
```

- **What it checks:** the checks' decisions and the tool path, deterministically. Each of the 21 scenarios in `tests/eval_gate/scenarios.yaml` is a question, the page filters, the model's scripted tool calls (one model turn each) and its scripted final answer. The gate runs the real agent graph, checks, lookup and grader on them with `FakeChat` in place of the model, and compares the override records, the arguments that reach `get_financial_fact`, the values it returns, the requested scale and the final answer's grade with what the scenario expects. The expected results were written by hand from the rules; the four golden facts' values are the hand-read ones in `tests/golden_facts.yaml`.
- **What it does not check:** accuracy on real models. A recorded model conversation cannot be replayed honestly once a tool result changes, so no model is called; accuracy is measured by `make eval`.
- **Coverage:** every check's pass, repair and reject (the metric, units and segment checks have no repair), the retry rule, a question with two companies, a page-filter question, a company outside the dataset, a quarterly question, a segment question, two plain controls, the four golden facts (one of them, American Express, under the bank revenue rule) and a filing whose fourth quarter ends on the year end (Johnson & Johnson FY2023, which guards the annual-only rule).
- **Facts:** `data/facts.jsonl` when it is present (locally), else `tests/eval_gate/facts_fixture.jsonl` (CI). For every filing the scenarios read, the fixture holds the no-dimension rows of every candidate tag of every metric, with their accession and concept, so a wrong tag order or a wrong period rule reaches the same wrong row on the fixture as on the real file; a test checks that it matches `data/facts.jsonl` whenever that file is present, and another runs every scenario on the fixture alone. Tests break the bank revenue rule and the annual-only rule on purpose and check that the gate fails, on the fixture and on the real file.
- **Where it runs:** in the unit job of CI, with no database and no network, in a few seconds (a test fails it at 10 seconds). It is part of `make test` too.

## The batch runner

```
uv run python -m filingcheck.answer batch --mode agent --questions eval/questions/examples.jsonl --out eval/results/<name>.jsonl
uv run python -m filingcheck.answer batch --mode baseline --questions eval/questions/examples.jsonl --out eval/results/<name>.jsonl [--repeats 3]
```

- **Mode and input:** it runs every question of a question file through one mode (`baseline`: plain RAG; `agent`: the agent with its three tools) in **batch mode**. Batch mode means waiting out rate limits and never falling back to another model.
- **Questions:** each is asked as its text only, with no company or year filter.
- **Output:** one JSON line per question.
- **Repeats:** with `--repeats N` each question is asked N times, one whole pass over the file after another; each row records its `repeat`.
- **Resumable:** a (question, repeat) pair already in the output file is skipped. A last line cut off by a crash (no line end) is dropped and that question is asked again. Any other line that is not a JSON object with an `id` stops the run with its line number, and the file is left as it is. Run the same command again to continue.
- **Failures:** a cut-off or empty answer is written with its error code and what the run spent up to it (see below). A provider failure on one row (after the client's own retries) is written as an error row too, with what the run spent on it, and the run goes on; a resume does not ask that row again (delete its line to retry it). Three failures in a row look like an outage and stop the run before the third is written, so it can be resumed. No question is ever answered by another model.

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

## The Week 5 question sets

`eval/questions/dev_traps.jsonl` (85), `dev_unanswerable.jsonl` (10) and `control.jsonl` (50), described in `eval/questions/README.md`. Gold values come from `python -m filingcheck.eval gold`, through the agent's own lookup, except four set by hand from the filing text (three segment changes and one fee), each with the 10-K wording in its `trap_note`.

**The control set follows FinanceBench's three question styles** (Islam et al., *FinanceBench: A New Benchmark for Financial Question Answering*, arXiv:2311.11944, CC BY-NC 4.0): metrics-generated, domain-relevant and novel-generated. FinanceBench's own questions are not used, because none of them is about the pinned filings; the questions here are written for this dataset in those styles, with FinanceBench credited as the template.

**Segment questions:** a segment's dollar total is usually in the filing's tables, which are not searched, while the text gives its change ("YouTube ads revenues increased $4.2 billion"). So a question about a segment's total expects a refusal that does not substitute the company total, and a question about a change the text states expects that figure.

**Overlap:** `uv run python eval/check_overlap.py` checks that no new question copies an older one (word overlap above 0.6).

## The LLM grader (`make grade`)

`make grade SET=<question file> RUN=eval/results/<file>.jsonl [CAP=1.0]` grades a stored results file with `filingcheck/eval/llm_grade.py` and writes `<file>_llm.jsonl` and `<file>_llm.md` next to it. It costs money (about $0.0003 per graded row) and stops once the spend passes `CAP`; a second run picks up where it stopped, because every grade is cached.

- **Model:** Claude Haiku 5.5 through OpenRouter, pinned to Anthropic's endpoint, a different model family from the one being graded. Its price is in `filingcheck/llm/pricing.yaml`, copied from OpenRouter.
- **Prompt:** `eval/grader_prompt.md`. Its version (`1-<first 12 hex digits of its SHA-256>`) is in every grade, so a changed prompt never reuses an old grade.
- **Inputs:** the question, the expected behavior, the gold value or `gold_text`, the `trap_note`, the answer, the text of the passages it cites and the facts it used (rebuilt from the database, so the local database must be loaded).
- **Output:** JSON checked against a schema: `verdict` (correct, partly, wrong, abstained, asked), `supported` (yes, partly, no, n/a), `reason` (one sentence), `evidence` (a short quote from a source, or empty). A reply that does not fit is recorded with `error: "invalid verdict"`, never guessed.
- **Uses:** the main grade for text questions (`gold_text` or `unanswerable_text`); a second opinion on every number question whose deterministic grade is not `correct`, where the deterministic grade stays the main one and each disagreement (an LLM `correct` on a row the deterministic grader failed) is listed for a person; and `supported` on every text answer.
- **Text questions name no year,** so an answer drawn from any of the company's pinned fiscal years is accepted unless the answer depends on the year.
- **Repeatability:** OpenRouter lists no temperature setting for this model, so none is sent; a grade is cached by the SHA-256 of the model, the prompt version and the messages (`eval/llm_grades/cache.jsonl`), and the same inputs always return the stored grade.

## The hand-graded sample

`uv run python eval/grade_stored.py --round <1 or 2> --key <file outside the repo>` grades the stored probe rows (`eval/probes/`), with the development-only questions in `eval/llm_grades/probe_questions.jsonl` for the text probes, and draws a fixed sample of 40 graded rows by seed (in the script): 15 text answers, 15 number answers whose deterministic grade is not `correct` and 10 that are. `eval/llm_grades/<date>_sample_hidden.md` shows each row's question, reference, answer and sources with the LLM verdict hidden, and marks the ten rows the owner also grades, picked by the same seed; the rows are shuffled and their strata are not shown. The verdicts go to the key file; it, the grade files and the grade cache are committed only after the hand grades are in. The agreement on `verdict` must reach 90%; if it does not, the prompt is fixed once and a fresh sample is drawn, and the second sample's result is reported whatever it is. Each round has its own seed, and round 2 never draws a row round 1 drew. Round 1 (seed 20261112, prompt version 1) agreed with the hand grader on 35 of 40 verdicts, so the prompt was fixed once (version 2, now frozen) and round 2 (seed 20261120) was drawn: `eval/llm_grades/2026-11-12_sample1_report.md`. Round 2 agreed with the review chat on 37 of 40 verdicts (14 of 15 text answers) and with the blind agent on 37 of 40; the two blind graders agreed with each other on 38 of 40: `eval/llm_grades/2026-11-12_sample2_report.md`.

**Who graded.** Round 2 has two blind graders, the review chat and a fresh AI agent (no conversation context, given only the grader prompt and the 40 rows in one message, with no tools), plus the owner's review of the review chat's grades on ten rows; the owner saw those grades first, so it is a review, not a blind grade. In round 1 the owner's ten were not graded independently, so round 1 has one hand grader. Every grade file's SHA-256 was recorded in `docs/decisions.md` before the LLM verdicts were opened.
