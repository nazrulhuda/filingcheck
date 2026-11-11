# FilingCheck

[![CI](https://github.com/nazrulhuda/filingcheck/actions/workflows/ci.yml/badge.svg)](https://github.com/nazrulhuda/filingcheck/actions/workflows/ci.yml)

**Live demo: [filingcheck.vercel.app](https://filingcheck.vercel.app)**. It answers questions about the 25 companies' 10-K filings with an agent that searches the text and looks up the filings' own XBRL numbers, and the model is asked to cite a passage or a fact for each claim. Before the agent fetches a number, the server checks the company, fiscal year, metric, units and segment it asked for. Numbers are not yet labeled against the SEC data, and text answers are not checked, so an answer can still be wrong.

FilingCheck answers questions about public companies' SEC 10-K filings and cites the passages each answer uses. It is a portfolio project by Nazrul Huda Shanto (New York), being built and measured over seven weeks.

What the project is building, and will measure: an LLM agent whose tools are *skeptical*. Before the number tool runs, the server checks the arguments the model sent (the company, the fiscal year, the metric, the units, the segment) against SEC data, fixes what the question settles and sends the rest back to the model. Every number in an answer will then be labeled **Verified**, **Unverified** or **Conflict** against the SEC's XBRL data. The measurement asks whether these checks cut wrong tool calls and confidently wrong answers, on a trap question set built for that purpose. The agent was built in week 3 and the checks in week 4; the number labels come in week 5 and the results in week 6.

**Status: week 4 of 7 done.** The page on Vercel, the API on Render and the database on Neon are deployed, and the page now runs the agent with its checks on. The only graded results so far are on 6 example questions, which prove nothing about accuracy; the measurement is week 6's ([week 4 summary](docs/week4_summary.md)).

## What works today

- **75 filings, pinned and checked:** the last three 10-Ks of 25 companies, pinned by accession number, split into sections and 42,612 passages, and checked by `make verify-data` ([data report](docs/data_report.md), [spot check](docs/spot_check.md), [week 1 summary](docs/week1_summary.md)).
- **Hybrid search, measured:** vector, keyword and hybrid search over the passages, scored on 40 questions with and without a company and year filter. Hybrid search did not beat vector search on these questions, and the report says so ([retrieval report](docs/retrieval_report.md)).
- **Baseline answers with citations:** plain retrieval-augmented answers from one model call, asked to cite every claim to its passage; an answer with an uncited figure is flagged. They are not checked, and on the example trap questions they guess the company or the year, or decline to answer ([baseline answers](docs/baseline_examples.md)).
- **The API:** a FastAPI service that answers or streams questions, keeps a request log, and limits questions per address and per day; it runs in a Docker image ([filingcheck/app](filingcheck/app/)).
- **The web page:** a Next.js page that asks the agent with its checks on and shows each tool step as it runs, a chip for each cited passage or number (a number's chip opens to the value as filed, its period and the SEC document), a "What was checked" panel, and seven saved example answers ([web](web/)).
- **The numbers and the agent:** company totals from each filing's own XBRL facts, cross-checked against the SEC's companyfacts; three tools with typed inputs (`search_filings`, `get_financial_fact`, `calculate`); and an agent that chooses between them and cites the passages and facts it used. It runs on the page, from the command line (`make ask MODE=agent`) and from the API (`mode: "agent"`) ([facts report](docs/facts_report.md), [metric coverage](docs/facts_coverage.md), [week 3 summary](docs/week3_summary.md)).
- **Skeptical checks on the number tool:** before `get_financial_fact` runs, five checks compare its arguments with the question's words and the SEC data: the company, the fiscal year (including "last year"), the metric and period, the units and the segment. Each passes the call, repairs it when the question settles the answer, or sends it back to the model with the options, once. Every decision, passes included, goes into an override log that is kept with each answer, in the request log and in the evaluation rows ([week 4 summary](docs/week4_summary.md)).
- **A deterministic gate in CI:** 21 scripted scenarios run the real agent, checks, lookup and grader with no model, and fail the build if a check's decision changes (`make eval-smoke`, [eval](eval/README.md)).

## Known limits

- The checks cover the arguments of `get_financial_fact` only. A text answer is not compared with the passage it cites, so it can be confidently unsupported: one answer gave a reason for a Goldman Sachs decision that the filing does not give, and a saved example calls Walmart's currency swaps "10-year-old", which the filing does not say.
- The model sometimes says it can't find the answer without searching at all.
- A passage's preview shows the start of the passage, not the part the answer cites.
- A number's chip can show the metric's standard line name instead of the company's own wording ("Revenues" for Verizon's "Total Operating Revenues").
- Accuracy has not been measured; that is week 6.

## How to run

Needs [uv](https://docs.astral.sh/uv/), GNU make and Docker, and Node 24 for the web page. On Windows, run the commands from Git Bash, and keep the clone outside the Temp folder: Windows can block programs there, including the pre-commit hook. Copy `.env.example` to `.env` and put your contact email in `SEC_CONTACT_EMAIL` (the SEC requires one on every request). Searching needs `OPENAI_API_KEY` and answering needs `OPENROUTER_API_KEY` (gpt-oss-20b through OpenRouter, on Groq's servers); `GEMINI_API_KEY` is the fallback model's.

```bash
make setup    # install Python 3.12, the dependencies and the pre-commit hooks
make db-up    # start the local Postgres + pgvector database
make ingest   # download the filings, split and chunk them, and load the database
make embed    # embed the passages (prints the plan and its cost, then asks)
make run      # the API on http://localhost:8000
cd web && npm ci && npm run dev   # the page on http://localhost:3000
```

`make lint` and `make test` run the same checks as CI; `make test-integration` runs the database tests against the local database from `make db-up`. In `web/`, `npm run lint`, `npm run typecheck` and `npm test` do the same for the page.

## Related work

- **VeriFin: A Neurosymbolic Framework for Verifying LLM-Generated Financial Claims** ([arXiv:2608.10213](https://arxiv.org/abs/2608.10213))
- **FinVerBench: Benchmark Validity and Calibration in Large Language Model Financial Statement Verification** ([arXiv:2605.29586](https://arxiv.org/abs/2605.29586))
- **FinanceBench: A New Benchmark for Financial Question Answering** ([arXiv:2311.11944](https://arxiv.org/abs/2311.11944), CC BY-NC 4.0): its 150 public questions cover filings from 2015 to 2023, which are outside this dataset. The "normal" question set here is instead written in FinanceBench's three question styles (metrics-generated, domain-relevant and novel-generated) about the pinned filings, with FinanceBench credited as the template.

The number-verification layer here builds on the first two. Tool-argument guardrails also exist in agent frameworks such as the OpenAI Agents SDK. What this project adds is server-side *repair* of arguments using domain data, plus measurement.
