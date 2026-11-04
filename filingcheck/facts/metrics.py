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
            _us("PaymentsToAcquirePropertyPlantAndEquipment"),
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
            "long_term_debt", _us("LongTermDebtNoncurrent", "LongTermDebt"), "instant", "USD"
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


def candidate_tags(metric: str, revenue_rule: str) -> tuple[str, ...]:
    """The tags tried for `metric`, in order; banks have their own revenue order."""
    if metric == "revenue" and revenue_rule == "bank":
        return BANK_REVENUE_TAGS
    return METRICS[metric].tags


def all_candidate_tags() -> list[str]:
    """Every candidate tag of every metric, once, in map order."""
    tags = [tag for spec in METRICS.values() for tag in spec.tags]
    return list(dict.fromkeys([*tags, *BANK_REVENUE_TAGS]))
