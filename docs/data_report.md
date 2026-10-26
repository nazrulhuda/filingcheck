# Data report

Written by `make ingest` from `data/manifest.json` and the files the ingest stages produce. Do not edit by hand.

## Totals

| | Count |
|---|---:|
| Companies | 25 |
| Filings | 75 |
| Items saved | 372 |
| Chunks | 44,272 |
| us-gaap tags (all companies) | 16,077 |
| Number tables set aside (table_chunks) | 7,794 |

## Gaps

No filing is missing an Item.

Items under 2,000 characters:

- AXP FY2023: Item 7A has 194 characters
- AXP FY2024: Item 7A has 194 characters
- AXP FY2025: Item 7A has 194 characters
- COF FY2023: Item 7A has 257 characters
- COF FY2024: Item 7A has 257 characters
- COF FY2025: Item 7A has 257 characters
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
- SPGI FY2023: Item 7A has 1,593 characters
- SPGI FY2024: Item 7A has 1,628 characters
- SPGI FY2025: Item 7A has 1,485 characters

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

- AAPL FY2023: 5
- AAPL FY2024: 4
- AAPL FY2025: 3
- AMZN FY2023: 1
- AMZN FY2024: 1
- AMZN FY2025: 1
- AXP FY2023: 19
- AXP FY2024: 19
- AXP FY2025: 17
- C FY2023: 1,165
- C FY2024: 1,112
- C FY2025: 1,070
- COF FY2023: 28
- COF FY2024: 32
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
- JPM FY2023: 58
- JPM FY2024: 62
- JPM FY2025: 54
- KO FY2023: 22
- KO FY2024: 28
- KO FY2025: 20
- MA FY2023: 2
- MA FY2024: 5
- MA FY2025: 2
- MCO FY2023: 28
- MCO FY2024: 27
- MCO FY2025: 26
- META FY2023: 3
- META FY2024: 3
- META FY2025: 3
- MS FY2023: 13
- MS FY2024: 17
- MS FY2025: 18
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
- SPGI FY2023: 56
- SPGI FY2024: 55
- SPGI FY2025: 56
- UNH FY2023: 1
- UNH FY2024: 1
- UNH FY2025: 3
- VZ FY2023: 26
- VZ FY2024: 31
- VZ FY2025: 30
- WMT FY2025: 2
- WMT FY2026: 2

## Number tables

Tables with more than half their non-empty cells numeric (contents lists aside) are taken out of the prose before the sections are cut, and each is saved as one record in table_chunks: its rows as "label: values" text, the Item that held it, and its position in the source document. companyfacts has whole-company numbers only; segment numbers are only in these tables. They are not searched with the chunks.

- Saved: 7,794, of which 326 lie outside the Items above

Where taking the tables out would move a section's start or end, that section is cut from the full document instead, and its tables are also left to the chunk filter:

- JPM FY2023: Item 7
- SPGI FY2023: Item 8
- SPGI FY2024: Item 8
- SPGI FY2025: Item 8

## AAPL

Apple Inc. · CIK 0000320193 · fiscal year ends in September · 503 us-gaap tags

| FY | Accession | Period of report | Item 1 | Item 1A | Item 7 | Item 7A | Item 8 | Chunks |
|---|---|---|---:|---:|---:|---:|---:|---:|
| 2023 | 0000320193-23-000106 | 2023-09-30 | 15,162 | 67,629 | 13,883 | 2,758 | 41,505 | 201 |
| 2024 | 0000320193-24-000123 | 2024-09-28 | 15,767 | 68,484 | 13,818 | 2,758 | 40,450 | 199 |
| 2025 | 0000320193-25-000079 | 2025-09-27 | 16,054 | 67,760 | 16,505 | 2,758 | 41,360 | 198 |

## AMZN

Amazon.com, Inc. · CIK 0001018724 · fiscal year ends in December · 545 us-gaap tags

| FY | Accession | Period of report | Item 1 | Item 1A | Item 7 | Item 7A | Item 8 | Chunks |
|---|---|---|---:|---:|---:|---:|---:|---:|
| 2023 | 0001018724-24-000008 | 2023-12-31 | 13,257 | 58,851 | 44,188 | 5,078 | 101,708 | 309 |
| 2024 | 0001018724-25-000004 | 2024-12-31 | 13,248 | 59,272 | 44,801 | 5,220 | 98,701 | 307 |
| 2025 | 0001018724-26-000004 | 2025-12-31 | 13,557 | 60,544 | 43,884 | 5,584 | 100,001 | 309 |

## AXP

American Express Company · CIK 0000004962 · fiscal year ends in December · 670 us-gaap tags

| FY | Accession | Period of report | Item 1 | Item 1A | Item 7 | Item 7A | Item 8 | Chunks |
|---|---|---|---:|---:|---:|---:|---:|---:|
| 2023 | 0000004962-24-000013 | 2023-12-31 | 87,186 | 102,651 | 142,592 | 194 | 153,885 | 679 |
| 2024 | 0000004962-25-000016 | 2024-12-31 | 90,233 | 104,560 | 142,781 | 194 | 161,434 | 697 |
| 2025 | 0000004962-26-000080 | 2025-12-31 | 86,325 | 112,781 | 139,340 | 194 | 161,853 | 694 |

## C

Citigroup Inc. · CIK 0000831001 · fiscal year ends in December · 796 us-gaap tags

| FY | Accession | Period of report | Item 1 | Item 1A | Item 7 | Item 7A | Item 8 | Items 1-7A (10-K text, sections not separable) | Chunks |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| 2023 | 0000831001-24-000033 | 2023-12-31 | in 1-7A | 100,297 (approx.) | 249,046 (approx.) | in 1-7A | 476,013 (relocated) | 139,575 (approx.) | 1,770 |
| 2024 | 0000831001-25-000067 | 2024-12-31 | in 1-7A | 96,990 (approx.) | 258,263 (approx.) | in 1-7A | 467,980 (relocated) | 133,489 (approx.) | 1,787 |
| 2025 | 0000831001-26-000011 | 2025-12-31 | in 1-7A | 88,529 (approx.) | 227,239 (approx.) | in 1-7A | 441,453 (relocated) | 150,506 (approx.) | 1,690 |

## COF

Capital One Financial Corporation · CIK 0000927628 · fiscal year ends in December · 1,041 us-gaap tags

| FY | Accession | Period of report | Item 1 | Item 1A | Item 7 | Item 7A | Item 8 | Chunks |
|---|---|---|---:|---:|---:|---:|---:|---:|
| 2023 | 0000927628-24-000094 | 2023-12-31 | 77,333 | 118,503 | 182,322 | 257 | 215,008 | 832 |
| 2024 | 0000927628-25-000092 | 2024-12-31 | 81,808 | 131,616 | 182,056 | 257 | 211,111 | 854 |
| 2025 | 0000927628-26-000024 | 2025-12-31 | 83,366 | 162,779 | 187,490 | 257 | 245,535 | 954 |

## COST

Costco Wholesale Corporation · CIK 0000909832 · fiscal year ends in August · 476 us-gaap tags

| FY | Accession | Period of report | Item 1 | Item 1A | Item 7 | Item 7A | Item 8 | Chunks |
|---|---|---|---:|---:|---:|---:|---:|---:|
| 2024 | 0000909832-24-000049 | 2024-09-01 | 20,089 | 40,692 | 26,437 | 4,442 | 71,689 | 229 |
| 2025 | 0000909832-25-000101 | 2025-08-31 | 20,374 | 42,417 | 25,648 | 4,442 | 68,260 | 228 |
| 2026 | 0000909832-26-000093 | 2026-08-30 | 19,409 | 44,404 | 27,267 | 4,248 | 69,298 | 235 |

## GOOGL

Alphabet Inc. · CIK 0001652044 · fiscal year ends in December · 543 us-gaap tags

| FY | Accession | Period of report | Item 1 | Item 1A | Item 7 | Item 7A | Item 8 | Chunks |
|---|---|---|---:|---:|---:|---:|---:|---:|
| 2023 | 0001652044-24-000022 | 2023-12-31 | 32,347 | 75,771 | 55,649 | 9,576 | 90,654 | 367 |
| 2024 | 0001652044-25-000014 | 2024-12-31 | 30,568 | 83,024 | 53,860 | 9,603 | 93,455 | 382 |
| 2025 | 0001652044-26-000018 | 2025-12-31 | 23,696 | 84,907 | 49,194 | 7,570 | 96,067 | 361 |

## GS

The Goldman Sachs Group, Inc. · CIK 0000886982 · fiscal year ends in December · 642 us-gaap tags

| FY | Accession | Period of report | Item 1 | Item 1A | Item 7 | Item 7A | Item 8 | Chunks |
|---|---|---|---:|---:|---:|---:|---:|---:|
| 2023 | 0000886982-24-000006 | 2023-12-31 | 153,626 | 139,572 | 247,123 | 336 | 375,326 | 1,279 |
| 2024 | 0000886982-25-000005 | 2024-12-31 | 151,040 | 142,176 | 248,298 | 336 | 367,241 | 1,275 |
| 2025 | 0000886982-26-000091 | 2025-12-31 | 149,780 | 139,751 | 262,628 | 336 | 345,625 | 1,258 |

## IBM

International Business Machines Corporation · CIK 0000051143 · fiscal year ends in December · 781 us-gaap tags

| FY | Accession | Period of report | Item 1 | Item 1A | Item 7 | Item 7A | Item 8 | Chunks |
|---|---|---|---:|---:|---:|---:|---:|---:|
| 2023 | 0000051143-24-000012 | 2023-12-31 | 9,436 | 35,055 | 129,302 (EX-13) | 218 | 223,073 (EX-13) | 552 |
| 2024 | 0000051143-25-000015 | 2024-12-31 | 9,649 | 36,380 | 137,480 (EX-13) | 210 | 230,687 (EX-13) | 580 |
| 2025 | 0000051143-26-000010 | 2025-12-31 | 9,565 | 36,167 | 120,254 (EX-13) | 210 | 205,695 (EX-13) | 525 |

## JNJ

Johnson & Johnson · CIK 0000200406 · fiscal year ends in December · 610 us-gaap tags

| FY | Accession | Period of report | Item 1 | Item 1A | Item 7 | Item 7A | Item 8 | Chunks |
|---|---|---|---:|---:|---:|---:|---:|---:|
| 2023 | 0000200406-24-000013 | 2023-12-31 | 32,877 | 42,293 | 59,605 | 482 | 178,203 | 433 |
| 2024 | 0000200406-25-000038 | 2024-12-29 | 32,075 | 41,332 | 61,223 | 482 | 181,470 | 440 |
| 2025 | 0000200406-26-000016 | 2025-12-28 | 34,526 | 43,416 | 59,811 | 506 | 174,709 | 430 |

## JPM

JPMorgan Chase & Co. · CIK 0000019617 · fiscal year ends in December · 918 us-gaap tags

| FY | Accession | Period of report | Item 1 | Item 1A | Item 7 | Item 7A | Item 8 | Items 1-7A (10-K text, sections not separable) | Chunks |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| 2023 | 0000019617-24-000225 | 2023-12-31 | 42,431 (approx.) | 132,015 (approx.) | in 1-7A | 250 (approx.) | 416,028 (relocated) | 425,642 (approx.) | 1,395 |
| 2024 | 0000019617-25-000270 | 2024-12-31 | 40,154 (approx.) | 136,203 (approx.) | in 1-7A | 250 (approx.) | 412,354 (relocated) | 323,990 (approx.) | 1,478 |
| 2025 | 0001628280-26-008131 | 2025-12-31 | 38,811 (approx.) | 112,539 (approx.) | in 1-7A | 250 (approx.) | 405,849 (relocated) | 320,754 (approx.) | 1,432 |

## KO

The Coca-Cola Company · CIK 0000021344 · fiscal year ends in December · 724 us-gaap tags

| FY | Accession | Period of report | Item 1 | Item 1A | Item 7 | Item 7A | Item 8 | Chunks |
|---|---|---|---:|---:|---:|---:|---:|---:|
| 2023 | 0000021344-24-000009 | 2023-12-31 | 54,720 | 89,332 | 106,596 | 6,026 | 191,878 | 625 |
| 2024 | 0000021344-25-000011 | 2024-12-31 | 54,940 | 90,801 | 106,824 | 6,028 | 185,225 | 623 |
| 2025 | 0001628280-26-010047 | 2025-12-31 | 55,340 | 92,387 | 104,820 | 6,026 | 185,645 | 623 |

## MA

Mastercard Incorporated · CIK 0001141391 · fiscal year ends in December · 607 us-gaap tags

| FY | Accession | Period of report | Item 1 | Item 1A | Item 7 | Item 7A | Item 8 | Chunks |
|---|---|---|---:|---:|---:|---:|---:|---:|
| 2023 | 0001141391-24-000022 | 2023-12-31 | 77,841 | 82,409 | 43,629 | 4,499 | 142,558 | 486 |
| 2024 | 0001141391-25-000011 | 2024-12-31 | 79,081 | 81,045 | 39,822 | 4,506 | 137,575 | 476 |
| 2025 | 0001141391-26-000013 | 2025-12-31 | 83,932 | 82,599 | 38,202 | 4,418 | 132,799 | 469 |

## MCO

Moody's Corporation · CIK 0001059556 · fiscal year ends in December · 705 us-gaap tags

| FY | Accession | Period of report | Item 1 | Item 1A | Item 7 | Item 7A | Item 8 | Chunks |
|---|---|---|---:|---:|---:|---:|---:|---:|
| 2023 | 0001059556-24-000017 | 2023-12-31 | 38,616 | 70,573 | 70,659 | 221 | 115,554 | 413 |
| 2024 | 0001059556-25-000025 | 2024-12-31 | 36,753 | 72,701 | 65,307 | 221 | 107,536 | 397 |
| 2025 | 0001628280-26-009136 | 2025-12-31 | 33,817 | 78,246 | 70,024 | 221 | 111,606 | 417 |

## META

Meta Platforms, Inc. · CIK 0001326801 · fiscal year ends in December · 462 us-gaap tags

| FY | Accession | Period of report | Item 1 | Item 1A | Item 7 | Item 7A | Item 8 | Chunks |
|---|---|---|---:|---:|---:|---:|---:|---:|
| 2023 | 0001326801-24-000012 | 2023-12-31 | 36,834 | 181,673 | 63,050 | 5,358 | 98,691 | 532 |
| 2024 | 0001326801-25-000017 | 2024-12-31 | 40,245 | 188,175 | 56,552 | 5,939 | 105,550 | 543 |
| 2025 | 0001628280-26-003942 | 2025-12-31 | 24,525 | 195,222 | 56,166 | 5,944 | 121,650 | 560 |

## MS

Morgan Stanley · CIK 0000895421 · fiscal year ends in December · 914 us-gaap tags

| FY | Accession | Period of report | Item 1 | Item 1A | Item 7 | Item 7A | Item 8 | Chunks |
|---|---|---|---:|---:|---:|---:|---:|---:|
| 2023 | 0000895421-24-000300 | 2023-12-31 | 44,489 | 74,245 | 124,109 | 79,661 | 240,546 | 778 |
| 2024 | 0000895421-25-000304 | 2024-12-31 | 46,066 | 72,798 | 116,477 | 92,158 | 244,938 | 799 |
| 2025 | 0000895421-26-000086 | 2025-12-31 | 44,923 | 72,343 | 122,657 | 90,843 | 239,796 | 789 |

## MSFT

Microsoft Corporation · CIK 0000789019 · fiscal year ends in June · 562 us-gaap tags

| FY | Accession | Period of report | Item 1 | Item 1A | Item 7 | Item 7A | Item 8 | Chunks |
|---|---|---|---:|---:|---:|---:|---:|---:|
| 2024 | 0000950170-24-087843 | 2024-06-30 | 69,878 | 73,749 | 48,742 | 1,972 | 77,019 | 379 |
| 2025 | 0000950170-25-100235 | 2025-06-30 | 48,629 | 68,807 | 45,450 | 1,950 | 67,353 | 327 |
| 2026 | 0001193125-26-323660 | 2026-06-30 | 41,145 | 81,040 | 47,840 | 1,949 | 70,313 | 338 |

## NFLX

Netflix, Inc. · CIK 0001065280 · fiscal year ends in December · 490 us-gaap tags

| FY | Accession | Period of report | Item 1 | Item 1A | Item 7 | Item 7A | Item 8 | Chunks |
|---|---|---|---:|---:|---:|---:|---:|---:|
| 2023 | 0001065280-24-000030 | 2023-12-31 | 11,006 | 70,347 | 29,257 | 5,133 | 55,535 (relocated) | 243 |
| 2024 | 0001065280-25-000044 | 2024-12-31 | 10,671 | 70,314 | 28,485 | 7,799 | 61,724 (relocated) | 253 |
| 2025 | 0001065280-26-000034 | 2025-12-31 | 9,167 | 75,225 | 33,193 | 6,735 | 72,213 (relocated) | 277 |

## NKE

NIKE, Inc. · CIK 0000320187 · fiscal year ends in May · 444 us-gaap tags

| FY | Accession | Period of report | Item 1 | Item 1A | Item 7 | Item 7A | Item 8 | Chunks |
|---|---|---|---:|---:|---:|---:|---:|---:|
| 2024 | 0000320187-24-000044 | 2024-05-31 | 38,878 | 98,014 | 63,176 | 6,706 | 93,878 | 420 |
| 2025 | 0000320187-25-000047 | 2025-05-31 | 38,091 | 96,451 | 57,854 | 6,741 | 92,011 | 403 |
| 2026 | 0000320187-26-000088 | 2026-05-31 | 36,929 | 96,989 | 58,526 | 6,700 | 92,539 | 408 |

## NVDA

NVIDIA Corporation · CIK 0001045810 · fiscal year ends in January · 627 us-gaap tags

| FY | Accession | Period of report | Item 1 | Item 1A | Item 7 | Item 7A | Item 8 | Chunks |
|---|---|---|---:|---:|---:|---:|---:|---:|
| 2024 | 0001045810-24-000029 | 2024-01-28 | 51,565 | 106,731 | 34,831 | 3,283 | 75,357 (relocated) | 381 |
| 2025 | 0001045810-25-000023 | 2025-01-26 | 54,778 | 109,356 | 29,655 | 3,293 | 73,720 (relocated) | 378 |
| 2026 | 0001045810-26-000021 | 2026-01-25 | 48,214 | 110,433 | 31,096 | 4,245 | 72,869 (relocated) | 371 |

## PFE

Pfizer Inc. · CIK 0000078003 · fiscal year ends in December · 667 us-gaap tags

| FY | Accession | Period of report | Item 1 | Item 1A | Item 7 | Item 7A | Item 8 | Chunks |
|---|---|---|---:|---:|---:|---:|---:|---:|
| 2023 | 0000078003-24-000039 | 2023-12-31 | 90,506 | 82,823 | 87,525 | 293 | 234,679 | 693 |
| 2024 | 0000078003-25-000054 | 2024-12-31 | 86,942 | 78,797 | 90,213 | 293 | 224,707 | 678 |
| 2025 | 0000078003-26-000026 | 2025-12-31 | 90,171 | 87,173 | 90,528 | 293 | 206,019 | 663 |

## SPGI

S&P Global Inc. · CIK 0000064040 · fiscal year ends in December · 622 us-gaap tags

| FY | Accession | Period of report | Item 1 | Item 1A | Item 7 | Item 7A | Item 8 | Chunks |
|---|---|---|---:|---:|---:|---:|---:|---:|
| 2023 | 0000064040-24-000071 | 2023-12-31 | 30,474 | 85,173 | 126,610 | 1,593 | 160,124 | 566 |
| 2024 | 0000064040-25-000052 | 2024-12-31 | 16,564 | 86,936 | 131,484 | 1,628 | 151,913 | 539 |
| 2025 | 0000064040-26-000013 | 2025-12-31 | 16,842 | 104,480 | 133,774 | 1,485 | 152,734 | 571 |

## UNH

UnitedHealth Group Incorporated · CIK 0000731766 · fiscal year ends in December · 573 us-gaap tags

| FY | Accession | Period of report | Item 1 | Item 1A | Item 7 | Item 7A | Item 8 | Chunks |
|---|---|---|---:|---:|---:|---:|---:|---:|
| 2023 | 0000731766-24-000081 | 2023-12-31 | 48,048 | 66,211 | 34,162 | 3,635 | 66,805 | 303 |
| 2024 | 0000731766-25-000063 | 2024-12-31 | 46,906 | 65,664 | 38,723 | 2,361 | 67,207 | 306 |
| 2025 | 0000731766-26-000062 | 2025-12-31 | 46,830 | 66,841 | 42,718 | 2,394 | 80,838 | 335 |

## VZ

Verizon Communications Inc. · CIK 0000732712 · fiscal year ends in December · 677 us-gaap tags

| FY | Accession | Period of report | Item 1 | Item 1A | Item 7 | Item 7A | Item 8 | Chunks |
|---|---|---|---:|---:|---:|---:|---:|---:|
| 2023 | 0000732712-24-000010 | 2023-12-31 | 49,224 | 31,299 | 106,501 | 7,417 | 158,186 | 488 |
| 2024 | 0000732712-25-000006 | 2024-12-31 | 48,352 | 35,585 | 105,781 | 6,640 | 159,777 | 495 |
| 2025 | 0000732712-26-000007 | 2025-12-31 | 39,273 | 36,379 | 103,283 | 6,736 | 160,150 | 484 |

## WMT

Walmart Inc. · CIK 0000104169 · fiscal year ends in January · 478 us-gaap tags

| FY | Accession | Period of report | Item 1 | Item 1A | Item 7 | Item 7A | Item 8 | Chunks |
|---|---|---|---:|---:|---:|---:|---:|---:|
| 2024 | 0000104169-24-000056 | 2024-01-31 | 45,690 | 88,927 | 55,191 | 4,661 | 10,488 | 287 |
| 2025 | 0000104169-25-000021 | 2025-01-31 | 39,901 | 97,631 | 52,646 | 4,754 | 92,317 | 408 |
| 2026 | 0000104169-26-000055 | 2026-01-31 | 37,364 | 93,305 | 51,650 | 4,306 | 85,859 | 389 |
