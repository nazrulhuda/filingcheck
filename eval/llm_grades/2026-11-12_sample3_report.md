# Hand-graded sample 3: the LLM grader against the review chat on text answers

Sample: `2026-11-12_sample3_hidden.md`, 20 text answers from the Day 33 dry run (both arms, seed 20261133). LLM verdicts: `2026-11-12_sample3_key.jsonl`, grader prompt version `2-8754c63e1ae3` (frozen). Hand grades: `2026-11-12_sample3_review_chat_grades.md`, made blind; its SHA-256 is in `docs/decisions.md`, recorded before the key was opened.

| Rows | Verdict agreement | Supported agreement |
|---|---:|---:|
| 20 text answers | 16/20 (80%) | 17/20 (85%) |

No prompt change follows: the prompt is frozen after sample 2. This sample is the text-only check the Day 32 samples lacked.

## Every row where the grades differ

| Row | LLM | Review chat | LLM's reason | Review chat's note |
|---:|---|---|---|---|
| 5 | partly / partly | correct / yes | The answer gives the gold 'Yes' and the quoted plan wording appears in the cited passage, but it attributes the statement to a '2023 Form 10-K' when the question concerns FY2025, and the passage shows no year. | (no note) |
| 8 | partly / partly | correct / yes | The answer names Comirnaty and Paxlovid, which match the gold, but it adds a third product from a 2023 filing and presents its list as the complete set, while the question is about FY2025. | (no note) |
| 10 | correct / partly | correct / yes | The answer says Yes and gives the gold substance, a lower-priced ad-supported plan, which passage [3] states; however, the attribution to the 2023 Form 10-K does not appear in the passage shown. | (no note) |
| 12 | partly / yes | correct / yes | The answer names both gold products, Comirnaty and Paxlovid, but draws its list from the 2023 10-K rather than FY2025 and adds vaccine items (the 2023-2024 formula EUA vaccine and the bivalent vaccines) that the reference does not list. | (no note) |
| 16 | wrong / partly | partly / partly | The answer says Mastercard wants to tokenize payment instruments and digital assets, which does not match the gold answer of credentials, identities, assets and data; it also cites the 2023 10-K instead of FY2025, though its cited passages do partly support tokenization claims. | "digital assets" overlaps the reference's "assets"; credentials, identities and data are missing; the spliced quote "focused on supporting digital currencies by ... tokenization capabilities" is not in the passages |

## The pattern

All four verdict disagreements are text answers drawn from the company's FY2023 filing when the reference is the FY2025 one (Pfizer's products, Netflix's ad plan, Mastercard's tokenization). The grader prompt accepts an answer from any pinned year unless the answer depends on the year; the LLM grader read these as depending on the year (`partly`), the review chat did not (`correct`). The dry-run report's search-year table shows why these answers come from 2023: the agent sent fiscal_year 2023 to `search_filings` on most text questions. A fiscal-year check on `search_filings` (the next PR) sends such searches to the latest pinned year, which removes the case rather than settling it.
