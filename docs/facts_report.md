# XBRL facts report

The numeric facts of each pinned filing, read from the filing's own inline XBRL (`data/facts.jsonl`), and a cross-check against the SEC's companyfacts files. For every filing and every candidate tag of the metric map, the company totals (facts with no dimensions) that end on the filing's period of report are compared with the companyfacts rows of the same accession, tag and period. companyfacts is only a cross-check; the numbers come from the filings. Written by `make verify-facts`; do not edit by hand.

## Facts per filing

| Ticker | FY | Accession | Facts | Company totals |
|---|---:|---|---:|---:|
| AAPL | 2024 | 0000320193-24-000123 | 877 | 476 |
| AAPL | 2025 | 0000320193-25-000079 | 878 | 471 |
| AAPL | 2026 | 0000320193-26-000026 | 965 | 507 |
| AMZN | 2023 | 0001018724-24-000008 | 1,175 | 649 |
| AMZN | 2024 | 0001018724-25-000004 | 1,149 | 640 |
| AMZN | 2025 | 0001018724-26-000004 | 1,241 | 730 |
| AXP | 2023 | 0000004962-24-000013 | 2,107 | 723 |
| AXP | 2024 | 0000004962-25-000016 | 2,201 | 724 |
| AXP | 2025 | 0000004962-26-000080 | 2,259 | 701 |
| C | 2023 | 0000831001-24-000033 | 8,820 | 1,203 |
| C | 2024 | 0000831001-25-000067 | 9,022 | 1,208 |
| C | 2025 | 0000831001-26-000011 | 9,059 | 1,262 |
| COF | 2023 | 0000927628-24-000094 | 3,909 | 900 |
| COF | 2024 | 0000927628-25-000092 | 4,013 | 875 |
| COF | 2025 | 0000927628-26-000024 | 4,470 | 990 |
| COST | 2024 | 0000909832-24-000049 | 778 | 525 |
| COST | 2025 | 0000909832-25-000101 | 769 | 513 |
| COST | 2026 | 0000909832-26-000093 | 752 | 514 |
| GOOGL | 2023 | 0001652044-24-000022 | 1,298 | 629 |
| GOOGL | 2024 | 0001652044-25-000014 | 1,391 | 696 |
| GOOGL | 2025 | 0001652044-26-000018 | 1,504 | 737 |
| GS | 2023 | 0000886982-24-000006 | 5,807 | 1,116 |
| GS | 2024 | 0000886982-25-000005 | 5,724 | 1,107 |
| GS | 2025 | 0000886982-26-000091 | 5,231 | 1,089 |
| IBM | 2023 | 0000051143-24-000012 | 3,418 | 924 |
| IBM | 2024 | 0000051143-25-000015 | 3,430 | 925 |
| IBM | 2025 | 0000051143-26-000010 | 3,241 | 931 |
| JNJ | 2023 | 0000200406-24-000013 | 2,835 | 911 |
| JNJ | 2024 | 0000200406-25-000038 | 2,834 | 793 |
| JNJ | 2025 | 0000200406-26-000016 | 2,800 | 800 |
| JPM | 2023 | 0000019617-24-000225 | 7,275 | 1,210 |
| JPM | 2024 | 0000019617-25-000270 | 7,316 | 1,226 |
| JPM | 2025 | 0001628280-26-008131 | 7,424 | 1,302 |
| KO | 2023 | 0000021344-24-000009 | 2,602 | 869 |
| KO | 2024 | 0000021344-25-000011 | 2,271 | 852 |
| KO | 2025 | 0001628280-26-010047 | 2,276 | 885 |
| MA | 2023 | 0001141391-24-000022 | 1,633 | 767 |
| MA | 2024 | 0001141391-25-000011 | 1,438 | 717 |
| MA | 2025 | 0001141391-26-000013 | 1,383 | 693 |
| MCO | 2023 | 0001059556-24-000017 | 2,515 | 828 |
| MCO | 2024 | 0001059556-25-000025 | 2,532 | 821 |
| MCO | 2025 | 0001628280-26-009136 | 2,646 | 855 |
| META | 2023 | 0001326801-24-000012 | 1,043 | 532 |
| META | 2024 | 0001326801-25-000017 | 985 | 551 |
| META | 2025 | 0001628280-26-003942 | 1,036 | 592 |
| MS | 2023 | 0000895421-24-000300 | 5,614 | 1,006 |
| MS | 2024 | 0000895421-25-000304 | 5,727 | 1,034 |
| MS | 2025 | 0000895421-26-000086 | 5,695 | 1,096 |
| MSFT | 2024 | 0000950170-24-087843 | 1,448 | 632 |
| MSFT | 2025 | 0000950170-25-100235 | 1,428 | 636 |
| MSFT | 2026 | 0001193125-26-323660 | 1,464 | 656 |
| NFLX | 2023 | 0001065280-24-000030 | 863 | 544 |
| NFLX | 2024 | 0001065280-25-000044 | 1,075 | 574 |
| NFLX | 2025 | 0001065280-26-000034 | 1,183 | 586 |
| NKE | 2024 | 0000320187-24-000044 | 1,196 | 451 |
| NKE | 2025 | 0000320187-25-000047 | 1,298 | 469 |
| NKE | 2026 | 0000320187-26-000088 | 1,344 | 500 |
| NVDA | 2024 | 0001045810-24-000029 | 1,096 | 627 |
| NVDA | 2025 | 0001045810-25-000023 | 1,116 | 641 |
| NVDA | 2026 | 0001045810-26-000021 | 1,031 | 584 |
| PFE | 2023 | 0000078003-24-000039 | 2,876 | 846 |
| PFE | 2024 | 0000078003-25-000054 | 2,779 | 852 |
| PFE | 2025 | 0000078003-26-000026 | 2,780 | 893 |
| SPGI | 2023 | 0000064040-24-000071 | 2,070 | 635 |
| SPGI | 2024 | 0000064040-25-000052 | 2,006 | 628 |
| SPGI | 2025 | 0000064040-26-000013 | 2,001 | 653 |
| UNH | 2023 | 0000731766-24-000081 | 1,819 | 646 |
| UNH | 2024 | 0000731766-25-000063 | 1,959 | 687 |
| UNH | 2025 | 0000731766-26-000062 | 2,063 | 749 |
| VZ | 2023 | 0000732712-24-000010 | 2,085 | 760 |
| VZ | 2024 | 0000732712-25-000006 | 2,138 | 806 |
| VZ | 2025 | 0000732712-26-000007 | 2,157 | 793 |
| WMT | 2024 | 0000104169-24-000056 | 1,100 | 549 |
| WMT | 2025 | 0000104169-25-000021 | 1,082 | 535 |
| WMT | 2026 | 0000104169-26-000055 | 1,074 | 543 |
| **All** | | | **199,899** | **57,580** |

## Cross-check with companyfacts

Candidate tags compared: 20 (`Revenues`, `RevenueFromContractWithCustomerExcludingAssessedTax`, `RevenuesNetOfInterestExpense`, `SalesRevenueNet`, `NetIncomeLoss`, `ProfitLoss`, `EarningsPerShareDiluted`, `OperatingIncomeLoss`, `Assets`, `Liabilities`, `StockholdersEquity`, `StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest`, `NetCashProvidedByUsedInOperatingActivities`, `PaymentsToAcquirePropertyPlantAndEquipment`, `CashAndCashEquivalentsAtCarryingValue`, `CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents`, `LongTermDebtNoncurrent`, `LongTermDebt`, `dei:EntityCommonStockSharesOutstanding`, `CommonStockSharesOutstanding`).

- Agreements: 953
- Disagreements: 0
- Not in companyfacts: 15
- Not in the filing's XBRL: 0

| Ticker | FY | Agree | Disagree | Not in companyfacts | Not in the filing's XBRL |
|---|---:|---:|---:|---:|---:|
| AAPL | 2024 | 14 | 0 | 0 | 0 |
| AAPL | 2025 | 14 | 0 | 0 | 0 |
| AAPL | 2026 | 14 | 0 | 0 | 0 |
| AMZN | 2023 | 12 | 0 | 0 | 0 |
| AMZN | 2024 | 12 | 0 | 0 | 0 |
| AMZN | 2025 | 12 | 0 | 0 | 0 |
| AXP | 2023 | 12 | 0 | 0 | 0 |
| AXP | 2024 | 12 | 0 | 0 | 0 |
| AXP | 2025 | 12 | 0 | 0 | 0 |
| C | 2023 | 12 | 0 | 0 | 0 |
| C | 2024 | 12 | 0 | 0 | 0 |
| C | 2025 | 12 | 0 | 0 | 0 |
| COF | 2023 | 11 | 0 | 0 | 0 |
| COF | 2024 | 11 | 0 | 0 | 0 |
| COF | 2025 | 11 | 0 | 0 | 0 |
| COST | 2024 | 16 | 0 | 0 | 0 |
| COST | 2025 | 16 | 0 | 0 | 0 |
| COST | 2026 | 13 | 0 | 0 | 0 |
| GOOGL | 2023 | 13 | 0 | 0 | 0 |
| GOOGL | 2024 | 14 | 0 | 0 | 0 |
| GOOGL | 2025 | 14 | 0 | 0 | 0 |
| GS | 2023 | 11 | 0 | 0 | 0 |
| GS | 2024 | 11 | 0 | 0 | 0 |
| GS | 2025 | 11 | 0 | 0 | 0 |
| IBM | 2023 | 13 | 0 | 0 | 0 |
| IBM | 2024 | 13 | 0 | 0 | 0 |
| IBM | 2025 | 13 | 0 | 0 | 0 |
| JNJ | 2023 | 15 | 0 | 0 | 0 |
| JNJ | 2024 | 12 | 0 | 0 | 0 |
| JNJ | 2025 | 12 | 0 | 0 | 0 |
| JPM | 2023 | 10 | 0 | 0 | 0 |
| JPM | 2024 | 10 | 0 | 0 | 0 |
| JPM | 2025 | 10 | 0 | 0 | 0 |
| KO | 2023 | 14 | 0 | 0 | 0 |
| KO | 2024 | 12 | 0 | 0 | 0 |
| KO | 2025 | 12 | 0 | 0 | 0 |
| MA | 2023 | 13 | 0 | 0 | 0 |
| MA | 2024 | 13 | 0 | 0 | 0 |
| MA | 2025 | 13 | 0 | 0 | 0 |
| MCO | 2023 | 15 | 0 | 0 | 0 |
| MCO | 2024 | 15 | 0 | 0 | 0 |
| MCO | 2025 | 15 | 0 | 0 | 0 |
| META | 2023 | 13 | 0 | 0 | 0 |
| META | 2024 | 13 | 0 | 0 | 0 |
| META | 2025 | 13 | 0 | 0 | 0 |
| MS | 2023 | 13 | 0 | 0 | 0 |
| MS | 2024 | 13 | 0 | 0 | 0 |
| MS | 2025 | 13 | 0 | 0 | 0 |
| MSFT | 2024 | 14 | 0 | 0 | 0 |
| MSFT | 2025 | 14 | 0 | 0 | 0 |
| MSFT | 2026 | 14 | 0 | 0 | 0 |
| NFLX | 2023 | 14 | 0 | 0 | 0 |
| NFLX | 2024 | 14 | 0 | 0 | 0 |
| NFLX | 2025 | 14 | 0 | 0 | 0 |
| NKE | 2024 | 11 | 0 | 0 | 0 |
| NKE | 2025 | 11 | 0 | 0 | 0 |
| NKE | 2026 | 11 | 0 | 0 | 0 |
| NVDA | 2024 | 13 | 0 | 0 | 0 |
| NVDA | 2025 | 13 | 0 | 0 | 0 |
| NVDA | 2026 | 13 | 0 | 0 | 0 |
| PFE | 2023 | 14 | 0 | 0 | 0 |
| PFE | 2024 | 13 | 0 | 0 | 0 |
| PFE | 2025 | 13 | 0 | 0 | 0 |
| SPGI | 2023 | 15 | 0 | 0 | 0 |
| SPGI | 2024 | 0 | 0 | 15 | 0 |
| SPGI | 2025 | 15 | 0 | 0 | 0 |
| UNH | 2023 | 14 | 0 | 0 | 0 |
| UNH | 2024 | 14 | 0 | 0 | 0 |
| UNH | 2025 | 14 | 0 | 0 | 0 |
| VZ | 2023 | 10 | 0 | 0 | 0 |
| VZ | 2024 | 10 | 0 | 0 | 0 |
| VZ | 2025 | 10 | 0 | 0 | 0 |
| WMT | 2024 | 15 | 0 | 0 | 0 |
| WMT | 2025 | 15 | 0 | 0 | 0 |
| WMT | 2026 | 15 | 0 | 0 | 0 |

Every row that is not an agreement:

| Ticker | FY | Tag | Period | Status | Filing's XBRL | companyfacts |
|---|---:|---|---|---|---:|---:|
| SPGI | 2024 | `Assets` | 2024-12-31 | not in companyfacts | 60221000000 | — |
| SPGI | 2024 | `CashAndCashEquivalentsAtCarryingValue` | 2024-12-31 | not in companyfacts | 1666000000 | — |
| SPGI | 2024 | `CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents` | 2024-12-31 | not in companyfacts | 1666000000 | — |
| SPGI | 2024 | `CommonStockSharesOutstanding` | 2024-12-31 | not in companyfacts | 307800000 | — |
| SPGI | 2024 | `EarningsPerShareDiluted` | 2024-01-01 to 2024-12-31 | not in companyfacts | 12.35 | — |
| SPGI | 2024 | `Liabilities` | 2024-12-31 | not in companyfacts | 22713000000 | — |
| SPGI | 2024 | `LongTermDebt` | 2024-12-31 | not in companyfacts | 11398000000 | — |
| SPGI | 2024 | `LongTermDebtNoncurrent` | 2024-12-31 | not in companyfacts | 11394000000 | — |
| SPGI | 2024 | `NetCashProvidedByUsedInOperatingActivities` | 2024-01-01 to 2024-12-31 | not in companyfacts | 5689000000 | — |
| SPGI | 2024 | `NetIncomeLoss` | 2024-01-01 to 2024-12-31 | not in companyfacts | 3852000000 | — |
| SPGI | 2024 | `OperatingIncomeLoss` | 2024-01-01 to 2024-12-31 | not in companyfacts | 5580000000 | — |
| SPGI | 2024 | `ProfitLoss` | 2024-01-01 to 2024-12-31 | not in companyfacts | 4167000000 | — |
| SPGI | 2024 | `RevenueFromContractWithCustomerExcludingAssessedTax` | 2024-01-01 to 2024-12-31 | not in companyfacts | 14208000000 | — |
| SPGI | 2024 | `StockholdersEquity` | 2024-12-31 | not in companyfacts | 33159000000 | — |
| SPGI | 2024 | `StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest` | 2024-12-31 | not in companyfacts | 33256000000 | — |

## Conflicts

Facts with the same concept, period, unit and dimensions but different values in one filing. Both values are kept and marked `conflict: true`.

Conflicts: 0 facts in 0 groups


## companyfacts files used

| Ticker | SHA-256 | Equals its pin in `data/companyfacts_pins.json` |
|---|---|---|
| AAPL | `75a78f918313f3336823517d6c34908d23dd07f07e90e625c61e705e3bb6d27b` | yes |
| AMZN | `7549fb68446eee40e1f50a166fa06b2d2ee6349e07c8553a4828757e032d3cd4` | yes |
| AXP | `b2a09852e08682394b31f43d2a3ce17855bcd622882ac8541898c5c6d87ebbd3` | yes |
| C | `47a2282b54a0ba98d22fc935214d7de76afc94be6c12fed2466b62f1c3b31a73` | yes |
| COF | `5c47020035b023847b723b1a1e10f7f737533ee75cc279cf03721762f3a8581a` | yes |
| COST | `b675ced201b27ede2b0d26ca6fd873befe96a1afa9679339a2d0b964187dcdff` | yes |
| GOOGL | `a017f26ee88cb4a639d1c1ddb06d53b4afe22f0ac89cabec7cd67c88919fe1c5` | yes |
| GS | `c4a3a86c892629ac1e2daadbda5880b7fb1c2bd6dc1d9dbf27d4f4722b5e3bdf` | yes |
| IBM | `10fa1fafa25440b2159e2054dfe47628ba4ed353a258f526704cf9beda432bb8` | yes |
| JNJ | `9ce98e50414e9a6704eaf485e1868c2298c6ae36acc85a82c0a3737485303be7` | yes |
| JPM | `c12d739195e280fb76969bb1d74e295cf2fa397cd40ff05ac0dc095b7c0d6d71` | yes |
| KO | `53d363a9aa3071406cda9857654358f4dca42e174a1defb8cc1ce9ad2a4c9e40` | yes |
| MA | `78082e9cbae91bfa8c1480d214bd20c8d35fcbbcc72d71eaf01739c48b1e9511` | yes |
| MCO | `1852804bdfdd74d7cabb866d6c7f68bcdc800be2012e0067a9788cf048f5708d` | yes |
| META | `ecbeee451a002c65e854fd89c68c5e5762740427f9edba01f015d6bc668c3e43` | yes |
| MS | `fc0a2c4c4eaf82503b7a91c940e18748b8cc14a0f6c5df62226af1cf48426ee7` | yes |
| MSFT | `dd0308149a8e96497989ed7c690b5a49a00bef9ceafbb24638bda41e8ae938dd` | yes |
| NFLX | `fd31bc147b36495f6912e063188aea71434077236f4e995268620b47fda99e61` | yes |
| NKE | `d7aeceae21e6649e163d195729849349b27d909ab1a6eb4630a7c0c227acd890` | yes |
| NVDA | `19ef503a5770f5660964b3c3aea6937579d9b359da344afe6a9adf59c63d26ff` | yes |
| PFE | `bd072131f9dcf001f22e843fded5910c2c7fc178e2a739ce0c58b1934e84d566` | yes |
| SPGI | `f392828aca3ccbf6288cd285dc099cfa91409c5dd08816846c4ac8d10b12291d` | yes |
| UNH | `6c9dff59732b7c597542b2d5eadaae0313ca0de03defdba2c00203e693632d76` | yes |
| VZ | `659fb8cc8457296f19511259c9a134be9468bc03020aee4a92fb66b0c5470eb9` | yes |
| WMT | `49330f98609f70fcef4054edc90bc811398a58c4bf26dc0b218d607967a8dbe4` | yes |
