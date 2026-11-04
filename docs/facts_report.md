# XBRL facts report

The numeric facts of each pinned filing, read from the filing's own inline XBRL (`data/facts.jsonl`), and a cross-check against the SEC's companyfacts files. For every filing and every candidate tag of the metric map, the company totals (facts with no dimensions) that end on the filing's period of report are compared with the companyfacts rows of the same accession, tag and period. companyfacts is only a cross-check; the numbers come from the filings. Written by `make verify-facts`; do not edit by hand.

## Facts per filing

| Ticker | FY | Accession | Facts | Company totals |
|---|---:|---|---:|---:|
| AAPL | 2024 | 0000320193-24-000123 | 879 | 478 |
| AAPL | 2025 | 0000320193-25-000079 | 880 | 473 |
| AAPL | 2026 | 0000320193-26-000026 | 967 | 509 |
| AMZN | 2023 | 0001018724-24-000008 | 1,188 | 662 |
| AMZN | 2024 | 0001018724-25-000004 | 1,162 | 653 |
| AMZN | 2025 | 0001018724-26-000004 | 1,257 | 746 |
| AXP | 2023 | 0000004962-24-000013 | 2,112 | 728 |
| AXP | 2024 | 0000004962-25-000016 | 2,204 | 727 |
| AXP | 2025 | 0000004962-26-000080 | 2,263 | 705 |
| C | 2023 | 0000831001-24-000033 | 8,831 | 1,213 |
| C | 2024 | 0000831001-25-000067 | 9,034 | 1,218 |
| C | 2025 | 0000831001-26-000011 | 9,075 | 1,272 |
| COF | 2023 | 0000927628-24-000094 | 3,917 | 903 |
| COF | 2024 | 0000927628-25-000092 | 4,023 | 881 |
| COF | 2025 | 0000927628-26-000024 | 4,483 | 996 |
| COST | 2024 | 0000909832-24-000049 | 778 | 525 |
| COST | 2025 | 0000909832-25-000101 | 769 | 513 |
| COST | 2026 | 0000909832-26-000093 | 753 | 515 |
| GOOGL | 2023 | 0001652044-24-000022 | 1,306 | 633 |
| GOOGL | 2024 | 0001652044-25-000014 | 1,397 | 700 |
| GOOGL | 2025 | 0001652044-26-000018 | 1,508 | 741 |
| GS | 2023 | 0000886982-24-000006 | 5,829 | 1,125 |
| GS | 2024 | 0000886982-25-000005 | 5,743 | 1,119 |
| GS | 2025 | 0000886982-26-000091 | 5,252 | 1,105 |
| IBM | 2023 | 0000051143-24-000012 | 3,425 | 930 |
| IBM | 2024 | 0000051143-25-000015 | 3,437 | 932 |
| IBM | 2025 | 0000051143-26-000010 | 3,248 | 937 |
| JNJ | 2023 | 0000200406-24-000013 | 2,839 | 912 |
| JNJ | 2024 | 0000200406-25-000038 | 2,841 | 796 |
| JNJ | 2025 | 0000200406-26-000016 | 2,809 | 805 |
| JPM | 2023 | 0000019617-24-000225 | 7,291 | 1,216 |
| JPM | 2024 | 0000019617-25-000270 | 7,333 | 1,232 |
| JPM | 2025 | 0001628280-26-008131 | 7,443 | 1,312 |
| KO | 2023 | 0000021344-24-000009 | 2,602 | 869 |
| KO | 2024 | 0000021344-25-000011 | 2,271 | 852 |
| KO | 2025 | 0001628280-26-010047 | 2,276 | 885 |
| MA | 2023 | 0001141391-24-000022 | 1,635 | 769 |
| MA | 2024 | 0001141391-25-000011 | 1,440 | 719 |
| MA | 2025 | 0001141391-26-000013 | 1,384 | 694 |
| MCO | 2023 | 0001059556-24-000017 | 2,515 | 828 |
| MCO | 2024 | 0001059556-25-000025 | 2,532 | 821 |
| MCO | 2025 | 0001628280-26-009136 | 2,646 | 855 |
| META | 2023 | 0001326801-24-000012 | 1,049 | 537 |
| META | 2024 | 0001326801-25-000017 | 992 | 558 |
| META | 2025 | 0001628280-26-003942 | 1,040 | 596 |
| MS | 2023 | 0000895421-24-000300 | 5,616 | 1,008 |
| MS | 2024 | 0000895421-25-000304 | 5,729 | 1,036 |
| MS | 2025 | 0000895421-26-000086 | 5,697 | 1,098 |
| MSFT | 2024 | 0000950170-24-087843 | 1,453 | 636 |
| MSFT | 2025 | 0000950170-25-100235 | 1,432 | 640 |
| MSFT | 2026 | 0001193125-26-323660 | 1,467 | 659 |
| NFLX | 2023 | 0001065280-24-000030 | 874 | 553 |
| NFLX | 2024 | 0001065280-25-000044 | 1,085 | 582 |
| NFLX | 2025 | 0001065280-26-000034 | 1,192 | 593 |
| NKE | 2024 | 0000320187-24-000044 | 1,196 | 451 |
| NKE | 2025 | 0000320187-25-000047 | 1,298 | 469 |
| NKE | 2026 | 0000320187-26-000088 | 1,344 | 500 |
| NVDA | 2024 | 0001045810-24-000029 | 1,102 | 632 |
| NVDA | 2025 | 0001045810-25-000023 | 1,121 | 646 |
| NVDA | 2026 | 0001045810-26-000021 | 1,042 | 594 |
| PFE | 2023 | 0000078003-24-000039 | 2,888 | 858 |
| PFE | 2024 | 0000078003-25-000054 | 2,792 | 864 |
| PFE | 2025 | 0000078003-26-000026 | 2,793 | 905 |
| SPGI | 2023 | 0000064040-24-000071 | 2,075 | 637 |
| SPGI | 2024 | 0000064040-25-000052 | 2,011 | 630 |
| SPGI | 2025 | 0000064040-26-000013 | 2,003 | 655 |
| UNH | 2023 | 0000731766-24-000081 | 1,822 | 646 |
| UNH | 2024 | 0000731766-25-000063 | 1,960 | 687 |
| UNH | 2025 | 0000731766-26-000062 | 2,065 | 749 |
| VZ | 2023 | 0000732712-24-000010 | 2,090 | 765 |
| VZ | 2024 | 0000732712-25-000006 | 2,145 | 812 |
| VZ | 2025 | 0000732712-26-000007 | 2,164 | 800 |
| WMT | 2024 | 0000104169-24-000056 | 1,116 | 565 |
| WMT | 2025 | 0000104169-25-000021 | 1,097 | 550 |
| WMT | 2026 | 0000104169-26-000055 | 1,092 | 561 |
| **All** | | | **200,419** | **57,976** |

## Cross-check with companyfacts

Candidate tags compared: 20 (`Revenues`, `RevenueFromContractWithCustomerExcludingAssessedTax`, `RevenuesNetOfInterestExpense`, `SalesRevenueNet`, `NetIncomeLoss`, `ProfitLoss`, `EarningsPerShareDiluted`, `OperatingIncomeLoss`, `Assets`, `Liabilities`, `StockholdersEquity`, `StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest`, `NetCashProvidedByUsedInOperatingActivities`, `PaymentsToAcquirePropertyPlantAndEquipment`, `CashAndCashEquivalentsAtCarryingValue`, `CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents`, `LongTermDebtNoncurrent`, `LongTermDebt`, `dei:EntityCommonStockSharesOutstanding`, `CommonStockSharesOutstanding`).

- Agreements: 935
- Agreements where the filing also prints a rounded copy: 18
- Disagreements: 0
- Not in companyfacts: 15
- Not in the filing's XBRL: 0

| Ticker | FY | Agree | Agree, rounded copy | Disagree | Not in companyfacts | Not in the filing's XBRL |
|---|---:|---:|---:|---:|---:|---:|
| AAPL | 2024 | 14 | 0 | 0 | 0 | 0 |
| AAPL | 2025 | 14 | 0 | 0 | 0 | 0 |
| AAPL | 2026 | 14 | 0 | 0 | 0 | 0 |
| AMZN | 2023 | 12 | 0 | 0 | 0 | 0 |
| AMZN | 2024 | 12 | 0 | 0 | 0 | 0 |
| AMZN | 2025 | 12 | 0 | 0 | 0 | 0 |
| AXP | 2023 | 11 | 1 | 0 | 0 | 0 |
| AXP | 2024 | 12 | 0 | 0 | 0 | 0 |
| AXP | 2025 | 12 | 0 | 0 | 0 | 0 |
| C | 2023 | 11 | 1 | 0 | 0 | 0 |
| C | 2024 | 11 | 1 | 0 | 0 | 0 |
| C | 2025 | 11 | 1 | 0 | 0 | 0 |
| COF | 2023 | 11 | 0 | 0 | 0 | 0 |
| COF | 2024 | 11 | 0 | 0 | 0 | 0 |
| COF | 2025 | 11 | 0 | 0 | 0 | 0 |
| COST | 2024 | 16 | 0 | 0 | 0 | 0 |
| COST | 2025 | 16 | 0 | 0 | 0 | 0 |
| COST | 2026 | 13 | 0 | 0 | 0 | 0 |
| GOOGL | 2023 | 13 | 0 | 0 | 0 | 0 |
| GOOGL | 2024 | 14 | 0 | 0 | 0 | 0 |
| GOOGL | 2025 | 14 | 0 | 0 | 0 | 0 |
| GS | 2023 | 11 | 0 | 0 | 0 | 0 |
| GS | 2024 | 11 | 0 | 0 | 0 | 0 |
| GS | 2025 | 11 | 0 | 0 | 0 | 0 |
| IBM | 2023 | 13 | 0 | 0 | 0 | 0 |
| IBM | 2024 | 13 | 0 | 0 | 0 | 0 |
| IBM | 2025 | 13 | 0 | 0 | 0 | 0 |
| JNJ | 2023 | 15 | 0 | 0 | 0 | 0 |
| JNJ | 2024 | 12 | 0 | 0 | 0 | 0 |
| JNJ | 2025 | 12 | 0 | 0 | 0 | 0 |
| JPM | 2023 | 10 | 0 | 0 | 0 | 0 |
| JPM | 2024 | 10 | 0 | 0 | 0 | 0 |
| JPM | 2025 | 10 | 0 | 0 | 0 | 0 |
| KO | 2023 | 14 | 0 | 0 | 0 | 0 |
| KO | 2024 | 12 | 0 | 0 | 0 | 0 |
| KO | 2025 | 12 | 0 | 0 | 0 | 0 |
| MA | 2023 | 13 | 0 | 0 | 0 | 0 |
| MA | 2024 | 13 | 0 | 0 | 0 | 0 |
| MA | 2025 | 13 | 0 | 0 | 0 | 0 |
| MCO | 2023 | 15 | 0 | 0 | 0 | 0 |
| MCO | 2024 | 15 | 0 | 0 | 0 | 0 |
| MCO | 2025 | 15 | 0 | 0 | 0 | 0 |
| META | 2023 | 13 | 0 | 0 | 0 | 0 |
| META | 2024 | 13 | 0 | 0 | 0 | 0 |
| META | 2025 | 13 | 0 | 0 | 0 | 0 |
| MS | 2023 | 12 | 1 | 0 | 0 | 0 |
| MS | 2024 | 12 | 1 | 0 | 0 | 0 |
| MS | 2025 | 12 | 1 | 0 | 0 | 0 |
| MSFT | 2024 | 14 | 0 | 0 | 0 | 0 |
| MSFT | 2025 | 14 | 0 | 0 | 0 | 0 |
| MSFT | 2026 | 14 | 0 | 0 | 0 | 0 |
| NFLX | 2023 | 14 | 0 | 0 | 0 | 0 |
| NFLX | 2024 | 14 | 0 | 0 | 0 | 0 |
| NFLX | 2025 | 14 | 0 | 0 | 0 | 0 |
| NKE | 2024 | 11 | 0 | 0 | 0 | 0 |
| NKE | 2025 | 11 | 0 | 0 | 0 | 0 |
| NKE | 2026 | 11 | 0 | 0 | 0 | 0 |
| NVDA | 2024 | 13 | 0 | 0 | 0 | 0 |
| NVDA | 2025 | 13 | 0 | 0 | 0 | 0 |
| NVDA | 2026 | 13 | 0 | 0 | 0 | 0 |
| PFE | 2023 | 12 | 2 | 0 | 0 | 0 |
| PFE | 2024 | 11 | 2 | 0 | 0 | 0 |
| PFE | 2025 | 11 | 2 | 0 | 0 | 0 |
| SPGI | 2023 | 14 | 1 | 0 | 0 | 0 |
| SPGI | 2024 | 0 | 0 | 0 | 15 | 0 |
| SPGI | 2025 | 14 | 1 | 0 | 0 | 0 |
| UNH | 2023 | 14 | 0 | 0 | 0 | 0 |
| UNH | 2024 | 14 | 0 | 0 | 0 | 0 |
| UNH | 2025 | 14 | 0 | 0 | 0 | 0 |
| VZ | 2023 | 10 | 0 | 0 | 0 | 0 |
| VZ | 2024 | 10 | 0 | 0 | 0 | 0 |
| VZ | 2025 | 10 | 0 | 0 | 0 | 0 |
| WMT | 2024 | 14 | 1 | 0 | 0 | 0 |
| WMT | 2025 | 14 | 1 | 0 | 0 | 0 |
| WMT | 2026 | 14 | 1 | 0 | 0 | 0 |

Every row that is not an agreement:

| Ticker | FY | Tag | Period | Status | Filing's XBRL | companyfacts |
|---|---:|---|---|---|---:|---:|
| SPGI | 2024 | `Assets` | 2024-12-31 | not in companyfacts | 60221000000 | — |
| SPGI | 2024 | `CashAndCashEquivalentsAtCarryingValue` | 2024-12-31 | not in companyfacts | 1666000000, 1700000000 | — |
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

Agreements where the filing also prints the same number rounded (for example a table and the text): companyfacts holds the exact value, and the other value equals it rounded to its own `decimals`:

| Ticker | FY | Tag | Period | Filing's XBRL | companyfacts |
|---|---:|---|---|---:|---:|
| AXP | 2023 | `Assets` | 2023-12-31 | 261000000000, 261108000000 | 261108000000 |
| C | 2023 | `Assets` | 2023-12-31 | 2411834000000, 2412000000000 | 2411834000000 |
| C | 2024 | `Assets` | 2024-12-31 | 2352945000000, 2353000000000 | 2352945000000 |
| C | 2025 | `Assets` | 2025-12-31 | 2657000000000, 2657202000000 | 2657202000000 |
| MS | 2023 | `CommonStockSharesOutstanding` | 2023-12-31 | 1626828437, 1627000000 | 1626828437 |
| MS | 2024 | `CommonStockSharesOutstanding` | 2024-12-31 | 1606653706, 1607000000 | 1606653706 |
| MS | 2025 | `CommonStockSharesOutstanding` | 2025-12-31 | 1582834137, 1583000000 | 1582834137 |
| PFE | 2023 | `Assets` | 2023-12-31 | 226501000000, 227000000000 | 226501000000 |
| PFE | 2023 | `LongTermDebtNoncurrent` | 2023-12-31 | 61538000000, 62000000000 | 61538000000 |
| PFE | 2024 | `Assets` | 2024-12-31 | 213000000000, 213396000000 | 213396000000 |
| PFE | 2024 | `LongTermDebtNoncurrent` | 2024-12-31 | 57000000000, 57405000000 | 57405000000 |
| PFE | 2025 | `Assets` | 2025-12-31 | 208000000000, 208160000000 | 208160000000 |
| PFE | 2025 | `LongTermDebtNoncurrent` | 2025-12-31 | 61641000000, 62000000000 | 61641000000 |
| SPGI | 2023 | `CashAndCashEquivalentsAtCarryingValue` | 2023-12-31 | 1290000000, 1300000000 | 1290000000 |
| SPGI | 2025 | `CashAndCashEquivalentsAtCarryingValue` | 2025-12-31 | 1700000000, 1745000000 | 1745000000 |
| WMT | 2024 | `CashAndCashEquivalentsAtCarryingValue` | 2024-01-31 | 9867000000, 9900000000 | 9867000000 |
| WMT | 2025 | `CashAndCashEquivalentsAtCarryingValue` | 2025-01-31 | 9000000000, 9037000000 | 9037000000 |
| WMT | 2026 | `CashAndCashEquivalentsAtCarryingValue` | 2026-01-31 | 10700000000, 10727000000 | 10727000000 |

## Conflicts

Facts with the same concept, period, unit and dimensions but different values in one filing. Both values are kept and marked `conflict: true`.

Conflicts: 1040 facts in 520 groups

- AAPL FY2024 `us-gaap:UnrecognizedTaxBenefits` 2023-09-30 (USD): 19454000000, 19500000000
- AAPL FY2024 `us-gaap:UnrecognizedTaxBenefits` 2024-09-28 (USD): 22000000000, 22038000000
- AAPL FY2025 `us-gaap:UnrecognizedTaxBenefits` 2024-09-28 (USD): 22000000000, 22038000000
- AAPL FY2025 `us-gaap:UnrecognizedTaxBenefits` 2025-09-27 (USD): 23200000000, 23242000000
- AAPL FY2026 `us-gaap:UnrecognizedTaxBenefits` 2025-09-27 (USD): 23200000000, 23242000000
- AAPL FY2026 `us-gaap:UnrecognizedTaxBenefits` 2026-09-26 (USD): 22487000000, 22500000000
- AMZN FY2023 `us-gaap:Depreciation` 2021-01-01 to 2021-12-31 (USD): 22900000000, 22909000000
- AMZN FY2023 `us-gaap:Depreciation` 2022-01-01 to 2022-12-31 (USD): 24900000000, 24924000000
- AMZN FY2023 `us-gaap:Depreciation` 2023-01-01 to 2023-12-31 (USD): 30200000000, 30225000000
- AMZN FY2023 `us-gaap:FinanceLeaseRightOfUseAssetAmortization` 2021-01-01 to 2021-12-31 (USD): 9857000000, 9900000000
- AMZN FY2023 `us-gaap:FinanceLeaseRightOfUseAssetAmortization` 2022-01-01 to 2022-12-31 (USD): 6097000000, 6100000000
- AMZN FY2023 `us-gaap:FinanceLeaseRightOfUseAssetAmortization` 2023-01-01 to 2023-12-31 (USD): 5899000000, 5900000000
- AMZN FY2023 `us-gaap:IncomeTaxExpenseBenefit` 2021-01-01 to 2021-12-31 (USD): 4791000000, 4800000000
- AMZN FY2023 `us-gaap:IncomeTaxExpenseBenefit` 2022-01-01 to 2022-12-31 (USD): -3200000000, -3217000000
- AMZN FY2023 `us-gaap:IncomeTaxExpenseBenefit` 2023-01-01 to 2023-12-31 (USD): 7100000000, 7120000000
- AMZN FY2023 `us-gaap:IncomeTaxesPaidNet` 2021-01-01 to 2021-12-31 (USD): 3688000000, 3700000000
- AMZN FY2023 `us-gaap:IncomeTaxesPaidNet` 2022-01-01 to 2022-12-31 (USD): 6000000000, 6035000000
- AMZN FY2023 `us-gaap:IncomeTaxesPaidNet` 2023-01-01 to 2023-12-31 (USD): 11179000000, 11200000000
- AMZN FY2023 `us-gaap:UnrecognizedTaxBenefits` 2023-12-31 (USD): 5200000000, 5228000000
- AMZN FY2024 `us-gaap:Depreciation` 2022-01-01 to 2022-12-31 (USD): 24900000000, 24924000000
- AMZN FY2024 `us-gaap:Depreciation` 2023-01-01 to 2023-12-31 (USD): 30200000000, 30225000000
- AMZN FY2024 `us-gaap:Depreciation` 2024-01-01 to 2024-12-31 (USD): 32067000000, 32100000000
- AMZN FY2024 `us-gaap:FinanceLeaseRightOfUseAssetAmortization` 2022-01-01 to 2022-12-31 (USD): 6097000000, 6100000000
- AMZN FY2024 `us-gaap:FinanceLeaseRightOfUseAssetAmortization` 2023-01-01 to 2023-12-31 (USD): 5899000000, 5900000000
- AMZN FY2024 `us-gaap:FinanceLeaseRightOfUseAssetAmortization` 2024-01-01 to 2024-12-31 (USD): 3866000000, 3900000000
- AMZN FY2024 `us-gaap:IncomeTaxExpenseBenefit` 2022-01-01 to 2022-12-31 (USD): -3200000000, -3217000000
- AMZN FY2024 `us-gaap:IncomeTaxExpenseBenefit` 2023-01-01 to 2023-12-31 (USD): 7100000000, 7120000000
- AMZN FY2024 `us-gaap:IncomeTaxExpenseBenefit` 2024-01-01 to 2024-12-31 (USD): 9265000000, 9300000000
- AMZN FY2024 `us-gaap:IncomeTaxesPaidNet` 2022-01-01 to 2022-12-31 (USD): 6000000000, 6035000000
- AMZN FY2024 `us-gaap:IncomeTaxesPaidNet` 2023-01-01 to 2023-12-31 (USD): 11179000000, 11200000000
- AMZN FY2024 `us-gaap:IncomeTaxesPaidNet` 2024-01-01 to 2024-12-31 (USD): 12300000000, 12308000000
- AMZN FY2024 `us-gaap:UnrecognizedTaxBenefits` 2024-12-31 (USD): 6485000000, 6500000000
- AMZN FY2025 `us-gaap:Depreciation` 2023-01-01 to 2023-12-31 (USD): 30200000000, 30225000000
- AMZN FY2025 `us-gaap:Depreciation` 2024-01-01 to 2024-12-31 (USD): 32067000000, 32100000000
- AMZN FY2025 `us-gaap:Depreciation` 2025-01-01 to 2025-12-31 (USD): 41860000000, 41900000000
- AMZN FY2025 `us-gaap:EquitySecuritiesWithoutReadilyDeterminableFairValueUpwardPriceAdjustmentAnnualAmount` 2025-01-01 to 2025-12-31 (USD): 7700000000, 7709000000
- AMZN FY2025 `us-gaap:FinanceLeaseRightOfUseAssetAmortization` 2023-01-01 to 2023-12-31 (USD): 5899000000, 5900000000
- AMZN FY2025 `us-gaap:FinanceLeaseRightOfUseAssetAmortization` 2024-01-01 to 2024-12-31 (USD): 3866000000, 3900000000
- AMZN FY2025 `us-gaap:FinanceLeaseRightOfUseAssetAmortization` 2025-01-01 to 2025-12-31 (USD): 3284000000, 3300000000
- AMZN FY2025 `us-gaap:IncomeTaxExpenseBenefit` 2023-01-01 to 2023-12-31 (USD): 7100000000, 7120000000
- AMZN FY2025 `us-gaap:IncomeTaxExpenseBenefit` 2024-01-01 to 2024-12-31 (USD): 9265000000, 9300000000
- AMZN FY2025 `us-gaap:IncomeTaxExpenseBenefit` 2025-01-01 to 2025-12-31 (USD): 19087000000, 19100000000
- AMZN FY2025 `us-gaap:IncomeTaxesPaidNet` 2023-01-01 to 2023-12-31 (USD): 11179000000, 11200000000
- AMZN FY2025 `us-gaap:IncomeTaxesPaidNet` 2024-01-01 to 2024-12-31 (USD): 12300000000, 12308000000
- AMZN FY2025 `us-gaap:IncomeTaxesPaidNet` 2025-01-01 to 2025-12-31 (USD): 8295000000, 8300000000
- AMZN FY2025 `us-gaap:MarketableSecuritiesUnrealizedGainLoss` 2024-01-01 to 2024-12-31 (USD): -1278000000, -1300000000
- AMZN FY2025 `us-gaap:MarketableSecuritiesUnrealizedGainLoss` 2025-01-01 to 2025-12-31 (USD): 1400000000, 1439000000
- AMZN FY2025 `us-gaap:UnrecognizedTaxBenefits` 2025-12-31 (USD): 6566000000, 6600000000
- AXP FY2023 `us-gaap:Assets` 2022-12-31 (USD): 228000000000, 228354000000
- AXP FY2023 `us-gaap:Assets` 2023-12-31 (USD): 261000000000, 261108000000
- AXP FY2023 `us-gaap:UnrecognizedTaxBenefits` 2021-12-31 (USD): 1000000000, 1024000000
- AXP FY2023 `us-gaap:UnrecognizedTaxBenefits` 2022-12-31 (USD): 1000000000, 962000000
- AXP FY2023 `us-gaap:UnrecognizedTaxBenefits` 2023-12-31 (USD): 875000000, 900000000
- AXP FY2024 `us-gaap:UnrecognizedTaxBenefits` 2022-12-31 (USD): 1000000000, 962000000
- AXP FY2024 `us-gaap:UnrecognizedTaxBenefits` 2023-12-31 (USD): 875000000, 900000000
- AXP FY2024 `us-gaap:UnrecognizedTaxBenefits` 2024-12-31 (USD): 1000000000, 1006000000
- AXP FY2025 `us-gaap:IncomeTaxesPaidNet` 2025-01-01 to 2025-12-31 (USD): 3195000000, 3200000000
- AXP FY2025 `us-gaap:UnrecognizedTaxBenefits` 2023-12-31 (USD): 875000000, 900000000
- AXP FY2025 `us-gaap:UnrecognizedTaxBenefits` 2024-12-31 (USD): 1000000000, 1006000000
- AXP FY2025 `us-gaap:UnrecognizedTaxBenefits` 2025-12-31 (USD): 1100000000, 1102000000
- C FY2023 `us-gaap:Assets` 2022-12-31 (USD): 2416676000000, 2417000000000
- C FY2023 `us-gaap:Assets` 2023-12-31 (USD): 2411834000000, 2412000000000
- C FY2023 `us-gaap:DeferredTaxAssetsLiabilitiesNet` 2022-12-31 (USD): 27672000000, 27700000000
- C FY2023 `us-gaap:DeferredTaxAssetsLiabilitiesNet` 2023-12-31 (USD): 29600000000, 29608000000
- C FY2023 `us-gaap:DeferredTaxAssetsValuationAllowance` 2022-12-31 (USD): 2400000000, 2438000000
- C FY2023 `us-gaap:DeferredTaxAssetsValuationAllowance` 2023-12-31 (USD): 3572000000, 3600000000
- C FY2023 `us-gaap:FinancingReceivableAllowanceForCreditLossExcludingAccruedInterest` 2022-12-31 (USD): 16974000000, 17000000000
- C FY2023 `us-gaap:FinancingReceivableAllowanceForCreditLossExcludingAccruedInterest` 2023-12-31 (USD): 18100000000, 18145000000
- C FY2023 `us-gaap:GuaranteeObligationsCurrentCarryingValue` 2022-12-31 (USD): 1376000000, 1400000000
- C FY2023 `us-gaap:GuaranteeObligationsCurrentCarryingValue` 2023-12-31 (USD): 1156000000, 1200000000
- C FY2023 `us-gaap:GuaranteeObligationsMaximumExposure` {"us-gaap:GuaranteeObligationsByNatureAxis": "c:CreditCardMerchantProcessingMember"} 2022-12-31 (USD): 129600000000, 130000000000
- C FY2024 `c:InvestmentsExcludingTradingSecuritiesExcludingAccruedInterest` {"us-gaap:FairValueByMeasurementBasisAxis": "us-gaap:PortionAtOtherThanFairValueFairValueDisclosureMember", "us-gaap:FinancialInstrumentAxis": "c:NonMarketableEquitySecuritiesMember"} 2023-12-31 (USD): 5497000000, 5500000000
- C FY2024 `c:InvestmentsExcludingTradingSecuritiesExcludingAccruedInterest` {"us-gaap:FairValueByMeasurementBasisAxis": "us-gaap:PortionAtOtherThanFairValueFairValueDisclosureMember", "us-gaap:FinancialInstrumentAxis": "c:NonMarketableEquitySecuritiesMember"} 2024-12-31 (USD): 5200000000, 5247000000
- C FY2024 `us-gaap:Assets` 2023-12-31 (USD): 2411834000000, 2412000000000
- C FY2024 `us-gaap:Assets` 2024-12-31 (USD): 2352945000000, 2353000000000
- C FY2024 `us-gaap:DeferredTaxAssetsLiabilitiesNet` 2023-12-31 (USD): 29600000000, 29608000000
- C FY2024 `us-gaap:DeferredTaxAssetsLiabilitiesNet` 2024-12-31 (USD): 29800000000, 29845000000
- C FY2024 `us-gaap:DeferredTaxAssetsValuationAllowance` 2023-12-31 (USD): 3572000000, 3600000000
- C FY2024 `us-gaap:DeferredTaxAssetsValuationAllowance` 2024-12-31 (USD): 4300000000, 4329000000
- C FY2024 `us-gaap:FinancingReceivableAllowanceForCreditLossExcludingAccruedInterest` 2023-12-31 (USD): 18100000000, 18145000000
- C FY2024 `us-gaap:FinancingReceivableAllowanceForCreditLossExcludingAccruedInterest` 2024-12-31 (USD): 18574000000, 18600000000
- C FY2024 `us-gaap:GuaranteeObligationsCurrentCarryingValue` 2023-12-31 (USD): 1156000000, 1200000000
- C FY2024 `us-gaap:GuaranteeObligationsCurrentCarryingValue` 2024-12-31 (USD): 1000000000, 964000000
- C FY2025 `c:InvestmentsExcludingTradingSecuritiesExcludingAccruedInterest` {"us-gaap:FairValueByMeasurementBasisAxis": "us-gaap:PortionAtOtherThanFairValueFairValueDisclosureMember", "us-gaap:FinancialInstrumentAxis": "c:NonMarketableEquitySecuritiesMember"} 2024-12-31 (USD): 5200000000, 5247000000
- C FY2025 `c:InvestmentsExcludingTradingSecuritiesExcludingAccruedInterest` {"us-gaap:FairValueByMeasurementBasisAxis": "us-gaap:PortionAtOtherThanFairValueFairValueDisclosureMember", "us-gaap:FinancialInstrumentAxis": "c:NonMarketableEquitySecuritiesMember"} 2025-12-31 (USD): 5050000000, 5100000000
- C FY2025 `us-gaap:Assets` 2024-12-31 (USD): 2352945000000, 2353000000000
- C FY2025 `us-gaap:Assets` 2025-12-31 (USD): 2657000000000, 2657202000000
- C FY2025 `us-gaap:DeferredTaxAssetsLiabilitiesNet` 2024-12-31 (USD): 29800000000, 29845000000
- C FY2025 `us-gaap:DeferredTaxAssetsLiabilitiesNet` 2025-12-31 (USD): 29500000000, 29531000000
- C FY2025 `us-gaap:DeferredTaxAssetsValuationAllowance` 2024-12-31 (USD): 4300000000, 4329000000
- C FY2025 `us-gaap:DeferredTaxAssetsValuationAllowance` 2025-12-31 (USD): 4984000000, 5000000000
- C FY2025 `us-gaap:FairValueMeasurementWithUnobservableInputsReconciliationLiabilityTransfersIntoLevel3` {"us-gaap:FairValueByLiabilityClassAxis": "us-gaap:LongTermDebtMember"} 2024-01-01 to 2024-12-31 (USD): 4600000000, 4626000000
- C FY2025 `us-gaap:FairValueMeasurementWithUnobservableInputsReconciliationLiabilityTransfersIntoLevel3` {"us-gaap:FairValueByLiabilityClassAxis": "us-gaap:LongTermDebtMember"} 2025-01-01 to 2025-12-31 (USD): 3100000000, 3120000000
- C FY2025 `us-gaap:FairValueMeasurementWithUnobservableInputsReconciliationLiabilityTransfersOutOfLevel3` {"us-gaap:FairValueByLiabilityClassAxis": "us-gaap:LongTermDebtMember"} 2024-01-01 to 2024-12-31 (USD): 22900000000, 22923000000
- C FY2025 `us-gaap:FairValueMeasurementWithUnobservableInputsReconciliationLiabilityTransfersOutOfLevel3` {"us-gaap:FairValueByLiabilityClassAxis": "us-gaap:LongTermDebtMember"} 2025-01-01 to 2025-12-31 (USD): 4158000000, 4200000000
- C FY2025 `us-gaap:FinancingReceivableAllowanceForCreditLossExcludingAccruedInterest` 2024-12-31 (USD): 18574000000, 18600000000
- C FY2025 `us-gaap:FinancingReceivableAllowanceForCreditLossExcludingAccruedInterest` 2025-12-31 (USD): 19200000000, 19247000000
- C FY2025 `us-gaap:GuaranteeObligationsCurrentCarryingValue` 2024-12-31 (USD): 1000000000, 964000000
- C FY2025 `us-gaap:GuaranteeObligationsCurrentCarryingValue` 2025-12-31 (USD): 1200000000, 1213000000
- COF FY2023 `us-gaap:Assets` {"srt:ConsolidatedEntitiesAxis": "us-gaap:VariableInterestEntityNotPrimaryBeneficiaryMember", "us-gaap:InvestmentTypeAxis": "cof:AffordableHousingEntitiesMember"} 2022-12-31 (USD): 4900000000, 4944000000
- COF FY2023 `us-gaap:Assets` {"srt:ConsolidatedEntitiesAxis": "us-gaap:VariableInterestEntityPrimaryBeneficiaryMember", "us-gaap:InvestmentTypeAxis": "cof:InvestmentCompaniesProvidingCapitaltoLowIncomeandRuralCommunitiesMember"} 2022-12-31 (USD): 2300000000, 2301000000
- COF FY2023 `us-gaap:Assets` {"srt:ConsolidatedEntitiesAxis": "us-gaap:VariableInterestEntityNotPrimaryBeneficiaryMember", "us-gaap:InvestmentTypeAxis": "cof:AffordableHousingEntitiesMember"} 2023-12-31 (USD): 5700000000, 5726000000
- COF FY2023 `us-gaap:Assets` {"srt:ConsolidatedEntitiesAxis": "us-gaap:VariableInterestEntityPrimaryBeneficiaryMember", "us-gaap:InvestmentTypeAxis": "cof:InvestmentCompaniesProvidingCapitaltoLowIncomeandRuralCommunitiesMember"} 2023-12-31 (USD): 2498000000, 2500000000
- COF FY2023 `us-gaap:DebtSecuritiesAvailableForSaleAmortizedCostExcludingAccruedInterestBeforeAllowanceForCreditLoss` 2022-12-31 (USD): 87000000000, 87047000000
- COF FY2023 `us-gaap:DebtSecuritiesAvailableForSaleAmortizedCostExcludingAccruedInterestBeforeAllowanceForCreditLoss` 2023-12-31 (USD): 88063000000, 88100000000
- COF FY2023 `us-gaap:FinancingReceivableAllowanceForCreditLossExcludingAccruedInterest` {"us-gaap:FinancingReceivableRecordedInvestmentByClassOfFinancingReceivableAxis": "us-gaap:AllowanceForLoanAndLeaseLossesMember"} 2023-12-31 (USD): 15296000000, 15300000000
- COF FY2023 `us-gaap:OtherComprehensiveIncomeLossTaxPortionAttributableToParent1` 2022-01-01 to 2022-12-31 (USD): -3184000000, -3200000000
- COF FY2024 `us-gaap:Assets` {"srt:ConsolidatedEntitiesAxis": "us-gaap:VariableInterestEntityNotPrimaryBeneficiaryMember", "us-gaap:InvestmentTypeAxis": "cof:AffordableHousingEntitiesMember"} 2023-12-31 (USD): 5700000000, 5726000000
- COF FY2024 `us-gaap:Assets` {"srt:ConsolidatedEntitiesAxis": "us-gaap:VariableInterestEntityPrimaryBeneficiaryMember", "us-gaap:InvestmentTypeAxis": "cof:InvestmentCompaniesProvidingCapitaltoLowIncomeandRuralCommunitiesMember"} 2023-12-31 (USD): 2498000000, 2500000000
- COF FY2024 `us-gaap:Assets` {"srt:ConsolidatedEntitiesAxis": "us-gaap:VariableInterestEntityNotPrimaryBeneficiaryMember", "us-gaap:InvestmentTypeAxis": "cof:AffordableHousingEntitiesMember"} 2024-12-31 (USD): 5500000000, 5544000000
- COF FY2024 `us-gaap:Assets` {"srt:ConsolidatedEntitiesAxis": "us-gaap:VariableInterestEntityPrimaryBeneficiaryMember", "us-gaap:InvestmentTypeAxis": "cof:InvestmentCompaniesProvidingCapitaltoLowIncomeandRuralCommunitiesMember"} 2024-12-31 (USD): 2600000000, 2605000000
- COF FY2024 `us-gaap:DebtSecuritiesAvailableForSaleAmortizedCostExcludingAccruedInterestBeforeAllowanceForCreditLoss` 2023-12-31 (USD): 88063000000, 88100000000
- COF FY2024 `us-gaap:DebtSecuritiesAvailableForSaleAmortizedCostExcludingAccruedInterestBeforeAllowanceForCreditLoss` 2024-12-31 (USD): 92995000000, 93000000000
- COF FY2024 `us-gaap:MarketingExpense` 2022-01-01 to 2022-12-31 (USD): 4000000000, 4017000000
- COF FY2024 `us-gaap:MarketingExpense` 2023-01-01 to 2023-12-31 (USD): 4000000000, 4009000000
- COF FY2024 `us-gaap:MarketingExpense` 2024-01-01 to 2024-12-31 (USD): 4562000000, 4600000000
- COF FY2024 `us-gaap:OtherComprehensiveIncomeLossTaxPortionAttributableToParent1` 2022-01-01 to 2022-12-31 (USD): -3184000000, -3200000000
- COF FY2025 `us-gaap:Assets` {"srt:ConsolidatedEntitiesAxis": "us-gaap:VariableInterestEntityNotPrimaryBeneficiaryMember", "us-gaap:InvestmentTypeAxis": "cof:AffordableHousingEntitiesMember"} 2024-12-31 (USD): 5500000000, 5544000000
- COF FY2025 `us-gaap:Assets` {"srt:ConsolidatedEntitiesAxis": "us-gaap:VariableInterestEntityPrimaryBeneficiaryMember", "us-gaap:InvestmentTypeAxis": "cof:InvestmentCompaniesProvidingCapitaltoLowIncomeandRuralCommunitiesMember"} 2024-12-31 (USD): 2600000000, 2605000000
- COF FY2025 `us-gaap:Assets` {"srt:ConsolidatedEntitiesAxis": "us-gaap:VariableInterestEntityNotPrimaryBeneficiaryMember", "us-gaap:InvestmentTypeAxis": "cof:AffordableHousingEntitiesMember"} 2025-12-31 (USD): 6485000000, 6500000000
- COF FY2025 `us-gaap:Assets` {"srt:ConsolidatedEntitiesAxis": "us-gaap:VariableInterestEntityPrimaryBeneficiaryMember", "us-gaap:InvestmentTypeAxis": "cof:InvestmentCompaniesProvidingCapitaltoLowIncomeandRuralCommunitiesMember"} 2025-12-31 (USD): 2900000000, 2942000000
- COF FY2025 `us-gaap:BusinessCombinationConsiderationTransferred1` {"us-gaap:BusinessAcquisitionAxis": "cof:DiscoverMember"} 2025-05-18 to 2025-05-18 (USD): 51793000000, 51800000000
- COF FY2025 `us-gaap:DebtSecuritiesAvailableForSaleAmortizedCostExcludingAccruedInterestBeforeAllowanceForCreditLoss` 2024-12-31 (USD): 92995000000, 93000000000
- COF FY2025 `us-gaap:DebtSecuritiesAvailableForSaleAmortizedCostExcludingAccruedInterestBeforeAllowanceForCreditLoss` 2025-12-31 (USD): 97656000000, 97700000000
- COF FY2025 `us-gaap:FinancingReceivableAllowanceForCreditLossExcludingAccruedInterest` {"us-gaap:FinancingReceivableRecordedInvestmentByClassOfFinancingReceivableAxis": "us-gaap:AllowanceForLoanAndLeaseLossesMember"} 2025-12-31 (USD): 23400000000, 23409000000
- COF FY2025 `us-gaap:MarketingExpense` 2023-01-01 to 2023-12-31 (USD): 4000000000, 4009000000
- COF FY2025 `us-gaap:MarketingExpense` 2024-01-01 to 2024-12-31 (USD): 4562000000, 4600000000
- COF FY2025 `us-gaap:MarketingExpense` 2025-01-01 to 2025-12-31 (USD): 5884000000, 5900000000
- COF FY2025 `us-gaap:OtherComprehensiveIncomeLossTaxPortionAttributableToParent1` 2025-01-01 to 2025-12-31 (USD): 1163000000, 1200000000
- COF FY2025 `us-gaap:VariableInterestEntityEntityMaximumLossExposureAmount` {"srt:ConsolidatedEntitiesAxis": "us-gaap:VariableInterestEntityNotPrimaryBeneficiaryMember", "us-gaap:InvestmentTypeAxis": "us-gaap:OtherInvestmentsMember"} 2025-12-31 (USD): 1389000000, 1400000000
- COST FY2026 `us-gaap:ProceedsFromIssuanceOfLongTermDebt` 2025-09-01 to 2026-08-30 (USD): 496000000, 500000000
- GOOGL FY2023 `us-gaap:EquitySecuritiesWithoutReadilyDeterminableFairValueAmount` 2023-12-31 (USD): 28766000000, 28800000000
- GOOGL FY2023 `us-gaap:RestructuringCharges` {"us-gaap:RestructuringCostAndReserveAxis": "us-gaap:EmployeeSeveranceMember"} 2023-01-01 to 2023-12-31 (USD): 2088000000, 2100000000
- GOOGL FY2023 `us-gaap:RestructuringCharges` {"us-gaap:RestructuringCostAndReserveAxis": "us-gaap:FacilityClosingMember"} 2023-01-01 to 2023-12-31 (USD): 1800000000, 1845000000
- GOOGL FY2023 `us-gaap:StockRepurchasedAndRetiredDuringPeriodValue` {"us-gaap:ShareRepurchaseProgramAxis": "goog:ShareRepurchaseProgramMember"} 2022-01-01 to 2022-12-31 (USD): 59296000000, 59300000000
- GOOGL FY2023 `us-gaap:StockRepurchasedAndRetiredDuringPeriodValue` {"us-gaap:ShareRepurchaseProgramAxis": "goog:ShareRepurchaseProgramMember"} 2023-01-01 to 2023-12-31 (USD): 62184000000, 62200000000
- GOOGL FY2023 `us-gaap:UnrecognizedTaxBenefits` 2021-12-31 (USD): 5158000000, 5200000000
- GOOGL FY2023 `us-gaap:UnrecognizedTaxBenefits` 2022-12-31 (USD): 7055000000, 7100000000
- GOOGL FY2023 `us-gaap:UnrecognizedTaxBenefits` 2023-12-31 (USD): 9400000000, 9438000000
- GOOGL FY2024 `us-gaap:EquitySecuritiesWithoutReadilyDeterminableFairValueAmount` 2024-12-31 (USD): 35500000000, 35531000000
- GOOGL FY2024 `us-gaap:StockRepurchasedAndRetiredDuringPeriodValue` {"srt:ShareRepurchaseProgramAxis": "goog:ShareRepurchaseProgramMember"} 2023-01-01 to 2023-12-31 (USD): 62184000000, 62200000000
- GOOGL FY2024 `us-gaap:StockRepurchasedAndRetiredDuringPeriodValue` {"srt:ShareRepurchaseProgramAxis": "goog:ShareRepurchaseProgramMember"} 2024-01-01 to 2024-12-31 (USD): 62000000000, 62047000000
- GOOGL FY2024 `us-gaap:UnrecognizedTaxBenefits` 2022-12-31 (USD): 7055000000, 7100000000
- GOOGL FY2024 `us-gaap:UnrecognizedTaxBenefits` 2023-12-31 (USD): 9400000000, 9438000000
- GOOGL FY2024 `us-gaap:UnrecognizedTaxBenefits` 2024-12-31 (USD): 12600000000, 12619000000
- GOOGL FY2025 `us-gaap:EquitySecuritiesWithoutReadilyDeterminableFairValueAmount` 2025-12-31 (USD): 64094000000, 64100000000
- GOOGL FY2025 `us-gaap:UnrecognizedTaxBenefits` 2023-12-31 (USD): 9400000000, 9438000000
- GOOGL FY2025 `us-gaap:UnrecognizedTaxBenefits` 2024-12-31 (USD): 12600000000, 12619000000
- GOOGL FY2025 `us-gaap:UnrecognizedTaxBenefits` 2025-12-31 (USD): 11500000000, 11512000000
- GS FY2023 `gs:ChangeInCreditRwas` {"us-gaap:RiskWeightedAssetsCalculationMethodologyAxis": "us-gaap:AdvancedApproachMember"} 2023-01-01 to 2023-12-31 (USD): -13440000000, -13443000000
- GS FY2023 `gs:ChangeInCreditRwas` {"us-gaap:RiskWeightedAssetsCalculationMethodologyAxis": "us-gaap:StandardizedApproachMember"} 2023-01-01 to 2023-12-31 (USD): 33710000000, 33714000000
- GS FY2023 `gs:ChangeInMarketRwas` {"us-gaap:RiskWeightedAssetsCalculationMethodologyAxis": "us-gaap:AdvancedApproachMember"} 2023-01-01 to 2023-12-31 (USD): 5600000000, 5604000000
- GS FY2023 `gs:ChangeInMarketRwas` {"us-gaap:RiskWeightedAssetsCalculationMethodologyAxis": "us-gaap:StandardizedApproachMember"} 2023-01-01 to 2023-12-31 (USD): 5600000000, 5604000000
- GS FY2023 `gs:ChangeInOperationalRWAs` {"us-gaap:RiskWeightedAssetsCalculationMethodologyAxis": "us-gaap:AdvancedApproachMember"} 2023-01-01 to 2023-12-31 (USD): -6260000000, -6263000000
- GS FY2023 `gs:FairValueMeasurementWithUnobservableInputsReconciliationRecurringBasisLiabilityNetUnrealizedGainLossIncludedInEarningsAndOtherComprehensiveIncome` {"us-gaap:FinancialInstrumentAxis": "gs:OtherFinancialLiabilitiesMember"} 2022-01-01 to 2022-12-31 (USD): 4459000000, 4460000000
- GS FY2023 `gs:FairValueMeasurementWithUnobservableInputsReconciliationRecurringBasisLiabilityNetUnrealizedGainLossIncludedInEarningsAndOtherComprehensiveIncome` {"us-gaap:FinancialInstrumentAxis": "gs:OtherFinancialLiabilitiesMember"} 2023-01-01 to 2023-12-31 (USD): -1667000000, -1670000000
- GS FY2023 `gs:SubordinatedDebtOutstanding` {"us-gaap:LongtermDebtTypeAxis": "us-gaap:SubordinatedDebtMember"} 2022-12-31 (USD): 11880000000, 11882000000
- GS FY2023 `gs:SubordinatedDebtOutstanding` {"us-gaap:LongtermDebtTypeAxis": "us-gaap:SubordinatedDebtMember"} 2023-12-31 (USD): 11898000000, 11900000000
- GS FY2023 `us-gaap:DebtInstrumentFaceAmount` {"us-gaap:LongtermDebtTypeAxis": "us-gaap:SubordinatedDebtMember"} 2022-12-31 (USD): 12260000000, 12261000000
- GS FY2023 `us-gaap:DebtInstrumentFaceAmount` {"us-gaap:LongtermDebtTypeAxis": "us-gaap:SubordinatedDebtMember"} 2023-12-31 (USD): 12215000000, 12220000000
- GS FY2023 `us-gaap:DepositsFairValueDisclosure` 2022-12-31 (USD): 15746000000, 15750000000
- GS FY2023 `us-gaap:FairValueAssetsMeasuredOnRecurringBasisChangeInUnrealizedGainLoss` {"us-gaap:FairValueByAssetClassAxis": "us-gaap:InvestmentsMember"} 2022-01-01 to 2022-12-31 (USD): -1649000000, -1650000000
- GS FY2023 `us-gaap:FairValueNetDerivativeAssetLiabilityMeasuredOnRecurringBasisChangeInUnrealizedGainLoss` 2022-01-01 to 2022-12-31 (USD): 1817000000, 1820000000
- GS FY2023 `us-gaap:FederalFundsSoldAndSecuritiesBorrowedOrPurchasedUnderAgreementsToResellFairValueDisclosure` 2022-12-31 (USD): 225117000000, 225120000000
- GS FY2023 `us-gaap:FederalFundsSoldAndSecuritiesBorrowedOrPurchasedUnderAgreementsToResellFairValueDisclosure` 2023-12-31 (USD): 223540000000, 223543000000
- GS FY2023 `us-gaap:Investments` {"us-gaap:PledgedStatusAxis": "us-gaap:AssetPledgedAsCollateralWithoutRightMember", "us-gaap:PledgingPurposeAxis": "us-gaap:SecuritiesSoldUnderAgreementsToRepurchaseMember"} 2022-12-31 (USD): 2930000000, 2932000000
- GS FY2023 `us-gaap:OtherComprehensiveIncomeLossAvailableForSaleSecuritiesAdjustmentNetOfTax` 2022-01-01 to 2022-12-31 (USD): -2126000000, -2130000000
- GS FY2023 `us-gaap:OtherComprehensiveIncomeLossAvailableForSaleSecuritiesAdjustmentNetOfTax` 2023-01-01 to 2023-12-31 (USD): 1245000000, 1250000000
- GS FY2023 `us-gaap:SecuritiesBorrowedFairValueDisclosure` 2022-12-31 (USD): 38578000000, 38580000000
- GS FY2023 `us-gaap:SecuritiesLoanedOrSoldUnderAgreementsToRepurchaseFairValueDisclosure` 2022-12-31 (USD): 4370000000, 4372000000
- GS FY2023 `us-gaap:SecuritiesLoanedOrSoldUnderAgreementsToRepurchaseFairValueDisclosure` 2023-12-31 (USD): 8930000000, 8934000000
- GS FY2024 `gs:ChangeInCreditRwas` {"us-gaap:RiskWeightedAssetsCalculationMethodologyAxis": "us-gaap:AdvancedApproachMember"} 2024-01-01 to 2024-12-31 (USD): 3140000000, 3144000000
- GS FY2024 `gs:ChangeInCreditRwas` {"us-gaap:RiskWeightedAssetsCalculationMethodologyAxis": "us-gaap:StandardizedApproachMember"} 2024-01-01 to 2024-12-31 (USD): -12146000000, -12150000000
- GS FY2024 `gs:FairValueMeasurementWithUnobservableInputsReconciliationRecurringBasisLiabilityNetUnrealizedGainLossIncludedInEarningsAndOtherComprehensiveIncome` {"us-gaap:FinancialInstrumentAxis": "gs:OtherFinancialLiabilitiesMember"} 2023-01-01 to 2023-12-31 (USD): -1667000000, -1670000000
- GS FY2024 `gs:OtherSecuredFinancingsFairValueDisclosure` 2023-12-31 (USD): 12550000000, 12554000000
- GS FY2024 `gs:OtherSecuredFinancingsFairValueDisclosure` 2024-12-31 (USD): 27985000000, 27990000000
- GS FY2024 `gs:SubordinatedDebtOutstanding` {"us-gaap:LongtermDebtTypeAxis": "us-gaap:SubordinatedDebtMember"} 2023-12-31 (USD): 11898000000, 11900000000
- GS FY2024 `gs:SubordinatedDebtOutstanding` {"us-gaap:LongtermDebtTypeAxis": "us-gaap:SubordinatedDebtMember"} 2024-12-31 (USD): 11217000000, 11220000000
- GS FY2024 `us-gaap:AmortizationMethodQualifiedAffordableHousingProjectInvestments` 2023-12-31 (USD): 3390000000, 3394000000
- GS FY2024 `us-gaap:AmortizationMethodQualifiedAffordableHousingProjectInvestments` 2024-12-31 (USD): 3456000000, 3460000000
- GS FY2024 `us-gaap:DebtInstrumentFaceAmount` {"us-gaap:LongtermDebtTypeAxis": "us-gaap:SubordinatedDebtMember"} 2023-12-31 (USD): 12215000000, 12220000000
- GS FY2024 `us-gaap:DebtInstrumentFaceAmount` {"us-gaap:LongtermDebtTypeAxis": "us-gaap:SubordinatedDebtMember"} 2024-12-31 (USD): 12130000000, 12131000000
- GS FY2024 `us-gaap:DepositsFairValueDisclosure` 2024-12-31 (USD): 44855000000, 44860000000
- GS FY2024 `us-gaap:FederalFundsSoldAndSecuritiesBorrowedOrPurchasedUnderAgreementsToResellFairValueDisclosure` 2023-12-31 (USD): 223540000000, 223543000000
- GS FY2024 `us-gaap:FederalFundsSoldAndSecuritiesBorrowedOrPurchasedUnderAgreementsToResellFairValueDisclosure` 2024-12-31 (USD): 179790000000, 179793000000
- GS FY2024 `us-gaap:LongTermDebtFairValue` 2024-12-31 (USD): 89189000000, 89190000000
- GS FY2024 `us-gaap:OtherComprehensiveIncomeLossAvailableForSaleSecuritiesAdjustmentNetOfTax` 2023-01-01 to 2023-12-31 (USD): 1245000000, 1250000000
- GS FY2024 `us-gaap:SecuritiesBorrowedFairValueDisclosure` 2024-12-31 (USD): 46900000000, 46902000000
- GS FY2024 `us-gaap:SecuritiesLoanedOrSoldUnderAgreementsToRepurchaseFairValueDisclosure` 2023-12-31 (USD): 8930000000, 8934000000
- GS FY2024 `us-gaap:SecuritiesLoanedOrSoldUnderAgreementsToRepurchaseFairValueDisclosure` 2024-12-31 (USD): 10246000000, 10250000000
- GS FY2025 `gs:FairValueMeasurementWithUnobservableInputsReconciliationRecurringBasisLiabilityNetUnrealizedGainLossIncludedInEarningsAndOtherComprehensiveIncome` {"us-gaap:FinancialInstrumentAxis": "gs:OtherFinancialLiabilitiesMember"} 2025-01-01 to 2025-12-31 (USD): -1680000000, -1684000000
- GS FY2025 `gs:OtherSecuredFinancingsFairValueDisclosure` 2024-12-31 (USD): 27985000000, 27990000000
- GS FY2025 `gs:OtherSecuredFinancingsFairValueDisclosure` 2025-12-31 (USD): 27830000000, 27833000000
- GS FY2025 `gs:SubordinatedDebtOutstanding` {"us-gaap:LongtermDebtTypeAxis": "us-gaap:SubordinatedDebtMember"} 2024-12-31 (USD): 11217000000, 11220000000
- GS FY2025 `gs:SubordinatedDebtOutstanding` {"us-gaap:LongtermDebtTypeAxis": "us-gaap:SubordinatedDebtMember"} 2025-12-31 (USD): 9410000000, 9413000000
- GS FY2025 `us-gaap:AmortizationMethodQualifiedAffordableHousingProjectInvestments` 2024-12-31 (USD): 3456000000, 3460000000
- GS FY2025 `us-gaap:AmortizationMethodQualifiedAffordableHousingProjectInvestments` 2025-12-31 (USD): 4120000000, 4123000000
- GS FY2025 `us-gaap:DebtInstrumentFaceAmount` {"us-gaap:LongtermDebtTypeAxis": "us-gaap:SubordinatedDebtMember"} 2024-12-31 (USD): 12130000000, 12131000000
- GS FY2025 `us-gaap:DebtInstrumentFaceAmount` {"us-gaap:LongtermDebtTypeAxis": "us-gaap:SubordinatedDebtMember"} 2025-12-31 (USD): 10096000000, 10100000000
- GS FY2025 `us-gaap:DepositsFairValueDisclosure` 2024-12-31 (USD): 44855000000, 44860000000
- GS FY2025 `us-gaap:DepositsFairValueDisclosure` 2025-12-31 (USD): 76569000000, 76570000000
- GS FY2025 `us-gaap:FairValueNetDerivativeAssetLiabilityMeasuredOnRecurringBasisChangeInUnrealizedGainLoss` 2025-01-01 to 2025-12-31 (USD): -1230000000, -1231000000
- GS FY2025 `us-gaap:FederalFundsSoldAndSecuritiesBorrowedOrPurchasedUnderAgreementsToResellFairValueDisclosure` 2024-12-31 (USD): 179790000000, 179793000000
- GS FY2025 `us-gaap:FederalFundsSoldAndSecuritiesBorrowedOrPurchasedUnderAgreementsToResellFairValueDisclosure` 2025-12-31 (USD): 126007000000, 126010000000
- GS FY2025 `us-gaap:LongTermDebtFairValue` 2024-12-31 (USD): 89189000000, 89190000000
- GS FY2025 `us-gaap:LongTermDebtFairValue` 2025-12-31 (USD): 112680000000, 112683000000
- GS FY2025 `us-gaap:OtherComprehensiveIncomeLossAvailableForSaleSecuritiesAdjustmentNetOfTax` 2025-01-01 to 2025-12-31 (USD): 1075000000, 1080000000
- GS FY2025 `us-gaap:SecuritiesBorrowedFairValueDisclosure` 2024-12-31 (USD): 46900000000, 46902000000
- GS FY2025 `us-gaap:SecuritiesBorrowedFairValueDisclosure` 2025-12-31 (USD): 51580000000, 51581000000
- GS FY2025 `us-gaap:SecuritiesLoanedOrSoldUnderAgreementsToRepurchaseFairValueDisclosure` 2024-12-31 (USD): 10246000000, 10250000000
- GS FY2025 `us-gaap:SecuritiesLoanedOrSoldUnderAgreementsToRepurchaseFairValueDisclosure` 2025-12-31 (USD): 11995000000, 12000000000
- IBM FY2023 `ibm:NetCashFlowProceedsFromDividendDistribution` 2021-01-01 to 2021-12-31 (USD): 879000000, 900000000
- IBM FY2023 `ibm:PensionSettlementCharge` 2022-01-01 to 2022-12-31 (USD): 5894000000, 5900000000
- IBM FY2023 `us-gaap:DefinedBenefitPlanFundedStatusOfPlan` {"us-gaap:RetirementPlanFundingStatusAxis": "us-gaap:OverfundedPlanMember", "us-gaap:RetirementPlanSponsorLocationAxis": "country:US", "us-gaap:RetirementPlanTypeAxis": "us-gaap:PensionPlansDefinedBenefitMember"} 2023-12-31 (USD): 4584000000, 4600000000
- IBM FY2023 `us-gaap:EffectiveIncomeTaxRateContinuingOperations` 2022-01-01 to 2022-12-31 (pure): -0.54, -0.542
- IBM FY2023 `us-gaap:EffectiveIncomeTaxRateContinuingOperations` 2023-01-01 to 2023-12-31 (pure): 0.135, 0.14
- IBM FY2023 `us-gaap:TreasuryStockCommonShares` 2022-12-31 (shares): 1351000000, 1351024943
- IBM FY2023 `us-gaap:TreasuryStockCommonShares` 2023-12-31 (shares): 1351897514, 1352000000
- IBM FY2024 `ibm:PensionSettlementCharge` 2022-01-01 to 2022-12-31 (USD): 5894000000, 5900000000
- IBM FY2024 `ibm:PensionSettlementCharge` 2024-01-01 to 2024-12-31 (USD): 3100000000, 3113000000
- IBM FY2024 `us-gaap:EffectiveIncomeTaxRateContinuingOperations` 2022-01-01 to 2022-12-31 (pure): -0.54, -0.542
- IBM FY2024 `us-gaap:EffectiveIncomeTaxRateContinuingOperations` 2023-01-01 to 2023-12-31 (pure): 0.135, 0.14
- IBM FY2024 `us-gaap:EffectiveIncomeTaxRateContinuingOperations` 2024-01-01 to 2024-12-31 (pure): -0.038, -0.04
- IBM FY2024 `us-gaap:TreasuryStockCommonShares` 2023-12-31 (shares): 1351897514, 1352000000
- IBM FY2024 `us-gaap:TreasuryStockCommonShares` 2024-12-31 (shares): 1352874243, 1353000000
- IBM FY2025 `ibm:PensionSettlementCharge` 2024-01-01 to 2024-12-31 (USD): 3100000000, 3113000000
- IBM FY2025 `us-gaap:EffectiveIncomeTaxRateContinuingOperations` 2023-01-01 to 2023-12-31 (pure): 0.135, 0.14
- IBM FY2025 `us-gaap:EffectiveIncomeTaxRateContinuingOperations` 2024-01-01 to 2024-12-31 (pure): -0.038, -0.04
- IBM FY2025 `us-gaap:EffectiveIncomeTaxRateContinuingOperations` 2025-01-01 to 2025-12-31 (pure): -0.02, -0.023
- IBM FY2025 `us-gaap:PaymentsToAcquireBusinessesGross` {"us-gaap:BusinessAcquisitionAxis": "ibm:HashiCorpMember", "us-gaap:EquityInterestIssuedOrIssuableByTypeAxis": "us-gaap:CommonStockMember"} 2025-02-27 to 2025-02-27 (USD): 7200000000, 7212000000
- IBM FY2025 `us-gaap:TreasuryStockCommonShares` 2024-12-31 (shares): 1352874243, 1353000000
- IBM FY2025 `us-gaap:TreasuryStockCommonShares` 2025-12-31 (shares): 1353666394, 1354000000
- JNJ FY2023 `us-gaap:BusinessCombinationContingentConsiderationLiability` {"us-gaap:BusinessAcquisitionAxis": "jnj:AbiomedMember"} 2023-12-31 (USD): 700000000, 704000000
- JNJ FY2023 `us-gaap:RestructuringCharges` {"srt:ConsolidationItemsAxis": "us-gaap:OperatingSegmentsMember", "us-gaap:StatementBusinessSegmentsAxis": "jnj:InnovativeMedicineMember"} 2023-01-02 to 2023-12-31 (USD): 479000000, 500000000
- JNJ FY2023 `us-gaap:RestructuringCharges` {"srt:ConsolidationItemsAxis": "us-gaap:OperatingSegmentsMember", "us-gaap:StatementBusinessSegmentsAxis": "jnj:MedTechMember"} 2023-01-02 to 2023-12-31 (USD): 300000000, 319000000
- JNJ FY2023 `us-gaap:UnrecognizedTaxBenefits` 2023-12-31 (USD): 2485000000, 2500000000
- JNJ FY2024 `us-gaap:RestructuringCharges` {"srt:ConsolidationItemsAxis": "us-gaap:OperatingSegmentsMember", "us-gaap:StatementBusinessSegmentsAxis": "jnj:InnovativeMedicineMember"} 2023-01-02 to 2023-12-31 (USD): 479000000, 500000000
- JNJ FY2024 `us-gaap:RestructuringCharges` {"srt:ConsolidationItemsAxis": "us-gaap:OperatingSegmentsMember", "us-gaap:StatementBusinessSegmentsAxis": "jnj:MedTechMember"} 2023-01-02 to 2023-12-31 (USD): 300000000, 319000000
- JNJ FY2024 `us-gaap:RestructuringCharges` {"srt:ConsolidationItemsAxis": "us-gaap:OperatingSegmentsMember", "us-gaap:StatementBusinessSegmentsAxis": "jnj:InnovativeMedicineMember"} 2024-01-01 to 2024-12-29 (USD): 100000000, 102000000
- JNJ FY2024 `us-gaap:RestructuringCharges` {"srt:ConsolidationItemsAxis": "us-gaap:OperatingSegmentsMember", "us-gaap:StatementBusinessSegmentsAxis": "jnj:MedTechMember"} 2024-01-01 to 2024-12-29 (USD): 167000000, 200000000
- JNJ FY2024 `us-gaap:SupplierFinanceProgramObligationCurrent` 2023-12-31 (USD): 700000000, 704000000
- JNJ FY2024 `us-gaap:SupplierFinanceProgramObligationCurrent` 2024-12-29 (USD): 788000000, 800000000
- JNJ FY2024 `us-gaap:UnrecognizedTaxBenefits` 2024-12-29 (USD): 2000000000, 2020000000
- JNJ FY2025 `us-gaap:PaymentsToAcquireBusinessesNetOfCashAcquired` 2024-01-01 to 2024-12-29 (USD): 15100000000, 15146000000
- JNJ FY2025 `us-gaap:PaymentsToAcquireBusinessesNetOfCashAcquired` 2024-12-30 to 2025-12-28 (USD): 17500000000, 17541000000
- JNJ FY2025 `us-gaap:RestructuringCharges` {"srt:ConsolidationItemsAxis": "us-gaap:OperatingSegmentsMember", "us-gaap:StatementBusinessSegmentsAxis": "jnj:InnovativeMedicineMember"} 2023-01-02 to 2023-12-31 (USD): 479000000, 500000000
- JNJ FY2025 `us-gaap:RestructuringCharges` {"srt:ConsolidationItemsAxis": "us-gaap:OperatingSegmentsMember", "us-gaap:StatementBusinessSegmentsAxis": "jnj:MedTechMember"} 2023-01-02 to 2023-12-31 (USD): 300000000, 319000000
- JNJ FY2025 `us-gaap:RestructuringCharges` {"srt:ConsolidationItemsAxis": "us-gaap:OperatingSegmentsMember", "us-gaap:StatementBusinessSegmentsAxis": "jnj:InnovativeMedicineMember"} 2024-01-01 to 2024-12-29 (USD): 100000000, 102000000
- JNJ FY2025 `us-gaap:RestructuringCharges` {"srt:ConsolidationItemsAxis": "us-gaap:OperatingSegmentsMember", "us-gaap:StatementBusinessSegmentsAxis": "jnj:MedTechMember"} 2024-01-01 to 2024-12-29 (USD): 167000000, 200000000
- JNJ FY2025 `us-gaap:SupplierFinanceProgramObligationCurrent` 2024-12-29 (USD): 788000000, 800000000
- JNJ FY2025 `us-gaap:SupplierFinanceProgramObligationCurrent` 2025-12-28 (USD): 784000000, 800000000
- JNJ FY2025 `us-gaap:UnrecognizedTaxBenefits` 2025-12-28 (USD): 2662000000, 2700000000
- JPM FY2023 `us-gaap:AssetsFairValueDisclosure` {"us-gaap:FairValueByAssetClassAxis": "us-gaap:OtherAssetsMember", "us-gaap:FairValueByFairValueHierarchyLevelAxis": "us-gaap:FairValueInputsLevel3Member", "us-gaap:FairValueByMeasurementFrequencyAxis": "us-gaap:FairValueMeasurementsNonrecurringMember"} 2023-12-31 (USD): 1300000000, 1334000000
- JPM FY2023 `us-gaap:AssetsFairValueDisclosure` {"us-gaap:FairValueByFairValueHierarchyLevelAxis": "us-gaap:FairValueInputsLevel3Member", "us-gaap:FairValueByMeasurementFrequencyAxis": "us-gaap:FairValueMeasurementsRecurringMember"} 2023-12-31 (USD): 23656000000, 23700000000
- JPM FY2023 `us-gaap:CommonStockSharesIssued` 2022-12-31 (shares): 4104900000, 4104933895
- JPM FY2023 `us-gaap:DebtSecuritiesAvailableForSaleExcludingAccruedInterest` {"us-gaap:FinancialInstrumentAxis": "us-gaap:USStatesAndPoliticalSubdivisionsMember"} 2022-12-31 (USD): 6786000000, 6800000000
- JPM FY2023 `us-gaap:DebtSecuritiesAvailableForSaleExcludingAccruedInterest` {"us-gaap:FinancialInstrumentAxis": "us-gaap:USStatesAndPoliticalSubdivisionsMember"} 2023-12-31 (USD): 21367000000, 21400000000
- JPM FY2023 `us-gaap:DebtSecuritiesHeldToMaturityExcludingAccruedInterestAfterAllowanceForCreditLoss` {"us-gaap:FinancialInstrumentAxis": "us-gaap:USStatesAndPoliticalSubdivisionsMember"} 2022-12-31 (USD): 19700000000, 19747000000
- JPM FY2023 `us-gaap:DebtSecuritiesHeldToMaturityExcludingAccruedInterestAfterAllowanceForCreditLoss` {"us-gaap:FinancialInstrumentAxis": "us-gaap:USStatesAndPoliticalSubdivisionsMember"} 2023-12-31 (USD): 9900000000, 9945000000
- JPM FY2023 `us-gaap:DefinedBenefitPlanFairValueOfPlanAssets` {"us-gaap:FairValueByFairValueHierarchyLevelAxis": "us-gaap:FairValueInputsLevel3Member"} 2023-12-31 (USD): 3100000000, 3124000000
- JPM FY2023 `us-gaap:LitigationSettlementExpense` 2023-01-01 to 2023-12-31 (USD): 1400000000, 1436000000
- JPM FY2023 `us-gaap:LongTermDebtFairValue` {"us-gaap:FairValueByMeasurementFrequencyAxis": "us-gaap:FairValueMeasurementsRecurringMember"} 2022-12-31 (USD): 72281000000, 72300000000
- JPM FY2023 `us-gaap:LongTermDebtFairValue` {"us-gaap:FairValueByMeasurementFrequencyAxis": "us-gaap:FairValueMeasurementsRecurringMember"} 2023-12-31 (USD): 87900000000, 87924000000
- JPM FY2023 `us-gaap:LongTermDebtMaturitiesRepaymentsOfPrincipalInNextRollingTwelveMonths` {"srt:ConsolidatedEntitiesAxis": "srt:ParentCompanyMember"} 2023-12-31 (USD): 9088000000, 9100000000
- JPM FY2023 `us-gaap:LongTermDebtMaturitiesRepaymentsOfPrincipalInNextRollingTwelveMonths` 2023-12-31 (USD): 51174000000, 51200000000
- JPM FY2023 `us-gaap:UnrecognizedTaxBenefits` 2021-12-31 (USD): 4600000000, 4636000000
- JPM FY2023 `us-gaap:UnrecognizedTaxBenefits` 2022-12-31 (USD): 5000000000, 5043000000
- JPM FY2023 `us-gaap:UnrecognizedTaxBenefits` 2023-12-31 (USD): 5400000000, 5401000000
- JPM FY2024 `us-gaap:AssetsFairValueDisclosure` {"us-gaap:FairValueByAssetClassAxis": "us-gaap:OtherAssetsMember", "us-gaap:FairValueByFairValueHierarchyLevelAxis": "us-gaap:FairValueInputsLevel3Member", "us-gaap:FairValueByMeasurementFrequencyAxis": "us-gaap:FairValueMeasurementsNonrecurringMember"} 2024-12-31 (USD): 1000000000, 1048000000
- JPM FY2024 `us-gaap:AssetsFairValueDisclosure` {"us-gaap:FairValueByFairValueHierarchyLevelAxis": "us-gaap:FairValueInputsLevel3Member", "us-gaap:FairValueByMeasurementFrequencyAxis": "us-gaap:FairValueMeasurementsRecurringMember"} 2024-12-31 (USD): 23783000000, 23800000000
- JPM FY2024 `us-gaap:BusinessCombinationBargainPurchaseGainRecognizedAmount` {"us-gaap:BusinessAcquisitionAxis": "jpm:FirstRepublicBankMember"} 2023-05-01 to 2024-12-31 (USD): 2878000000, 2900000000
- JPM FY2024 `us-gaap:CommonStockSharesIssued` 2023-12-31 (shares): 4104900000, 4104933895
- JPM FY2024 `us-gaap:DebtSecuritiesAvailableForSaleExcludingAccruedInterest` {"us-gaap:FinancialInstrumentAxis": "us-gaap:USStatesAndPoliticalSubdivisionsMember"} 2023-12-31 (USD): 21367000000, 21400000000
- JPM FY2024 `us-gaap:DebtSecuritiesAvailableForSaleExcludingAccruedInterest` {"us-gaap:FinancialInstrumentAxis": "us-gaap:USStatesAndPoliticalSubdivisionsMember"} 2024-12-31 (USD): 17900000000, 17913000000
- JPM FY2024 `us-gaap:DebtSecuritiesHeldToMaturityExcludingAccruedInterestAfterAllowanceForCreditLoss` {"us-gaap:FinancialInstrumentAxis": "us-gaap:USStatesAndPoliticalSubdivisionsMember"} 2023-12-31 (USD): 9900000000, 9945000000
- JPM FY2024 `us-gaap:DebtSecuritiesHeldToMaturityExcludingAccruedInterestAfterAllowanceForCreditLoss` {"us-gaap:FinancialInstrumentAxis": "us-gaap:USStatesAndPoliticalSubdivisionsMember"} 2024-12-31 (USD): 9300000000, 9310000000
- JPM FY2024 `us-gaap:DefinedBenefitPlanFairValueOfPlanAssets` {"us-gaap:FairValueByFairValueHierarchyLevelAxis": "us-gaap:FairValueInputsLevel3Member"} 2024-12-31 (USD): 3956000000, 4000000000
- JPM FY2024 `us-gaap:LitigationSettlementExpense` 2023-01-01 to 2023-12-31 (USD): 1400000000, 1436000000
- JPM FY2024 `us-gaap:LongTermDebtFairValue` {"us-gaap:FairValueByMeasurementFrequencyAxis": "us-gaap:FairValueMeasurementsRecurringMember"} 2023-12-31 (USD): 87900000000, 87924000000
- JPM FY2024 `us-gaap:LongTermDebtFairValue` {"us-gaap:FairValueByMeasurementFrequencyAxis": "us-gaap:FairValueMeasurementsRecurringMember"} 2024-12-31 (USD): 100780000000, 100800000000
- JPM FY2024 `us-gaap:LongTermDebtMaturitiesRepaymentsOfPrincipalInNextRollingTwelveMonths` {"srt:ConsolidatedEntitiesAxis": "srt:ParentCompanyMember"} 2024-12-31 (USD): 7669000000, 7700000000
- JPM FY2024 `us-gaap:LongTermDebtMaturitiesRepaymentsOfPrincipalInNextRollingTwelveMonths` 2024-12-31 (USD): 40962000000, 41000000000
- JPM FY2024 `us-gaap:UnrecognizedTaxBenefits` 2022-12-31 (USD): 5000000000, 5043000000
- JPM FY2024 `us-gaap:UnrecognizedTaxBenefits` 2023-12-31 (USD): 5400000000, 5401000000
- JPM FY2024 `us-gaap:UnrecognizedTaxBenefits` 2024-12-31 (USD): 6159000000, 6200000000
- JPM FY2025 `us-gaap:AssetsFairValueDisclosure` {"us-gaap:FairValueByFairValueHierarchyLevelAxis": "us-gaap:FairValueInputsLevel3Member", "us-gaap:FairValueByMeasurementFrequencyAxis": "us-gaap:FairValueMeasurementsRecurringMember"} 2025-12-31 (USD): 25100000000, 25107000000
- JPM FY2025 `us-gaap:BusinessCombinationBargainPurchaseGainRecognizedAmount` {"us-gaap:BusinessAcquisitionAxis": "jpm:FirstRepublicBankMember"} 2023-05-01 to 2024-12-31 (USD): 2878000000, 2900000000
- JPM FY2025 `us-gaap:CommonStockSharesIssued` 2024-12-31 (shares): 4104900000, 4104933895
- JPM FY2025 `us-gaap:DebtSecuritiesAvailableForSaleExcludingAccruedInterest` {"us-gaap:FinancialInstrumentAxis": "us-gaap:USStatesAndPoliticalSubdivisionsMember"} 2024-12-31 (USD): 17900000000, 17913000000
- JPM FY2025 `us-gaap:DebtSecuritiesAvailableForSaleExcludingAccruedInterest` {"us-gaap:FinancialInstrumentAxis": "us-gaap:USStatesAndPoliticalSubdivisionsMember"} 2025-12-31 (USD): 20200000000, 20240000000
- JPM FY2025 `us-gaap:DebtSecuritiesHeldToMaturityExcludingAccruedInterestAfterAllowanceForCreditLoss` {"us-gaap:FinancialInstrumentAxis": "us-gaap:USStatesAndPoliticalSubdivisionsMember"} 2024-12-31 (USD): 9300000000, 9310000000
- JPM FY2025 `us-gaap:DeferredTaxAssetsTaxCreditCarryforwardsOther` 2025-12-31 (USD): 2252000000, 2300000000
- JPM FY2025 `us-gaap:DefinedBenefitPlanFairValueOfPlanAssets` {"us-gaap:FairValueByFairValueHierarchyLevelAxis": "us-gaap:FairValueInputsLevel3Member"} 2025-12-31 (USD): 4160000000, 4200000000
- JPM FY2025 `us-gaap:IncomeTaxesPaidNet` 2023-01-01 to 2023-12-31 (USD): 9900000000, 9908000000
- JPM FY2025 `us-gaap:IncomeTaxesPaidNet` 2024-01-01 to 2024-12-31 (USD): 11700000000, 11715000000
- JPM FY2025 `us-gaap:IncomeTaxesPaidNet` 2025-01-01 to 2025-12-31 (USD): 5300000000, 5309000000
- JPM FY2025 `us-gaap:LitigationSettlementExpense` 2023-01-01 to 2023-12-31 (USD): 1400000000, 1436000000
- JPM FY2025 `us-gaap:LongTermDebtFairValue` {"us-gaap:FairValueByMeasurementFrequencyAxis": "us-gaap:FairValueMeasurementsRecurringMember"} 2024-12-31 (USD): 100780000000, 100800000000
- JPM FY2025 `us-gaap:LongTermDebtFairValue` {"us-gaap:FairValueByMeasurementFrequencyAxis": "us-gaap:FairValueMeasurementsRecurringMember"} 2025-12-31 (USD): 134559000000, 134600000000
- JPM FY2025 `us-gaap:LongTermDebtMaturitiesRepaymentsOfPrincipalInNextRollingTwelveMonths` {"srt:ConsolidatedEntitiesAxis": "srt:ParentCompanyMember"} 2025-12-31 (USD): 14298000000, 14300000000
- JPM FY2025 `us-gaap:LongTermDebtMaturitiesRepaymentsOfPrincipalInNextRollingTwelveMonths` 2025-12-31 (USD): 42589000000, 42600000000
- JPM FY2025 `us-gaap:UnrecognizedTaxBenefits` 2023-12-31 (USD): 5400000000, 5401000000
- JPM FY2025 `us-gaap:UnrecognizedTaxBenefits` 2024-12-31 (USD): 6159000000, 6200000000
- JPM FY2025 `us-gaap:UnrecognizedTaxBenefits` 2025-12-31 (USD): 5600000000, 5624000000
- MA FY2023 `us-gaap:DebtLongtermAndShorttermCombinedAmount` 2022-12-31 (USD): 14000000000, 14023000000
- MA FY2023 `us-gaap:DebtLongtermAndShorttermCombinedAmount` 2023-12-31 (USD): 15681000000, 15700000000
- MA FY2024 `us-gaap:DebtLongtermAndShorttermCombinedAmount` 2023-12-31 (USD): 15681000000, 15700000000
- MA FY2024 `us-gaap:DebtLongtermAndShorttermCombinedAmount` 2024-12-31 (USD): 18200000000, 18226000000
- MA FY2025 `us-gaap:DebtLongtermAndShorttermCombinedAmount` 2024-12-31 (USD): 18200000000, 18226000000
- META FY2023 `us-gaap:ContractualObligation` 2023-12-31 (USD): 16489000000, 16490000000
- META FY2023 `us-gaap:DeferredTaxAssetsValuationAllowance` 2022-12-31 (USD): 2490000000, 2493000000
- META FY2023 `us-gaap:DeferredTaxAssetsValuationAllowance` 2023-12-31 (USD): 2879000000, 2880000000
- META FY2023 `us-gaap:RestructuringCharges` {"us-gaap:RestructuringCostAndReserveAxis": "us-gaap:EmployeeSeveranceMember", "us-gaap:RestructuringPlanAxis": "meta:A2023RestructuringMember"} 2023-01-01 to 2023-12-31 (USD): 1197000000, 1200000000
- META FY2023 `us-gaap:StockRepurchasedAndRetiredDuringPeriodValue` 2023-01-01 to 2023-12-31 (USD): 20030000000, 20033000000
- META FY2023 `us-gaap:UnrecognizedTaxBenefits` 2023-12-31 (USD): 11666000000, 11670000000
- META FY2024 `us-gaap:ContractualObligation` 2024-12-31 (USD): 32820000000, 32824000000
- META FY2024 `us-gaap:DeferredTaxAssetsValuationAllowance` 2023-12-31 (USD): 2879000000, 2880000000
- META FY2024 `us-gaap:DeferredTaxAssetsValuationAllowance` 2024-12-31 (USD): 3506000000, 3510000000
- META FY2024 `us-gaap:ImpairmentOfLongLivedAssetsHeldForUse` 2022-01-01 to 2022-12-31 (USD): 2218000000, 2220000000
- META FY2024 `us-gaap:ImpairmentOfLongLivedAssetsHeldForUse` 2023-01-01 to 2023-12-31 (USD): 2430000000, 2432000000
- META FY2024 `us-gaap:StockRepurchasedAndRetiredDuringPeriodValue` 2024-01-01 to 2024-12-31 (USD): 29750000000, 29754000000
- META FY2024 `us-gaap:UnrecognizedTaxBenefits` 2024-12-31 (USD): 15130000000, 15131000000
- META FY2025 `us-gaap:ContractualObligation` 2025-12-31 (USD): 131046000000, 131050000000
- META FY2025 `us-gaap:DeferredTaxAssetsValuationAllowance` 2024-12-31 (USD): 3506000000, 3510000000
- META FY2025 `us-gaap:DeferredTaxAssetsValuationAllowance` 2025-12-31 (USD): 15895000000, 15900000000
- META FY2025 `us-gaap:StockRepurchasedAndRetiredDuringPeriodValue` 2025-01-01 to 2025-12-31 (USD): 26260000000, 26264000000
- MS FY2023 `us-gaap:CommonStockSharesOutstanding` 2022-12-31 (shares): 1675000000, 1675487409
- MS FY2023 `us-gaap:CommonStockSharesOutstanding` 2023-12-31 (shares): 1626828437, 1627000000
- MS FY2024 `us-gaap:CommonStockSharesOutstanding` 2023-12-31 (shares): 1626828437, 1627000000
- MS FY2024 `us-gaap:CommonStockSharesOutstanding` 2024-12-31 (shares): 1606653706, 1607000000
- MS FY2025 `us-gaap:CommonStockSharesOutstanding` 2024-12-31 (shares): 1606653706, 1607000000
- MS FY2025 `us-gaap:CommonStockSharesOutstanding` 2025-12-31 (shares): 1582834137, 1583000000
- MSFT FY2024 `us-gaap:CommercialPaper` 2024-06-30 (USD): 6693000000, 6700000000
- MSFT FY2024 `us-gaap:Goodwill` {"us-gaap:BusinessAcquisitionAxis": "msft:ActivisionBlizzardIncMember"} 2023-10-13 (USD): 50969000000, 51000000000
- MSFT FY2024 `us-gaap:UnrecognizedTaxBenefits` 2022-06-30 (USD): 15593000000, 15600000000
- MSFT FY2024 `us-gaap:UnrecognizedTaxBenefits` 2023-06-30 (USD): 17100000000, 17120000000
- MSFT FY2024 `us-gaap:UnrecognizedTaxBenefits` 2024-06-30 (USD): 22760000000, 22800000000
- MSFT FY2025 `us-gaap:CommercialPaper` 2024-06-30 (USD): 6693000000, 6700000000
- MSFT FY2025 `us-gaap:UnrecognizedTaxBenefits` 2023-06-30 (USD): 17100000000, 17120000000
- MSFT FY2025 `us-gaap:UnrecognizedTaxBenefits` 2024-06-30 (USD): 22760000000, 22800000000
- MSFT FY2025 `us-gaap:UnrecognizedTaxBenefits` 2025-06-30 (USD): 24700000000, 24729000000
- MSFT FY2026 `us-gaap:UnrecognizedTaxBenefits` 2024-06-30 (USD): 22760000000, 22800000000
- MSFT FY2026 `us-gaap:UnrecognizedTaxBenefits` 2025-06-30 (USD): 24700000000, 24729000000
- MSFT FY2026 `us-gaap:UnrecognizedTaxBenefits` 2026-06-30 (USD): 25800000000, 25831000000
- NFLX FY2023 `us-gaap:ContractWithCustomerLiabilityCurrent` 2022-12-31 (USD): 1264661000, 1265000000
- NFLX FY2023 `us-gaap:ContractWithCustomerLiabilityCurrent` 2023-12-31 (USD): 1442969000, 1443000000
- NFLX FY2023 `us-gaap:DeferredTaxAssetsValuationAllowance` 2023-12-31 (USD): 442000000, 442293000
- NFLX FY2023 `us-gaap:FiniteLivedIntangibleAssetsNet` {"us-gaap:FiniteLivedIntangibleAssetsByMajorClassAxis": "nflx:LicensedContentMember"} 2023-12-31 (USD): 12722701000, 12723000000
- NFLX FY2023 `us-gaap:FiniteLivedIntangibleAssetsNet` {"us-gaap:FiniteLivedIntangibleAssetsByMajorClassAxis": "nflx:ProducedContentMember"} 2023-12-31 (USD): 9843000000, 9843150000
- NFLX FY2023 `us-gaap:PaymentsForRepurchaseOfCommonStock` 2023-01-01 to 2023-12-31 (USD): 6045000000, 6045347000
- NFLX FY2023 `us-gaap:PurchaseObligation` 2022-12-31 (USD): 21800000000, 21831947000
- NFLX FY2023 `us-gaap:PurchaseObligation` 2023-12-31 (USD): 21700000000, 21713349000
- NFLX FY2023 `us-gaap:ShortTermBorrowings` 2023-12-31 (USD): 399844000, 400000000
- NFLX FY2023 `us-gaap:UnrecognizedTaxBenefits` 2022-12-31 (USD): 226977000, 227000000
- NFLX FY2023 `us-gaap:UnrecognizedTaxBenefits` 2023-12-31 (USD): 327000000, 327105000
- NFLX FY2024 `us-gaap:ContractWithCustomerLiabilityCurrent` 2023-12-31 (USD): 1442969000, 1443000000
- NFLX FY2024 `us-gaap:ContractWithCustomerLiabilityCurrent` 2024-12-31 (USD): 1520813000, 1521000000
- NFLX FY2024 `us-gaap:DeferredTaxAssetsValuationAllowance` 2024-12-31 (USD): 540000000, 540272000
- NFLX FY2024 `us-gaap:FiniteLivedIntangibleAssetsNet` {"us-gaap:FiniteLivedIntangibleAssetsByMajorClassAxis": "nflx:LicensedContentMember"} 2024-12-31 (USD): 12422000000, 12422309000
- NFLX FY2024 `us-gaap:FiniteLivedIntangibleAssetsNet` {"us-gaap:FiniteLivedIntangibleAssetsByMajorClassAxis": "nflx:ProducedContentMember"} 2024-12-31 (USD): 10151543000, 10152000000
- NFLX FY2024 `us-gaap:PurchaseObligation` 2023-12-31 (USD): 21700000000, 21713349000
- NFLX FY2024 `us-gaap:PurchaseObligation` 2024-12-31 (USD): 23200000000, 23248931000
- NFLX FY2024 `us-gaap:ShortTermBorrowings` 2024-12-31 (USD): 1784000000, 1784453000
- NFLX FY2024 `us-gaap:UnrecognizedTaxBenefits` 2023-12-31 (USD): 327000000, 327105000
- NFLX FY2024 `us-gaap:UnrecognizedTaxBenefits` 2024-12-31 (USD): 432000000, 432280000
- NFLX FY2025 `nflx:FiniteLivedIntangibleAssetsReleasedNetLessAmortization` {"us-gaap:FiniteLivedIntangibleAssetsByMajorClassAxis": "nflx:ProducedContentMember"} 2025-12-31 (USD): 10687000000, 10687444000
- NFLX FY2025 `us-gaap:ContractWithCustomerLiabilityCurrent` 2024-12-31 (USD): 1520813000, 1521000000
- NFLX FY2025 `us-gaap:ContractWithCustomerLiabilityCurrent` 2025-12-31 (USD): 1775730000, 1776000000
- NFLX FY2025 `us-gaap:DeferredTaxAssetsValuationAllowance` 2025-12-31 (USD): 617575000, 618000000
- NFLX FY2025 `us-gaap:FiniteLivedIntangibleAssetsNet` {"us-gaap:FiniteLivedIntangibleAssetsByMajorClassAxis": "nflx:LicensedContentMember"} 2025-12-31 (USD): 12138578000, 12139000000
- NFLX FY2025 `us-gaap:PurchaseObligation` 2024-12-31 (USD): 23200000000, 23248931000
- NFLX FY2025 `us-gaap:PurchaseObligation` 2025-12-31 (USD): 24000000000, 24039228000
- NFLX FY2025 `us-gaap:UnrecognizedTaxBenefits` 2024-12-31 (USD): 432000000, 432280000
- NFLX FY2025 `us-gaap:UnrecognizedTaxBenefits` 2025-12-31 (USD): 566000000, 566363000
- NVDA FY2024 `us-gaap:DeferredTaxAssetsValuationAllowance` 2023-01-29 (USD): 1484000000, 1500000000
- NVDA FY2024 `us-gaap:DeferredTaxAssetsValuationAllowance` 2024-01-28 (USD): 1552000000, 1600000000
- NVDA FY2024 `us-gaap:Goodwill` 2023-01-29 (USD): 4372000000, 4400000000
- NVDA FY2024 `us-gaap:Goodwill` 2024-01-28 (USD): 4400000000, 4430000000
- NVDA FY2024 `us-gaap:StockRepurchasedAndRetiredDuringPeriodValue` 2023-01-30 to 2024-01-28 (USD): 9700000000, 9746000000
- NVDA FY2024 `us-gaap:TreasuryStockRetiredCostMethodAmount` {"us-gaap:StatementEquityComponentsAxis": "us-gaap:RetainedEarningsMember"} 2021-02-01 to 2022-01-30 (USD): 12000000000, 12026000000
- NVDA FY2025 `us-gaap:Goodwill` 2024-01-28 (USD): 4400000000, 4430000000
- NVDA FY2025 `us-gaap:Goodwill` 2025-01-26 (USD): 5188000000, 5200000000
- NVDA FY2025 `us-gaap:ProductWarrantyAccrual` 2025-01-26 (USD): 1290000000, 1300000000
- NVDA FY2025 `us-gaap:StockRepurchasedAndRetiredDuringPeriodValue` 2023-01-30 to 2024-01-28 (USD): 9700000000, 9746000000
- NVDA FY2025 `us-gaap:StockRepurchasedAndRetiredDuringPeriodValue` 2024-01-29 to 2025-01-26 (USD): 34000000000, 34015000000
- NVDA FY2026 `us-gaap:DeferredIncomeTaxAssetsNet` 2025-01-26 (USD): 10979000000, 11000000000
- NVDA FY2026 `us-gaap:DeferredIncomeTaxAssetsNet` 2026-01-25 (USD): 13258000000, 13300000000
- NVDA FY2026 `us-gaap:DeferredIncomeTaxLiabilitiesNet` 2026-01-25 (USD): 1774000000, 1800000000
- NVDA FY2026 `us-gaap:DeferredTaxAssetsValuationAllowance` 2025-01-26 (USD): 1600000000, 1610000000
- NVDA FY2026 `us-gaap:EquitySecuritiesFvNiCurrentAndNoncurrent` {"us-gaap:BalanceSheetLocationAxis": "us-gaap:OtherNoncurrentAssetsMember", "us-gaap:FairValueByFairValueHierarchyLevelAxis": "us-gaap:FairValueInputsLevel1Member", "us-gaap:FinancialInstrumentAxis": "nvda:PubliclyHeldEquitySecuritiesMember"} 2026-01-25 (USD): 4800000000, 4840000000
- NVDA FY2026 `us-gaap:Goodwill` 2025-01-26 (USD): 5188000000, 5200000000
- NVDA FY2026 `us-gaap:Goodwill` 2026-01-25 (USD): 20800000000, 20832000000
- NVDA FY2026 `us-gaap:ProductWarrantyAccrual` 2025-01-26 (USD): 1290000000, 1300000000
- NVDA FY2026 `us-gaap:ProductWarrantyAccrual` 2026-01-25 (USD): 2800000000, 2807000000
- NVDA FY2026 `us-gaap:StockRepurchasedAndRetiredDuringPeriodValue` 2024-01-29 to 2025-01-26 (USD): 34000000000, 34015000000
- NVDA FY2026 `us-gaap:StockRepurchasedAndRetiredDuringPeriodValue` 2025-01-27 to 2026-01-25 (USD): 40388000000, 40400000000
- PFE FY2023 `us-gaap:AssetImpairmentCharges` 2023-01-01 to 2023-12-31 (USD): 3000000000, 3024000000
- PFE FY2023 `us-gaap:Assets` 2022-12-31 (USD): 197000000000, 197205000000
- PFE FY2023 `us-gaap:Assets` 2023-12-31 (USD): 226501000000, 227000000000
- PFE FY2023 `us-gaap:EquitySecuritiesFvNiGainLoss` 2021-01-01 to 2021-12-31 (USD): 1300000000, 1344000000
- PFE FY2023 `us-gaap:EquitySecuritiesFvNiGainLoss` 2022-01-01 to 2022-12-31 (USD): -1273000000, -1300000000
- PFE FY2023 `us-gaap:EquitySecuritiesFvNiGainLoss` 2023-01-01 to 2023-12-31 (USD): 1590000000, 1600000000
- PFE FY2023 `us-gaap:ImpairmentOfIntangibleAssetsExcludingGoodwill` 2023-01-01 to 2023-12-31 (USD): 3000000000, 3008000000
- PFE FY2023 `us-gaap:IncomeTaxExpenseBenefit` 2022-01-01 to 2022-12-31 (USD): 3300000000, 3328000000
- PFE FY2023 `us-gaap:IncomeTaxExpenseBenefit` 2023-01-01 to 2023-12-31 (USD): -1100000000, -1115000000
- PFE FY2023 `us-gaap:IncreaseDecreaseInInventories` 2023-01-01 to 2023-12-31 (USD): 1169000000, 1200000000
- PFE FY2023 `us-gaap:LongTermDebtNoncurrent` 2022-12-31 (USD): 32884000000, 33000000000
- PFE FY2023 `us-gaap:LongTermDebtNoncurrent` 2023-12-31 (USD): 61538000000, 62000000000
- PFE FY2024 `us-gaap:AssetImpairmentCharges` 2023-01-01 to 2023-12-31 (USD): 3000000000, 3024000000
- PFE FY2024 `us-gaap:AssetImpairmentCharges` 2024-01-01 to 2024-12-31 (USD): 3295000000, 3300000000
- PFE FY2024 `us-gaap:Assets` 2023-12-31 (USD): 226501000000, 227000000000
- PFE FY2024 `us-gaap:Assets` 2024-12-31 (USD): 213000000000, 213396000000
- PFE FY2024 `us-gaap:EquitySecuritiesFvNiGainLoss` 2022-01-01 to 2022-12-31 (USD): -1273000000, -1300000000
- PFE FY2024 `us-gaap:EquitySecuritiesFvNiGainLoss` 2023-01-01 to 2023-12-31 (USD): 1590000000, 1600000000
- PFE FY2024 `us-gaap:EquitySecuritiesFvNiGainLoss` 2024-01-01 to 2024-12-31 (USD): 1000000000, 1008000000
- PFE FY2024 `us-gaap:ImpairmentOfIntangibleAssetsExcludingGoodwill` {"us-gaap:IndefiniteLivedIntangibleAssetsByMajorClassAxis": "us-gaap:InProcessResearchAndDevelopmentMember"} 2024-01-01 to 2024-12-31 (USD): 1873000000, 1900000000
- PFE FY2024 `us-gaap:ImpairmentOfIntangibleAssetsExcludingGoodwill` 2024-01-01 to 2024-12-31 (USD): 3295000000, 3300000000
- PFE FY2024 `us-gaap:IncomeTaxExpenseBenefit` 2022-01-01 to 2022-12-31 (USD): 3300000000, 3328000000
- PFE FY2024 `us-gaap:IncomeTaxExpenseBenefit` 2023-01-01 to 2023-12-31 (USD): -1100000000, -1115000000
- PFE FY2024 `us-gaap:LongTermDebtNoncurrent` 2023-12-31 (USD): 61538000000, 62000000000
- PFE FY2024 `us-gaap:LongTermDebtNoncurrent` 2024-12-31 (USD): 57000000000, 57405000000
- PFE FY2025 `us-gaap:AssetImpairmentCharges` 2023-01-01 to 2023-12-31 (USD): 3000000000, 3024000000
- PFE FY2025 `us-gaap:AssetImpairmentCharges` 2024-01-01 to 2024-12-31 (USD): 3295000000, 3300000000
- PFE FY2025 `us-gaap:AssetImpairmentCharges` 2025-01-01 to 2025-12-31 (USD): 4900000000, 4940000000
- PFE FY2025 `us-gaap:Assets` 2024-12-31 (USD): 213000000000, 213396000000
- PFE FY2025 `us-gaap:Assets` 2025-12-31 (USD): 208000000000, 208160000000
- PFE FY2025 `us-gaap:BusinessCombinationContingentConsiderationLiabilityNoncurrent` 2025-12-31 (USD): 1695000000, 1700000000
- PFE FY2025 `us-gaap:EquitySecuritiesFvNiGainLoss` 2023-01-01 to 2023-12-31 (USD): 1590000000, 1600000000
- PFE FY2025 `us-gaap:EquitySecuritiesFvNiGainLoss` 2024-01-01 to 2024-12-31 (USD): 1000000000, 1008000000
- PFE FY2025 `us-gaap:GainLossRelatedToLitigationSettlement` 2025-01-01 to 2025-12-31 (USD): -1057000000, -1100000000
- PFE FY2025 `us-gaap:ImpairmentOfIntangibleAssetsExcludingGoodwill` {"us-gaap:IndefiniteLivedIntangibleAssetsByMajorClassAxis": "us-gaap:InProcessResearchAndDevelopmentMember"} 2025-01-01 to 2025-12-31 (USD): 3900000000, 3903000000
- PFE FY2025 `us-gaap:IncomeTaxExpenseBenefit` 2023-01-01 to 2023-12-31 (USD): -1100000000, -1115000000
- PFE FY2025 `us-gaap:LongTermDebtNoncurrent` 2024-12-31 (USD): 57000000000, 57405000000
- PFE FY2025 `us-gaap:LongTermDebtNoncurrent` 2025-12-31 (USD): 61641000000, 62000000000
- SPGI FY2023 `us-gaap:BusinessAcquisitionEquityInterestIssuedOrIssuableValueAssigned` {"us-gaap:BusinessAcquisitionAxis": "spgi:IHSMarkitLtdMember"} 2022-02-28 (USD): 43500000000, 43536000000
- SPGI FY2023 `us-gaap:BusinessAcquisitionEquityInterestsIssuedOrIssuableNumberOfSharesIssued` {"us-gaap:BusinessAcquisitionAxis": "spgi:IHSMarkitLtdMember"} 2022-02-28 to 2022-02-28 (shares): 113800000, 113800453
- SPGI FY2023 `us-gaap:CashAndCashEquivalentsAtCarryingValue` 2022-12-31 (USD): 1286000000, 1300000000
- SPGI FY2023 `us-gaap:CashAndCashEquivalentsAtCarryingValue` 2023-12-31 (USD): 1290000000, 1300000000
- SPGI FY2023 `us-gaap:GainLossOnSaleOfBusiness` {"us-gaap:DisposalGroupClassificationAxis": "us-gaap:DisposalGroupDisposedOfBySaleNotDiscontinuedOperationsMember", "us-gaap:IncomeStatementBalanceSheetAndAdditionalDisclosuresByDisposalGroupsIncludingDiscontinuedOperationsAxis": "spgi:CUSIPGlobalServicesMember"} 2022-01-01 to 2022-12-31 (USD): 1300000000, 1342000000
- SPGI FY2024 `us-gaap:BusinessAcquisitionEquityInterestIssuedOrIssuableValueAssigned` {"us-gaap:BusinessAcquisitionAxis": "spgi:IHSMarkitLtdMember"} 2022-02-28 (USD): 43500000000, 43536000000
- SPGI FY2024 `us-gaap:BusinessAcquisitionEquityInterestsIssuedOrIssuableNumberOfSharesIssued` {"us-gaap:BusinessAcquisitionAxis": "spgi:IHSMarkitLtdMember"} 2022-02-28 to 2022-02-28 (shares): 113800000, 113800453
- SPGI FY2024 `us-gaap:CashAndCashEquivalentsAtCarryingValue` 2023-12-31 (USD): 1290000000, 1300000000
- SPGI FY2024 `us-gaap:CashAndCashEquivalentsAtCarryingValue` 2024-12-31 (USD): 1666000000, 1700000000
- SPGI FY2024 `us-gaap:GainLossOnSaleOfBusiness` {"us-gaap:DisposalGroupClassificationAxis": "us-gaap:DisposalGroupDisposedOfBySaleNotDiscontinuedOperationsMember", "us-gaap:IncomeStatementBalanceSheetAndAdditionalDisclosuresByDisposalGroupsIncludingDiscontinuedOperationsAxis": "spgi:CUSIPGlobalServicesMember"} 2022-01-01 to 2022-12-31 (USD): 1300000000, 1342000000
- SPGI FY2025 `us-gaap:CashAndCashEquivalentsAtCarryingValue` 2024-12-31 (USD): 1666000000, 1700000000
- SPGI FY2025 `us-gaap:CashAndCashEquivalentsAtCarryingValue` 2025-12-31 (USD): 1700000000, 1745000000
- UNH FY2023 `us-gaap:ProceedsFromContributionsFromAffiliates` {"srt:ConsolidatedEntitiesAxis": "srt:ParentCompanyMember"} 2021-01-01 to 2021-12-31 (USD): 200000000, 245000000
- UNH FY2023 `us-gaap:ProceedsFromContributionsFromAffiliates` {"srt:ConsolidatedEntitiesAxis": "srt:ParentCompanyMember"} 2022-01-01 to 2022-12-31 (USD): 1400000000, 1424000000
- UNH FY2023 `us-gaap:ProceedsFromContributionsFromAffiliates` {"srt:ConsolidatedEntitiesAxis": "srt:ParentCompanyMember"} 2023-01-01 to 2023-12-31 (USD): 600000000, 639000000
- UNH FY2024 `us-gaap:ProceedsFromContributionsFromAffiliates` {"srt:ConsolidatedEntitiesAxis": "srt:ParentCompanyMember"} 2022-01-01 to 2022-12-31 (USD): 1400000000, 1424000000
- UNH FY2025 `unh:Capitalcontributionstosubsidiaries` {"srt:ConsolidatedEntitiesAxis": "srt:ParentCompanyMember"} 2023-01-01 to 2023-12-31 (USD): 2472000000, 2500000000
- UNH FY2025 `unh:Capitalcontributionstosubsidiaries` {"srt:ConsolidatedEntitiesAxis": "srt:ParentCompanyMember"} 2025-01-01 to 2025-12-31 (USD): 6800000000, 6822000000
- VZ FY2023 `us-gaap:DeferredTaxAssetsOperatingLossCarryforwards` 2023-12-31 (USD): 1900000000, 1922000000
- VZ FY2023 `us-gaap:DeferredTaxAssetsValuationAllowance` 2023-12-31 (USD): 1300000000, 1341000000
- VZ FY2023 `us-gaap:DerivativeLiabilityFairValueOfCollateral` 2022-12-31 (USD): 2286000000, 2300000000
- VZ FY2023 `us-gaap:DerivativeLiabilityFairValueOfCollateral` 2023-12-31 (USD): 1400000000, 1406000000
- VZ FY2023 `us-gaap:GoodwillImpairmentLoss` 2023-01-01 to 2023-12-31 (USD): 5800000000, 5841000000
- VZ FY2024 `us-gaap:DeferredTaxAssetsOperatingLossCarryforwards` 2024-12-31 (USD): 1700000000, 1719000000
- VZ FY2024 `us-gaap:DeferredTaxAssetsValuationAllowance` 2024-12-31 (USD): 1399000000, 1400000000
- VZ FY2024 `us-gaap:DefinedBenefitPlanAssetsTransferredToFromPlan` {"us-gaap:RetirementPlanTypeAxis": "us-gaap:PensionPlansDefinedBenefitMember"} 2024-01-01 to 2024-12-31 (USD): 5600000000, 5611000000
- VZ FY2024 `us-gaap:DerivativeLiabilityFairValueOfCollateral` 2023-12-31 (USD): 1400000000, 1406000000
- VZ FY2024 `us-gaap:DerivativeLiabilityFairValueOfCollateral` 2024-12-31 (USD): 2100000000, 2118000000
- VZ FY2024 `us-gaap:GoodwillImpairmentLoss` 2023-01-01 to 2023-12-31 (USD): 5800000000, 5841000000
- VZ FY2024 `vz:SeveranceLiabilityChargedToExpense` 2024-01-01 to 2024-12-31 (USD): 1494000000, 1500000000
- VZ FY2025 `us-gaap:DeferredTaxAssetsOperatingLossCarryforwards` 2025-12-31 (USD): 1400000000, 1423000000
- VZ FY2025 `us-gaap:DeferredTaxAssetsValuationAllowance` 2025-12-31 (USD): 1161000000, 1200000000
- VZ FY2025 `us-gaap:DerivativeLiabilityFairValueOfCollateral` 2024-12-31 (USD): 2100000000, 2118000000
- VZ FY2025 `us-gaap:DerivativeLiabilityFairValueOfCollateral` 2025-12-31 (USD): 1074000000, 1100000000
- VZ FY2025 `us-gaap:GoodwillImpairmentLoss` 2023-01-01 to 2023-12-31 (USD): 5800000000, 5841000000
- VZ FY2025 `vz:SeveranceLiabilityChargedToExpense` 2024-01-01 to 2024-12-31 (USD): 1494000000, 1500000000
- VZ FY2025 `vz:SeveranceLiabilityChargedToExpense` 2025-01-01 to 2025-12-31 (USD): 1491000000, 1500000000
- WMT FY2024 `us-gaap:AllocatedShareBasedCompensationExpense` 2021-02-01 to 2022-01-31 (USD): 1163000000, 1200000000
- WMT FY2024 `us-gaap:AllocatedShareBasedCompensationExpense` 2022-02-01 to 2023-01-31 (USD): 1578000000, 1600000000
- WMT FY2024 `us-gaap:AllocatedShareBasedCompensationExpense` 2023-02-01 to 2024-01-31 (USD): 2093000000, 2100000000
- WMT FY2024 `us-gaap:CashAndCashEquivalentsAtCarryingValue` 2023-01-31 (USD): 8600000000, 8625000000
- WMT FY2024 `us-gaap:CashAndCashEquivalentsAtCarryingValue` 2024-01-31 (USD): 9867000000, 9900000000
- WMT FY2024 `us-gaap:DeferredTaxAssetsValuationAllowance` 2023-01-31 (USD): 7800000000, 7815000000
- WMT FY2024 `us-gaap:DeferredTaxAssetsValuationAllowance` 2024-01-31 (USD): 7485000000, 7500000000
- WMT FY2024 `us-gaap:DepreciationAmortizationAndAccretionNet` 2021-02-01 to 2022-01-31 (USD): 10658000000, 10700000000
- WMT FY2024 `us-gaap:DepreciationAmortizationAndAccretionNet` 2022-02-01 to 2023-01-31 (USD): 10900000000, 10945000000
- WMT FY2024 `us-gaap:DepreciationAmortizationAndAccretionNet` 2023-02-01 to 2024-01-31 (USD): 11853000000, 11900000000
- WMT FY2024 `us-gaap:ProceedsFromIssuanceOrSaleOfEquity` 2021-02-01 to 2022-01-31 (USD): 3200000000, 3239000000
- WMT FY2024 `us-gaap:ProceedsFromIssuanceOrSaleOfEquity` 2023-02-01 to 2024-01-31 (USD): 700000000, 716000000
- WMT FY2024 `us-gaap:ShortTermBorrowings` 2023-01-31 (USD): 372000000, 400000000
- WMT FY2024 `us-gaap:ShortTermBorrowings` 2024-01-31 (USD): 878000000, 900000000
- WMT FY2024 `us-gaap:UnrecognizedTaxBenefits` 2023-01-31 (USD): 3300000000, 3307000000
- WMT FY2024 `us-gaap:UnrecognizedTaxBenefits` 2024-01-31 (USD): 3500000000, 3540000000
- WMT FY2025 `us-gaap:AllocatedShareBasedCompensationExpense` 2022-02-01 to 2023-01-31 (USD): 1578000000, 1600000000
- WMT FY2025 `us-gaap:AllocatedShareBasedCompensationExpense` 2023-02-01 to 2024-01-31 (USD): 2093000000, 2100000000
- WMT FY2025 `us-gaap:AllocatedShareBasedCompensationExpense` 2024-02-01 to 2025-01-31 (USD): 2769000000, 2800000000
- WMT FY2025 `us-gaap:CashAndCashEquivalentsAtCarryingValue` 2024-01-31 (USD): 9867000000, 9900000000
- WMT FY2025 `us-gaap:CashAndCashEquivalentsAtCarryingValue` 2025-01-31 (USD): 9000000000, 9037000000
- WMT FY2025 `us-gaap:DeferredTaxAssetsValuationAllowance` 2024-01-31 (USD): 7485000000, 7500000000
- WMT FY2025 `us-gaap:DeferredTaxAssetsValuationAllowance` 2025-01-31 (USD): 7400000000, 7405000000
- WMT FY2025 `us-gaap:DepreciationAmortizationAndAccretionNet` 2022-02-01 to 2023-01-31 (USD): 10900000000, 10945000000
- WMT FY2025 `us-gaap:DepreciationAmortizationAndAccretionNet` 2023-02-01 to 2024-01-31 (USD): 11853000000, 11900000000
- WMT FY2025 `us-gaap:DepreciationAmortizationAndAccretionNet` 2024-02-01 to 2025-01-31 (USD): 12973000000, 13000000000
- WMT FY2025 `us-gaap:ProceedsFromIssuanceOrSaleOfEquity` 2023-02-01 to 2024-01-31 (USD): 700000000, 716000000
- WMT FY2025 `us-gaap:ShortTermBorrowings` 2024-01-31 (USD): 878000000, 900000000
- WMT FY2025 `us-gaap:ShortTermBorrowings` 2025-01-31 (USD): 3068000000, 3100000000
- WMT FY2025 `us-gaap:UnrecognizedTaxBenefits` 2024-01-31 (USD): 3500000000, 3540000000
- WMT FY2025 `us-gaap:UnrecognizedTaxBenefits` 2025-01-31 (USD): 3757000000, 3800000000
- WMT FY2026 `us-gaap:AllocatedShareBasedCompensationExpense` 2023-02-01 to 2024-01-31 (USD): 2093000000, 2100000000
- WMT FY2026 `us-gaap:AllocatedShareBasedCompensationExpense` 2024-02-01 to 2025-01-31 (USD): 2769000000, 2800000000
- WMT FY2026 `us-gaap:AllocatedShareBasedCompensationExpense` 2025-02-01 to 2026-01-31 (USD): 3600000000, 3603000000
- WMT FY2026 `us-gaap:CashAndCashEquivalentsAtCarryingValue` 2025-01-31 (USD): 9000000000, 9037000000
- WMT FY2026 `us-gaap:CashAndCashEquivalentsAtCarryingValue` 2026-01-31 (USD): 10700000000, 10727000000
- WMT FY2026 `us-gaap:DeferredTaxAssetsValuationAllowance` 2025-01-31 (USD): 7400000000, 7405000000
- WMT FY2026 `us-gaap:DeferredTaxAssetsValuationAllowance` 2026-01-31 (USD): 4400000000, 4421000000
- WMT FY2026 `us-gaap:DepreciationAmortizationAndAccretionNet` 2023-02-01 to 2024-01-31 (USD): 11853000000, 11900000000
- WMT FY2026 `us-gaap:DepreciationAmortizationAndAccretionNet` 2024-02-01 to 2025-01-31 (USD): 12973000000, 13000000000
- WMT FY2026 `us-gaap:DepreciationAmortizationAndAccretionNet` 2025-02-01 to 2026-01-31 (USD): 14200000000, 14203000000
- WMT FY2026 `us-gaap:NonoperatingIncomeExpense` 2023-02-01 to 2024-01-31 (USD): -3000000000, -3027000000
- WMT FY2026 `us-gaap:NonoperatingIncomeExpense` 2024-02-01 to 2025-01-31 (USD): -794000000, -800000000
- WMT FY2026 `us-gaap:NonoperatingIncomeExpense` 2025-02-01 to 2026-01-31 (USD): 2075000000, 2100000000
- WMT FY2026 `us-gaap:ProceedsFromIssuanceOrSaleOfEquity` 2023-02-01 to 2024-01-31 (USD): 700000000, 716000000
- WMT FY2026 `us-gaap:ShortTermBorrowings` 2025-01-31 (USD): 3068000000, 3100000000
- WMT FY2026 `us-gaap:ShortTermBorrowings` 2026-01-31 (USD): 6596000000, 6600000000
- WMT FY2026 `us-gaap:UnrecognizedTaxBenefits` 2025-01-31 (USD): 3757000000, 3800000000
- WMT FY2026 `us-gaap:UnrecognizedTaxBenefits` 2026-01-31 (USD): 2400000000, 2440000000

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
