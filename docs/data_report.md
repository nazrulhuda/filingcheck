# Data report

Written by `make ingest` from `data/manifest.json` and the files the ingest stages produce. Do not edit by hand. The us-gaap tag counts include only tags with a fact from one of the 75 pinned filings, so they stay the same when the SEC's companyfacts files grow with later filings.

## Totals

| | Count |
|---|---:|
| Companies | 25 |
| Filings | 75 |
| Items saved | 372 |
| Chunks | 42,612 |
| us-gaap tags in the pinned filings (all companies) | 8,010 |
| Number tables set aside (table_chunks) | 7,796 |

## Gaps

No filing is missing an Item.

Items under 2,000 characters:

- AXP FY2023: Item 7A has 175 characters
- AXP FY2024: Item 7A has 175 characters
- AXP FY2025: Item 7A has 175 characters
- COF FY2023: Item 7A has 238 characters
- COF FY2024: Item 7A has 238 characters
- COF FY2025: Item 7A has 238 characters
- GS FY2023: Item 7A has 336 characters
- GS FY2024: Item 7A has 336 characters
- GS FY2025: Item 7A has 336 characters
- IBM FY2023: Item 7A has 218 characters
- IBM FY2024: Item 7A has 210 characters
- IBM FY2025: Item 7A has 210 characters
- JNJ FY2023: Item 7A has 482 characters
- JNJ FY2024: Item 7A has 482 characters
- JNJ FY2025: Item 7A has 506 characters
- JPM FY2023: Item 7A has 250 characters
- JPM FY2024: Item 7A has 250 characters
- JPM FY2025: Item 7A has 250 characters
- MCO FY2023: Item 7A has 221 characters
- MCO FY2024: Item 7A has 221 characters
- MCO FY2025: Item 7A has 221 characters
- MSFT FY2024: Item 7A has 1,972 characters
- MSFT FY2025: Item 7A has 1,950 characters
- MSFT FY2026: Item 7A has 1,949 characters
- PFE FY2023: Item 7A has 293 characters
- PFE FY2024: Item 7A has 293 characters
- PFE FY2025: Item 7A has 293 characters
- SPGI FY2023: Item 7A has 1,570 characters
- SPGI FY2024: Item 7A has 1,605 characters
- SPGI FY2025: Item 7A has 1,462 characters

A short Item 7A is usually a one-line pointer to the market-risk discussion inside Item 7.

## Sections taken from elsewhere

- C FY2023: Item 8 from later in the same 10-K
- C FY2024: Item 8 from later in the same 10-K
- C FY2025: Item 8 from later in the same 10-K
- IBM FY2023: Items 7, 8 from Exhibit 13
- IBM FY2024: Items 7, 8 from Exhibit 13
- IBM FY2025: Items 7, 8 from Exhibit 13
- JPM FY2023: Item 8 from later in the same 10-K
- JPM FY2024: Item 8 from later in the same 10-K
- JPM FY2025: Item 8 from later in the same 10-K
- NFLX FY2023: Item 8 from later in the same 10-K
- NFLX FY2024: Item 8 from later in the same 10-K
- NFLX FY2025: Item 8 from later in the same 10-K
- NVDA FY2024: Item 8 from later in the same 10-K
- NVDA FY2025: Item 8 from later in the same 10-K
- NVDA FY2026: Item 8 from later in the same 10-K
- WMT FY2024: Item 8 from later in the same 10-K

## Sections with approximate boundaries

These 10-Ks map their Items to page ranges through their own index, so a section starts and ends where those pages do, not at a heading. Item 8 is cut instead from the auditor's report on the financial statements, so its start is exact. A section that does not start at its own heading is not given a label that may not fit it: those are kept together as Items 1-7A, "10-K text, sections not separable".

- C FY2023: Items 1A, 7, 1-7A (1, 7A kept together as 1-7A)
- C FY2024: Items 1A, 7, 1-7A (1, 7A kept together as 1-7A)
- C FY2025: Items 1A, 7, 1-7A (1, 7A kept together as 1-7A)
- JPM FY2023: Items 1, 1A, 7A, 1-7A (7 kept together as 1-7A)
- JPM FY2024: Items 1, 1A, 7A, 1-7A (7 kept together as 1-7A)
- JPM FY2025: Items 1, 1A, 7A, 1-7A (7 kept together as 1-7A)

## Repeated passages removed

Passages that appear more than once in the same filing are kept once, under the first Item that has them, and their chunks list the other Items. Repeats across fiscal years are kept.

- AAPL FY2024: 4
- AAPL FY2025: 3
- AAPL FY2026: 4
- AMZN FY2023: 1
- AMZN FY2024: 1
- AMZN FY2025: 1
- AXP FY2023: 19
- AXP FY2024: 19
- AXP FY2025: 17
- C FY2023: 1,110
- C FY2024: 1,069
- C FY2025: 1,035
- COF FY2023: 29
- COF FY2024: 33
- COF FY2025: 28
- GOOGL FY2023: 11
- GOOGL FY2024: 14
- GOOGL FY2025: 17
- GS FY2023: 28
- GS FY2024: 26
- GS FY2025: 27
- IBM FY2023: 15
- IBM FY2024: 10
- IBM FY2025: 10
- JNJ FY2023: 6
- JNJ FY2024: 7
- JNJ FY2025: 10
- JPM FY2023: 56
- JPM FY2024: 58
- JPM FY2025: 55
- KO FY2023: 24
- KO FY2024: 28
- KO FY2025: 23
- MA FY2023: 2
- MA FY2024: 5
- MA FY2025: 2
- MCO FY2023: 28
- MCO FY2024: 27
- MCO FY2025: 28
- META FY2023: 4
- META FY2024: 3
- META FY2025: 3
- MS FY2023: 14
- MS FY2024: 18
- MS FY2025: 19
- MSFT FY2024: 20
- MSFT FY2025: 20
- MSFT FY2026: 17
- NFLX FY2023: 1
- NFLX FY2025: 1
- NKE FY2024: 3
- NKE FY2025: 6
- NKE FY2026: 10
- NVDA FY2024: 8
- NVDA FY2025: 18
- NVDA FY2026: 20
- PFE FY2024: 3
- SPGI FY2023: 57
- SPGI FY2024: 56
- SPGI FY2025: 56
- UNH FY2023: 1
- UNH FY2024: 1
- UNH FY2025: 4
- VZ FY2023: 26
- VZ FY2024: 31
- VZ FY2025: 30
- WMT FY2024: 1
- WMT FY2025: 2
- WMT FY2026: 2

## Number tables

Tables with more than half their non-empty cells numeric (contents lists aside) are taken out of the prose before the sections are cut, and each is saved as one record in table_chunks: its rows as "label: values" text, the Item that held it, and its position in the source document. companyfacts has whole-company numbers only; segment numbers are only in these tables. They are not searched with the chunks.

- Saved: 7,796, of which 297 lie outside the Items above

Where taking the tables out would move a section's start or end, that section is cut from the full document instead, and its tables are also left to the chunk filter:

- JPM FY2023: Item 7
- SPGI FY2023: Item 8
- SPGI FY2024: Item 8
- SPGI FY2025: Item 8

## AAPL

Apple Inc. · CIK 0000320193 · fiscal year ends in September · 219 us-gaap tags in its pinned filings

| FY | Accession | Period of report | Item 1 | Item 1A | Item 7 | Item 7A | Item 8 | Items 1-7A (10-K text, sections not separable) | Chunks |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| 2024 | 0000320193-24-000123 | 2024-09-28 | 15,767 | 68,484 | 13,818 | 2,758 | 40,450 | — | 199 |
| 2025 | 0000320193-25-000079 | 2025-09-27 | 16,054 | 67,760 | 16,505 | 2,758 | 41,360 | — | 198 |
| 2026 | 0000320193-26-000026 | 2026-09-26 | 20,800 | 86,034 | 16,152 | 2,758 | 42,307 | — | 232 |

## AMZN

Amazon.com, Inc. · CIK 0001018724 · fiscal year ends in December · 301 us-gaap tags in its pinned filings

| FY | Accession | Period of report | Item 1 | Item 1A | Item 7 | Item 7A | Item 8 | Items 1-7A (10-K text, sections not separable) | Chunks |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| 2023 | 0001018724-24-000008 | 2023-12-31 | 13,254 | 58,814 | 44,125 | 5,059 | 101,548 | — | 308 |
| 2024 | 0001018724-25-000004 | 2024-12-31 | 13,245 | 59,236 | 44,742 | 5,201 | 98,535 | — | 308 |
| 2025 | 0001018724-26-000004 | 2025-12-31 | 13,554 | 60,506 | 43,825 | 5,259 | 99,832 | — | 309 |

## AXP

American Express Company · CIK 0000004962 · fiscal year ends in December · 336 us-gaap tags in its pinned filings

| FY | Accession | Period of report | Item 1 | Item 1A | Item 7 | Item 7A | Item 8 | Items 1-7A (10-K text, sections not separable) | Chunks |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| 2023 | 0000004962-24-000013 | 2023-12-31 | 87,118 | 102,572 | 142,392 | 175 | 153,572 | — | 678 |
| 2024 | 0000004962-25-000016 | 2024-12-31 | 90,164 | 104,481 | 142,574 | 175 | 161,100 | — | 697 |
| 2025 | 0000004962-26-000080 | 2025-12-31 | 86,325 | 112,754 | 139,321 | 175 | 161,853 | — | 693 |

## C

Citigroup Inc. · CIK 0000831001 · fiscal year ends in December · 401 us-gaap tags in its pinned filings

| FY | Accession | Period of report | Item 1 | Item 1A | Item 7 | Item 7A | Item 8 | Items 1-7A (10-K text, sections not separable) | Chunks |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| 2023 | 0000831001-24-000033 | 2023-12-31 | in 1-7A | 100,264 (approx.) | 249,019 (approx.) | in 1-7A | 474,888 (relocated) | 143,427 (approx.) | 1,339 |
| 2024 | 0000831001-25-000067 | 2024-12-31 | in 1-7A | 96,973 (approx.) | 258,227 (approx.) | in 1-7A | 466,862 (relocated) | 134,459 (approx.) | 1,331 |
| 2025 | 0000831001-26-000011 | 2025-12-31 | in 1-7A | 88,504 (approx.) | 227,210 (approx.) | in 1-7A | 440,368 (relocated) | 150,592 (approx.) | 1,256 |

## COF

Capital One Financial Corporation · CIK 0000927628 · fiscal year ends in December · 380 us-gaap tags in its pinned filings

| FY | Accession | Period of report | Item 1 | Item 1A | Item 7 | Item 7A | Item 8 | Items 1-7A (10-K text, sections not separable) | Chunks |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| 2023 | 0000927628-24-000094 | 2023-12-31 | 77,289 | 118,452 | 182,277 | 238 | 213,806 | — | 830 |
| 2024 | 0000927628-25-000092 | 2024-12-31 | 81,765 | 131,563 | 182,015 | 238 | 210,523 | — | 853 |
| 2025 | 0000927628-26-000024 | 2025-12-31 | 83,324 | 162,722 | 187,446 | 238 | 245,490 | — | 952 |

## COST

Costco Wholesale Corporation · CIK 0000909832 · fiscal year ends in August · 253 us-gaap tags in its pinned filings

| FY | Accession | Period of report | Item 1 | Item 1A | Item 7 | Item 7A | Item 8 | Items 1-7A (10-K text, sections not separable) | Chunks |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| 2024 | 0000909832-24-000049 | 2024-09-01 | 20,080 | 40,637 | 26,389 | 4,441 | 71,546 | — | 230 |
| 2025 | 0000909832-25-000101 | 2025-08-31 | 20,361 | 42,362 | 25,596 | 4,442 | 68,118 | — | 226 |
| 2026 | 0000909832-26-000093 | 2026-08-30 | 19,399 | 44,350 | 27,217 | 4,247 | 69,154 | — | 234 |

## GOOGL

Alphabet Inc. · CIK 0001652044 · fiscal year ends in December · 302 us-gaap tags in its pinned filings

| FY | Accession | Period of report | Item 1 | Item 1A | Item 7 | Item 7A | Item 8 | Items 1-7A (10-K text, sections not separable) | Chunks |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| 2023 | 0001652044-24-000022 | 2023-12-31 | 32,347 | 75,771 | 55,649 | 9,576 | 90,654 | — | 367 |
| 2024 | 0001652044-25-000014 | 2024-12-31 | 30,568 | 83,024 | 53,860 | 9,603 | 93,454 | — | 382 |
| 2025 | 0001652044-26-000018 | 2025-12-31 | 23,696 | 84,907 | 49,194 | 7,570 | 96,067 | — | 361 |

## GS

The Goldman Sachs Group, Inc. · CIK 0000886982 · fiscal year ends in December · 421 us-gaap tags in its pinned filings

| FY | Accession | Period of report | Item 1 | Item 1A | Item 7 | Item 7A | Item 8 | Items 1-7A (10-K text, sections not separable) | Chunks |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| 2023 | 0000886982-24-000006 | 2023-12-31 | 153,626 | 139,572 | 247,123 | 336 | 375,326 | — | 1,279 |
| 2024 | 0000886982-25-000005 | 2024-12-31 | 151,040 | 142,176 | 248,298 | 336 | 367,241 | — | 1,275 |
| 2025 | 0000886982-26-000091 | 2025-12-31 | 149,780 | 139,751 | 262,628 | 336 | 345,625 | — | 1,258 |

## IBM

International Business Machines Corporation · CIK 0000051143 · fiscal year ends in December · 365 us-gaap tags in its pinned filings

| FY | Accession | Period of report | Item 1 | Item 1A | Item 7 | Item 7A | Item 8 | Items 1-7A (10-K text, sections not separable) | Chunks |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| 2023 | 0000051143-24-000012 | 2023-12-31 | 9,436 | 35,039 | 129,154 (EX-13) | 218 | 222,718 (EX-13) | — | 552 |
| 2024 | 0000051143-25-000015 | 2024-12-31 | 9,649 | 36,366 | 137,320 (EX-13) | 210 | 230,344 (EX-13) | — | 580 |
| 2025 | 0000051143-26-000010 | 2025-12-31 | 9,564 | 36,149 | 120,115 (EX-13) | 210 | 205,361 (EX-13) | — | 526 |

## JNJ

Johnson & Johnson · CIK 0000200406 · fiscal year ends in December · 341 us-gaap tags in its pinned filings

| FY | Accession | Period of report | Item 1 | Item 1A | Item 7 | Item 7A | Item 8 | Items 1-7A (10-K text, sections not separable) | Chunks |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| 2023 | 0000200406-24-000013 | 2023-12-31 | 32,867 | 42,281 | 59,561 | 482 | 178,055 | — | 435 |
| 2024 | 0000200406-25-000038 | 2024-12-29 | 32,065 | 41,319 | 61,178 | 482 | 181,323 | — | 439 |
| 2025 | 0000200406-26-000016 | 2025-12-28 | 34,517 | 43,404 | 59,766 | 506 | 174,554 | — | 430 |

## JPM

JPMorgan Chase & Co. · CIK 0000019617 · fiscal year ends in December · 451 us-gaap tags in its pinned filings

| FY | Accession | Period of report | Item 1 | Item 1A | Item 7 | Item 7A | Item 8 | Items 1-7A (10-K text, sections not separable) | Chunks |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| 2023 | 0000019617-24-000225 | 2023-12-31 | 42,406 (approx.) | 131,901 (approx.) | in 1-7A | 250 (approx.) | 415,200 (relocated) | 425,610 (approx.) | 1,394 |
| 2024 | 0000019617-25-000270 | 2024-12-31 | 40,126 (approx.) | 136,069 (approx.) | in 1-7A | 250 (approx.) | 411,492 (relocated) | 324,330 (approx.) | 1,260 |
| 2025 | 0001628280-26-008131 | 2025-12-31 | 38,784 (approx.) | 112,431 (approx.) | in 1-7A | 250 (approx.) | 404,989 (relocated) | 318,628 (approx.) | 1,204 |

## KO

The Coca-Cola Company · CIK 0000021344 · fiscal year ends in December · 412 us-gaap tags in its pinned filings

| FY | Accession | Period of report | Item 1 | Item 1A | Item 7 | Item 7A | Item 8 | Items 1-7A (10-K text, sections not separable) | Chunks |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| 2023 | 0000021344-24-000009 | 2023-12-31 | 54,683 | 89,267 | 105,210 | 6,022 | 190,462 | — | 623 |
| 2024 | 0000021344-25-000011 | 2024-12-31 | 54,906 | 90,736 | 106,724 | 6,024 | 184,927 | — | 625 |
| 2025 | 0001628280-26-010047 | 2025-12-31 | 55,304 | 92,325 | 103,488 | 6,021 | 183,171 | — | 616 |

## MA

Mastercard Incorporated · CIK 0001141391 · fiscal year ends in December · 296 us-gaap tags in its pinned filings

| FY | Accession | Period of report | Item 1 | Item 1A | Item 7 | Item 7A | Item 8 | Items 1-7A (10-K text, sections not separable) | Chunks |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| 2023 | 0001141391-24-000022 | 2023-12-31 | 77,841 | 82,405 | 43,628 | 4,499 | 142,552 | — | 485 |
| 2024 | 0001141391-25-000011 | 2024-12-31 | 79,079 | 81,035 | 39,822 | 4,506 | 137,568 | — | 474 |
| 2025 | 0001141391-26-000013 | 2025-12-31 | 83,930 | 82,596 | 38,201 | 4,418 | 132,795 | — | 469 |

## MCO

Moody's Corporation · CIK 0001059556 · fiscal year ends in December · 336 us-gaap tags in its pinned filings

| FY | Accession | Period of report | Item 1 | Item 1A | Item 7 | Item 7A | Item 8 | Items 1-7A (10-K text, sections not separable) | Chunks |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| 2023 | 0001059556-24-000017 | 2023-12-31 | 38,616 | 70,569 | 70,656 | 221 | 115,550 | — | 413 |
| 2024 | 0001059556-25-000025 | 2024-12-31 | 36,715 | 72,657 | 65,266 | 221 | 107,495 | — | 398 |
| 2025 | 0001628280-26-009136 | 2025-12-31 | 33,779 | 78,203 | 69,984 | 221 | 109,356 | — | 413 |

## META

Meta Platforms, Inc. · CIK 0001326801 · fiscal year ends in December · 269 us-gaap tags in its pinned filings

| FY | Accession | Period of report | Item 1 | Item 1A | Item 7 | Item 7A | Item 8 | Items 1-7A (10-K text, sections not separable) | Chunks |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| 2023 | 0001326801-24-000012 | 2023-12-31 | 36,830 | 181,399 | 63,029 | 5,339 | 98,667 | — | 533 |
| 2024 | 0001326801-25-000017 | 2024-12-31 | 40,242 | 188,137 | 56,531 | 5,939 | 105,528 | — | 543 |
| 2025 | 0001628280-26-003942 | 2025-12-31 | 24,514 | 195,047 | 56,071 | 5,944 | 121,419 | — | 558 |

## MS

Morgan Stanley · CIK 0000895421 · fiscal year ends in December · 375 us-gaap tags in its pinned filings

| FY | Accession | Period of report | Item 1 | Item 1A | Item 7 | Item 7A | Item 8 | Items 1-7A (10-K text, sections not separable) | Chunks |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| 2023 | 0000895421-24-000300 | 2023-12-31 | 44,442 | 74,189 | 124,052 | 79,608 | 239,733 | — | 781 |
| 2024 | 0000895421-25-000304 | 2024-12-31 | 46,018 | 72,746 | 116,423 | 92,102 | 244,127 | — | 801 |
| 2025 | 0000895421-26-000086 | 2025-12-31 | 44,876 | 72,288 | 122,606 | 90,788 | 239,436 | — | 789 |

## MSFT

Microsoft Corporation · CIK 0000789019 · fiscal year ends in June · 268 us-gaap tags in its pinned filings

| FY | Accession | Period of report | Item 1 | Item 1A | Item 7 | Item 7A | Item 8 | Items 1-7A (10-K text, sections not separable) | Chunks |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| 2024 | 0000950170-24-087843 | 2024-06-30 | 69,878 | 73,749 | 48,742 | 1,972 | 77,019 | — | 379 |
| 2025 | 0000950170-25-100235 | 2025-06-30 | 48,629 | 68,807 | 45,450 | 1,950 | 67,353 | — | 327 |
| 2026 | 0001193125-26-323660 | 2026-06-30 | 41,145 | 81,040 | 47,840 | 1,949 | 70,313 | — | 338 |

## NFLX

Netflix, Inc. · CIK 0001065280 · fiscal year ends in December · 262 us-gaap tags in its pinned filings

| FY | Accession | Period of report | Item 1 | Item 1A | Item 7 | Item 7A | Item 8 | Items 1-7A (10-K text, sections not separable) | Chunks |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| 2023 | 0001065280-24-000030 | 2023-12-31 | 11,005 | 70,283 | 29,209 | 5,132 | 55,419 (relocated) | — | 241 |
| 2024 | 0001065280-25-000044 | 2024-12-31 | 10,671 | 70,252 | 28,437 | 7,799 | 61,597 (relocated) | — | 253 |
| 2025 | 0001065280-26-000034 | 2025-12-31 | 9,167 | 75,165 | 33,141 | 6,735 | 72,078 (relocated) | — | 277 |

## NKE

NIKE, Inc. · CIK 0000320187 · fiscal year ends in May · 213 us-gaap tags in its pinned filings

| FY | Accession | Period of report | Item 1 | Item 1A | Item 7 | Item 7A | Item 8 | Items 1-7A (10-K text, sections not separable) | Chunks |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| 2024 | 0000320187-24-000044 | 2024-05-31 | 38,839 | 97,968 | 63,137 | 6,668 | 93,837 | — | 419 |
| 2025 | 0000320187-25-000047 | 2025-05-31 | 38,052 | 96,405 | 57,816 | 6,703 | 91,972 | — | 401 |
| 2026 | 0000320187-26-000088 | 2026-05-31 | 36,891 | 96,943 | 58,487 | 6,662 | 92,501 | — | 408 |

## NVDA

NVIDIA Corporation · CIK 0001045810 · fiscal year ends in January · 273 us-gaap tags in its pinned filings

| FY | Accession | Period of report | Item 1 | Item 1A | Item 7 | Item 7A | Item 8 | Items 1-7A (10-K text, sections not separable) | Chunks |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| 2024 | 0001045810-24-000029 | 2024-01-28 | 51,538 | 106,657 | 34,778 | 3,282 | 75,217 (relocated) | — | 377 |
| 2025 | 0001045810-25-000023 | 2025-01-26 | 54,750 | 109,278 | 29,603 | 3,292 | 73,586 (relocated) | — | 375 |
| 2026 | 0001045810-26-000021 | 2026-01-25 | 48,190 | 110,353 | 31,049 | 4,245 | 72,729 (relocated) | — | 372 |

## PFE

Pfizer Inc. · CIK 0000078003 · fiscal year ends in December · 350 us-gaap tags in its pinned filings

| FY | Accession | Period of report | Item 1 | Item 1A | Item 7 | Item 7A | Item 8 | Items 1-7A (10-K text, sections not separable) | Chunks |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| 2023 | 0000078003-24-000039 | 2023-12-31 | 90,497 | 82,816 | 87,521 | 293 | 234,669 | — | 692 |
| 2024 | 0000078003-25-000054 | 2024-12-31 | 86,935 | 78,794 | 90,209 | 293 | 224,697 | — | 679 |
| 2025 | 0000078003-26-000026 | 2025-12-31 | 90,164 | 87,169 | 90,521 | 293 | 206,008 | — | 663 |

## SPGI

S&P Global Inc. · CIK 0000064040 · fiscal year ends in December · 284 us-gaap tags in its pinned filings

| FY | Accession | Period of report | Item 1 | Item 1A | Item 7 | Item 7A | Item 8 | Items 1-7A (10-K text, sections not separable) | Chunks |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| 2023 | 0000064040-24-000071 | 2023-12-31 | 30,448 | 85,104 | 125,686 | 1,570 | 160,078 | — | 568 |
| 2024 | 0000064040-25-000052 | 2024-12-31 | 16,475 | 86,867 | 130,558 | 1,605 | 151,870 | — | 539 |
| 2025 | 0000064040-26-000013 | 2025-12-31 | 16,753 | 104,400 | 133,622 | 1,462 | 152,691 | — | 571 |

## UNH

UnitedHealth Group Incorporated · CIK 0000731766 · fiscal year ends in December · 316 us-gaap tags in its pinned filings

| FY | Accession | Period of report | Item 1 | Item 1A | Item 7 | Item 7A | Item 8 | Items 1-7A (10-K text, sections not separable) | Chunks |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| 2023 | 0000731766-24-000081 | 2023-12-31 | 48,023 | 66,174 | 34,110 | 3,635 | 66,668 | — | 301 |
| 2024 | 0000731766-25-000063 | 2024-12-31 | 46,887 | 65,605 | 38,664 | 2,342 | 67,072 | — | 306 |
| 2025 | 0000731766-26-000062 | 2025-12-31 | 46,807 | 66,798 | 42,658 | 2,375 | 79,685 | — | 334 |

## VZ

Verizon Communications Inc. · CIK 0000732712 · fiscal year ends in December · 333 us-gaap tags in its pinned filings

| FY | Accession | Period of report | Item 1 | Item 1A | Item 7 | Item 7A | Item 8 | Items 1-7A (10-K text, sections not separable) | Chunks |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| 2023 | 0000732712-24-000010 | 2023-12-31 | 49,197 | 31,286 | 106,403 | 7,415 | 157,941 | — | 489 |
| 2024 | 0000732712-25-000006 | 2024-12-31 | 48,327 | 35,566 | 105,680 | 6,640 | 159,522 | — | 494 |
| 2025 | 0000732712-26-000007 | 2025-12-31 | 39,257 | 36,359 | 103,162 | 6,735 | 159,897 | — | 483 |

## WMT

Walmart Inc. · CIK 0000104169 · fiscal year ends in January · 253 us-gaap tags in its pinned filings

| FY | Accession | Period of report | Item 1 | Item 1A | Item 7 | Item 7A | Item 8 | Items 1-7A (10-K text, sections not separable) | Chunks |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| 2024 | 0000104169-24-000056 | 2024-01-31 | 45,658 | 88,866 | 55,138 | 4,657 | 90,062 (relocated) | — | 399 |
| 2025 | 0000104169-25-000021 | 2025-01-31 | 39,877 | 97,563 | 52,590 | 4,750 | 92,172 | — | 406 |
| 2026 | 0000104169-26-000055 | 2026-01-31 | 37,344 | 93,240 | 51,598 | 4,302 | 85,715 | — | 385 |
