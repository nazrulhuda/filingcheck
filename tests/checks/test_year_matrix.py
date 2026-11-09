"""A generated matrix for the fiscal-year reader: every strong way of naming a year, in every
sentence shape, for companies with five different year ends, must be read as that year; every
weak cue (a date after "on", "to", "at", "compared to", a filing date) must count for nothing;
calendar years are read apart. Hand-picked sentences hide blind spots; a matrix does not."""

import itertools
from datetime import date
from typing import Any

import pytest

from filingcheck.checks.fiscal_year import read_calendar_years, read_years
from tests.checks.conftest import MANIFEST

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
