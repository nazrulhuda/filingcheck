# FilingCheck

[![CI](https://github.com/nazrulhuda/filingcheck/actions/workflows/ci.yml/badge.svg)](https://github.com/nazrulhuda/filingcheck/actions/workflows/ci.yml)

**Live demo: [filingcheck.vercel.app](https://filingcheck.vercel.app)**. It answers questions about the 25 companies' 10-K filings with an agent that searches the text and looks up the filings' own XBRL numbers, and the model is asked to cite a passage or a fact for each claim. Before the agent fetches a number, the server checks the company, fiscal year, metric, units and segment it asked for. Every number in an answer is labeled Verified, Conflict or Unverified against its cited source; text answers are not checked, so an answer can still be wrong.

FilingCheck answers questions about public companies' SEC 10-K filings and cites the passages each answer uses. It is a portfolio project by Nazrul Huda Shanto (New York), being built and measured over seven weeks.

What the project is building, and will measure: an LLM agent whose tools are *skeptical*. Before the number tool runs, the server checks the arguments the model sent (the company, the fiscal year, the metric, the units, the segment) against SEC data, fixes what the question settles and sends the rest back to the model. Every number in an answer is then labeled **Verified**, **Unverified** or **Conflict** against the facts and passages the answer cites. The measurement asks whether these checks cut wrong tool calls and confidently wrong answers, on a trap question set built for that purpose. The agent was built in week 3, the checks in week 4 and the number labels in week 5; the results come in week 6.

**Status: week 5 of 7 done.** The page on Vercel, the API on Render and the database on Neon are deployed; the page runs the agent with its checks on and labels every number. The question sets, the graders and a dry run are in place; the held-out set is sealed and unrun. Nothing measured yet proves accuracy; the measurement is week 6's ([week 5 summary](docs/week5_summary.md), [week 4 summary](docs/week4_summary.md)).

## What works today

- **75 filings, pinned and checked:** the last three 10-Ks of 25 companies, pinned by accession number, split into sections and 42,612 passages, and checked by `make verify-data` ([data report](docs/data_report.md), [spot check](docs/spot_check.md), [week 1 summary](docs/week1_summary.md)).
- **Hybrid search, measured:** vector, keyword and hybrid search over the passages, scored on 40 questions with and without a company and year filter. Hybrid search did not beat vector search on these questions, and the report says so ([retrieval report](docs/retrieval_report.md)).
- **Baseline answers with citations:** plain retrieval-augmented answers from one model call, asked to cite every claim to its passage; an answer with an uncited figure is flagged. They are not checked, and on the example trap questions they guess the company or the year, or decline to answer ([baseline answers](docs/baseline_examples.md)).
- **The API:** a FastAPI service that answers or streams questions, keeps a request log, and limits questions per address and per day; it runs in a Docker image ([filingcheck/app](filingcheck/app/)).
- **The web page:** a Next.js page that asks the agent with its checks on and shows each tool step as it runs, a chip for each cited passage or number (a number's chip opens to the value as filed, its period and the SEC document), a "What was checked" panel, and seven saved example answers ([web](web/)).
- **The numbers and the agent:** company totals from each filing's own XBRL facts, cross-checked against the SEC's companyfacts; three tools with typed inputs (`search_filings`, `get_financial_fact`, `calculate`); and an agent that chooses between them and cites the passages and facts it used. It runs on the page, from the command line (`make ask MODE=agent`) and from the API (`mode: "agent"`) ([facts report](docs/facts_report.md), [metric coverage](docs/facts_coverage.md), [week 3 summary](docs/week3_summary.md)).
- **Skeptical checks on the tools:** before `get_financial_fact` runs, five checks compare its arguments with the question's words and the SEC data: the company, the fiscal year (including "last year"), the metric and period, the units and the segment. Before `search_filings` runs, the fiscal-year check does the same for its year, and sends a search that names no year to the company's latest filing. Each passes the call, repairs it when the question settles the answer, or sends it back to the model with the options, once. Every decision, passes included, goes into an override log that is kept with each answer, in the request log and in the evaluation rows ([week 4 summary](docs/week4_summary.md)).
- **Graders:** a deterministic grader for numbers, and an LLM grader for text answers and for a second opinion on failed number grades ([eval](eval/README.md)). The LLM grader was checked on two samples of 40 stored answers, graded blind by AI: the first by a reviewing AI session, the second by that session and a fresh AI agent given the rules and the answers (it also received the project's description file, but no development question, gold value or verdict). On the second sample, after one fix to its prompt, it agreed with the reviewing session on 37 of 40 verdicts; on a later sample of 20 text answers, 16 of 20. The owner reviewed the grades on ten rows. No blind human grader took part.
- **A held-out trap set** (28 questions, `eval/questions/heldout_traps.jsonl`), written by a fresh AI agent, not by a person. Its prompt held only the category names and the company list, but the agent also received the project's description file, which names the five checks and the goal (no development question, gold value or verdict). It is sealed after review and first run in week 6.
- **Number labels:** every figure in an answer is labeled Verified (it is in a cited fact or passage), Conflict (it differs from the cited fact) or Unverified, after the model answers and without changing what it wrote; the page shows the label next to each figure ([labels](filingcheck/labels/), [week 5 summary](docs/week5_summary.md)).
- **A deterministic gate in CI:** 24 scripted scenarios run the real agent, checks, lookup and grader with no model, and fail the build if a check's decision changes (`make eval-smoke`, [eval](eval/README.md)).

## Known limits

- The checks cover the arguments of the tools, not the text of an answer. A text answer is not compared with the passage it cites, so it can be confidently unsupported: one answer gave a reason for a Goldman Sachs decision that the filing does not give, and a saved example calls Walmart's currency swaps "10-year-old", which the filing does not say. In the Week 5 dry run, a third or more of the text answers to normal questions said more than their cited passages support, and sending searches to the latest filing did not change that.
- On questions the filings do not answer (a reason a filing never gives), searching the right filing makes the model answer more often, not less: it turns a description in the passage into a reason. In the dry run, 5 of 30 such questions were answered after the search check was added, against 1 before it (both with the checks on).
- The model sometimes says it can't find the answer without searching at all.
- A number's chip can show the metric's standard line name instead of the company's own wording ("Revenues" for Verizon's "Total Operating Revenues").
- Verified means the number is in a cited source, not that the sentence is right: a Verified figure can be the wrong number for the question.
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
