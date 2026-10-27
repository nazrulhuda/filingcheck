"""Which candidate XBRL tags have a 10-K fact for each pinned fiscal year (coverage only)."""

from datetime import date
from typing import Any

from filingcheck.ingest.facts_coverage import METRICS, build_coverage, find_fact, near_miss
from tests.db.test_load import APPLE, FILING

PERIOD_END = "2025-09-27"


def fact(
    end: str, start: str | None = None, form: str = "10-K", accn: str = "a-1"
) -> dict[str, Any]:
    row: dict[str, Any] = {"end": end, "val": 1, "accn": accn, "form": form, "fy": 2025, "fp": "FY"}
    if start:
        row["start"] = start
    return row


def facts(**tags: list[dict[str, Any]]) -> dict[str, Any]:
    gaap = {tag: {"units": {"USD": rows}} for tag, rows in tags.items() if tag != "Shares"}
    dei = {}
    if "Shares" in tags:
        dei["EntityCommonStockSharesOutstanding"] = {"units": {"shares": tags["Shares"]}}
    return {"facts": {"us-gaap": gaap, "dei": dei}}


def candidates(metric: str) -> Any:
    return next(m for m in METRICS if m.name == metric)


def test_the_first_candidate_tag_with_an_annual_10k_fact_is_reported() -> None:
    data = facts(
        RevenueFromContractWithCustomerExcludingAssessedTax=[fact(PERIOD_END, "2024-09-29")]
    )
    found = find_fact(data, candidates("revenue"), PERIOD_END)
    assert found == "RevenueFromContractWithCustomerExcludingAssessedTax"


def test_a_quarter_ending_on_the_same_day_does_not_count() -> None:
    data = facts(Revenues=[fact(PERIOD_END, "2025-06-29")])  # 10-Ks also carry quarters
    assert find_fact(data, candidates("revenue"), PERIOD_END) is None


def test_a_53_week_year_counts_as_annual() -> None:
    data = facts(NetIncomeLoss=[fact("2024-02-03", "2023-01-29")])  # 371 days
    assert find_fact(data, candidates("net income"), "2024-02-03") == "NetIncomeLoss"


def test_only_10k_facts_count() -> None:
    data = facts(Assets=[fact(PERIOD_END, form="10-Q")])
    assert find_fact(data, candidates("total assets"), PERIOD_END) is None
    data = facts(Assets=[fact(PERIOD_END)])
    assert find_fact(data, candidates("total assets"), PERIOD_END) == "Assets"


def test_a_cover_page_share_count_dated_after_the_period_end_is_a_near_miss() -> None:
    data = facts(Shares=[fact("2025-10-17", accn=FILING.accession)])
    metric = candidates("shares outstanding")
    assert find_fact(data, metric, PERIOD_END) is None
    assert near_miss(data, metric, FILING.accession) == (
        "dei:EntityCommonStockSharesOutstanding dated 2025-10-17 in this 10-K"
    )


def test_the_coverage_page_has_a_grid_per_company_and_totals() -> None:
    data = facts(
        Revenues=[fact(PERIOD_END, "2024-09-29")],
        Assets=[fact(PERIOD_END)],
        Shares=[fact("2025-10-17", accn=FILING.accession)],
    )
    page = build_coverage([APPLE], [FILING], {"AAPL": data})
    assert FILING.period_of_report == date(2025, 9, 27)
    assert "| revenue | found: `Revenues` |" in page
    assert "| total assets | found: `Assets` |" in page
    assert "| net income | missing |" in page
    assert "dei:EntityCommonStockSharesOutstanding dated 2025-10-17 in this 10-K" in page
    assert "| revenue | 1 of 1 |" in page
    assert len(METRICS) == 12
