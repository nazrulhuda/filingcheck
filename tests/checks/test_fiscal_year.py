"""The fiscal-year check on the real manifest: years the question states, relative words, the
page filter, years with no pinned filing, and the period dates in every reason."""

from datetime import date
from typing import Any

import pytest

from filingcheck.checks import CheckResult
from filingcheck.checks.fiscal_year import FiscalYearCheck, period_text, read_years
from tests.checks.conftest import MANIFEST, run_check

CHECK = FiscalYearCheck()


def run(question: str, **kwargs: Any) -> CheckResult:
    return run_check(CHECK, question, **kwargs)


# ---------------------------------------------------------------- reading the question


@pytest.mark.parametrize(
    ("question", "ticker", "years"),
    [
        ("What was Walmart's revenue for 2025?", "WMT", {2025}),
        ("Revenue in fiscal 2025?", "WMT", {2025}),
        ("FY2025 revenue?", "WMT", {2025}),
        ("FY25 revenue?", "WMT", {2025}),
        ("FY 2025 revenue?", "WMT", {2025}),
        ("Revenue for fiscal year 2025?", "WMT", {2025}),
        ("Revenue in fiscal '25?", "WMT", {2025}),
        ("Revenue for the year ended January 31, 2025?", "WMT", {2025}),
        ("Revenue for the year ended Jan. 31, 2025?", "WMT", {2025}),
        ("Revenue for the year ended September 27, 2025?", "AAPL", {2025}),
        (
            "By what percentage did revenue grow from fiscal 2025 to fiscal 2026?",
            "WMT",
            {2025, 2026},
        ),
        ("Revenue from 2025 to 2026?", "WMT", {2025, 2026}),
        ("Revenue in fiscal years 2024 and 2025?", "WMT", {2024, 2025}),
        ("What was Goldman Sachs's quarterly net revenue in Q3 2025?", "GS", {2025}),
        ("Revenue in the 10-K filed on March 15, 2026?", "WMT", set()),  # a filing date
        ("What was revenue?", "WMT", set()),
        ("Revenue of $2025 million?", "WMT", set()),  # an amount, not a year
    ],
)
def test_the_years_a_question_states(question: str, ticker: str, years: set[int]) -> None:
    assert set(read_years(question, ticker, MANIFEST)) == years


@pytest.mark.parametrize(
    ("question", "ticker", "years"),
    [
        ("What was Nvidia's net income last year?", "NVDA", {2026}),
        ("Nvidia's latest net income?", "NVDA", {2026}),
        ("Nvidia's most recent net income?", "NVDA", {2026}),
        ("Nvidia's net income this year?", "NVDA", {2026}),
        ("Net income in the latest report?", "NVDA", {2026}),
        ("Net income two years ago?", "NVDA", {2024}),
        ("Net income the year before?", "NVDA", {2025}),
        ("Apple's net income last year?", "AAPL", {2026}),
    ],
)
def test_relative_words_resolve_to_the_companys_pinned_years(
    question: str, ticker: str, years: set[int]
) -> None:
    assert set(read_years(question, ticker, MANIFEST)) == years


def test_a_relative_word_says_why_it_was_read_that_way() -> None:
    years = read_years("What was Nvidia's net income last year?", "NVDA", MANIFEST)
    assert "'last year'" in years[2026] and "latest annual report" in years[2026]


# ---------------------------------------------------------------- the period dates


def test_the_period_dates_come_from_the_manifest() -> None:
    assert period_text("WMT", 2025, MANIFEST) == "fiscal 2025 (Feb 1, 2024 to Jan 31, 2025)"
    assert period_text("NVDA", 2026, MANIFEST) == "fiscal 2026 (Jan 27, 2025 to Jan 25, 2026)"
    # The earliest pinned year has no earlier filing to start from; the facts give the start.
    assert period_text("NVDA", 2024, MANIFEST) == "fiscal 2024 (year ended Jan 28, 2024)"


def test_the_earliest_years_start_comes_from_the_facts_when_they_are_given() -> None:
    from filingcheck.facts.lookup import FilingRef
    from tests.facts.test_lookup import FakeFacts, duration

    nvda = FilingRef(
        ticker="NVDA",
        fiscal_year=2024,
        accession="0001045810-24-000029",
        period_of_report=date(2024, 1, 28),
        source_url="https://www.sec.gov/x",
        revenue_rule="standard",
    )
    cash = duration(
        "us-gaap:NetCashProvidedByUsedInOperatingActivities",
        "28090000000",
        date(2023, 1, 30),
        date(2024, 1, 28),
    )
    text = period_text("NVDA", 2024, MANIFEST, FakeFacts([cash], filing=nvda))
    assert text == "fiscal 2024 (Jan 30, 2023 to Jan 28, 2024)"


# ---------------------------------------------------------------- the rules


def test_rule_a_the_stated_year_equals_the_argument_and_passes_with_the_period() -> None:
    result = run("What was Walmart's revenue for 2025?", ticker="WMT", fiscal_year=2025)
    assert result.outcome == "pass"
    record = result.override
    assert (record.check, record.argument, record.sent, record.used) == (
        "fiscal_year",
        "fiscal_year",
        2025,
        2025,
    )
    assert "fiscal 2025 (Feb 1, 2024 to Jan 31, 2025)" in record.reason


def test_rule_b_a_different_argument_is_repaired_to_the_stated_year() -> None:
    result = run("What was Walmart's revenue for 2025?", ticker="WMT", fiscal_year=2026)
    assert result.outcome == "repair"
    assert result.arguments["fiscal_year"] == 2025
    record = result.override
    assert (record.sent, record.used) == (2026, 2025)
    assert "Feb 1, 2024 to Jan 31, 2025" in record.reason


def test_rule_c_a_relative_word_is_repaired_to_the_latest_pinned_year() -> None:
    result = run("What was Nvidia's net income last year?", ticker="NVDA", fiscal_year=2025)
    assert result.outcome == "repair"
    assert result.arguments["fiscal_year"] == 2026
    reason = result.override.reason
    assert "'last year' read as the latest annual report" in reason
    assert "fiscal 2026 (Jan 27, 2025 to Jan 25, 2026)" in reason
    assert run("Nvidia's net income last year?", ticker="NVDA", fiscal_year=2026).outcome == "pass"


def test_rule_d_a_year_with_no_pinned_filing_is_rejected_with_the_pinned_years() -> None:
    for question, year in (
        ("What was Apple's revenue in fiscal 2023?", 2023),  # stated, not pinned
        ("What was Apple's revenue?", 2023),  # sent, not pinned
        ("What was Apple's revenue in 2021?", 2025),  # repair target not pinned
    ):
        result = run(question, ticker="AAPL", fiscal_year=year)
        assert result.outcome == "reject", question
        assert result.override.options == ["2024", "2025", "2026"]
        assert "no 10-K" in result.override.reason


def test_two_stated_years_both_pass_and_a_third_is_rejected() -> None:
    question = "By what percentage did Walmart's revenue grow from fiscal 2025 to fiscal 2026?"
    assert run(question, ticker="WMT", fiscal_year=2025).outcome == "pass"
    assert run(question, ticker="WMT", fiscal_year=2026).outcome == "pass"
    result = run(question, ticker="WMT", fiscal_year=2024)
    assert result.outcome == "reject"
    assert result.override.options == ["2025", "2026"]


def test_rule_e_no_year_and_no_filter_passes_with_a_log_line() -> None:
    result = run("What was Walmart's revenue?", ticker="WMT", fiscal_year=2024)
    assert result.outcome == "pass"
    assert "no year in the question" in result.override.reason


def test_no_year_in_the_question_follows_the_page_filter() -> None:
    assert (
        run("What was revenue?", ticker="WMT", fiscal_year=2025, page_year=2025).outcome == "pass"
    )
    result = run("What was revenue?", ticker="WMT", fiscal_year=2026, page_year=2025)
    assert result.outcome == "repair"
    assert result.arguments["fiscal_year"] == 2025
    assert "selected fiscal 2025" in result.override.reason


def test_a_stated_or_relative_year_that_differs_from_the_filter_is_rejected_with_both() -> None:
    result = run("What was revenue in 2026?", ticker="WMT", fiscal_year=2026, page_year=2025)
    assert result.outcome == "reject"
    assert result.override.options == ["2025", "2026"]
    result = run("Net income last year?", ticker="NVDA", fiscal_year=2026, page_year=2025)
    assert result.outcome == "reject"
    assert result.override.options == ["2025", "2026"]
    # The stated year equal to the filter is simply rule (a).
    assert run("Revenue in 2025?", ticker="WMT", fiscal_year=2025, page_year=2025).outcome == "pass"
