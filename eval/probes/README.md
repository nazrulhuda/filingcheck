# Development probes

**These are development probes, not evaluation rows.** Each set was run to find a fault in the agent and to check its fix. No probe question is in an evaluation set, and the eval runner never reads this folder.

## Company names in the tool schemas (2026-11-09)

Run to find out why the agent abstained on Coca-Cola's control question, and to check the fix: the company names in both tools' ticker descriptions (`docs/decisions.md`, 2026-11-10). All runs are from 2026-11-09:
- Model `openrouter:openai/gpt-oss-20b`, temperature 0.6, reasoning effort low unless the row says otherwise.
- max_tokens 700, batch router, question text only, checks on.
- `tool_schema` says whether the run saw the tickers alone (before the change) or the tickers with company names (after it).

### Files

| File | Rows | What |
|---|---:|---|
| `2026-11-09_coca-cola-diagnosis.jsonl` | 70 | 55 full agent runs on Coca-Cola's control question and variants, including 10 at reasoning effort medium; then 15 runs of the agent's first model call only, with the model's reasoning text returned and no tool run |
| `2026-11-09_names-before.jsonl` | 45 | Nine more companies, 5 runs each, before the change |
| `2026-11-09_names-after.jsonl` | 65 | The same nine companies plus three Coca-Cola questions, after the change |
| `2026-11-09_names-before_discarded.jsonl` | 5 | Moody's runs whose question text had a typo ("Moody's's"); re-run with the right text, and not counted below |

### Results

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

### Row fields

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

## Search without the Items filter (2026-11-11)

Run to check removing the `items` filter from `search_filings` (`docs/decisions.md`, 2026-11-11). On the page's five example questions the agent had narrowed its searches to 10-K Items that did not hold the answer.
- Same model and settings as above, checks on, and each question asked with the page filters (its company and fiscal year), 3 runs each.
- **Before:** `search_filings` with its `items` filter (code at `e65cafd`). **After:** without it (`09a006f`). Nothing else changed.
- **Questions:** the page's 5 example questions, and 10 new text questions written for this probe across ten companies and Items 1, 1A, 7, 7A, 8 and the banks' merged "1-7A". None is in `eval/questions`.
- **Key phrase:** for each question, a phrase the right passage contains. It was looked up in the saved section text before the runs.

| File | Rows |
|---|---:|
| `2026-11-11_search-items-before.jsonl` | 45 |
| `2026-11-11_search-items-after.jsonl` | 45 |

| Questions | Runs each side | Answered before / after | Cited passage has the key phrase before / after | Can't find before / after | No tool call at all before / after | Provider error before / after |
|---|---:|---:|---:|---:|---:|---:|
| The 5 page examples | 15 | 6 / 12 | 4 / 11 | 9 / 3 | 1 / 3 | 0 / 0 |
| The 10 new questions | 30 | 26 / 28 | 13 / 18 | 3 / 2 | 0 / 0 | 1 / 0 |
| All 15 | 45 | 32 / 40 | 17 / 29 | 12 / 5 | 1 / 3 | 1 / 0 |

| Question | Company, fiscal year | Key phrase | Answered before / after | Can't find before / after | Cited passage has the key phrase before / after | Items the model passed before |
|---|---|---|---:|---:|---:|---|
| Citi, Argentina and the peso | C 2025 | "Argentin" | 3 / 3 | 0 / 0 | 2 / 3 | "1/7" x1, "7" x1, "1/1A/7" x1 |
| Walmart, currency swaps | WMT 2024 | "currency swap" | 0 / 1 | 3 / 2 | 0 / 1 | "8" x3 |
| UnitedHealth, unswapped fixed-rate debt | UNH 2023 | "fixed-rate" | 0 / 2 | 3 / 1 | 0 / 1 | "7" x2, "8" x1 |
| Netflix, infringement claims | NFLX 2023 | "infring" | 3 / 3 | 0 / 0 | 2 / 3 | "1/1A/7" x2, "1/1A" x1 |
| American Express, controls framework | AXP 2025 | "COSO" | 0 / 3 | 3 / 0 | 0 / 3 | "1A" x7, "1/1A" x2, "1A/7" x1 |
| Costco, Executive member benefit | COST 2025 | "2% reward" | 3 / 3 | 0 / 0 | 3 / 3 | "1" x2, "1/1A/7" x1 |
| Pfizer, cost realignment program | PFE 2024 | "cost realignment" | 3 / 3 | 0 / 0 | 0 / 0 | "1/7" x2, "7" x1 |
| JPMorgan, trading market risk | JPM 2025 | "value-at-risk" | 3 / 3 | 0 / 0 | 1 / 2 | "7/7A" x2, "7A" x1 |
| Alphabet, foreign exchange hedging | GOOGL 2024 | "foreign currency forward" | 3 / 3 | 0 / 0 | 0 / 3 | "7/7A" x1, "1/7" x1, "1/1A/7" x1 |
| Mastercard, multi-rail | MA 2025 | "multi-rail" | 3 / 3 | 0 / 0 | 1 / 0 | "1/1A/7" x1, "1/7" x1, "1" x1 |
| Goldman, narrowing consumer banking | GS 2023 | "narrow" | 3 / 3 | 0 / 0 | 0 / 0 | "1A" x1, "7/1A" x1, "1A/7" x1 |
| Coca-Cola, refranchising | KO 2024 | "refranchis" | 2 / 3 | 1 / 0 | 2 / 3 | "7" x2, "1/1A/7" x1, "1A" x1 |
| Nvidia, export controls | NVDA 2025 | "export control" | 3 / 3 | 0 / 0 | 3 / 3 | "1/1A/7" x1, "7/7A/1" x1, "1/1A/7/7A/8" x1 |
| Verizon, Frontier | VZ 2025 | "Frontier" | 3 / 3 | 0 / 0 | 3 / 3 | "1/1A/7/7A/8" x1, "1/1A/7" x1, "1/7" x1 |
| Nike, Converse revenues | NKE 2025 | "Converse revenues" | 0 / 1 | 2 / 2 | 0 / 1 | "8" x2 |

### How to read it

- **Answered** means the answer does not say it can't find the information. It is not a grade.
- **Can't find** means the answer says it can't find the information. The test is the project's `is_abstain`, or the probe's wider pattern ("can't find", "cannot find", "could not find", "unable to find"), because `is_abstain` misses some wordings.
- **Cited passage has the key phrase** means the full text of a passage the answer cites contains the key phrase. This is the closer measure of finding the right text.
  - An answer can be counted as answered without it, by citing another passage or none.
  - Pfizer, Goldman and Mastercard were answered 3 of 3 times after the change, but none of those answers cited a passage with the key phrase. The phrase test does not show whether those answers are right.

### No search and errors

- **No tool call at all:** 1 run before, 3 runs after. These are WMT run 2 before, and WMT run 1, WMT run 3, UNH run 2 after. Each said it couldn't find the information without searching. The change does not touch this.
- **Fact lookups but no search:** on Nike's Converse question, some runs called `get_financial_fact` five times and never searched: 2 before, 1 after.
- **Provider errors:** 1 run before ended in a provider error, and none after. On the agent's last allowed model call, which offers no tools, the model called a tool, and the provider refused the reply.

### Lost runs

The first attempt at the before batch stopped on that same error after 43 runs. A fault in the probe script's restart then overwrote those 43 rows before anyone read them, so they are not kept.
- The before file holds the 12 runs of the restart, the page examples for Citi, Walmart, UnitedHealth and Netflix.
- It also holds the 33 runs that finished the batch, on the same code.

### Cost

- Before: $0.0244, for the rows kept.
- After: $0.0205.
- The 43 lost runs cost about $0.023, by the kept runs' average.
