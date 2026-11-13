# Refusal questions whose answer the filings hold (both held-out files)

Every held-out question with `expected_behavior: refuse` that names a covered company (types 5 and 6) was searched in the pinned filing's passages (`chunks`) and tables (`table_chunks`) for the figure asked. Where the figure is found, or where the writer's own note allows an answer, the question carries the refusal note as `also_accept`:

> An answer that gives the figure from the filing's text or tables with a citation is also acceptable, as long as it does not present a company total as the part or another metric under the asked name; the LLM grader decides that case.

The note was tested on the LLM grader before it was added (`eval/probes/2026-11-13_refusal-note-check.md`). **`search_filings` searches passages only, not tables**, so a figure that only a table holds can rarely be retrieved and cited by the agent; those notes are added for consistency. Chunk ids are the local database's.

## The first file

| Question | Asked | Where the filing states it | Note | Reason |
|---|---|---|---|---|
| held-017 | YouTube ads revenue 2024 | tables 2026 (Item 7) and 2045 (Item 8): "YouTube ads: 31,510 \| 36,147"; passage 11437 gives only the change ("increased $4.6 billion") | its own note, unchanged | the writer's note allows quoting the filing |
| held-018 | iPhone net sales FY2025 | tables 48 (Item 7) and 59 (Item 8): "iPhone: $209,586" | yes | the filing holds it (tables only) |
| held-019 | Sam's Club net sales FY2025 | table 7732 (Item 8): "Sam's Club U.S. (1) Net sales: $90,238" | yes | the filing holds it (tables only) |
| held-020 | UnitedHealth revenue excluding Optum 2024 | table 7224 (Item 7) gives the segments ("UnitedHealthcare: $298,208", "Optum: 252,957"), not revenue excluding Optum | no | not the figure asked; the writer's note expects "only totals" |
| held-021 | Mastercard EBITDA 2025 | not found | yes | the writer's note allows offering operating income, not called EBITDA |
| held-022 | Amazon employees | passages 640, 948 and 1256 (Item 1, Human Capital); FY2025: "approximately 1,576,000 full-time and part-time employees" | yes | the filing holds it (a passage) |
| held-023 | Citigroup net income, Q2 2024 | not found (no quarter is stated) | no | not found |

held-024 (Pepsi) names no covered company.

## The second file

| Question | Asked | Where the filing states it | Note | Reason |
|---|---|---|---|---|
| held-077 | Google Cloud revenue 2024 | table 2026 (Item 7): "Google Cloud: 33,088 \| 43,229"; passage 11439 gives only the change ("increased $10.1 billion") | yes | the filing holds it (tables) |
| held-078 | Azure revenue 2024 | not found | no | not found |
| held-079 | Mac net sales FY2024 | tables 4 (Item 7) and 15 (Item 8): "Mac: 29,984" | yes | the filing holds it (tables only) |
| held-080 | Reels revenue 2023 | not found | no | not found |
| held-081 | Costco gas station sales 2024 | not found (passages 10272 and 10273 discuss gasoline prices, with no amount) | no | not found |
| held-082 | Walmart U.S. revenue without International, FY2024 | passage 41431 (Item 1): "Walmart U.S. had net sales of $441.8 billion for fiscal 2024" | yes | the filing holds it (a passage); "U.S." may also mean Walmart U.S. plus Sam's Club |
| held-083 | Verizon Consumer segment revenue 2023 | passage 39959 (Item 1): "In 2023, the Consumer segment's revenues were $101.6 billion" | yes | the filing holds it (a passage) |
| held-084 | Pfizer vaccine revenue 2024 | not found (product lines only, no vaccine total) | no | not found |
| held-085 | IBM revenue from Red Hat 2024 | not found as an amount: passages 16479 and table 2933 give growth rates only; passage 16486's "approximately $3 billion" is the Red Hat consulting practice, not Red Hat revenue | no | not found |
| held-086 | Netflix ad-tier revenue 2024 | not found | no | not found |
| held-087 | JPMorgan investment banking fees 2024 | tables 3686 ("Investment banking fees: $8,910") and 3703 ("$9,116"), two tables with different scopes | yes | the filing holds it (tables only) |
| held-088 | Amazon North America retail sales excluding cloud 2024 | table 191 (Item 7): "North America: $352,828 \| $387,497" | yes | the filing holds it (tables only) |
| held-089 | Microsoft stock price, end of 2024 | not found | no | not found |
| held-090 | Netflix revenue, Q3 2024 | not found | no | not found |
| held-091 | Coca-Cola dividend per share 2023 | passages 22952 and 22953 (Item 7): "Our annualized common stock dividend was $1.84 per share ... in 2023"; table 4216 too | yes | the filing holds it (a passage) |
| held-093 | Alphabet EBITDA 2024 | not found | no | not found; the writer's note does not allow an answer |
| held-094 | Apple headcount 2024 | passage 18 (Item 1): "approximately 164,000 full-time equivalent employees" | yes | the filing holds it (a passage) |
| held-095 | Amazon operating income, Q4 2023 | not found | no | not found |
| held-097 | Meta dividends paid 2024 | passages 27979 and 27980 (Item 7): "total dividend and dividend equivalent payments were $5.07 billion" | yes | the filing holds it (a passage) |
| held-098 | Nvidia revenue, Q1 FY2025 | not found | no | not found |
| held-099 | JPMorgan P/E ratio | not found | no | not found |
| held-100 | Costco warehouse count 2024 | passage 10184 (Item 1): "Costco operated 890, 861, and 838 warehouses worldwide at September 1, 2024, ..." | yes | the filing holds it (a passage) |

held-092 (Target) and held-096 (Exxon Mobil) name no covered company.
