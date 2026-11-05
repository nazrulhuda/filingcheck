"""The 13 metrics and the XBRL tags that may hold each one, in the order they are tried.

The one place that maps a metric to its candidate tags, the kind of period it covers and its
unit; the lookup, the coverage page and the companyfacts cross-check all import it.
"""

from dataclasses import dataclass
from typing import Literal, get_args

Metric = Literal[
    "revenue",
    "net_income",
    "diluted_eps",
    "operating_income",
    "pretax_income",
    "total_assets",
    "total_liabilities",
    "stockholders_equity",
    "operating_cash_flow",
    "capital_expenditures",
    "cash_and_equivalents",
    "long_term_debt",
    "shares_outstanding",
]
RevenueRule = Literal["standard", "bank"]

# A fiscal year in days: 365 or 366, or 364 and 371 for 52- and 53-week years. 10-Ks also
# carry quarters that end on the same day, which must not count as the year.
ANNUAL_DAYS = range(350, 381)

# The cover-page share count is dated a few weeks after the fiscal year ends.
COVER_PAGE_SHARES = "dei:EntityCommonStockSharesOutstanding"

# Banks (decisions.md, Nov 1): never RevenueFromContract..., which is fee revenue only.
BANK_REVENUE_TAGS = ("us-gaap:RevenuesNetOfInterestExpense", "us-gaap:Revenues")


@dataclass(frozen=True)
class MetricSpec:
    """One metric: its candidate tags in order, its kind of period and its unit."""

    name: str
    tags: tuple[str, ...]  # "taxonomy:Name"
    period: Literal["duration", "instant"]
    unit: str


def _us(*names: str) -> tuple[str, ...]:
    return tuple(f"us-gaap:{name}" for name in names)


METRICS: dict[str, MetricSpec] = {
    spec.name: spec
    for spec in (
        MetricSpec(
            "revenue",
            _us(
                "Revenues",
                "RevenueFromContractWithCustomerExcludingAssessedTax",
                "RevenuesNetOfInterestExpense",
                "SalesRevenueNet",
            ),
            "duration",
            "USD",
        ),
        MetricSpec("net_income", _us("NetIncomeLoss", "ProfitLoss"), "duration", "USD"),
        MetricSpec("diluted_eps", _us("EarningsPerShareDiluted"), "duration", "USD/shares"),
        MetricSpec("operating_income", _us("OperatingIncomeLoss"), "duration", "USD"),
        MetricSpec(
            "pretax_income",
            _us(
                "IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest",
                "IncomeLossFromContinuingOperationsBeforeIncomeTaxesMinorityInterestAndIncomeLossFromEquityMethodInvestments",
            ),
            "duration",
            "USD",
        ),
        MetricSpec("total_assets", _us("Assets"), "instant", "USD"),
        MetricSpec("total_liabilities", _us("Liabilities"), "instant", "USD"),
        MetricSpec(
            "stockholders_equity",
            _us(
                "StockholdersEquity",
                "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest",
            ),
            "instant",
            "USD",
        ),
        MetricSpec(
            "operating_cash_flow",
            _us("NetCashProvidedByUsedInOperatingActivities"),
            "duration",
            "USD",
        ),
        MetricSpec(
            "capital_expenditures",
            _us(
                "PaymentsToAcquirePropertyPlantAndEquipment",
                "PaymentsToAcquireProductiveAssets",
                "PaymentsToAcquireOtherProductiveAssets",
            ),
            "duration",
            "USD",
        ),
        MetricSpec(
            "cash_and_equivalents",
            _us(
                "CashAndCashEquivalentsAtCarryingValue",
                "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents",
            ),
            "instant",
            "USD",
        ),
        MetricSpec(
            "long_term_debt",
            _us(
                "LongTermDebtNoncurrent",
                # The balance-sheet line before LongTermDebt: Alphabet FY2023 tags its
                # balance-sheet "Long-term debt" this way and uses LongTermDebt for the debt
                # note's total, which includes the part due within a year.
                "LongTermDebtAndCapitalLeaseObligations",
                "LongTermDebt",
                "UnsecuredLongTermDebt",
                "LongTermDebtAndCapitalLeaseObligationsIncludingCurrentMaturities",
            ),
            "instant",
            "USD",
        ),
        MetricSpec(
            "shares_outstanding",
            (*_us("CommonStockSharesOutstanding"), COVER_PAGE_SHARES),
            "instant",
            "shares",
        ),
    )
}
assert set(METRICS) == set(get_args(Metric))  # one entry per metric name


# The line each tag stands for, in the plain wording of a financial statement. Where a
# company's own statement words its line differently, COMPANY_LABELS gives that wording
# (read from the printed statement); answers use it when it differs from the question.
LABELS: dict[str, str] = {
    "us-gaap:Revenues": "Revenues",
    "us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax": (
        "Revenue from contracts with customers"
    ),
    "us-gaap:RevenuesNetOfInterestExpense": "Revenues, net of interest expense",
    "us-gaap:SalesRevenueNet": "Net sales",
    "us-gaap:NetIncomeLoss": "Net income",
    "us-gaap:ProfitLoss": "Net income, including noncontrolling interests",
    "us-gaap:EarningsPerShareDiluted": "Diluted earnings per share",
    "us-gaap:OperatingIncomeLoss": "Operating income",
    "us-gaap:IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest": (  # noqa: E501 (an XBRL tag name)
        "Income before income taxes"
    ),
    "us-gaap:IncomeLossFromContinuingOperationsBeforeIncomeTaxesMinorityInterestAndIncomeLossFromEquityMethodInvestments": (  # noqa: E501 (an XBRL tag name)
        "Income before income taxes"  # the printed line in every filing that uses this tag
    ),
    "us-gaap:Assets": "Total assets",
    "us-gaap:Liabilities": "Total liabilities",
    "us-gaap:StockholdersEquity": "Total shareholders' equity",
    "us-gaap:StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest": (
        "Total equity, including noncontrolling interests"
    ),
    "us-gaap:NetCashProvidedByUsedInOperatingActivities": (
        "Net cash provided by operating activities"
    ),
    "us-gaap:PaymentsToAcquirePropertyPlantAndEquipment": (
        "Purchases of property, plant and equipment"
    ),
    "us-gaap:PaymentsToAcquireProductiveAssets": "Capital expenditures",
    "us-gaap:PaymentsToAcquireOtherProductiveAssets": "Capital expenditures",
    "us-gaap:CashAndCashEquivalentsAtCarryingValue": "Cash and cash equivalents",
    "us-gaap:CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents": (
        "Cash, cash equivalents and restricted cash"
    ),
    "us-gaap:LongTermDebtNoncurrent": "Long-term debt",
    "us-gaap:LongTermDebt": "Long-term debt",
    "us-gaap:LongTermDebtAndCapitalLeaseObligations": "Long-term debt",
    "us-gaap:UnsecuredLongTermDebt": "Unsecured long-term borrowings",
    "us-gaap:LongTermDebtAndCapitalLeaseObligationsIncludingCurrentMaturities": (
        "Long-term debt, including current maturities"
    ),
    "us-gaap:CommonStockSharesOutstanding": "Common shares outstanding",
    COVER_PAGE_SHARES: "Common shares outstanding (cover page)",
}

_CONTRACT_REVENUE = "us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax"
_PRETAX_EQUITY_METHOD = (
    "us-gaap:IncomeLossFromContinuingOperationsBeforeIncomeTaxes"
    "MinorityInterestAndIncomeLossFromEquityMethodInvestments"
)
_CAPEX = "us-gaap:PaymentsToAcquirePropertyPlantAndEquipment"
_CASH_WITH_RESTRICTED = "us-gaap:CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents"
COMPANY_LABELS: dict[tuple[str, str], str] = {
    (_CONTRACT_REVENUE, "AAPL"): "Total net sales",
    (_CONTRACT_REVENUE, "AMZN"): "Total net sales",
    (_CONTRACT_REVENUE, "COST"): "Total revenue",
    ("us-gaap:Revenues", "COST"): "Total revenue",
    (_CONTRACT_REVENUE, "MSFT"): "Total revenue",
    (_CONTRACT_REVENUE, "GOOGL"): "Revenues",
    (_CONTRACT_REVENUE, "JNJ"): "Sales to customers",
    (_CONTRACT_REVENUE, "NKE"): "Revenues",
    ("us-gaap:Revenues", "WMT"): "Total revenues",
    ("us-gaap:RevenuesNetOfInterestExpense", "JPM"): "Total net revenue",
    ("us-gaap:RevenuesNetOfInterestExpense", "AXP"): "Total revenues net of interest expense",
    # Amazon prints "Income (loss) before income taxes" in FY2023-24 and "Income before income
    # taxes" in FY2025, so it keeps the generic label.
    ("us-gaap:StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest", "JNJ"): (
        "Total shareholders' equity"
    ),
    (_CAPEX, "AXP"): "Purchase of premises and equipment, net of sales",
    (_CAPEX, "C"): "Capital expenditures on premises and equipment and capitalized software",
    (_CAPEX, "UNH"): "Purchases of property, equipment and capitalized software",
    (_CAPEX, "COF"): "Changes in premises and equipment",
    # The banks' cash is the cash-flow statement's total, deposits with banks included.
    (_CASH_WITH_RESTRICTED, "JPM"): (
        "Cash and due from banks and deposits with banks at the end of the period"
    ),
    (_CASH_WITH_RESTRICTED, "C"): "Cash, due from banks and deposits with banks at end of year",
    (_CASH_WITH_RESTRICTED, "AXP"): "Cash and cash equivalents at end of year",
    ("us-gaap:LongTermDebt", "MS"): "Borrowings with original maturities greater than one year",
    ("us-gaap:PaymentsToAcquireProductiveAssets", "AMZN"): "Purchases of property and equipment",
    ("us-gaap:PaymentsToAcquireProductiveAssets", "SPGI"): "Capital expenditures",
    ("us-gaap:PaymentsToAcquireProductiveAssets", "NVDA"): (
        "Purchases related to property and equipment and intangible assets"
    ),
    ("us-gaap:PaymentsToAcquireOtherProductiveAssets", "VZ"): (
        "Capital expenditures (including capitalized software)"
    ),
    ("us-gaap:LongTermDebtAndCapitalLeaseObligations", "KO"): "Long-term debt",
    ("us-gaap:LongTermDebtAndCapitalLeaseObligations", "VZ"): "Long-term debt",
    ("us-gaap:LongTermDebtAndCapitalLeaseObligations", "COF"): "Total long-term debt",
    ("us-gaap:UnsecuredLongTermDebt", "GS"): "Unsecured long-term borrowings",
    ("us-gaap:LongTermDebtAndCapitalLeaseObligationsIncludingCurrentMaturities", "JPM"): (
        "Long-term debt"
    ),
}


def line_label(tag: str, ticker: str) -> str:
    """The statement line `tag` stands for, in the company's own wording where known."""
    return COMPANY_LABELS.get((tag, ticker), LABELS[tag])


def candidate_tags(metric: str, revenue_rule: str) -> tuple[str, ...]:
    """The tags tried for `metric`, in order; banks have their own revenue order."""
    if metric == "revenue" and revenue_rule == "bank":
        return BANK_REVENUE_TAGS
    return METRICS[metric].tags


def all_candidate_tags() -> list[str]:
    """Every candidate tag of every metric, once, in map order."""
    tags = [tag for spec in METRICS.values() for tag in spec.tags]
    return list(dict.fromkeys([*tags, *BANK_REVENUE_TAGS]))
