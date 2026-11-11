# FilingCheck

[![CI](https://github.com/nazrulhuda/filingcheck/actions/workflows/ci.yml/badge.svg)](https://github.com/nazrulhuda/filingcheck/actions/workflows/ci.yml)

**Live demo: [filingcheck.vercel.app](https://filingcheck.vercel.app)**. It answers questions about the 25 companies' filings, and the model is asked to cite a passage for each claim. It uses the plain baseline: the agent runs only from the command line and the API so far, and there are no skeptical checks or number labels yet, so answers are not checked and numbers may be wrong.

FilingCheck answers questions about public companies' SEC 10-K filings and cites the passages each answer uses. It is a portfolio project by Nazrul Huda Shanto (New York), being built and measured over seven weeks.

What the project is building, and will measure: an LLM agent whose tools are *skeptical*. Before a tool runs, the server will check every argument the model sent (the company, the fiscal year, the metric, the units) against SEC data, fix what it can and reject the rest. Every number in an answer will then be labeled **Verified**, **Unverified** or **Conflict** against the SEC's XBRL data. The measurement asks whether these checks cut wrong tool calls and confidently wrong answers, on a trap question set built for that purpose. The agent is built, without checks (week 3); the checks arrive in week 4, the number labels in week 5 and the results in week 6.

**Status: week 3 of 7 done.** Search, baseline answers, the API and the web page are built and deployed: the page on Vercel, the API on Render and the database on Neon. The filings' own XBRL numbers, three tools and the agent are built; the agent is not on the page yet. The only graded results so far are on 6 example questions, which prove nothing ([week 3 summary](docs/week3_summary.md)).

## What works today

- **75 filings, pinned and checked:** the last three 10-Ks of 25 companies, pinned by accession number, split into sections and 42,612 passages, and checked by `make verify-data` ([data report](docs/data_report.md), [spot check](docs/spot_check.md), [week 1 summary](docs/week1_summary.md)).
- **Hybrid search, measured:** vector, keyword and hybrid search over the passages, scored on 40 questions with and without a company and year filter. Hybrid search did not beat vector search on these questions, and the report says so ([retrieval report](docs/retrieval_report.md)).
- **Baseline answers with citations:** plain retrieval-augmented answers from one model call, asked to cite every claim to its passage; an answer with an uncited figure is flagged. They are not checked, and on the example trap questions they guess the company or the year, or decline to answer ([baseline answers](docs/baseline_examples.md)).
- **The API:** a FastAPI service that answers or streams questions, keeps a request log, and limits questions per address and per day; it runs in a Docker image ([filingcheck/app](filingcheck/app/)).
- **The web page:** a Next.js page with a citation chip for each source and seven saved example answers, each checked against the passages and numbers it cites ([web](web/)).
- **The numbers and the agent:** company totals from each filing's own XBRL facts, cross-checked against the SEC's companyfacts; three tools with typed inputs (`search_filings`, `get_financial_fact`, `calculate`); and an agent that chooses between them and cites the passages and facts it used. It runs from the command line (`make ask MODE=agent`) and the API (`mode: "agent"`); the page still runs the baseline, and the agent has no skeptical checks yet ([facts report](docs/facts_report.md), [metric coverage](docs/facts_coverage.md), [week 3 summary](docs/week3_summary.md)).

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
