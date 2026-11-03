# Week 2 summary

## What is live

A public page (Next.js on Vercel) sends each question to the API (FastAPI on Render, Virginia). The API searches a Postgres 16 database on Neon (AWS us-east-1) and has `gpt-oss-20b` write the answer through OpenRouter, on Groq's servers, with Gemini as the fallback. Each answer is the plain baseline: one model call over 8 retrieved passages; the model is asked to cite a passage for each claim. There is no agent yet, and no skeptical checks or number labels, so answers are not checked. The live smoke test passes; the README links the demo.

## Retrieval

On 40 questions ([retrieval report](retrieval_report.md), right fiscal year), with the company and year filter:

| Search | Recall@5 | Recall@10 | MRR |
|---|---|---|---|
| vector | 0.72 | 0.80 | 0.511 |
| hybrid | 0.60 | 0.80 | 0.426 |
| keyword | 0.45 | 0.55 | 0.293 |

Hybrid search did not beat vector search on these questions. The app uses hybrid search for now; the Week 5 comparison on the full question sets decides the default.

## Costs so far

- Embedding the 42,581 passages (36,042 distinct texts, 6,307,674 tokens): $0.1262.
- Answers through OpenRouter, to Nov 3: $0.0013.
- Development calls on Groq's and Gemini's free tiers: not billed.
- Hosting: Render $7 a month; Neon and Vercel on free plans.

## Database

432 MB on Neon (432,136,192 bytes, of which the vector index is 148 MB), under the free plan's 1 GB. The Neon copy matches the checked local database field by field.

## Not done

Apple's FY2026 10-K was not filed as of Nov 3, 00:34 UTC (its newest 10-K is FY2025, filed 2025-10-31), so the planned re-pin moves to Week 3.

## Week 3

The XBRL metric map, the three tools (`search_filings`, `get_financial_fact`, `calculate`) and the agent.
