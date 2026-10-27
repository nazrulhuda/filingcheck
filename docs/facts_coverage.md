# XBRL facts coverage

For each company and pinned fiscal year: does its companyfacts file hold a fact from a 10-K that ends on the filing's period of report, under one of the candidate tags? Amounts over a period must cover a whole fiscal year (350 to 380 days), because 10-Ks also report quarters ending on the same day. The first candidate that matches is shown. Where none matches, a candidate that the filing reports with another date is named in brackets. Coverage only: this does not choose the tag an answer will use. Written by `make verify-facts`; do not edit by hand.

## Totals

| Metric | Found | Tags that matched |
|---|---:|---|
| revenue | 75 of 75 | `Revenues` 41, `RevenueFromContractWithCustomerExcludingAssessedTax` 28, `RevenuesNetOfInterestExpense` 6 |
| net income | 75 of 75 | `NetIncomeLoss` 72, `ProfitLoss` 3 |
| diluted EPS | 75 of 75 | `EarningsPerShareDiluted` 75 |
| operating income | 45 of 75 | `OperatingIncomeLoss` 45 |
| total assets | 75 of 75 | `Assets` 75 |
| total liabilities | 60 of 75 | `Liabilities` 60 |
| equity | 75 of 75 | `StockholdersEquity` 66, `StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest` 9 |
| operating cash flow | 75 of 75 | `NetCashProvidedByUsedInOperatingActivities` 75 |
| capex | 57 of 75 | `PaymentsToAcquirePropertyPlantAndEquipment` 57 |
| cash | 75 of 75 | `CashAndCashEquivalentsAtCarryingValue` 63, `CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents` 12 |
| long-term debt | 61 of 75 | `LongTermDebtNoncurrent` 52, `LongTermDebt` 9 |
| shares outstanding | 45 of 75 | `CommonStockSharesOutstanding` 42, `dei:EntityCommonStockSharesOutstanding` 3 |

Candidate tags, in the order they are tried:

- revenue: `Revenues`, `RevenueFromContractWithCustomerExcludingAssessedTax`, `RevenuesNetOfInterestExpense`, `SalesRevenueNet`
- net income: `NetIncomeLoss`, `ProfitLoss`
- diluted EPS: `EarningsPerShareDiluted`
- operating income: `OperatingIncomeLoss`
- total assets: `Assets`
- total liabilities: `Liabilities`
- equity: `StockholdersEquity`, `StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest`
- operating cash flow: `NetCashProvidedByUsedInOperatingActivities`
- capex: `PaymentsToAcquirePropertyPlantAndEquipment`
- cash: `CashAndCashEquivalentsAtCarryingValue`, `CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents`
- long-term debt: `LongTermDebtNoncurrent`, `LongTermDebt`
- shares outstanding: `dei:EntityCommonStockSharesOutstanding`, `CommonStockSharesOutstanding`

## AAPL

| Metric | FY2023 | FY2024 | FY2025 |
|---|---|---|---|
| revenue | found: `RevenueFromContractWithCustomerExcludingAssessedTax` | found: `RevenueFromContractWithCustomerExcludingAssessedTax` | found: `RevenueFromContractWithCustomerExcludingAssessedTax` |
| net income | found: `NetIncomeLoss` | found: `NetIncomeLoss` | found: `NetIncomeLoss` |
| diluted EPS | found: `EarningsPerShareDiluted` | found: `EarningsPerShareDiluted` | found: `EarningsPerShareDiluted` |
| operating income | found: `OperatingIncomeLoss` | found: `OperatingIncomeLoss` | found: `OperatingIncomeLoss` |
| total assets | found: `Assets` | found: `Assets` | found: `Assets` |
| total liabilities | found: `Liabilities` | found: `Liabilities` | found: `Liabilities` |
| equity | found: `StockholdersEquity` | found: `StockholdersEquity` | found: `StockholdersEquity` |
| operating cash flow | found: `NetCashProvidedByUsedInOperatingActivities` | found: `NetCashProvidedByUsedInOperatingActivities` | found: `NetCashProvidedByUsedInOperatingActivities` |
| capex | found: `PaymentsToAcquirePropertyPlantAndEquipment` | found: `PaymentsToAcquirePropertyPlantAndEquipment` | found: `PaymentsToAcquirePropertyPlantAndEquipment` |
| cash | found: `CashAndCashEquivalentsAtCarryingValue` | found: `CashAndCashEquivalentsAtCarryingValue` | found: `CashAndCashEquivalentsAtCarryingValue` |
| long-term debt | found: `LongTermDebtNoncurrent` | found: `LongTermDebtNoncurrent` | found: `LongTermDebtNoncurrent` |
| shares outstanding | found: `CommonStockSharesOutstanding` | found: `CommonStockSharesOutstanding` | found: `CommonStockSharesOutstanding` |

## AMZN

| Metric | FY2023 | FY2024 | FY2025 |
|---|---|---|---|
| revenue | found: `RevenueFromContractWithCustomerExcludingAssessedTax` | found: `RevenueFromContractWithCustomerExcludingAssessedTax` | found: `RevenueFromContractWithCustomerExcludingAssessedTax` |
| net income | found: `NetIncomeLoss` | found: `NetIncomeLoss` | found: `NetIncomeLoss` |
| diluted EPS | found: `EarningsPerShareDiluted` | found: `EarningsPerShareDiluted` | found: `EarningsPerShareDiluted` |
| operating income | found: `OperatingIncomeLoss` | found: `OperatingIncomeLoss` | found: `OperatingIncomeLoss` |
| total assets | found: `Assets` | found: `Assets` | found: `Assets` |
| total liabilities | missing | missing | missing |
| equity | found: `StockholdersEquity` | found: `StockholdersEquity` | found: `StockholdersEquity` |
| operating cash flow | found: `NetCashProvidedByUsedInOperatingActivities` | found: `NetCashProvidedByUsedInOperatingActivities` | found: `NetCashProvidedByUsedInOperatingActivities` |
| capex | missing | missing | missing |
| cash | found: `CashAndCashEquivalentsAtCarryingValue` | found: `CashAndCashEquivalentsAtCarryingValue` | found: `CashAndCashEquivalentsAtCarryingValue` |
| long-term debt | found: `LongTermDebtNoncurrent` | found: `LongTermDebtNoncurrent` | found: `LongTermDebtNoncurrent` |
| shares outstanding | found: `CommonStockSharesOutstanding` | found: `CommonStockSharesOutstanding` | found: `CommonStockSharesOutstanding` |

## AXP

| Metric | FY2023 | FY2024 | FY2025 |
|---|---|---|---|
| revenue | found: `RevenueFromContractWithCustomerExcludingAssessedTax` | found: `RevenueFromContractWithCustomerExcludingAssessedTax` | found: `RevenueFromContractWithCustomerExcludingAssessedTax` |
| net income | found: `NetIncomeLoss` | found: `NetIncomeLoss` | found: `NetIncomeLoss` |
| diluted EPS | found: `EarningsPerShareDiluted` | found: `EarningsPerShareDiluted` | found: `EarningsPerShareDiluted` |
| operating income | missing | missing | missing |
| total assets | found: `Assets` | found: `Assets` | found: `Assets` |
| total liabilities | found: `Liabilities` | found: `Liabilities` | found: `Liabilities` |
| equity | found: `StockholdersEquity` | found: `StockholdersEquity` | found: `StockholdersEquity` |
| operating cash flow | found: `NetCashProvidedByUsedInOperatingActivities` | found: `NetCashProvidedByUsedInOperatingActivities` | found: `NetCashProvidedByUsedInOperatingActivities` |
| capex | found: `PaymentsToAcquirePropertyPlantAndEquipment` | found: `PaymentsToAcquirePropertyPlantAndEquipment` | found: `PaymentsToAcquirePropertyPlantAndEquipment` |
| cash | found: `CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents` | found: `CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents` | found: `CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents` |
| long-term debt | found: `LongTermDebt` | found: `LongTermDebt` | found: `LongTermDebt` |
| shares outstanding | found: `CommonStockSharesOutstanding` | found: `CommonStockSharesOutstanding` | found: `CommonStockSharesOutstanding` |

## C

| Metric | FY2023 | FY2024 | FY2025 |
|---|---|---|---|
| revenue | found: `Revenues` | found: `Revenues` | found: `Revenues` |
| net income | found: `NetIncomeLoss` | found: `NetIncomeLoss` | found: `NetIncomeLoss` |
| diluted EPS | found: `EarningsPerShareDiluted` | found: `EarningsPerShareDiluted` | found: `EarningsPerShareDiluted` |
| operating income | missing | missing | missing |
| total assets | found: `Assets` | found: `Assets` | found: `Assets` |
| total liabilities | found: `Liabilities` | found: `Liabilities` | found: `Liabilities` |
| equity | found: `StockholdersEquity` | found: `StockholdersEquity` | found: `StockholdersEquity` |
| operating cash flow | found: `NetCashProvidedByUsedInOperatingActivities` | found: `NetCashProvidedByUsedInOperatingActivities` | found: `NetCashProvidedByUsedInOperatingActivities` |
| capex | found: `PaymentsToAcquirePropertyPlantAndEquipment` | found: `PaymentsToAcquirePropertyPlantAndEquipment` | found: `PaymentsToAcquirePropertyPlantAndEquipment` |
| cash | found: `CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents` | found: `CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents` | found: `CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents` |
| long-term debt | found: `LongTermDebt` | found: `LongTermDebt` | found: `LongTermDebt` |
| shares outstanding | missing (dei:EntityCommonStockSharesOutstanding dated 2024-01-31 in this 10-K) | missing (dei:EntityCommonStockSharesOutstanding dated 2025-01-31 in this 10-K) | missing (dei:EntityCommonStockSharesOutstanding dated 2026-01-31 in this 10-K) |

## COF

| Metric | FY2023 | FY2024 | FY2025 |
|---|---|---|---|
| revenue | found: `Revenues` | found: `Revenues` | found: `Revenues` |
| net income | found: `NetIncomeLoss` | found: `NetIncomeLoss` | found: `NetIncomeLoss` |
| diluted EPS | found: `EarningsPerShareDiluted` | found: `EarningsPerShareDiluted` | found: `EarningsPerShareDiluted` |
| operating income | missing | missing | missing |
| total assets | found: `Assets` | found: `Assets` | found: `Assets` |
| total liabilities | found: `Liabilities` | found: `Liabilities` | found: `Liabilities` |
| equity | found: `StockholdersEquity` | found: `StockholdersEquity` | found: `StockholdersEquity` |
| operating cash flow | found: `NetCashProvidedByUsedInOperatingActivities` | found: `NetCashProvidedByUsedInOperatingActivities` | found: `NetCashProvidedByUsedInOperatingActivities` |
| capex | found: `PaymentsToAcquirePropertyPlantAndEquipment` | found: `PaymentsToAcquirePropertyPlantAndEquipment` | found: `PaymentsToAcquirePropertyPlantAndEquipment` |
| cash | found: `CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents` | found: `CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents` | found: `CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents` |
| long-term debt | missing | missing | missing |
| shares outstanding | found: `CommonStockSharesOutstanding` | found: `CommonStockSharesOutstanding` | found: `CommonStockSharesOutstanding` |

## COST

| Metric | FY2024 | FY2025 | FY2026 |
|---|---|---|---|
| revenue | found: `Revenues` | found: `Revenues` | found: `RevenueFromContractWithCustomerExcludingAssessedTax` |
| net income | found: `NetIncomeLoss` | found: `NetIncomeLoss` | found: `NetIncomeLoss` |
| diluted EPS | found: `EarningsPerShareDiluted` | found: `EarningsPerShareDiluted` | found: `EarningsPerShareDiluted` |
| operating income | found: `OperatingIncomeLoss` | found: `OperatingIncomeLoss` | found: `OperatingIncomeLoss` |
| total assets | found: `Assets` | found: `Assets` | found: `Assets` |
| total liabilities | found: `Liabilities` | found: `Liabilities` | found: `Liabilities` |
| equity | found: `StockholdersEquity` | found: `StockholdersEquity` | found: `StockholdersEquity` |
| operating cash flow | found: `NetCashProvidedByUsedInOperatingActivities` | found: `NetCashProvidedByUsedInOperatingActivities` | found: `NetCashProvidedByUsedInOperatingActivities` |
| capex | found: `PaymentsToAcquirePropertyPlantAndEquipment` | found: `PaymentsToAcquirePropertyPlantAndEquipment` | found: `PaymentsToAcquirePropertyPlantAndEquipment` |
| cash | found: `CashAndCashEquivalentsAtCarryingValue` | found: `CashAndCashEquivalentsAtCarryingValue` | found: `CashAndCashEquivalentsAtCarryingValue` |
| long-term debt | found: `LongTermDebtNoncurrent` | found: `LongTermDebtNoncurrent` | found: `LongTermDebtNoncurrent` |
| shares outstanding | found: `CommonStockSharesOutstanding` | found: `CommonStockSharesOutstanding` | found: `CommonStockSharesOutstanding` |

## GOOGL

| Metric | FY2023 | FY2024 | FY2025 |
|---|---|---|---|
| revenue | found: `Revenues` | found: `Revenues` | found: `Revenues` |
| net income | found: `NetIncomeLoss` | found: `NetIncomeLoss` | found: `NetIncomeLoss` |
| diluted EPS | found: `EarningsPerShareDiluted` | found: `EarningsPerShareDiluted` | found: `EarningsPerShareDiluted` |
| operating income | found: `OperatingIncomeLoss` | found: `OperatingIncomeLoss` | found: `OperatingIncomeLoss` |
| total assets | found: `Assets` | found: `Assets` | found: `Assets` |
| total liabilities | found: `Liabilities` | found: `Liabilities` | found: `Liabilities` |
| equity | found: `StockholdersEquity` | found: `StockholdersEquity` | found: `StockholdersEquity` |
| operating cash flow | found: `NetCashProvidedByUsedInOperatingActivities` | found: `NetCashProvidedByUsedInOperatingActivities` | found: `NetCashProvidedByUsedInOperatingActivities` |
| capex | found: `PaymentsToAcquirePropertyPlantAndEquipment` | found: `PaymentsToAcquirePropertyPlantAndEquipment` | found: `PaymentsToAcquirePropertyPlantAndEquipment` |
| cash | found: `CashAndCashEquivalentsAtCarryingValue` | found: `CashAndCashEquivalentsAtCarryingValue` | found: `CashAndCashEquivalentsAtCarryingValue` |
| long-term debt | found: `LongTermDebtNoncurrent` | found: `LongTermDebtNoncurrent` | found: `LongTermDebtNoncurrent` |
| shares outstanding | found: `CommonStockSharesOutstanding` | found: `CommonStockSharesOutstanding` | found: `CommonStockSharesOutstanding` |

## GS

| Metric | FY2023 | FY2024 | FY2025 |
|---|---|---|---|
| revenue | found: `RevenuesNetOfInterestExpense` | found: `RevenuesNetOfInterestExpense` | found: `RevenuesNetOfInterestExpense` |
| net income | found: `NetIncomeLoss` | found: `NetIncomeLoss` | found: `NetIncomeLoss` |
| diluted EPS | found: `EarningsPerShareDiluted` | found: `EarningsPerShareDiluted` | found: `EarningsPerShareDiluted` |
| operating income | missing | missing | missing |
| total assets | found: `Assets` | found: `Assets` | found: `Assets` |
| total liabilities | found: `Liabilities` | found: `Liabilities` | found: `Liabilities` |
| equity | found: `StockholdersEquity` | found: `StockholdersEquity` | found: `StockholdersEquity` |
| operating cash flow | found: `NetCashProvidedByUsedInOperatingActivities` | found: `NetCashProvidedByUsedInOperatingActivities` | found: `NetCashProvidedByUsedInOperatingActivities` |
| capex | found: `PaymentsToAcquirePropertyPlantAndEquipment` | found: `PaymentsToAcquirePropertyPlantAndEquipment` | found: `PaymentsToAcquirePropertyPlantAndEquipment` |
| cash | found: `CashAndCashEquivalentsAtCarryingValue` | found: `CashAndCashEquivalentsAtCarryingValue` | found: `CashAndCashEquivalentsAtCarryingValue` |
| long-term debt | missing | missing | missing |
| shares outstanding | found: `CommonStockSharesOutstanding` | found: `CommonStockSharesOutstanding` | found: `CommonStockSharesOutstanding` |

## IBM

| Metric | FY2023 | FY2024 | FY2025 |
|---|---|---|---|
| revenue | found: `Revenues` | found: `Revenues` | found: `Revenues` |
| net income | found: `NetIncomeLoss` | found: `NetIncomeLoss` | found: `NetIncomeLoss` |
| diluted EPS | found: `EarningsPerShareDiluted` | found: `EarningsPerShareDiluted` | found: `EarningsPerShareDiluted` |
| operating income | missing | missing | missing |
| total assets | found: `Assets` | found: `Assets` | found: `Assets` |
| total liabilities | found: `Liabilities` | found: `Liabilities` | found: `Liabilities` |
| equity | found: `StockholdersEquity` | found: `StockholdersEquity` | found: `StockholdersEquity` |
| operating cash flow | found: `NetCashProvidedByUsedInOperatingActivities` | found: `NetCashProvidedByUsedInOperatingActivities` | found: `NetCashProvidedByUsedInOperatingActivities` |
| capex | found: `PaymentsToAcquirePropertyPlantAndEquipment` | found: `PaymentsToAcquirePropertyPlantAndEquipment` | found: `PaymentsToAcquirePropertyPlantAndEquipment` |
| cash | found: `CashAndCashEquivalentsAtCarryingValue` | found: `CashAndCashEquivalentsAtCarryingValue` | found: `CashAndCashEquivalentsAtCarryingValue` |
| long-term debt | found: `LongTermDebtNoncurrent` | found: `LongTermDebtNoncurrent` | found: `LongTermDebtNoncurrent` |
| shares outstanding | found: `CommonStockSharesOutstanding` | found: `CommonStockSharesOutstanding` | found: `CommonStockSharesOutstanding` |

## JNJ

| Metric | FY2023 | FY2024 | FY2025 |
|---|---|---|---|
| revenue | found: `RevenueFromContractWithCustomerExcludingAssessedTax` | found: `RevenueFromContractWithCustomerExcludingAssessedTax` | found: `RevenueFromContractWithCustomerExcludingAssessedTax` |
| net income | found: `NetIncomeLoss` | found: `NetIncomeLoss` | found: `NetIncomeLoss` |
| diluted EPS | found: `EarningsPerShareDiluted` | found: `EarningsPerShareDiluted` | found: `EarningsPerShareDiluted` |
| operating income | missing | missing | missing |
| total assets | found: `Assets` | found: `Assets` | found: `Assets` |
| total liabilities | found: `Liabilities` | found: `Liabilities` | found: `Liabilities` |
| equity | found: `StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest` | found: `StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest` | found: `StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest` |
| operating cash flow | found: `NetCashProvidedByUsedInOperatingActivities` | found: `NetCashProvidedByUsedInOperatingActivities` | found: `NetCashProvidedByUsedInOperatingActivities` |
| capex | found: `PaymentsToAcquirePropertyPlantAndEquipment` | found: `PaymentsToAcquirePropertyPlantAndEquipment` | found: `PaymentsToAcquirePropertyPlantAndEquipment` |
| cash | found: `CashAndCashEquivalentsAtCarryingValue` | found: `CashAndCashEquivalentsAtCarryingValue` | found: `CashAndCashEquivalentsAtCarryingValue` |
| long-term debt | found: `LongTermDebtNoncurrent` | found: `LongTermDebtNoncurrent` | found: `LongTermDebtNoncurrent` |
| shares outstanding | missing (dei:EntityCommonStockSharesOutstanding dated 2024-02-09 in this 10-K) | missing (dei:EntityCommonStockSharesOutstanding dated 2025-02-06 in this 10-K) | missing (dei:EntityCommonStockSharesOutstanding dated 2026-02-06 in this 10-K) |

## JPM

| Metric | FY2023 | FY2024 | FY2025 |
|---|---|---|---|
| revenue | found: `Revenues` | found: `Revenues` | found: `Revenues` |
| net income | found: `NetIncomeLoss` | found: `NetIncomeLoss` | found: `NetIncomeLoss` |
| diluted EPS | found: `EarningsPerShareDiluted` | found: `EarningsPerShareDiluted` | found: `EarningsPerShareDiluted` |
| operating income | missing | missing | missing |
| total assets | found: `Assets` | found: `Assets` | found: `Assets` |
| total liabilities | found: `Liabilities` | found: `Liabilities` | found: `Liabilities` |
| equity | found: `StockholdersEquity` | found: `StockholdersEquity` | found: `StockholdersEquity` |
| operating cash flow | found: `NetCashProvidedByUsedInOperatingActivities` | found: `NetCashProvidedByUsedInOperatingActivities` | found: `NetCashProvidedByUsedInOperatingActivities` |
| capex | missing | missing | missing |
| cash | found: `CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents` | found: `CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents` | found: `CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents` |
| long-term debt | missing | missing | missing |
| shares outstanding | found: `CommonStockSharesOutstanding` | found: `CommonStockSharesOutstanding` | found: `CommonStockSharesOutstanding` |

## KO

| Metric | FY2023 | FY2024 | FY2025 |
|---|---|---|---|
| revenue | found: `Revenues` | found: `Revenues` | found: `Revenues` |
| net income | found: `NetIncomeLoss` | found: `NetIncomeLoss` | found: `NetIncomeLoss` |
| diluted EPS | found: `EarningsPerShareDiluted` | found: `EarningsPerShareDiluted` | found: `EarningsPerShareDiluted` |
| operating income | found: `OperatingIncomeLoss` | found: `OperatingIncomeLoss` | found: `OperatingIncomeLoss` |
| total assets | found: `Assets` | found: `Assets` | found: `Assets` |
| total liabilities | missing | missing | missing |
| equity | found: `StockholdersEquity` | found: `StockholdersEquity` | found: `StockholdersEquity` |
| operating cash flow | found: `NetCashProvidedByUsedInOperatingActivities` | found: `NetCashProvidedByUsedInOperatingActivities` | found: `NetCashProvidedByUsedInOperatingActivities` |
| capex | found: `PaymentsToAcquirePropertyPlantAndEquipment` | found: `PaymentsToAcquirePropertyPlantAndEquipment` | found: `PaymentsToAcquirePropertyPlantAndEquipment` |
| cash | found: `CashAndCashEquivalentsAtCarryingValue` | found: `CashAndCashEquivalentsAtCarryingValue` | found: `CashAndCashEquivalentsAtCarryingValue` |
| long-term debt | found: `LongTermDebtNoncurrent` | missing | missing |
| shares outstanding | missing (dei:EntityCommonStockSharesOutstanding dated 2024-02-16 in this 10-K) | missing (dei:EntityCommonStockSharesOutstanding dated 2025-02-18 in this 10-K) | missing (dei:EntityCommonStockSharesOutstanding dated 2026-02-18 in this 10-K) |

## MA

| Metric | FY2023 | FY2024 | FY2025 |
|---|---|---|---|
| revenue | found: `Revenues` | found: `Revenues` | found: `Revenues` |
| net income | found: `ProfitLoss` | found: `ProfitLoss` | found: `ProfitLoss` |
| diluted EPS | found: `EarningsPerShareDiluted` | found: `EarningsPerShareDiluted` | found: `EarningsPerShareDiluted` |
| operating income | found: `OperatingIncomeLoss` | found: `OperatingIncomeLoss` | found: `OperatingIncomeLoss` |
| total assets | found: `Assets` | found: `Assets` | found: `Assets` |
| total liabilities | found: `Liabilities` | found: `Liabilities` | found: `Liabilities` |
| equity | found: `StockholdersEquity` | found: `StockholdersEquity` | found: `StockholdersEquity` |
| operating cash flow | found: `NetCashProvidedByUsedInOperatingActivities` | found: `NetCashProvidedByUsedInOperatingActivities` | found: `NetCashProvidedByUsedInOperatingActivities` |
| capex | found: `PaymentsToAcquirePropertyPlantAndEquipment` | found: `PaymentsToAcquirePropertyPlantAndEquipment` | found: `PaymentsToAcquirePropertyPlantAndEquipment` |
| cash | found: `CashAndCashEquivalentsAtCarryingValue` | found: `CashAndCashEquivalentsAtCarryingValue` | found: `CashAndCashEquivalentsAtCarryingValue` |
| long-term debt | found: `LongTermDebtNoncurrent` | found: `LongTermDebtNoncurrent` | found: `LongTermDebtNoncurrent` |
| shares outstanding | missing | missing | missing |

## MCO

| Metric | FY2023 | FY2024 | FY2025 |
|---|---|---|---|
| revenue | found: `RevenueFromContractWithCustomerExcludingAssessedTax` | found: `RevenueFromContractWithCustomerExcludingAssessedTax` | found: `RevenueFromContractWithCustomerExcludingAssessedTax` |
| net income | found: `NetIncomeLoss` | found: `NetIncomeLoss` | found: `NetIncomeLoss` |
| diluted EPS | found: `EarningsPerShareDiluted` | found: `EarningsPerShareDiluted` | found: `EarningsPerShareDiluted` |
| operating income | found: `OperatingIncomeLoss` | found: `OperatingIncomeLoss` | found: `OperatingIncomeLoss` |
| total assets | found: `Assets` | found: `Assets` | found: `Assets` |
| total liabilities | found: `Liabilities` | found: `Liabilities` | found: `Liabilities` |
| equity | found: `StockholdersEquity` | found: `StockholdersEquity` | found: `StockholdersEquity` |
| operating cash flow | found: `NetCashProvidedByUsedInOperatingActivities` | found: `NetCashProvidedByUsedInOperatingActivities` | found: `NetCashProvidedByUsedInOperatingActivities` |
| capex | found: `PaymentsToAcquirePropertyPlantAndEquipment` | found: `PaymentsToAcquirePropertyPlantAndEquipment` | found: `PaymentsToAcquirePropertyPlantAndEquipment` |
| cash | found: `CashAndCashEquivalentsAtCarryingValue` | found: `CashAndCashEquivalentsAtCarryingValue` | found: `CashAndCashEquivalentsAtCarryingValue` |
| long-term debt | found: `LongTermDebtNoncurrent` | found: `LongTermDebtNoncurrent` | found: `LongTermDebtNoncurrent` |
| shares outstanding | missing (dei:EntityCommonStockSharesOutstanding dated 2024-01-31 in this 10-K) | missing (dei:EntityCommonStockSharesOutstanding dated 2025-01-31 in this 10-K) | missing (dei:EntityCommonStockSharesOutstanding dated 2026-01-31 in this 10-K) |

## META

| Metric | FY2023 | FY2024 | FY2025 |
|---|---|---|---|
| revenue | found: `RevenueFromContractWithCustomerExcludingAssessedTax` | found: `RevenueFromContractWithCustomerExcludingAssessedTax` | found: `RevenueFromContractWithCustomerExcludingAssessedTax` |
| net income | found: `NetIncomeLoss` | found: `NetIncomeLoss` | found: `NetIncomeLoss` |
| diluted EPS | found: `EarningsPerShareDiluted` | found: `EarningsPerShareDiluted` | found: `EarningsPerShareDiluted` |
| operating income | found: `OperatingIncomeLoss` | found: `OperatingIncomeLoss` | found: `OperatingIncomeLoss` |
| total assets | found: `Assets` | found: `Assets` | found: `Assets` |
| total liabilities | found: `Liabilities` | found: `Liabilities` | found: `Liabilities` |
| equity | found: `StockholdersEquity` | found: `StockholdersEquity` | found: `StockholdersEquity` |
| operating cash flow | found: `NetCashProvidedByUsedInOperatingActivities` | found: `NetCashProvidedByUsedInOperatingActivities` | found: `NetCashProvidedByUsedInOperatingActivities` |
| capex | found: `PaymentsToAcquirePropertyPlantAndEquipment` | found: `PaymentsToAcquirePropertyPlantAndEquipment` | found: `PaymentsToAcquirePropertyPlantAndEquipment` |
| cash | found: `CashAndCashEquivalentsAtCarryingValue` | found: `CashAndCashEquivalentsAtCarryingValue` | found: `CashAndCashEquivalentsAtCarryingValue` |
| long-term debt | found: `LongTermDebtNoncurrent` | found: `LongTermDebtNoncurrent` | found: `LongTermDebtNoncurrent` |
| shares outstanding | missing | missing | missing |

## MS

| Metric | FY2023 | FY2024 | FY2025 |
|---|---|---|---|
| revenue | found: `RevenuesNetOfInterestExpense` | found: `RevenuesNetOfInterestExpense` | found: `RevenuesNetOfInterestExpense` |
| net income | found: `NetIncomeLoss` | found: `NetIncomeLoss` | found: `NetIncomeLoss` |
| diluted EPS | found: `EarningsPerShareDiluted` | found: `EarningsPerShareDiluted` | found: `EarningsPerShareDiluted` |
| operating income | missing | missing | missing |
| total assets | found: `Assets` | found: `Assets` | found: `Assets` |
| total liabilities | found: `Liabilities` | found: `Liabilities` | found: `Liabilities` |
| equity | found: `StockholdersEquity` | found: `StockholdersEquity` | found: `StockholdersEquity` |
| operating cash flow | found: `NetCashProvidedByUsedInOperatingActivities` | found: `NetCashProvidedByUsedInOperatingActivities` | found: `NetCashProvidedByUsedInOperatingActivities` |
| capex | missing | missing | missing |
| cash | found: `CashAndCashEquivalentsAtCarryingValue` | found: `CashAndCashEquivalentsAtCarryingValue` | found: `CashAndCashEquivalentsAtCarryingValue` |
| long-term debt | found: `LongTermDebt` | found: `LongTermDebt` | found: `LongTermDebt` |
| shares outstanding | found: `CommonStockSharesOutstanding` | found: `CommonStockSharesOutstanding` | found: `CommonStockSharesOutstanding` |

## MSFT

| Metric | FY2024 | FY2025 | FY2026 |
|---|---|---|---|
| revenue | found: `RevenueFromContractWithCustomerExcludingAssessedTax` | found: `RevenueFromContractWithCustomerExcludingAssessedTax` | found: `RevenueFromContractWithCustomerExcludingAssessedTax` |
| net income | found: `NetIncomeLoss` | found: `NetIncomeLoss` | found: `NetIncomeLoss` |
| diluted EPS | found: `EarningsPerShareDiluted` | found: `EarningsPerShareDiluted` | found: `EarningsPerShareDiluted` |
| operating income | found: `OperatingIncomeLoss` | found: `OperatingIncomeLoss` | found: `OperatingIncomeLoss` |
| total assets | found: `Assets` | found: `Assets` | found: `Assets` |
| total liabilities | found: `Liabilities` | found: `Liabilities` | found: `Liabilities` |
| equity | found: `StockholdersEquity` | found: `StockholdersEquity` | found: `StockholdersEquity` |
| operating cash flow | found: `NetCashProvidedByUsedInOperatingActivities` | found: `NetCashProvidedByUsedInOperatingActivities` | found: `NetCashProvidedByUsedInOperatingActivities` |
| capex | found: `PaymentsToAcquirePropertyPlantAndEquipment` | found: `PaymentsToAcquirePropertyPlantAndEquipment` | found: `PaymentsToAcquirePropertyPlantAndEquipment` |
| cash | found: `CashAndCashEquivalentsAtCarryingValue` | found: `CashAndCashEquivalentsAtCarryingValue` | found: `CashAndCashEquivalentsAtCarryingValue` |
| long-term debt | found: `LongTermDebtNoncurrent` | found: `LongTermDebtNoncurrent` | found: `LongTermDebtNoncurrent` |
| shares outstanding | found: `CommonStockSharesOutstanding` | found: `CommonStockSharesOutstanding` | found: `CommonStockSharesOutstanding` |

## NFLX

| Metric | FY2023 | FY2024 | FY2025 |
|---|---|---|---|
| revenue | found: `Revenues` | found: `Revenues` | found: `Revenues` |
| net income | found: `NetIncomeLoss` | found: `NetIncomeLoss` | found: `NetIncomeLoss` |
| diluted EPS | found: `EarningsPerShareDiluted` | found: `EarningsPerShareDiluted` | found: `EarningsPerShareDiluted` |
| operating income | found: `OperatingIncomeLoss` | found: `OperatingIncomeLoss` | found: `OperatingIncomeLoss` |
| total assets | found: `Assets` | found: `Assets` | found: `Assets` |
| total liabilities | found: `Liabilities` | found: `Liabilities` | found: `Liabilities` |
| equity | found: `StockholdersEquity` | found: `StockholdersEquity` | found: `StockholdersEquity` |
| operating cash flow | found: `NetCashProvidedByUsedInOperatingActivities` | found: `NetCashProvidedByUsedInOperatingActivities` | found: `NetCashProvidedByUsedInOperatingActivities` |
| capex | found: `PaymentsToAcquirePropertyPlantAndEquipment` | found: `PaymentsToAcquirePropertyPlantAndEquipment` | found: `PaymentsToAcquirePropertyPlantAndEquipment` |
| cash | found: `CashAndCashEquivalentsAtCarryingValue` | found: `CashAndCashEquivalentsAtCarryingValue` | found: `CashAndCashEquivalentsAtCarryingValue` |
| long-term debt | found: `LongTermDebtNoncurrent` | found: `LongTermDebtNoncurrent` | found: `LongTermDebtNoncurrent` |
| shares outstanding | found: `dei:EntityCommonStockSharesOutstanding` | found: `dei:EntityCommonStockSharesOutstanding` | found: `dei:EntityCommonStockSharesOutstanding` |

## NKE

| Metric | FY2024 | FY2025 | FY2026 |
|---|---|---|---|
| revenue | found: `RevenueFromContractWithCustomerExcludingAssessedTax` | found: `RevenueFromContractWithCustomerExcludingAssessedTax` | found: `RevenueFromContractWithCustomerExcludingAssessedTax` |
| net income | found: `NetIncomeLoss` | found: `NetIncomeLoss` | found: `NetIncomeLoss` |
| diluted EPS | found: `EarningsPerShareDiluted` | found: `EarningsPerShareDiluted` | found: `EarningsPerShareDiluted` |
| operating income | missing | missing | missing |
| total assets | found: `Assets` | found: `Assets` | found: `Assets` |
| total liabilities | missing | missing | missing |
| equity | found: `StockholdersEquity` | found: `StockholdersEquity` | found: `StockholdersEquity` |
| operating cash flow | found: `NetCashProvidedByUsedInOperatingActivities` | found: `NetCashProvidedByUsedInOperatingActivities` | found: `NetCashProvidedByUsedInOperatingActivities` |
| capex | found: `PaymentsToAcquirePropertyPlantAndEquipment` | found: `PaymentsToAcquirePropertyPlantAndEquipment` | found: `PaymentsToAcquirePropertyPlantAndEquipment` |
| cash | found: `CashAndCashEquivalentsAtCarryingValue` | found: `CashAndCashEquivalentsAtCarryingValue` | found: `CashAndCashEquivalentsAtCarryingValue` |
| long-term debt | found: `LongTermDebtNoncurrent` | found: `LongTermDebtNoncurrent` | found: `LongTermDebtNoncurrent` |
| shares outstanding | missing | missing | missing |

## NVDA

| Metric | FY2024 | FY2025 | FY2026 |
|---|---|---|---|
| revenue | found: `Revenues` | found: `Revenues` | found: `Revenues` |
| net income | found: `NetIncomeLoss` | found: `NetIncomeLoss` | found: `NetIncomeLoss` |
| diluted EPS | found: `EarningsPerShareDiluted` | found: `EarningsPerShareDiluted` | found: `EarningsPerShareDiluted` |
| operating income | found: `OperatingIncomeLoss` | found: `OperatingIncomeLoss` | found: `OperatingIncomeLoss` |
| total assets | found: `Assets` | found: `Assets` | found: `Assets` |
| total liabilities | found: `Liabilities` | found: `Liabilities` | found: `Liabilities` |
| equity | found: `StockholdersEquity` | found: `StockholdersEquity` | found: `StockholdersEquity` |
| operating cash flow | found: `NetCashProvidedByUsedInOperatingActivities` | found: `NetCashProvidedByUsedInOperatingActivities` | found: `NetCashProvidedByUsedInOperatingActivities` |
| capex | missing | missing | missing |
| cash | found: `CashAndCashEquivalentsAtCarryingValue` | found: `CashAndCashEquivalentsAtCarryingValue` | found: `CashAndCashEquivalentsAtCarryingValue` |
| long-term debt | found: `LongTermDebtNoncurrent` | found: `LongTermDebtNoncurrent` | found: `LongTermDebtNoncurrent` |
| shares outstanding | found: `CommonStockSharesOutstanding` | found: `CommonStockSharesOutstanding` | found: `CommonStockSharesOutstanding` |

## PFE

| Metric | FY2023 | FY2024 | FY2025 |
|---|---|---|---|
| revenue | found: `Revenues` | found: `Revenues` | found: `Revenues` |
| net income | found: `NetIncomeLoss` | found: `NetIncomeLoss` | found: `NetIncomeLoss` |
| diluted EPS | found: `EarningsPerShareDiluted` | found: `EarningsPerShareDiluted` | found: `EarningsPerShareDiluted` |
| operating income | missing | missing | missing |
| total assets | found: `Assets` | found: `Assets` | found: `Assets` |
| total liabilities | found: `Liabilities` | found: `Liabilities` | found: `Liabilities` |
| equity | found: `StockholdersEquity` | found: `StockholdersEquity` | found: `StockholdersEquity` |
| operating cash flow | found: `NetCashProvidedByUsedInOperatingActivities` | found: `NetCashProvidedByUsedInOperatingActivities` | found: `NetCashProvidedByUsedInOperatingActivities` |
| capex | found: `PaymentsToAcquirePropertyPlantAndEquipment` | found: `PaymentsToAcquirePropertyPlantAndEquipment` | found: `PaymentsToAcquirePropertyPlantAndEquipment` |
| cash | found: `CashAndCashEquivalentsAtCarryingValue` | found: `CashAndCashEquivalentsAtCarryingValue` | found: `CashAndCashEquivalentsAtCarryingValue` |
| long-term debt | found: `LongTermDebtNoncurrent` | found: `LongTermDebtNoncurrent` | found: `LongTermDebtNoncurrent` |
| shares outstanding | missing (dei:EntityCommonStockSharesOutstanding dated 2024-02-15 in this 10-K) | missing (dei:EntityCommonStockSharesOutstanding dated 2025-02-20 in this 10-K) | missing (dei:EntityCommonStockSharesOutstanding dated 2026-02-19 in this 10-K) |

## SPGI

| Metric | FY2023 | FY2024 | FY2025 |
|---|---|---|---|
| revenue | found: `RevenueFromContractWithCustomerExcludingAssessedTax` | found: `RevenueFromContractWithCustomerExcludingAssessedTax` | found: `RevenueFromContractWithCustomerExcludingAssessedTax` |
| net income | found: `NetIncomeLoss` | found: `NetIncomeLoss` | found: `NetIncomeLoss` |
| diluted EPS | found: `EarningsPerShareDiluted` | found: `EarningsPerShareDiluted` | found: `EarningsPerShareDiluted` |
| operating income | found: `OperatingIncomeLoss` | found: `OperatingIncomeLoss` | found: `OperatingIncomeLoss` |
| total assets | found: `Assets` | found: `Assets` | found: `Assets` |
| total liabilities | found: `Liabilities` | found: `Liabilities` | found: `Liabilities` |
| equity | found: `StockholdersEquity` | found: `StockholdersEquity` | found: `StockholdersEquity` |
| operating cash flow | found: `NetCashProvidedByUsedInOperatingActivities` | found: `NetCashProvidedByUsedInOperatingActivities` | found: `NetCashProvidedByUsedInOperatingActivities` |
| capex | missing | missing | missing |
| cash | found: `CashAndCashEquivalentsAtCarryingValue` | found: `CashAndCashEquivalentsAtCarryingValue` | found: `CashAndCashEquivalentsAtCarryingValue` |
| long-term debt | found: `LongTermDebtNoncurrent` | found: `LongTermDebtNoncurrent` | found: `LongTermDebtNoncurrent` |
| shares outstanding | found: `CommonStockSharesOutstanding` | found: `CommonStockSharesOutstanding` | found: `CommonStockSharesOutstanding` |

## UNH

| Metric | FY2023 | FY2024 | FY2025 |
|---|---|---|---|
| revenue | found: `Revenues` | found: `Revenues` | found: `Revenues` |
| net income | found: `NetIncomeLoss` | found: `NetIncomeLoss` | found: `NetIncomeLoss` |
| diluted EPS | found: `EarningsPerShareDiluted` | found: `EarningsPerShareDiluted` | found: `EarningsPerShareDiluted` |
| operating income | found: `OperatingIncomeLoss` | found: `OperatingIncomeLoss` | found: `OperatingIncomeLoss` |
| total assets | found: `Assets` | found: `Assets` | found: `Assets` |
| total liabilities | found: `Liabilities` | found: `Liabilities` | found: `Liabilities` |
| equity | found: `StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest` | found: `StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest` | found: `StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest` |
| operating cash flow | found: `NetCashProvidedByUsedInOperatingActivities` | found: `NetCashProvidedByUsedInOperatingActivities` | found: `NetCashProvidedByUsedInOperatingActivities` |
| capex | found: `PaymentsToAcquirePropertyPlantAndEquipment` | found: `PaymentsToAcquirePropertyPlantAndEquipment` | found: `PaymentsToAcquirePropertyPlantAndEquipment` |
| cash | found: `CashAndCashEquivalentsAtCarryingValue` | found: `CashAndCashEquivalentsAtCarryingValue` | found: `CashAndCashEquivalentsAtCarryingValue` |
| long-term debt | found: `LongTermDebtNoncurrent` | found: `LongTermDebtNoncurrent` | found: `LongTermDebtNoncurrent` |
| shares outstanding | found: `CommonStockSharesOutstanding` | found: `CommonStockSharesOutstanding` | found: `CommonStockSharesOutstanding` |

## VZ

| Metric | FY2023 | FY2024 | FY2025 |
|---|---|---|---|
| revenue | found: `Revenues` | found: `Revenues` | found: `Revenues` |
| net income | found: `NetIncomeLoss` | found: `NetIncomeLoss` | found: `NetIncomeLoss` |
| diluted EPS | found: `EarningsPerShareDiluted` | found: `EarningsPerShareDiluted` | found: `EarningsPerShareDiluted` |
| operating income | found: `OperatingIncomeLoss` | found: `OperatingIncomeLoss` | found: `OperatingIncomeLoss` |
| total assets | found: `Assets` | found: `Assets` | found: `Assets` |
| total liabilities | missing | missing | missing |
| equity | found: `StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest` | found: `StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest` | found: `StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest` |
| operating cash flow | found: `NetCashProvidedByUsedInOperatingActivities` | found: `NetCashProvidedByUsedInOperatingActivities` | found: `NetCashProvidedByUsedInOperatingActivities` |
| capex | missing | missing | missing |
| cash | found: `CashAndCashEquivalentsAtCarryingValue` | found: `CashAndCashEquivalentsAtCarryingValue` | found: `CashAndCashEquivalentsAtCarryingValue` |
| long-term debt | missing | missing | missing |
| shares outstanding | missing (dei:EntityCommonStockSharesOutstanding dated 2024-01-31 in this 10-K) | missing (dei:EntityCommonStockSharesOutstanding dated 2025-01-31 in this 10-K) | missing (dei:EntityCommonStockSharesOutstanding dated 2026-01-30 in this 10-K) |

## WMT

| Metric | FY2024 | FY2025 | FY2026 |
|---|---|---|---|
| revenue | found: `Revenues` | found: `Revenues` | found: `Revenues` |
| net income | found: `NetIncomeLoss` | found: `NetIncomeLoss` | found: `NetIncomeLoss` |
| diluted EPS | found: `EarningsPerShareDiluted` | found: `EarningsPerShareDiluted` | found: `EarningsPerShareDiluted` |
| operating income | found: `OperatingIncomeLoss` | found: `OperatingIncomeLoss` | found: `OperatingIncomeLoss` |
| total assets | found: `Assets` | found: `Assets` | found: `Assets` |
| total liabilities | missing | missing | missing |
| equity | found: `StockholdersEquity` | found: `StockholdersEquity` | found: `StockholdersEquity` |
| operating cash flow | found: `NetCashProvidedByUsedInOperatingActivities` | found: `NetCashProvidedByUsedInOperatingActivities` | found: `NetCashProvidedByUsedInOperatingActivities` |
| capex | found: `PaymentsToAcquirePropertyPlantAndEquipment` | found: `PaymentsToAcquirePropertyPlantAndEquipment` | found: `PaymentsToAcquirePropertyPlantAndEquipment` |
| cash | found: `CashAndCashEquivalentsAtCarryingValue` | found: `CashAndCashEquivalentsAtCarryingValue` | found: `CashAndCashEquivalentsAtCarryingValue` |
| long-term debt | found: `LongTermDebtNoncurrent` | found: `LongTermDebtNoncurrent` | found: `LongTermDebtNoncurrent` |
| shares outstanding | missing (dei:EntityCommonStockSharesOutstanding dated 2024-03-13 in this 10-K) | missing (dei:EntityCommonStockSharesOutstanding dated 2025-03-12 in this 10-K) | missing (dei:EntityCommonStockSharesOutstanding dated 2026-03-11 in this 10-K) |
