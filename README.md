# FilingCheck

[![CI](https://github.com/nazrulhuda/filingcheck/actions/workflows/ci.yml/badge.svg)](https://github.com/nazrulhuda/filingcheck/actions/workflows/ci.yml)

An LLM agent that answers questions about public companies' SEC 10-K filings. Before any tool runs, the server checks every argument the model sent it (the company, the fiscal year, the metric, the units) against SEC data, fixes what it can and rejects the rest. These are *skeptical tools*. Every number in an answer is then labeled **Verified**, **Unverified** or **Conflict** against the SEC's XBRL data. Built and measured as a portfolio project by Nazrul Huda Shanto (New York). The headline claim is a measured one: skeptical checks cut wrong tool calls and confidently wrong answers on a public "trap" question set.

**Status: work in progress, week 1 of 7 done** (the data pipeline; see [docs/week1_summary.md](docs/week1_summary.md) and [docs/data_report.md](docs/data_report.md)). No results yet.

## How to run

Needs [uv](https://docs.astral.sh/uv/), GNU make and Docker. On Windows, run the commands from Git Bash, and keep the clone outside the Temp folder: Windows can block programs there, including the pre-commit hook. Copy `.env.example` to `.env` and put your contact email in `SEC_CONTACT_EMAIL` (the SEC requires one on every request).

```bash
make setup    # install Python 3.12, the dependencies and the pre-commit hooks
make db-up    # start the local Postgres + pgvector database
make ingest   # download the filings, split and chunk them, and load the database
```

`make lint` and `make test` run the same checks as CI; `make test-integration` runs the database tests against the local database from `make db-up`.

## Related work

- **VeriFin: A Neurosymbolic Framework for Verifying LLM-Generated Financial Claims** ([arXiv:2608.10213](https://arxiv.org/abs/2608.10213))
- **FinVerBench: Benchmark Validity and Calibration in Large Language Model Financial Statement Verification** ([arXiv:2605.29586](https://arxiv.org/abs/2605.29586))
- **FinanceBench: A New Benchmark for Financial Question Answering** ([arXiv:2311.11944](https://arxiv.org/abs/2311.11944)): the 150 public questions, used here as the "normal" question set (CC BY-NC 4.0)

The number-verification layer here builds on the first two. Tool-argument guardrails also exist in agent frameworks such as the OpenAI Agents SDK. What this project adds is server-side *repair* of arguments using domain data, plus measurement.
