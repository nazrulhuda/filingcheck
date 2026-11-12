"""The fiscal-year check on `search_filings` (added after the freeze; see docs/decisions.md).

The Day 33 dry run found the agent sending fiscal_year 2023 to search_filings on most text
questions that name no year (124 of 159 calls), and a year the company does not hold in 32.
The rules: no year in the question or the page filter means the latest pinned year, as a repair;
a year in the question follows the fact tool's rules; a year the company does not hold is a
reject with the years held.
"""

from typing import Any

from filingcheck.checks import CheckContext, CheckedCall, CheckResult
from filingcheck.checks.fiscal_year import SearchYearCheck
from tests.checks.conftest import COMPANIES, MANIFEST, NOT_COVERED

CHECK = SearchYearCheck()


def run(
    question: str,
    *,
    ticker: str | None = "AAPL",
    fiscal_year: int | None = 2023,
    page_ticker: str | None = None,
    page_year: int | None = None,
) -> CheckResult:
    arguments: dict[str, Any] = {"query": "data center revenue drivers", "k": 5}
    if ticker is not None:
        arguments["ticker"] = ticker
    if fiscal_year is not None:
        arguments["fiscal_year"] = fiscal_year
    context = CheckContext(
        question=question,
        ticker=page_ticker,
        fiscal_year=page_year,
        companies=COMPANIES,
        not_covered=NOT_COVERED,
        manifest=MANIFEST,
    )
    return CHECK.run(CheckedCall("search_filings", arguments), context)


def test_no_year_in_the_question_means_the_latest_pinned_year_as_a_repair() -> None:
    result = run("How does Apple describe its services business?", fiscal_year=2023)
    assert result.outcome == "repair"
    assert result.arguments["fiscal_year"] == 2026  # Apple's latest pinned year
    assert result.arguments["query"] == "data center revenue drivers"  # the rest untouched
    assert result.override.check == "fiscal_year" and result.override.argument == "fiscal_year"
    assert (result.override.sent, result.override.used) == (2023, 2026)
    assert "latest" in result.override.reason and "2026" in result.override.reason


def test_no_year_sent_and_none_in_the_question_is_repaired_to_the_latest_too() -> None:
    result = run("What does Netflix say about content costs?", ticker="NFLX", fiscal_year=None)
    assert result.outcome == "repair" and result.arguments["fiscal_year"] == 2025
    assert result.override.sent is None and result.override.used == 2025


def test_the_latest_year_already_sent_passes() -> None:
    result = run("How does Apple describe its services business?", fiscal_year=2026)
    assert result.outcome == "pass" and result.arguments["fiscal_year"] == 2026


def test_a_year_in_the_question_follows_the_fact_tools_rules() -> None:
    repaired = run("What did Walmart say about Mexico in its fiscal 2024 10-K?", ticker="WMT")
    assert repaired.outcome == "repair" and repaired.arguments["fiscal_year"] == 2024
    passed = run(
        "What did Walmart say about Mexico in fiscal 2024?", ticker="WMT", fiscal_year=2024
    )
    assert passed.outcome == "pass"
    stated_last = run("What did Walmart say about Mexico last year?", ticker="WMT")
    assert stated_last.outcome == "repair" and stated_last.arguments["fiscal_year"] == 2026


def test_a_year_the_company_does_not_hold_is_rejected_with_the_years_held() -> None:
    result = run("What did Walmart's 2023 10-K say about Mexico?", ticker="WMT", fiscal_year=2023)
    assert result.outcome == "reject"
    assert result.override.options == ["2024", "2025", "2026"]
    assert "2024, 2025, 2026" in result.override.reason


def test_the_page_filters_year_settles_a_question_with_no_year() -> None:
    # The agent fills the page's year into the call before the check; the check agrees with it.
    result = run(
        "What are the main risks?",
        ticker="AAPL",
        fiscal_year=2024,
        page_ticker="AAPL",
        page_year=2024,
    )
    assert result.outcome == "pass" and result.arguments["fiscal_year"] == 2024
    # The model sent another year than the page's: the page wins, as for the fact tool.
    other = run(
        "What are the main risks?",
        ticker="AAPL",
        fiscal_year=2023,
        page_ticker="AAPL",
        page_year=2024,
    )
    assert other.outcome == "repair" and other.arguments["fiscal_year"] == 2024


def test_without_a_company_the_year_is_not_checked() -> None:
    result = run("Which companies mention tariffs?", ticker=None, fiscal_year=2023)
    assert result.outcome == "pass" and result.arguments.get("fiscal_year") == 2023
    assert "no company" in result.override.reason


def test_the_record_names_the_tool() -> None:
    result = run("How does Apple describe its services business?")
    assert result.override.tool == "search_filings"
