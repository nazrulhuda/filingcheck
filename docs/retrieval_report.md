# Retrieval report

Written by `make retrieval-eval`; do not edit by hand.

## Settings

- date: 2026-11-03
- questions: 40 (eval/questions/retrieval.jsonl)
- embedding model: text-embedding-3-small
- hits scored per search (k): 10
- RRF: score = sum of 1 / (60 + rank) over the vector and keyword rankings; top 50 taken from each
- vector search: cosine distance; HNSW (m = 16, ef_construction = 64) with ef_search = 100 and iterative scan (relaxed order) when unfiltered; an exact scan when filtered to one company and year
- keyword search: Postgres full-text search on the chunk text: a chunk matches if it has any word of the question (the question's lexemes joined with OR); chunks with every word (websearch_to_tsquery('english')) come first, then by ts_rank_cd
- near-duplicates: a hit whose first 300 characters equal an earlier hit's from the same filing is dropped before the cut to k

## Scores

Each question is searched once per row; the top 10 hits are scored two ways. **Text found**: a hit from the question's company that is the expected chunk or contains its `must_contain` phrase, in any fiscal year. **Right year**: the same, and the fiscal year matches too. With the company + year filter the two coincide.

| Retriever | Filter | Recall@5 text found | Recall@5 right year | Recall@10 text found | Recall@10 right year | MRR text found | MRR right year | Median latency (ms) | Near-duplicates collapsed |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| vector | none | 0.45 | 0.40 | 0.55 | 0.42 | 0.334 | 0.237 | 54 | 1 |
| keyword | none | 0.12 | 0.07 | 0.20 | 0.15 | 0.106 | 0.057 | 286 | 0 |
| hybrid | none | 0.40 | 0.33 | 0.47 | 0.42 | 0.271 | 0.188 | 359 | 0 |
| vector | company + year | 0.72 | 0.72 | 0.80 | 0.80 | 0.511 | 0.511 | 51 | 2 |
| keyword | company + year | 0.45 | 0.45 | 0.55 | 0.55 | 0.293 | 0.293 | 15 | 0 |
| hybrid | company + year | 0.60 | 0.60 | 0.80 | 0.80 | 0.426 | 0.426 | 73 | 0 |

## Notes

- Searches that returned no hit at all: vector 0 unfiltered and 0 filtered, keyword 0 unfiltered and 0 filtered, hybrid 0 unfiltered and 0 filtered (of 40 questions).
- On these 40 questions hybrid search did not beat vector search. With the company + year filter: recall@10 0.80 against 0.80 (equal), recall@5 0.60 against 0.72 (below), MRR 0.43 against 0.51 (below). Without it: recall@10 0.42 against 0.42 (equal), recall@5 0.33 against 0.40 (below), MRR 0.19 against 0.24 (below), recall@10 text found 0.47 against 0.55 (below) (right year unless marked). Keyword search is kept for exact-term queries and as the fallback when the embeddings API is down. The agent in week 3 searches with company and year, so the filtered rows describe the live app.
- Unfiltered rows: the gap between recall@10 text found and right year (vector +0.13, keyword +0.05, hybrid +0.05) is how often search alone cannot pick the fiscal year. About a quarter of the chunks have an identical copy in another year's filing, and identical texts tie in an unfiltered search (same vector, same keyword score). This is the measured reason for the fiscal-year check in week 4.
- Latency is the search alone: the question vectors were embedded beforehand (loaded from eval/results/retrieval_queries.parquet).
- Query embeddings: 40 questions, 621 tokens, $0.000012, paid once when the vectors were made; this run reused them and made no API call.

## Questions

Longest run: the longest run of consecutive words a question shares with its source chunk (questions are written in a user's words; the limit is 3).

| Id | Company | Fiscal year | Item | Longest run | Question |
|---|---|---:|---|---:|---|
| ret-001 | JPM | 2024 | 1 | 1 | What does JPMorgan say about the Labor Department rule on retirement advice, and is it in force yet? |
| ret-002 | JPM | 2023 | 1-7A | 2 | Under the new income tax disclosure rule, when does JPMorgan first have to break out the taxes it pays by country and by federal versus state? |
| ret-003 | GS | 2024 | 7 | 2 | How large a cushion above the regulatory capital minimums does Goldman aim to keep? |
| ret-004 | GS | 2025 | 8 | 3 | What did Goldman's auditor do to test the company's controls over financial reporting? |
| ret-005 | MS | 2023 | 1A | 2 | Why could the move away from LIBOR hurt Morgan Stanley? |
| ret-006 | MS | 2024 | 1A | 2 | Which economic conditions does Morgan Stanley list as able to swing its results? |
| ret-007 | C | 2025 | 8 | 1 | How much intangible amortization does Citi expect over the next few years? |
| ret-008 | C | 2025 | 7 | 2 | How much money does Citi have tied up in Argentina, and how does it handle the peso? |
| ret-009 | AXP | 2023 | 1 | 2 | What does American Express see as the main ways card companies compete with each other? |
| ret-010 | AXP | 2025 | 8 | 1 | What framework did American Express management use to judge its internal controls? |
| ret-011 | COF | 2024 | 1 | 2 | Can a bank that is only adequately capitalized take brokered deposits, according to Capital One? |
| ret-012 | COF | 2024 | 7 | 3 | What was Capital One's effective tax rate and what moved it? |
| ret-013 | IBM | 2024 | 1A | 1 | Which kinds of cyber attacks does IBM say could hit it, and what might they lead to? |
| ret-014 | IBM | 2025 | 1 | 2 | Who does IBM's lending arm compete with when it helps customers pay for hardware and software? |
| ret-015 | NFLX | 2024 | 1A | 2 | How could Netflix's debt and content obligations limit what it can do? |
| ret-016 | NFLX | 2023 | 1A | 3 | What does Netflix say about others claiming it infringed their intellectual property? |
| ret-017 | NVDA | 2026 | 1 | 2 | Which kinds of customers use Nvidia's data center platforms, and what do they run on them? |
| ret-018 | NVDA | 2024 | 1A | 1 | Why does Nvidia worry that rivals could undercut it on price? |
| ret-019 | AAPL | 2024 | 1 | 1 | What does AppleCare actually give customers? |
| ret-020 | MSFT | 2026 | 7 | 2 | What could limit how fast Microsoft builds out new datacenters for AI? |
| ret-021 | AMZN | 2024 | 8 | 2 | How does Amazon account for the money it gets from suppliers for marketing and volume discounts? |
| ret-022 | GOOGL | 2025 | 7 | 1 | What does Alphabet say about IRS audits and how it decides whether its tax reserves are enough? |
| ret-023 | META | 2023 | 1 | 1 | Why does Meta say the privacy and data laws it faces are hard to predict? |
| ret-024 | WMT | 2024 | 7A | 2 | How much would Walmart's currency swaps change in value if the dollar weakened by ten percent? |
| ret-025 | COST | 2026 | 1 | 1 | How many Costco workers stick around after their first year? |
| ret-026 | KO | 2025 | 1 | 3 | How is Coca-Cola dealing with the growing number of privacy and data rules around the world? |
| ret-027 | NKE | 2024 | 1 | 1 | Which anti-corruption law does Nike have to follow overseas, and how does it handle it? |
| ret-028 | PFE | 2023 | 1 | 1 | Why does Pfizer limit its business in certain foreign markets? |
| ret-029 | JNJ | 2024 | 7 | 1 | How much had J&J set aside for rebates it owes customers? |
| ret-030 | UNH | 2025 | 7 | 2 | How did the IRA drug-pricing law change UnitedHealth's Medicare prescription plans? |
| ret-031 | VZ | 2024 | 8 | 1 | How many renewable power deals has Verizon signed and how long do they run? |
| ret-032 | MA | 2023 | 7 | 1 | How much did Mastercard book for lawsuits and legal matters? |
| ret-033 | MCO | 2024 | 1 | 2 | How many Moody's staff take part in its employee resource groups? |
| ret-034 | SPGI | 2023 | 8 | 1 | What did S&P Global buy to add car pricing data to its Mobility business? |
| ret-035 | AAPL | 2025 | 7A | 1 | How do rising rates affect Apple's bond holdings and its borrowing costs? |
| ret-036 | MSFT | 2024 | 8 | 1 | Why did Microsoft's auditor single out the valuation of intangibles from an acquisition? |
| ret-037 | AMZN | 2024 | 7 | 1 | Besides AWS, what longer-term projects is Amazon putting money into? |
| ret-038 | WMT | 2025 | 8 | 2 | Which agencies have investigated Walmart over money transfers? |
| ret-039 | JNJ | 2025 | 1 | 3 | What drugs does J&J sell for multiple myeloma? |
| ret-040 | UNH | 2023 | 7A | 2 | How much of UnitedHealth's debt carries a fixed rate that isn't swapped? |
