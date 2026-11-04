"""`get_financial_fact`: one company total from the pinned filing's own XBRL facts."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from filingcheck.facts.lookup import FactResult, FactsSource, lookup
from filingcheck.facts.metrics import Metric
from filingcheck.tools.inputs import Ticker


class GetFinancialFactInput(BaseModel):
    """A company, one of its fiscal years and a metric."""

    model_config = ConfigDict(extra="forbid")

    ticker: Ticker = Field(description="The company's ticker, one of the 25 companies.")
    fiscal_year: int = Field(
        description=(
            "The company's own fiscal year, as its 10-K names it (for example Walmart's fiscal "
            "2026 ended January 31, 2026)."
        )
    )
    metric: Metric = Field(description="The metric to look up.")


class FactFound(BaseModel):
    """The fact, as the filing reports it."""

    status: Literal["found"] = "found"
    fact: FactResult


class FactUnavailable(BaseModel):
    """Why there is no fact."""

    status: Literal["unavailable"] = "unavailable"
    reason: Literal["no_filing", "not_reported"]
    message: str


def get_financial_fact(
    arguments: GetFinancialFactInput, facts: FactsSource
) -> FactFound | FactUnavailable:
    """Run the tool: the fact, or why it is unavailable. Arguments are never repaired."""
    ticker, year, metric = arguments.ticker, arguments.fiscal_year, arguments.metric
    if facts.filing(ticker, year) is None:
        return FactUnavailable(
            reason="no_filing",
            message=f"No 10-K for {ticker} fiscal year {year} is in the dataset.",
        )
    result = lookup(facts, ticker, year, metric)
    if result is None:
        return FactUnavailable(
            reason="not_reported",
            message=(
                f"{ticker}'s 10-K for fiscal year {year} does not report {metric} under any "
                "of the tags this tool reads; it is not derived from other numbers."
            ),
        )
    return FactFound(fact=result)
