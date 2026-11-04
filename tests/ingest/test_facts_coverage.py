"""docs/facts_coverage.md: the lookup's result for every filing and metric."""

from datetime import date

from filingcheck.facts.lookup import FilingRef, TotalFact
from filingcheck.ingest.facts_coverage import build_coverage
from tests.db.test_load import APPLE, FILING
from tests.facts.test_lookup import FakeFacts, duration, instant


def apple_source(facts: list[TotalFact]) -> FakeFacts:
    """A source holding the Apple filing of tests.db.test_load."""
    filing = FilingRef(
        ticker="AAPL",
        fiscal_year=2025,
        accession=FILING.accession,
        period_of_report=FILING.period_of_report,
        source_url=FILING.primary_document_url,
        revenue_rule="standard",
    )
    return FakeFacts(facts, filing=filing)


def test_the_coverage_page_shows_the_lookups_tag_or_unavailable_per_metric() -> None:
    year = (date(2024, 9, 29), date(2025, 9, 27))
    source = apple_source(
        [
            duration(
                "us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax", "416161000000", *year
            ),
            instant("us-gaap:Assets", "359241000000", on=date(2025, 9, 27)),
            instant(
                "dei:EntityCommonStockSharesOutstanding",
                "14776353000",
                on=date(2025, 10, 17),
                unit="shares",
                decimals="INF",
            ),
        ]
    )
    page = build_coverage([APPLE], [FILING], source)
    assert "| revenue | found: `RevenueFromContractWithCustomerExcludingAssessedTax` |" in page
    assert "| total_assets | found: `Assets` |" in page
    assert "| net_income | unavailable |" in page
    assert (
        "| shares_outstanding | found: `dei:EntityCommonStockSharesOutstanding` "
        "(cover page, 2025-10-17) |" in page
    )
    assert "| revenue | 1 of 1 |" in page
    assert "| pretax_income | 0 of 1 |" in page
