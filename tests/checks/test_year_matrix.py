"""A generated matrix for the fiscal-year reader: every strong way of naming a year, in every
sentence shape, for companies with five different year ends, must be read as that year; every
weak cue (a date after "on", "to", "at", "compared to", a filing date) must count for nothing;
calendar years are read apart; a date that is no fiscal year end of the company, for all 25
companies, is rejected with "ask the user", never repaired; a range must be one whole fiscal
year. Hand-picked sentences hide blind spots; a matrix does not."""

import calendar
import itertools
from datetime import date, timedelta
from typing import Any

import pytest

from filingcheck.checks.fiscal_year import FiscalYearCheck, read_calendar_years, read_years
from tests.checks.conftest import COMPANIES, MANIFEST, run_check

PINNED = {
    ticker: {f.fiscal_year: f.period_of_report for f in MANIFEST.filings if f.ticker == ticker}
    for ticker in ("WMT", "AAPL", "KO", "NVDA", "MSFT")
}
NAMES = {
    "WMT": "Walmart",
    "AAPL": "Apple",
    "KO": "Coca-Cola",
    "NVDA": "Nvidia",
    "MSFT": "Microsoft",
}


def long(day: date) -> str:
    return f"{day:%B} {day.day}, {day.year}"


def short(day: date) -> str:
    return f"{day:%b}. {day.day}, {day.year}"


def year_forms(year: int, end: date) -> list[str]:
    """Every strong way of naming one fiscal year."""
    two = f"{year % 100:02d}"
    return [
        f"{year}",
        f"fiscal {year}",
        f"fiscal year {year}",
        f"FY{year}",
        f"FY {year}",
        f"FY{two}",
        f"fiscal '{two}",
        f"the year ended {long(end)}",
        f"the fiscal year ending {long(end)}",
        f"the year ended {short(end)}",
        f"the year ended {end.isoformat()}",
        f"as of {long(end)}",
    ]


TEMPLATES = [
    "What was {c}'s revenue in {y}?",
    "{c} revenue for {y}?",
    "In {y}, how much did {c} earn?",
    "Give {c}'s total assets for {y}.",
]


def strong_cases() -> list[Any]:
    cases = []
    for ticker, pinned in PINNED.items():
        for year in sorted(pinned)[-2:]:
            for form, template in itertools.product(year_forms(year, pinned[year]), TEMPLATES):
                question = template.format(c=NAMES[ticker], y=form)
                cases.append(
                    pytest.param(
                        question,
                        ticker,
                        year,
                        id=f"{ticker}-{year}-{form}-{TEMPLATES.index(template)}",
                    )
                )
    return cases


@pytest.mark.parametrize(("question", "ticker", "year"), strong_cases())
def test_every_strong_form_is_read_as_that_fiscal_year(
    question: str, ticker: str, year: int
) -> None:
    assert set(read_years(question, ticker, MANIFEST)) == {year}, question


RELATIVE = [
    ("last year", 0),
    ("the latest annual report", 0),
    ("the most recent year", 0),
    ("this year", 0),
    ("the year before", 1),
    ("the prior year", 1),
    ("two years ago", 2),
]
RELATIVE_TEMPLATES = [
    "What was {c}'s net income for {r}?",
    "How much did {c} earn {r}?",
    "{c}'s revenue, {r}?",
]


def relative_cases() -> list[Any]:
    cases = []
    for ticker, pinned in PINNED.items():
        latest = max(pinned)
        for (word, back), template in itertools.product(RELATIVE, RELATIVE_TEMPLATES):
            question = template.format(c=NAMES[ticker], r=word)
            cases.append(
                pytest.param(
                    question,
                    ticker,
                    latest - back,
                    id=f"{ticker}-{word}-{RELATIVE_TEMPLATES.index(template)}",
                )
            )
    return cases


@pytest.mark.parametrize(("question", "ticker", "year"), relative_cases())
def test_every_relative_word_resolves_to_the_companys_pinned_year(
    question: str, ticker: str, year: int
) -> None:
    assert set(read_years(question, ticker, MANIFEST)) == {year}, question


WEAK_TEMPLATES = [
    "{c} reported on {d} that revenue grew; what was it?",
    "What was {c}'s revenue compared to {d}?",
    "{c} announced on {d} its results. What was its revenue?",
    "In the 10-K filed on {d}, what was {c}'s revenue?",
    "At {d}, what did {c} report as revenue?",
    "Revenue of {c} up to {d}?",
    "What was {c}'s revenue, as reported at the {d} earnings release?",
    "What was {c}'s revenue in the 10-K dated {d}?",
]


def weak_cases() -> list[Any]:
    cases = []
    for ticker, pinned in PINNED.items():
        # A date that is not a period end, and the period end itself: the cue decides, not the date.
        dates = [date(2026, 3, 20), pinned[max(pinned)]]
        for day, template in itertools.product(dates, WEAK_TEMPLATES):
            question = template.format(c=NAMES[ticker], d=long(day))
            cases.append(
                pytest.param(
                    question, ticker, id=f"{ticker}-{day}-{WEAK_TEMPLATES.index(template)}"
                )
            )
    return cases


@pytest.mark.parametrize(("question", "ticker"), weak_cases())
def test_a_date_after_a_weak_cue_counts_for_nothing(question: str, ticker: str) -> None:
    assert read_years(question, ticker, MANIFEST) == {}, question


@pytest.mark.parametrize(
    ("question", "ticker", "years"),
    [
        ("What was Apple's revenue in fiscal 2025 compared to September 28, 2024?", "AAPL", {2025}),
        ("Walmart reported on March 20, 2026 its fiscal 2026 revenue; what was it?", "WMT", {2026}),
        ("What was Apple's revenue in the 10-K filed November 2025?", "AAPL", set()),
        ("Revenue of $2025 million?", "WMT", set()),
        ("Revenue of 2,025 million?", "WMT", set()),
        ("Q3 results?", "WMT", set()),
        ("What was Nvidia's net income for January 27, 2025 to January 25, 2026?", "NVDA", {2026}),
        ("Walmart's revenue from 2024-02-01 through 2025-01-31?", "WMT", {2025}),
        ("Nvidia net income, 2024-01-29 - 2025-01-26?", "NVDA", {2025}),
        ("Revenue from fiscal 2025 to fiscal 2026?", "WMT", {2025, 2026}),
    ],
)
def test_mixed_strong_and_weak_evidence(question: str, ticker: str, years: set[int]) -> None:
    assert set(read_years(question, ticker, MANIFEST)) == years


@pytest.mark.parametrize(
    "form", ["calendar 2025", "calendar year 2025", "CY2025", "CY 2025", "the 2025 calendar year"]
)
def test_calendar_years_are_read_apart_from_fiscal_years(form: str) -> None:
    question = f"What was Microsoft's revenue in {form}?"
    assert read_calendar_years(question) == {2025}
    assert read_years(question, "MSFT", MANIFEST) == {}  # not a fiscal-year label


# ---------------------------------------------------------------- dates that are no year end
# The oracle is each company's year-end month in companies.yaml, not the manifest's dates the
# check reads: a month end outside that month is no fiscal year end of the company.

CHECK = FiscalYearCheck()
ASK = "ask the user which fiscal year"
ODD_FORMS = [
    "What was {c}'s revenue for the year ended {d}?",
    "What was {c}'s revenue for the fiscal year ending {d}?",
    "What were {c}'s total assets as of {d}?",
    "What was {c}'s revenue for the twelve months ended {d}?",
    "What was {c}'s net income for the year ended {iso}?",
    "What was {c}'s revenue for the year ended {s}?",
]
ALL_PINNED = {
    company.ticker: {
        f.fiscal_year: f.period_of_report for f in MANIFEST.filings if f.ticker == company.ticker
    }
    for company in COMPANIES
}


def month_end(year: int, month: int) -> date:
    return date(year, month, calendar.monthrange(year, month)[1])


def odd_dates(year_end_month: int) -> list[date]:
    return [
        month_end(year, month)
        for year in range(2023, 2027)
        for month in range(1, 13)
        if month != year_end_month
    ]


@pytest.mark.parametrize("form", ODD_FORMS)
@pytest.mark.parametrize("company", COMPANIES, ids=lambda c: c.ticker)
def test_a_date_that_is_no_year_end_is_rejected_never_repaired(company: Any, form: str) -> None:
    pinned = ALL_PINNED[company.ticker]
    wrong = []
    for day in odd_dates(company.fiscal_year_end):
        question = form.format(c=company.name, d=long(day), iso=day.isoformat(), s=short(day))
        for sent in (min(pinned), max(pinned)):
            result = run_check(CHECK, question, ticker=company.ticker, fiscal_year=sent)
            if result.outcome != "reject" or ASK not in result.override.reason:
                wrong.append((question, sent, result.outcome, result.override.reason))
    assert wrong == [], wrong[:3]


@pytest.mark.parametrize("company", COMPANIES, ids=lambda c: c.ticker)
def test_a_real_year_end_is_that_fiscal_year_in_or_out_of_the_dataset(company: Any) -> None:
    pinned = ALL_PINNED[company.ticker]
    for year in range(2021, 2028):
        day = month_end(year, company.fiscal_year_end)
        question = f"What was {company.name}'s revenue for the year ended {long(day)}?"
        assert set(read_years(question, company.ticker, MANIFEST)) == {year}, question
        result = run_check(CHECK, question, ticker=company.ticker, fiscal_year=max(pinned))
        if year in pinned:
            assert result.outcome in ("pass", "repair"), question
            assert result.override.used is None or result.override.used == year
        else:
            assert result.outcome == "reject", question
            assert f"no 10-K for fiscal {year}" in result.override.reason


@pytest.mark.parametrize("company", COMPANIES, ids=lambda c: c.ticker)
def test_a_range_counts_only_as_one_whole_fiscal_year(company: Any) -> None:
    pinned = ALL_PINNED[company.ticker]
    name = company.name
    for year in sorted(pinned)[1:]:
        start, end = pinned[year - 1] + timedelta(days=1), pinned[year]
        whole = f"What was {name}'s revenue from {long(start)} to {long(end)}?"
        assert set(read_years(whole, company.ticker, MANIFEST)) == {year}, whole
        result = run_check(CHECK, whole, ticker=company.ticker, fiscal_year=year)
        assert result.outcome == "pass", whole
        for first, last in [
            (end - timedelta(days=181), end),  # the second half of the year
            (start, start + timedelta(days=181)),  # the first half
            (start + timedelta(days=92), end + timedelta(days=92)),  # a year, shifted
        ]:
            question = f"What was {name}'s revenue from {long(first)} to {long(last)}?"
            result = run_check(CHECK, question, ticker=company.ticker, fiscal_year=year)
            assert result.outcome == "reject" and ASK in result.override.reason, question


@pytest.mark.parametrize(
    ("question", "ticker", "sent", "options", "said"),
    [
        (
            "What was Walmart's revenue for the year ended December 31, 2025?",
            "WMT",
            2026,
            ["2026"],
            ["no fiscal year of WMT ends on Dec 31, 2025", "Feb 1, 2025 to Jan 31, 2026"],
        ),
        (
            "What were Apple's total assets as of December 31, 2024?",
            "AAPL",
            2025,
            ["2025"],
            ["no fiscal year of AAPL ends on Dec 31, 2024", "Sep 29, 2024 to Sep 27, 2025"],
        ),
        (
            "What was Coca-Cola's revenue from January 1, 2025 to June 30, 2025?",
            "KO",
            2024,
            ["2025"],
            ["Jan 1, 2025 to Jun 30, 2025 is not one of KO's fiscal years"],
        ),
        (
            "What was Microsoft's revenue for the year ended December 31, 2025?",
            "MSFT",
            2026,
            ["2026"],
            ["no fiscal year of MSFT ends on Dec 31, 2025", "Jul 1, 2025 to Jun 30, 2026"],
        ),
    ],
)
def test_the_reject_names_the_date_the_real_periods_and_the_overlapping_year(
    question: str, ticker: str, sent: int, options: list[str], said: list[str]
) -> None:
    result = run_check(CHECK, question, ticker=ticker, fiscal_year=sent)
    assert result.outcome == "reject"
    assert result.override.options == options
    for words in [*said, ASK]:
        assert words in result.override.reason, result.override.reason
