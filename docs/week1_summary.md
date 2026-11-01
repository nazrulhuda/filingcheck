# Week 1 summary

## What was built

A data pipeline. `make setup && make db-up && make ingest` downloads the latest three 10-K filings and the XBRL facts for 25 companies through one rate-limited, cached SEC client. It splits each 10-K into Items 1, 1A, 7, 7A and 8, sets number tables aside, cuts the text into chunks, loads Postgres with pgvector, and writes `docs/data_report.md`. CI runs about 200 unit tests and 11 database tests on every pull request.

## The data

| | Count |
|---|---:|
| Companies | 25 |
| Filings (latest three 10-Ks each) | 75 |
| Sections saved | 372 |
| Chunks | 44,382 |
| Number tables set aside | 7,794 |
| us-gaap tags | 16,077 |

372, not 375: Citigroup's Items 1 and 7A do not start at their own headings, so each year they are kept together as one section.

## How the data was checked

`make verify-data` is an independent checker: it reads the saved files with its own patterns and imports none of the pipeline code. On its first run it found 54 problems while every unit test passed.

It led to four data bugs, each fixed by a general rule with a test:

1. Citigroup and JPMorgan map Items to page ranges through their own index, not headings.
2. IBM keeps its MD&A and financial statements in an Exhibit 13.
3. Netflix and Nvidia keep their financial statements further down the same 10-K.
4. Walmart's FY2024 Item 8, as parsed, stopped before the notes.

Every pinned filing was checked against its EDGAR filing index page: form, company, period and filing date. A test in CI now fails if any pinned filing changes. Committed snapshots of each section (size and both ends) and of each filing's chunk count fail `make verify-data` on any difference.

## Still open

- Re-pin the manifest once in November to add Apple's FY2026 10-K.
- Write the first 40 trap questions.
- The XBRL companyfacts files are not yet pinned. A hash manifest comes with the metric map in week 3.
- Citigroup's FY2025 10-K reclassified a prior-year figure: 2023 revenue of 78,462 became 78,066 (millions). Number checks will compare a number against the filing it came from.
- Bank revenue tags are confirmed for all six banks (see decisions.md); the metric map in week 3 applies the rule.
