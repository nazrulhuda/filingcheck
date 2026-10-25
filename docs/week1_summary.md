# Week 1 summary

## What was built

A data pipeline. `make setup && make db-up && make ingest` downloads the latest three 10-K filings and the XBRL facts for 25 companies through one rate-limited, cached SEC client. It splits each 10-K into Items 1, 1A, 7, 7A and 8, cuts them into chunks, loads Postgres with pgvector, and writes `docs/data_report.md`. A fresh clone with an empty cache rebuilds the same files, byte for byte, in about four minutes. CI runs 118 unit tests and 8 database tests on every pull request.

## The data

| | Count |
|---|---:|
| Companies | 25 |
| Filings (latest three 10-Ks each) | 75 |
| Items saved | 375 |
| Chunks | 51,906 |
| us-gaap tags | 16,077 |

No filing is missing an Item.

## Three surprises

1. **BlackRock's history is split across two SEC IDs.** It re-registered in 2024, so its last three 10-Ks sit under two CIKs. It was replaced with Moody's.
2. **IBM keeps its MD&A and financial statements in an exhibit.** Its 10-K points to an Exhibit 13 annual report for them. A general rule now finds and splits such exhibits.
3. **Netflix and Nvidia keep their statements further down the same 10-K.** Their Item 8 only points to them, and Netflix also has an earlier auditor's report on internal control. Item 8 now starts at the auditor's report that gives an opinion on the financial statements.

## Still open

- Re-pin the manifest once in early November to add Apple's FY2026 10-K, then freeze it.
- Write the first 40 trap questions.

## Week 2

- **Embeddings,** with a content hash per chunk and a cache keyed by model and hash, so re-running ingest never re-embeds unchanged text.
- **Hybrid search:** vector search and keyword search, merged with Reciprocal Rank Fusion.
- **The first FastAPI endpoint.**
- **The first deploy.**
