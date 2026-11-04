# XBRL facts coverage

For each company and pinned fiscal year, what the lookup returns for each metric from the filing's own XBRL facts: the tag it used, or "unavailable" when the filing reports the metric under none of the candidate tags. Only company totals (facts with no dimensions) count; amounts over a period must end on the filing's period of report and cover a whole fiscal year (350 to 380 days), and balances must fall on that date. The cover-page share count is the one exception: it is dated a few weeks after the year ends and is used only when the filing has no count dated at year end. Nothing is derived. Written by `make verify-facts`; do not edit by hand.

## Totals

| Metric | Found | Tags used |
|---|---:|---|
| revenue | 75 of 75 | `Revenues` 36, `RevenueFromContractWithCustomerExcludingAssessedTax` 27, `RevenuesNetOfInterestExpense` 12 |
| net_income | 75 of 75 | `NetIncomeLoss` 72, `ProfitLoss` 3 |
| diluted_eps | 75 of 75 | `EarningsPerShareDiluted` 75 |
| operating_income | 45 of 75 | `OperatingIncomeLoss` 45 |
| pretax_income | 75 of 75 | `IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest` 71, `IncomeLossFromContinuingOperationsBeforeIncomeTaxesMinorityInterestAndIncomeLossFromEquityMethodInvestments` 4 |
| total_assets | 75 of 75 | `Assets` 75 |
| total_liabilities | 60 of 75 | `Liabilities` 60 |
| stockholders_equity | 75 of 75 | `StockholdersEquity` 66, `StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest` 9 |
| operating_cash_flow | 75 of 75 | `NetCashProvidedByUsedInOperatingActivities` 75 |
| capital_expenditures | 57 of 75 | `PaymentsToAcquirePropertyPlantAndEquipment` 57 |
| cash_and_equivalents | 75 of 75 | `CashAndCashEquivalentsAtCarryingValue` 63, `CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents` 12 |
| long_term_debt | 61 of 75 | `LongTermDebtNoncurrent` 51, `LongTermDebt` 10 |
| shares_outstanding | 66 of 75 | `CommonStockSharesOutstanding` 45, `dei:EntityCommonStockSharesOutstanding` 21 |

Candidate tags, in the order they are tried:

- revenue: `Revenues`, `RevenueFromContractWithCustomerExcludingAssessedTax`, `RevenuesNetOfInterestExpense`, `SalesRevenueNet`
- net_income: `NetIncomeLoss`, `ProfitLoss`
- diluted_eps: `EarningsPerShareDiluted`
- operating_income: `OperatingIncomeLoss`
- pretax_income: `IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest`, `IncomeLossFromContinuingOperationsBeforeIncomeTaxesMinorityInterestAndIncomeLossFromEquityMethodInvestments`
- total_assets: `Assets`
- total_liabilities: `Liabilities`
- stockholders_equity: `StockholdersEquity`, `StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest`
- operating_cash_flow: `NetCashProvidedByUsedInOperatingActivities`
- capital_expenditures: `PaymentsToAcquirePropertyPlantAndEquipment`
- cash_and_equivalents: `CashAndCashEquivalentsAtCarryingValue`, `CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents`
- long_term_debt: `LongTermDebtNoncurrent`, `LongTermDebt`
- shares_outstanding: `CommonStockSharesOutstanding`, `dei:EntityCommonStockSharesOutstanding`
- revenue, for companies with `revenue_rule: bank`: `RevenuesNetOfInterestExpense`, `Revenues`

## Unavailable

- operating_income (30): AXP FY2023, AXP FY2024, AXP FY2025, C FY2023, C FY2024, C FY2025, COF FY2023, COF FY2024, COF FY2025, GS FY2023, GS FY2024, GS FY2025, IBM FY2023, IBM FY2024, IBM FY2025, JNJ FY2023, JNJ FY2024, JNJ FY2025, JPM FY2023, JPM FY2024, JPM FY2025, MS FY2023, MS FY2024, MS FY2025, NKE FY2024, NKE FY2025, NKE FY2026, PFE FY2023, PFE FY2024, PFE FY2025
- total_liabilities (15): AMZN FY2023, AMZN FY2024, AMZN FY2025, KO FY2023, KO FY2024, KO FY2025, NKE FY2024, NKE FY2025, NKE FY2026, VZ FY2023, VZ FY2024, VZ FY2025, WMT FY2024, WMT FY2025, WMT FY2026
- capital_expenditures (18): AMZN FY2023, AMZN FY2024, AMZN FY2025, JPM FY2023, JPM FY2024, JPM FY2025, MS FY2023, MS FY2024, MS FY2025, NVDA FY2024, NVDA FY2025, NVDA FY2026, SPGI FY2023, SPGI FY2024, SPGI FY2025, VZ FY2023, VZ FY2024, VZ FY2025
- long_term_debt (14): COF FY2023, COF FY2024, COF FY2025, GS FY2023, GS FY2024, GS FY2025, JPM FY2023, JPM FY2024, JPM FY2025, KO FY2024, KO FY2025, VZ FY2023, VZ FY2024, VZ FY2025
- shares_outstanding (9): MA FY2023, MA FY2024, MA FY2025, META FY2023, META FY2024, META FY2025, NKE FY2024, NKE FY2025, NKE FY2026

## AAPL

| Metric | FY2024 | FY2025 | FY2026 |
|---|---|---|---|
| revenue | found: `RevenueFromContractWithCustomerExcludingAssessedTax` | found: `RevenueFromContractWithCustomerExcludingAssessedTax` | found: `RevenueFromContractWithCustomerExcludingAssessedTax` |
| net_income | found: `NetIncomeLoss` | found: `NetIncomeLoss` | found: `NetIncomeLoss` |
| diluted_eps | found: `EarningsPerShareDiluted` | found: `EarningsPerShareDiluted` | found: `EarningsPerShareDiluted` |
| operating_income | found: `OperatingIncomeLoss` | found: `OperatingIncomeLoss` | found: `OperatingIncomeLoss` |
| pretax_income | found: `IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest` | found: `IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest` | found: `IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest` |
| total_assets | found: `Assets` | found: `Assets` | found: `Assets` |
| total_liabilities | found: `Liabilities` | found: `Liabilities` | found: `Liabilities` |
| stockholders_equity | found: `StockholdersEquity` | found: `StockholdersEquity` | found: `StockholdersEquity` |
| operating_cash_flow | found: `NetCashProvidedByUsedInOperatingActivities` | found: `NetCashProvidedByUsedInOperatingActivities` | found: `NetCashProvidedByUsedInOperatingActivities` |
| capital_expenditures | found: `PaymentsToAcquirePropertyPlantAndEquipment` | found: `PaymentsToAcquirePropertyPlantAndEquipment` | found: `PaymentsToAcquirePropertyPlantAndEquipment` |
| cash_and_equivalents | found: `CashAndCashEquivalentsAtCarryingValue` | found: `CashAndCashEquivalentsAtCarryingValue` | found: `CashAndCashEquivalentsAtCarryingValue` |
| long_term_debt | found: `LongTermDebtNoncurrent` | found: `LongTermDebtNoncurrent` | found: `LongTermDebtNoncurrent` |
| shares_outstanding | found: `CommonStockSharesOutstanding` | found: `CommonStockSharesOutstanding` | found: `CommonStockSharesOutstanding` |

## AMZN

| Metric | FY2023 | FY2024 | FY2025 |
|---|---|---|---|
| revenue | found: `RevenueFromContractWithCustomerExcludingAssessedTax` | found: `RevenueFromContractWithCustomerExcludingAssessedTax` | found: `RevenueFromContractWithCustomerExcludingAssessedTax` |
| net_income | found: `NetIncomeLoss` | found: `NetIncomeLoss` | found: `NetIncomeLoss` |
| diluted_eps | found: `EarningsPerShareDiluted` | found: `EarningsPerShareDiluted` | found: `EarningsPerShareDiluted` |
| operating_income | found: `OperatingIncomeLoss` | found: `OperatingIncomeLoss` | found: `OperatingIncomeLoss` |
| pretax_income | found: `IncomeLossFromContinuingOperationsBeforeIncomeTaxesMinorityInterestAndIncomeLossFromEquityMethodInvestments` | found: `IncomeLossFromContinuingOperationsBeforeIncomeTaxesMinorityInterestAndIncomeLossFromEquityMethodInvestments` | found: `IncomeLossFromContinuingOperationsBeforeIncomeTaxesMinorityInterestAndIncomeLossFromEquityMethodInvestments` |
| total_assets | found: `Assets` | found: `Assets` | found: `Assets` |
| total_liabilities | unavailable | unavailable | unavailable |
| stockholders_equity | found: `StockholdersEquity` | found: `StockholdersEquity` | found: `StockholdersEquity` |
| operating_cash_flow | found: `NetCashProvidedByUsedInOperatingActivities` | found: `NetCashProvidedByUsedInOperatingActivities` | found: `NetCashProvidedByUsedInOperatingActivities` |
| capital_expenditures | unavailable | unavailable | unavailable |
| cash_and_equivalents | found: `CashAndCashEquivalentsAtCarryingValue` | found: `CashAndCashEquivalentsAtCarryingValue` | found: `CashAndCashEquivalentsAtCarryingValue` |
| long_term_debt | found: `LongTermDebtNoncurrent` | found: `LongTermDebtNoncurrent` | found: `LongTermDebtNoncurrent` |
| shares_outstanding | found: `CommonStockSharesOutstanding` | found: `CommonStockSharesOutstanding` | found: `CommonStockSharesOutstanding` |

## AXP

| Metric | FY2023 | FY2024 | FY2025 |
|---|---|---|---|
| revenue | found: `RevenuesNetOfInterestExpense` | found: `RevenuesNetOfInterestExpense` | found: `RevenuesNetOfInterestExpense` |
| net_income | found: `NetIncomeLoss` | found: `NetIncomeLoss` | found: `NetIncomeLoss` |
| diluted_eps | found: `EarningsPerShareDiluted` | found: `EarningsPerShareDiluted` | found: `EarningsPerShareDiluted` |
| operating_income | unavailable | unavailable | unavailable |
| pretax_income | found: `IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest` | found: `IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest` | found: `IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest` |
| total_assets | found: `Assets` | found: `Assets` | found: `Assets` |
| total_liabilities | found: `Liabilities` | found: `Liabilities` | found: `Liabilities` |
| stockholders_equity | found: `StockholdersEquity` | found: `StockholdersEquity` | found: `StockholdersEquity` |
| operating_cash_flow | found: `NetCashProvidedByUsedInOperatingActivities` | found: `NetCashProvidedByUsedInOperatingActivities` | found: `NetCashProvidedByUsedInOperatingActivities` |
| capital_expenditures | found: `PaymentsToAcquirePropertyPlantAndEquipment` | found: `PaymentsToAcquirePropertyPlantAndEquipment` | found: `PaymentsToAcquirePropertyPlantAndEquipment` |
| cash_and_equivalents | found: `CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents` | found: `CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents` | found: `CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents` |
| long_term_debt | found: `LongTermDebt` | found: `LongTermDebt` | found: `LongTermDebt` |
| shares_outstanding | found: `CommonStockSharesOutstanding` | found: `CommonStockSharesOutstanding` | found: `CommonStockSharesOutstanding` |

## C

| Metric | FY2023 | FY2024 | FY2025 |
|---|---|---|---|
| revenue | found: `Revenues` | found: `Revenues` | found: `Revenues` |
| net_income | found: `NetIncomeLoss` | found: `NetIncomeLoss` | found: `NetIncomeLoss` |
| diluted_eps | found: `EarningsPerShareDiluted` | found: `EarningsPerShareDiluted` | found: `EarningsPerShareDiluted` |
| operating_income | unavailable | unavailable | unavailable |
| pretax_income | found: `IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest` | found: `IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest` | found: `IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest` |
| total_assets | found: `Assets` | found: `Assets` | found: `Assets` |
| total_liabilities | found: `Liabilities` | found: `Liabilities` | found: `Liabilities` |
| stockholders_equity | found: `StockholdersEquity` | found: `StockholdersEquity` | found: `StockholdersEquity` |
| operating_cash_flow | found: `NetCashProvidedByUsedInOperatingActivities` | found: `NetCashProvidedByUsedInOperatingActivities` | found: `NetCashProvidedByUsedInOperatingActivities` |
| capital_expenditures | found: `PaymentsToAcquirePropertyPlantAndEquipment` | found: `PaymentsToAcquirePropertyPlantAndEquipment` | found: `PaymentsToAcquirePropertyPlantAndEquipment` |
| cash_and_equivalents | found: `CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents` | found: `CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents` | found: `CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents` |
| long_term_debt | found: `LongTermDebt` | found: `LongTermDebt` | found: `LongTermDebt` |
| shares_outstanding | found: `dei:EntityCommonStockSharesOutstanding` (cover page, 2024-01-31) | found: `dei:EntityCommonStockSharesOutstanding` (cover page, 2025-01-31) | found: `dei:EntityCommonStockSharesOutstanding` (cover page, 2026-01-31) |

## COF

| Metric | FY2023 | FY2024 | FY2025 |
|---|---|---|---|
| revenue | found: `Revenues` | found: `Revenues` | found: `Revenues` |
| net_income | found: `NetIncomeLoss` | found: `NetIncomeLoss` | found: `NetIncomeLoss` |
| diluted_eps | found: `EarningsPerShareDiluted` | found: `EarningsPerShareDiluted` | found: `EarningsPerShareDiluted` |
| operating_income | unavailable | unavailable | unavailable |
| pretax_income | found: `IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest` | found: `IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest` | found: `IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest` |
| total_assets | found: `Assets` | found: `Assets` | found: `Assets` |
| total_liabilities | found: `Liabilities` | found: `Liabilities` | found: `Liabilities` |
| stockholders_equity | found: `StockholdersEquity` | found: `StockholdersEquity` | found: `StockholdersEquity` |
| operating_cash_flow | found: `NetCashProvidedByUsedInOperatingActivities` | found: `NetCashProvidedByUsedInOperatingActivities` | found: `NetCashProvidedByUsedInOperatingActivities` |
| capital_expenditures | found: `PaymentsToAcquirePropertyPlantAndEquipment` | found: `PaymentsToAcquirePropertyPlantAndEquipment` | found: `PaymentsToAcquirePropertyPlantAndEquipment` |
| cash_and_equivalents | found: `CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents` | found: `CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents` | found: `CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents` |
| long_term_debt | unavailable | unavailable | unavailable |
| shares_outstanding | found: `CommonStockSharesOutstanding` | found: `CommonStockSharesOutstanding` | found: `CommonStockSharesOutstanding` |

## COST

| Metric | FY2024 | FY2025 | FY2026 |
|---|---|---|---|
| revenue | found: `Revenues` | found: `Revenues` | found: `RevenueFromContractWithCustomerExcludingAssessedTax` |
| net_income | found: `NetIncomeLoss` | found: `NetIncomeLoss` | found: `NetIncomeLoss` |
| diluted_eps | found: `EarningsPerShareDiluted` | found: `EarningsPerShareDiluted` | found: `EarningsPerShareDiluted` |
| operating_income | found: `OperatingIncomeLoss` | found: `OperatingIncomeLoss` | found: `OperatingIncomeLoss` |
| pretax_income | found: `IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest` | found: `IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest` | found: `IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest` |
| total_assets | found: `Assets` | found: `Assets` | found: `Assets` |
| total_liabilities | found: `Liabilities` | found: `Liabilities` | found: `Liabilities` |
| stockholders_equity | found: `StockholdersEquity` | found: `StockholdersEquity` | found: `StockholdersEquity` |
| operating_cash_flow | found: `NetCashProvidedByUsedInOperatingActivities` | found: `NetCashProvidedByUsedInOperatingActivities` | found: `NetCashProvidedByUsedInOperatingActivities` |
| capital_expenditures | found: `PaymentsToAcquirePropertyPlantAndEquipment` | found: `PaymentsToAcquirePropertyPlantAndEquipment` | found: `PaymentsToAcquirePropertyPlantAndEquipment` |
| cash_and_equivalents | found: `CashAndCashEquivalentsAtCarryingValue` | found: `CashAndCashEquivalentsAtCarryingValue` | found: `CashAndCashEquivalentsAtCarryingValue` |
| long_term_debt | found: `LongTermDebtNoncurrent` | found: `LongTermDebtNoncurrent` | found: `LongTermDebtNoncurrent` |
| shares_outstanding | found: `CommonStockSharesOutstanding` | found: `CommonStockSharesOutstanding` | found: `CommonStockSharesOutstanding` |

## GOOGL

| Metric | FY2023 | FY2024 | FY2025 |
|---|---|---|---|
| revenue | found: `RevenueFromContractWithCustomerExcludingAssessedTax` | found: `RevenueFromContractWithCustomerExcludingAssessedTax` | found: `Revenues` |
| net_income | found: `NetIncomeLoss` | found: `NetIncomeLoss` | found: `NetIncomeLoss` |
| diluted_eps | found: `EarningsPerShareDiluted` | found: `EarningsPerShareDiluted` | found: `EarningsPerShareDiluted` |
| operating_income | found: `OperatingIncomeLoss` | found: `OperatingIncomeLoss` | found: `OperatingIncomeLoss` |
| pretax_income | found: `IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest` | found: `IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest` | found: `IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest` |
| total_assets | found: `Assets` | found: `Assets` | found: `Assets` |
| total_liabilities | found: `Liabilities` | found: `Liabilities` | found: `Liabilities` |
| stockholders_equity | found: `StockholdersEquity` | found: `StockholdersEquity` | found: `StockholdersEquity` |
| operating_cash_flow | found: `NetCashProvidedByUsedInOperatingActivities` | found: `NetCashProvidedByUsedInOperatingActivities` | found: `NetCashProvidedByUsedInOperatingActivities` |
| capital_expenditures | found: `PaymentsToAcquirePropertyPlantAndEquipment` | found: `PaymentsToAcquirePropertyPlantAndEquipment` | found: `PaymentsToAcquirePropertyPlantAndEquipment` |
| cash_and_equivalents | found: `CashAndCashEquivalentsAtCarryingValue` | found: `CashAndCashEquivalentsAtCarryingValue` | found: `CashAndCashEquivalentsAtCarryingValue` |
| long_term_debt | found: `LongTermDebt` | found: `LongTermDebtNoncurrent` | found: `LongTermDebtNoncurrent` |
| shares_outstanding | found: `CommonStockSharesOutstanding` | found: `CommonStockSharesOutstanding` | found: `CommonStockSharesOutstanding` |

## GS

| Metric | FY2023 | FY2024 | FY2025 |
|---|---|---|---|
| revenue | found: `RevenuesNetOfInterestExpense` | found: `RevenuesNetOfInterestExpense` | found: `RevenuesNetOfInterestExpense` |
| net_income | found: `NetIncomeLoss` | found: `NetIncomeLoss` | found: `NetIncomeLoss` |
| diluted_eps | found: `EarningsPerShareDiluted` | found: `EarningsPerShareDiluted` | found: `EarningsPerShareDiluted` |
| operating_income | unavailable | unavailable | unavailable |
| pretax_income | found: `IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest` | found: `IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest` | found: `IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest` |
| total_assets | found: `Assets` | found: `Assets` | found: `Assets` |
| total_liabilities | found: `Liabilities` | found: `Liabilities` | found: `Liabilities` |
| stockholders_equity | found: `StockholdersEquity` | found: `StockholdersEquity` | found: `StockholdersEquity` |
| operating_cash_flow | found: `NetCashProvidedByUsedInOperatingActivities` | found: `NetCashProvidedByUsedInOperatingActivities` | found: `NetCashProvidedByUsedInOperatingActivities` |
| capital_expenditures | found: `PaymentsToAcquirePropertyPlantAndEquipment` | found: `PaymentsToAcquirePropertyPlantAndEquipment` | found: `PaymentsToAcquirePropertyPlantAndEquipment` |
| cash_and_equivalents | found: `CashAndCashEquivalentsAtCarryingValue` | found: `CashAndCashEquivalentsAtCarryingValue` | found: `CashAndCashEquivalentsAtCarryingValue` |
| long_term_debt | unavailable | unavailable | unavailable |
| shares_outstanding | found: `CommonStockSharesOutstanding` | found: `CommonStockSharesOutstanding` | found: `CommonStockSharesOutstanding` |

## IBM

| Metric | FY2023 | FY2024 | FY2025 |
|---|---|---|---|
| revenue | found: `Revenues` | found: `Revenues` | found: `Revenues` |
| net_income | found: `NetIncomeLoss` | found: `NetIncomeLoss` | found: `NetIncomeLoss` |
| diluted_eps | found: `EarningsPerShareDiluted` | found: `EarningsPerShareDiluted` | found: `EarningsPerShareDiluted` |
| operating_income | unavailable | unavailable | unavailable |
| pretax_income | found: `IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest` | found: `IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest` | found: `IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest` |
| total_assets | found: `Assets` | found: `Assets` | found: `Assets` |
| total_liabilities | found: `Liabilities` | found: `Liabilities` | found: `Liabilities` |
| stockholders_equity | found: `StockholdersEquity` | found: `StockholdersEquity` | found: `StockholdersEquity` |
| operating_cash_flow | found: `NetCashProvidedByUsedInOperatingActivities` | found: `NetCashProvidedByUsedInOperatingActivities` | found: `NetCashProvidedByUsedInOperatingActivities` |
| capital_expenditures | found: `PaymentsToAcquirePropertyPlantAndEquipment` | found: `PaymentsToAcquirePropertyPlantAndEquipment` | found: `PaymentsToAcquirePropertyPlantAndEquipment` |
| cash_and_equivalents | found: `CashAndCashEquivalentsAtCarryingValue` | found: `CashAndCashEquivalentsAtCarryingValue` | found: `CashAndCashEquivalentsAtCarryingValue` |
| long_term_debt | found: `LongTermDebtNoncurrent` | found: `LongTermDebtNoncurrent` | found: `LongTermDebtNoncurrent` |
| shares_outstanding | found: `CommonStockSharesOutstanding` | found: `CommonStockSharesOutstanding` | found: `CommonStockSharesOutstanding` |

## JNJ

| Metric | FY2023 | FY2024 | FY2025 |
|---|---|---|---|
| revenue | found: `RevenueFromContractWithCustomerExcludingAssessedTax` | found: `RevenueFromContractWithCustomerExcludingAssessedTax` | found: `RevenueFromContractWithCustomerExcludingAssessedTax` |
| net_income | found: `NetIncomeLoss` | found: `NetIncomeLoss` | found: `NetIncomeLoss` |
| diluted_eps | found: `EarningsPerShareDiluted` | found: `EarningsPerShareDiluted` | found: `EarningsPerShareDiluted` |
| operating_income | unavailable | unavailable | unavailable |
| pretax_income | found: `IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest` | found: `IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest` | found: `IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest` |
| total_assets | found: `Assets` | found: `Assets` | found: `Assets` |
| total_liabilities | found: `Liabilities` | found: `Liabilities` | found: `Liabilities` |
| stockholders_equity | found: `StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest` | found: `StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest` | found: `StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest` |
| operating_cash_flow | found: `NetCashProvidedByUsedInOperatingActivities` | found: `NetCashProvidedByUsedInOperatingActivities` | found: `NetCashProvidedByUsedInOperatingActivities` |
| capital_expenditures | found: `PaymentsToAcquirePropertyPlantAndEquipment` | found: `PaymentsToAcquirePropertyPlantAndEquipment` | found: `PaymentsToAcquirePropertyPlantAndEquipment` |
| cash_and_equivalents | found: `CashAndCashEquivalentsAtCarryingValue` | found: `CashAndCashEquivalentsAtCarryingValue` | found: `CashAndCashEquivalentsAtCarryingValue` |
| long_term_debt | found: `LongTermDebtNoncurrent` | found: `LongTermDebtNoncurrent` | found: `LongTermDebtNoncurrent` |
| shares_outstanding | found: `dei:EntityCommonStockSharesOutstanding` (cover page, 2024-02-09) | found: `dei:EntityCommonStockSharesOutstanding` (cover page, 2025-02-06) | found: `dei:EntityCommonStockSharesOutstanding` (cover page, 2026-02-06) |

## JPM

| Metric | FY2023 | FY2024 | FY2025 |
|---|---|---|---|
| revenue | found: `RevenuesNetOfInterestExpense` | found: `RevenuesNetOfInterestExpense` | found: `RevenuesNetOfInterestExpense` |
| net_income | found: `NetIncomeLoss` | found: `NetIncomeLoss` | found: `NetIncomeLoss` |
| diluted_eps | found: `EarningsPerShareDiluted` | found: `EarningsPerShareDiluted` | found: `EarningsPerShareDiluted` |
| operating_income | unavailable | unavailable | unavailable |
| pretax_income | found: `IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest` | found: `IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest` | found: `IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest` |
| total_assets | found: `Assets` | found: `Assets` | found: `Assets` |
| total_liabilities | found: `Liabilities` | found: `Liabilities` | found: `Liabilities` |
| stockholders_equity | found: `StockholdersEquity` | found: `StockholdersEquity` | found: `StockholdersEquity` |
| operating_cash_flow | found: `NetCashProvidedByUsedInOperatingActivities` | found: `NetCashProvidedByUsedInOperatingActivities` | found: `NetCashProvidedByUsedInOperatingActivities` |
| capital_expenditures | unavailable | unavailable | unavailable |
| cash_and_equivalents | found: `CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents` | found: `CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents` | found: `CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents` |
| long_term_debt | unavailable | unavailable | unavailable |
| shares_outstanding | found: `CommonStockSharesOutstanding` | found: `CommonStockSharesOutstanding` | found: `CommonStockSharesOutstanding` |

## KO

| Metric | FY2023 | FY2024 | FY2025 |
|---|---|---|---|
| revenue | found: `Revenues` | found: `Revenues` | found: `Revenues` |
| net_income | found: `NetIncomeLoss` | found: `NetIncomeLoss` | found: `NetIncomeLoss` |
| diluted_eps | found: `EarningsPerShareDiluted` | found: `EarningsPerShareDiluted` | found: `EarningsPerShareDiluted` |
| operating_income | found: `OperatingIncomeLoss` | found: `OperatingIncomeLoss` | found: `OperatingIncomeLoss` |
| pretax_income | found: `IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest` | found: `IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest` | found: `IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest` |
| total_assets | found: `Assets` | found: `Assets` | found: `Assets` |
| total_liabilities | unavailable | unavailable | unavailable |
| stockholders_equity | found: `StockholdersEquity` | found: `StockholdersEquity` | found: `StockholdersEquity` |
| operating_cash_flow | found: `NetCashProvidedByUsedInOperatingActivities` | found: `NetCashProvidedByUsedInOperatingActivities` | found: `NetCashProvidedByUsedInOperatingActivities` |
| capital_expenditures | found: `PaymentsToAcquirePropertyPlantAndEquipment` | found: `PaymentsToAcquirePropertyPlantAndEquipment` | found: `PaymentsToAcquirePropertyPlantAndEquipment` |
| cash_and_equivalents | found: `CashAndCashEquivalentsAtCarryingValue` | found: `CashAndCashEquivalentsAtCarryingValue` | found: `CashAndCashEquivalentsAtCarryingValue` |
| long_term_debt | found: `LongTermDebtNoncurrent` | unavailable | unavailable |
| shares_outstanding | found: `dei:EntityCommonStockSharesOutstanding` (cover page, 2024-02-16) | found: `dei:EntityCommonStockSharesOutstanding` (cover page, 2025-02-18) | found: `dei:EntityCommonStockSharesOutstanding` (cover page, 2026-02-18) |

## MA

| Metric | FY2023 | FY2024 | FY2025 |
|---|---|---|---|
| revenue | found: `Revenues` | found: `Revenues` | found: `Revenues` |
| net_income | found: `ProfitLoss` | found: `ProfitLoss` | found: `ProfitLoss` |
| diluted_eps | found: `EarningsPerShareDiluted` | found: `EarningsPerShareDiluted` | found: `EarningsPerShareDiluted` |
| operating_income | found: `OperatingIncomeLoss` | found: `OperatingIncomeLoss` | found: `OperatingIncomeLoss` |
| pretax_income | found: `IncomeLossFromContinuingOperationsBeforeIncomeTaxesMinorityInterestAndIncomeLossFromEquityMethodInvestments` | found: `IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest` | found: `IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest` |
| total_assets | found: `Assets` | found: `Assets` | found: `Assets` |
| total_liabilities | found: `Liabilities` | found: `Liabilities` | found: `Liabilities` |
| stockholders_equity | found: `StockholdersEquity` | found: `StockholdersEquity` | found: `StockholdersEquity` |
| operating_cash_flow | found: `NetCashProvidedByUsedInOperatingActivities` | found: `NetCashProvidedByUsedInOperatingActivities` | found: `NetCashProvidedByUsedInOperatingActivities` |
| capital_expenditures | found: `PaymentsToAcquirePropertyPlantAndEquipment` | found: `PaymentsToAcquirePropertyPlantAndEquipment` | found: `PaymentsToAcquirePropertyPlantAndEquipment` |
| cash_and_equivalents | found: `CashAndCashEquivalentsAtCarryingValue` | found: `CashAndCashEquivalentsAtCarryingValue` | found: `CashAndCashEquivalentsAtCarryingValue` |
| long_term_debt | found: `LongTermDebtNoncurrent` | found: `LongTermDebtNoncurrent` | found: `LongTermDebtNoncurrent` |
| shares_outstanding | unavailable | unavailable | unavailable |

## MCO

| Metric | FY2023 | FY2024 | FY2025 |
|---|---|---|---|
| revenue | found: `RevenueFromContractWithCustomerExcludingAssessedTax` | found: `RevenueFromContractWithCustomerExcludingAssessedTax` | found: `RevenueFromContractWithCustomerExcludingAssessedTax` |
| net_income | found: `NetIncomeLoss` | found: `NetIncomeLoss` | found: `NetIncomeLoss` |
| diluted_eps | found: `EarningsPerShareDiluted` | found: `EarningsPerShareDiluted` | found: `EarningsPerShareDiluted` |
| operating_income | found: `OperatingIncomeLoss` | found: `OperatingIncomeLoss` | found: `OperatingIncomeLoss` |
| pretax_income | found: `IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest` | found: `IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest` | found: `IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest` |
| total_assets | found: `Assets` | found: `Assets` | found: `Assets` |
| total_liabilities | found: `Liabilities` | found: `Liabilities` | found: `Liabilities` |
| stockholders_equity | found: `StockholdersEquity` | found: `StockholdersEquity` | found: `StockholdersEquity` |
| operating_cash_flow | found: `NetCashProvidedByUsedInOperatingActivities` | found: `NetCashProvidedByUsedInOperatingActivities` | found: `NetCashProvidedByUsedInOperatingActivities` |
| capital_expenditures | found: `PaymentsToAcquirePropertyPlantAndEquipment` | found: `PaymentsToAcquirePropertyPlantAndEquipment` | found: `PaymentsToAcquirePropertyPlantAndEquipment` |
| cash_and_equivalents | found: `CashAndCashEquivalentsAtCarryingValue` | found: `CashAndCashEquivalentsAtCarryingValue` | found: `CashAndCashEquivalentsAtCarryingValue` |
| long_term_debt | found: `LongTermDebtNoncurrent` | found: `LongTermDebtNoncurrent` | found: `LongTermDebtNoncurrent` |
| shares_outstanding | found: `dei:EntityCommonStockSharesOutstanding` (cover page, 2024-01-31) | found: `dei:EntityCommonStockSharesOutstanding` (cover page, 2025-01-31) | found: `dei:EntityCommonStockSharesOutstanding` (cover page, 2026-01-31) |

## META

| Metric | FY2023 | FY2024 | FY2025 |
|---|---|---|---|
| revenue | found: `RevenueFromContractWithCustomerExcludingAssessedTax` | found: `RevenueFromContractWithCustomerExcludingAssessedTax` | found: `RevenueFromContractWithCustomerExcludingAssessedTax` |
| net_income | found: `NetIncomeLoss` | found: `NetIncomeLoss` | found: `NetIncomeLoss` |
| diluted_eps | found: `EarningsPerShareDiluted` | found: `EarningsPerShareDiluted` | found: `EarningsPerShareDiluted` |
| operating_income | found: `OperatingIncomeLoss` | found: `OperatingIncomeLoss` | found: `OperatingIncomeLoss` |
| pretax_income | found: `IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest` | found: `IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest` | found: `IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest` |
| total_assets | found: `Assets` | found: `Assets` | found: `Assets` |
| total_liabilities | found: `Liabilities` | found: `Liabilities` | found: `Liabilities` |
| stockholders_equity | found: `StockholdersEquity` | found: `StockholdersEquity` | found: `StockholdersEquity` |
| operating_cash_flow | found: `NetCashProvidedByUsedInOperatingActivities` | found: `NetCashProvidedByUsedInOperatingActivities` | found: `NetCashProvidedByUsedInOperatingActivities` |
| capital_expenditures | found: `PaymentsToAcquirePropertyPlantAndEquipment` | found: `PaymentsToAcquirePropertyPlantAndEquipment` | found: `PaymentsToAcquirePropertyPlantAndEquipment` |
| cash_and_equivalents | found: `CashAndCashEquivalentsAtCarryingValue` | found: `CashAndCashEquivalentsAtCarryingValue` | found: `CashAndCashEquivalentsAtCarryingValue` |
| long_term_debt | found: `LongTermDebtNoncurrent` | found: `LongTermDebtNoncurrent` | found: `LongTermDebtNoncurrent` |
| shares_outstanding | unavailable | unavailable | unavailable |

## MS

| Metric | FY2023 | FY2024 | FY2025 |
|---|---|---|---|
| revenue | found: `RevenuesNetOfInterestExpense` | found: `RevenuesNetOfInterestExpense` | found: `RevenuesNetOfInterestExpense` |
| net_income | found: `NetIncomeLoss` | found: `NetIncomeLoss` | found: `NetIncomeLoss` |
| diluted_eps | found: `EarningsPerShareDiluted` | found: `EarningsPerShareDiluted` | found: `EarningsPerShareDiluted` |
| operating_income | unavailable | unavailable | unavailable |
| pretax_income | found: `IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest` | found: `IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest` | found: `IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest` |
| total_assets | found: `Assets` | found: `Assets` | found: `Assets` |
| total_liabilities | found: `Liabilities` | found: `Liabilities` | found: `Liabilities` |
| stockholders_equity | found: `StockholdersEquity` | found: `StockholdersEquity` | found: `StockholdersEquity` |
| operating_cash_flow | found: `NetCashProvidedByUsedInOperatingActivities` | found: `NetCashProvidedByUsedInOperatingActivities` | found: `NetCashProvidedByUsedInOperatingActivities` |
| capital_expenditures | unavailable | unavailable | unavailable |
| cash_and_equivalents | found: `CashAndCashEquivalentsAtCarryingValue` | found: `CashAndCashEquivalentsAtCarryingValue` | found: `CashAndCashEquivalentsAtCarryingValue` |
| long_term_debt | found: `LongTermDebt` | found: `LongTermDebt` | found: `LongTermDebt` |
| shares_outstanding | found: `CommonStockSharesOutstanding` | found: `CommonStockSharesOutstanding` | found: `CommonStockSharesOutstanding` |

## MSFT

| Metric | FY2024 | FY2025 | FY2026 |
|---|---|---|---|
| revenue | found: `RevenueFromContractWithCustomerExcludingAssessedTax` | found: `RevenueFromContractWithCustomerExcludingAssessedTax` | found: `RevenueFromContractWithCustomerExcludingAssessedTax` |
| net_income | found: `NetIncomeLoss` | found: `NetIncomeLoss` | found: `NetIncomeLoss` |
| diluted_eps | found: `EarningsPerShareDiluted` | found: `EarningsPerShareDiluted` | found: `EarningsPerShareDiluted` |
| operating_income | found: `OperatingIncomeLoss` | found: `OperatingIncomeLoss` | found: `OperatingIncomeLoss` |
| pretax_income | found: `IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest` | found: `IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest` | found: `IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest` |
| total_assets | found: `Assets` | found: `Assets` | found: `Assets` |
| total_liabilities | found: `Liabilities` | found: `Liabilities` | found: `Liabilities` |
| stockholders_equity | found: `StockholdersEquity` | found: `StockholdersEquity` | found: `StockholdersEquity` |
| operating_cash_flow | found: `NetCashProvidedByUsedInOperatingActivities` | found: `NetCashProvidedByUsedInOperatingActivities` | found: `NetCashProvidedByUsedInOperatingActivities` |
| capital_expenditures | found: `PaymentsToAcquirePropertyPlantAndEquipment` | found: `PaymentsToAcquirePropertyPlantAndEquipment` | found: `PaymentsToAcquirePropertyPlantAndEquipment` |
| cash_and_equivalents | found: `CashAndCashEquivalentsAtCarryingValue` | found: `CashAndCashEquivalentsAtCarryingValue` | found: `CashAndCashEquivalentsAtCarryingValue` |
| long_term_debt | found: `LongTermDebtNoncurrent` | found: `LongTermDebtNoncurrent` | found: `LongTermDebtNoncurrent` |
| shares_outstanding | found: `CommonStockSharesOutstanding` | found: `CommonStockSharesOutstanding` | found: `CommonStockSharesOutstanding` |

## NFLX

| Metric | FY2023 | FY2024 | FY2025 |
|---|---|---|---|
| revenue | found: `Revenues` | found: `Revenues` | found: `Revenues` |
| net_income | found: `NetIncomeLoss` | found: `NetIncomeLoss` | found: `NetIncomeLoss` |
| diluted_eps | found: `EarningsPerShareDiluted` | found: `EarningsPerShareDiluted` | found: `EarningsPerShareDiluted` |
| operating_income | found: `OperatingIncomeLoss` | found: `OperatingIncomeLoss` | found: `OperatingIncomeLoss` |
| pretax_income | found: `IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest` | found: `IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest` | found: `IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest` |
| total_assets | found: `Assets` | found: `Assets` | found: `Assets` |
| total_liabilities | found: `Liabilities` | found: `Liabilities` | found: `Liabilities` |
| stockholders_equity | found: `StockholdersEquity` | found: `StockholdersEquity` | found: `StockholdersEquity` |
| operating_cash_flow | found: `NetCashProvidedByUsedInOperatingActivities` | found: `NetCashProvidedByUsedInOperatingActivities` | found: `NetCashProvidedByUsedInOperatingActivities` |
| capital_expenditures | found: `PaymentsToAcquirePropertyPlantAndEquipment` | found: `PaymentsToAcquirePropertyPlantAndEquipment` | found: `PaymentsToAcquirePropertyPlantAndEquipment` |
| cash_and_equivalents | found: `CashAndCashEquivalentsAtCarryingValue` | found: `CashAndCashEquivalentsAtCarryingValue` | found: `CashAndCashEquivalentsAtCarryingValue` |
| long_term_debt | found: `LongTermDebtNoncurrent` | found: `LongTermDebtNoncurrent` | found: `LongTermDebtNoncurrent` |
| shares_outstanding | found: `CommonStockSharesOutstanding` | found: `CommonStockSharesOutstanding` | found: `CommonStockSharesOutstanding` |

## NKE

| Metric | FY2024 | FY2025 | FY2026 |
|---|---|---|---|
| revenue | found: `RevenueFromContractWithCustomerExcludingAssessedTax` | found: `RevenueFromContractWithCustomerExcludingAssessedTax` | found: `RevenueFromContractWithCustomerExcludingAssessedTax` |
| net_income | found: `NetIncomeLoss` | found: `NetIncomeLoss` | found: `NetIncomeLoss` |
| diluted_eps | found: `EarningsPerShareDiluted` | found: `EarningsPerShareDiluted` | found: `EarningsPerShareDiluted` |
| operating_income | unavailable | unavailable | unavailable |
| pretax_income | found: `IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest` | found: `IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest` | found: `IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest` |
| total_assets | found: `Assets` | found: `Assets` | found: `Assets` |
| total_liabilities | unavailable | unavailable | unavailable |
| stockholders_equity | found: `StockholdersEquity` | found: `StockholdersEquity` | found: `StockholdersEquity` |
| operating_cash_flow | found: `NetCashProvidedByUsedInOperatingActivities` | found: `NetCashProvidedByUsedInOperatingActivities` | found: `NetCashProvidedByUsedInOperatingActivities` |
| capital_expenditures | found: `PaymentsToAcquirePropertyPlantAndEquipment` | found: `PaymentsToAcquirePropertyPlantAndEquipment` | found: `PaymentsToAcquirePropertyPlantAndEquipment` |
| cash_and_equivalents | found: `CashAndCashEquivalentsAtCarryingValue` | found: `CashAndCashEquivalentsAtCarryingValue` | found: `CashAndCashEquivalentsAtCarryingValue` |
| long_term_debt | found: `LongTermDebtNoncurrent` | found: `LongTermDebtNoncurrent` | found: `LongTermDebtNoncurrent` |
| shares_outstanding | unavailable | unavailable | unavailable |

## NVDA

| Metric | FY2024 | FY2025 | FY2026 |
|---|---|---|---|
| revenue | found: `Revenues` | found: `Revenues` | found: `Revenues` |
| net_income | found: `NetIncomeLoss` | found: `NetIncomeLoss` | found: `NetIncomeLoss` |
| diluted_eps | found: `EarningsPerShareDiluted` | found: `EarningsPerShareDiluted` | found: `EarningsPerShareDiluted` |
| operating_income | found: `OperatingIncomeLoss` | found: `OperatingIncomeLoss` | found: `OperatingIncomeLoss` |
| pretax_income | found: `IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest` | found: `IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest` | found: `IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest` |
| total_assets | found: `Assets` | found: `Assets` | found: `Assets` |
| total_liabilities | found: `Liabilities` | found: `Liabilities` | found: `Liabilities` |
| stockholders_equity | found: `StockholdersEquity` | found: `StockholdersEquity` | found: `StockholdersEquity` |
| operating_cash_flow | found: `NetCashProvidedByUsedInOperatingActivities` | found: `NetCashProvidedByUsedInOperatingActivities` | found: `NetCashProvidedByUsedInOperatingActivities` |
| capital_expenditures | unavailable | unavailable | unavailable |
| cash_and_equivalents | found: `CashAndCashEquivalentsAtCarryingValue` | found: `CashAndCashEquivalentsAtCarryingValue` | found: `CashAndCashEquivalentsAtCarryingValue` |
| long_term_debt | found: `LongTermDebtNoncurrent` | found: `LongTermDebtNoncurrent` | found: `LongTermDebtNoncurrent` |
| shares_outstanding | found: `CommonStockSharesOutstanding` | found: `CommonStockSharesOutstanding` | found: `CommonStockSharesOutstanding` |

## PFE

| Metric | FY2023 | FY2024 | FY2025 |
|---|---|---|---|
| revenue | found: `Revenues` | found: `Revenues` | found: `Revenues` |
| net_income | found: `NetIncomeLoss` | found: `NetIncomeLoss` | found: `NetIncomeLoss` |
| diluted_eps | found: `EarningsPerShareDiluted` | found: `EarningsPerShareDiluted` | found: `EarningsPerShareDiluted` |
| operating_income | unavailable | unavailable | unavailable |
| pretax_income | found: `IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest` | found: `IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest` | found: `IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest` |
| total_assets | found: `Assets` | found: `Assets` | found: `Assets` |
| total_liabilities | found: `Liabilities` | found: `Liabilities` | found: `Liabilities` |
| stockholders_equity | found: `StockholdersEquity` | found: `StockholdersEquity` | found: `StockholdersEquity` |
| operating_cash_flow | found: `NetCashProvidedByUsedInOperatingActivities` | found: `NetCashProvidedByUsedInOperatingActivities` | found: `NetCashProvidedByUsedInOperatingActivities` |
| capital_expenditures | found: `PaymentsToAcquirePropertyPlantAndEquipment` | found: `PaymentsToAcquirePropertyPlantAndEquipment` | found: `PaymentsToAcquirePropertyPlantAndEquipment` |
| cash_and_equivalents | found: `CashAndCashEquivalentsAtCarryingValue` | found: `CashAndCashEquivalentsAtCarryingValue` | found: `CashAndCashEquivalentsAtCarryingValue` |
| long_term_debt | found: `LongTermDebtNoncurrent` | found: `LongTermDebtNoncurrent` | found: `LongTermDebtNoncurrent` |
| shares_outstanding | found: `dei:EntityCommonStockSharesOutstanding` (cover page, 2024-02-15) | found: `dei:EntityCommonStockSharesOutstanding` (cover page, 2025-02-20) | found: `dei:EntityCommonStockSharesOutstanding` (cover page, 2026-02-19) |

## SPGI

| Metric | FY2023 | FY2024 | FY2025 |
|---|---|---|---|
| revenue | found: `RevenueFromContractWithCustomerExcludingAssessedTax` | found: `RevenueFromContractWithCustomerExcludingAssessedTax` | found: `RevenueFromContractWithCustomerExcludingAssessedTax` |
| net_income | found: `NetIncomeLoss` | found: `NetIncomeLoss` | found: `NetIncomeLoss` |
| diluted_eps | found: `EarningsPerShareDiluted` | found: `EarningsPerShareDiluted` | found: `EarningsPerShareDiluted` |
| operating_income | found: `OperatingIncomeLoss` | found: `OperatingIncomeLoss` | found: `OperatingIncomeLoss` |
| pretax_income | found: `IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest` | found: `IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest` | found: `IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest` |
| total_assets | found: `Assets` | found: `Assets` | found: `Assets` |
| total_liabilities | found: `Liabilities` | found: `Liabilities` | found: `Liabilities` |
| stockholders_equity | found: `StockholdersEquity` | found: `StockholdersEquity` | found: `StockholdersEquity` |
| operating_cash_flow | found: `NetCashProvidedByUsedInOperatingActivities` | found: `NetCashProvidedByUsedInOperatingActivities` | found: `NetCashProvidedByUsedInOperatingActivities` |
| capital_expenditures | unavailable | unavailable | unavailable |
| cash_and_equivalents | found: `CashAndCashEquivalentsAtCarryingValue` | found: `CashAndCashEquivalentsAtCarryingValue` | found: `CashAndCashEquivalentsAtCarryingValue` |
| long_term_debt | found: `LongTermDebtNoncurrent` | found: `LongTermDebtNoncurrent` | found: `LongTermDebtNoncurrent` |
| shares_outstanding | found: `CommonStockSharesOutstanding` | found: `CommonStockSharesOutstanding` | found: `CommonStockSharesOutstanding` |

## UNH

| Metric | FY2023 | FY2024 | FY2025 |
|---|---|---|---|
| revenue | found: `Revenues` | found: `Revenues` | found: `Revenues` |
| net_income | found: `NetIncomeLoss` | found: `NetIncomeLoss` | found: `NetIncomeLoss` |
| diluted_eps | found: `EarningsPerShareDiluted` | found: `EarningsPerShareDiluted` | found: `EarningsPerShareDiluted` |
| operating_income | found: `OperatingIncomeLoss` | found: `OperatingIncomeLoss` | found: `OperatingIncomeLoss` |
| pretax_income | found: `IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest` | found: `IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest` | found: `IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest` |
| total_assets | found: `Assets` | found: `Assets` | found: `Assets` |
| total_liabilities | found: `Liabilities` | found: `Liabilities` | found: `Liabilities` |
| stockholders_equity | found: `StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest` | found: `StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest` | found: `StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest` |
| operating_cash_flow | found: `NetCashProvidedByUsedInOperatingActivities` | found: `NetCashProvidedByUsedInOperatingActivities` | found: `NetCashProvidedByUsedInOperatingActivities` |
| capital_expenditures | found: `PaymentsToAcquirePropertyPlantAndEquipment` | found: `PaymentsToAcquirePropertyPlantAndEquipment` | found: `PaymentsToAcquirePropertyPlantAndEquipment` |
| cash_and_equivalents | found: `CashAndCashEquivalentsAtCarryingValue` | found: `CashAndCashEquivalentsAtCarryingValue` | found: `CashAndCashEquivalentsAtCarryingValue` |
| long_term_debt | found: `LongTermDebtNoncurrent` | found: `LongTermDebtNoncurrent` | found: `LongTermDebtNoncurrent` |
| shares_outstanding | found: `CommonStockSharesOutstanding` | found: `CommonStockSharesOutstanding` | found: `CommonStockSharesOutstanding` |

## VZ

| Metric | FY2023 | FY2024 | FY2025 |
|---|---|---|---|
| revenue | found: `Revenues` | found: `Revenues` | found: `Revenues` |
| net_income | found: `NetIncomeLoss` | found: `NetIncomeLoss` | found: `NetIncomeLoss` |
| diluted_eps | found: `EarningsPerShareDiluted` | found: `EarningsPerShareDiluted` | found: `EarningsPerShareDiluted` |
| operating_income | found: `OperatingIncomeLoss` | found: `OperatingIncomeLoss` | found: `OperatingIncomeLoss` |
| pretax_income | found: `IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest` | found: `IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest` | found: `IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest` |
| total_assets | found: `Assets` | found: `Assets` | found: `Assets` |
| total_liabilities | unavailable | unavailable | unavailable |
| stockholders_equity | found: `StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest` | found: `StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest` | found: `StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest` |
| operating_cash_flow | found: `NetCashProvidedByUsedInOperatingActivities` | found: `NetCashProvidedByUsedInOperatingActivities` | found: `NetCashProvidedByUsedInOperatingActivities` |
| capital_expenditures | unavailable | unavailable | unavailable |
| cash_and_equivalents | found: `CashAndCashEquivalentsAtCarryingValue` | found: `CashAndCashEquivalentsAtCarryingValue` | found: `CashAndCashEquivalentsAtCarryingValue` |
| long_term_debt | unavailable | unavailable | unavailable |
| shares_outstanding | found: `dei:EntityCommonStockSharesOutstanding` (cover page, 2024-01-31) | found: `dei:EntityCommonStockSharesOutstanding` (cover page, 2025-01-31) | found: `dei:EntityCommonStockSharesOutstanding` (cover page, 2026-01-30) |

## WMT

| Metric | FY2024 | FY2025 | FY2026 |
|---|---|---|---|
| revenue | found: `Revenues` | found: `Revenues` | found: `Revenues` |
| net_income | found: `NetIncomeLoss` | found: `NetIncomeLoss` | found: `NetIncomeLoss` |
| diluted_eps | found: `EarningsPerShareDiluted` | found: `EarningsPerShareDiluted` | found: `EarningsPerShareDiluted` |
| operating_income | found: `OperatingIncomeLoss` | found: `OperatingIncomeLoss` | found: `OperatingIncomeLoss` |
| pretax_income | found: `IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest` | found: `IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest` | found: `IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest` |
| total_assets | found: `Assets` | found: `Assets` | found: `Assets` |
| total_liabilities | unavailable | unavailable | unavailable |
| stockholders_equity | found: `StockholdersEquity` | found: `StockholdersEquity` | found: `StockholdersEquity` |
| operating_cash_flow | found: `NetCashProvidedByUsedInOperatingActivities` | found: `NetCashProvidedByUsedInOperatingActivities` | found: `NetCashProvidedByUsedInOperatingActivities` |
| capital_expenditures | found: `PaymentsToAcquirePropertyPlantAndEquipment` | found: `PaymentsToAcquirePropertyPlantAndEquipment` | found: `PaymentsToAcquirePropertyPlantAndEquipment` |
| cash_and_equivalents | found: `CashAndCashEquivalentsAtCarryingValue` | found: `CashAndCashEquivalentsAtCarryingValue` | found: `CashAndCashEquivalentsAtCarryingValue` |
| long_term_debt | found: `LongTermDebtNoncurrent` | found: `LongTermDebtNoncurrent` | found: `LongTermDebtNoncurrent` |
| shares_outstanding | found: `dei:EntityCommonStockSharesOutstanding` (cover page, 2024-03-13) | found: `dei:EntityCommonStockSharesOutstanding` (cover page, 2025-03-12) | found: `dei:EntityCommonStockSharesOutstanding` (cover page, 2026-03-11) |
