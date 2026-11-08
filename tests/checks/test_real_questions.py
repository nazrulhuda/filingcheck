"""The whole chain over every real question in the repo, each with its intended company and
year, and over the ten Day 23 review probes. A question about one company and one year, sent
with those arguments, must pass every check unless it is a trap; the probes must come out as
the review expects. Development probes only: none of these is an evaluation question."""

import json
from pathlib import Path
from typing import Any

import pytest

from filingcheck.checks import CHECKS, CheckContext, CheckedCall, run_checks
from tests.checks.conftest import COMPANIES, MANIFEST, NOT_COVERED

REPO = Path(__file__).resolve().parents[2]
LATEST: dict[str, int] = {}
for filing in MANIFEST.filings:
    LATEST[filing.ticker] = max(LATEST.get(filing.ticker, 0), filing.fiscal_year)


def chain(
    question: str,
    ticker: str,
    year: int,
    metric: str = "revenue",
    page_ticker: str | None = None,
    page_year: int | None = None,
) -> tuple[Any, list[Any]]:
    call = CheckedCall(
        "get_financial_fact", {"ticker": ticker, "fiscal_year": year, "metric": metric}
    )
    context = CheckContext(
        question=question,
        ticker=page_ticker,
        fiscal_year=page_year,
        companies=COMPANIES,
        not_covered=NOT_COVERED,
        manifest=MANIFEST,
    )
    return run_checks(call, context, CHECKS)


def real_questions() -> list[object]:
    cases = []
    for name in ("examples.jsonl", "page_examples.jsonl", "retrieval.jsonl"):
        for line in (REPO / "eval" / "questions" / name).read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            ticker = row.get("company") or row.get("ticker")
            if ticker is None:
                continue  # trap-001 names no company on purpose
            cases.append(
                pytest.param(
                    row["question"],
                    ticker,
                    row.get("fiscal_year") or LATEST[ticker],
                    row.get("metric") or "revenue",
                    id=row["id"],
                )
            )
    return cases


EXPECTED_NOT_PASS = {"trap-005": [("metric", "reject")]}  # the quarterly Goldman question


@pytest.mark.parametrize(("question", "ticker", "year", "metric"), real_questions())
def test_every_real_question_passes_unless_it_is_a_trap(
    question: str, ticker: str, year: int, metric: str, request: pytest.FixtureRequest
) -> None:
    _, overrides = chain(question, ticker, year, metric)
    odd = [(o.check, o.outcome) for o in overrides if o.outcome != "pass"]
    qid = request.node.callspec.id
    assert odd == EXPECTED_NOT_PASS.get(qid, []), (
        f"{question!r}: {[o.reason for o in overrides if o.outcome != 'pass']}"
    )


def test_the_real_question_files_are_the_ones_meant() -> None:
    assert len(real_questions()) == 50  # 6 + 5 + 40 questions, trap-001 left out


# ---------------------------------------------------------------- the ten review probes


def test_probe_aws_revenue_is_a_segment_reject() -> None:
    call, overrides = chain("How much revenue did AWS make in 2025?", "AMZN", 2025)
    assert call is None and [(o.check, o.outcome) for o in overrides][-1] == ("segment", "reject")


def test_probe_tesla_is_a_company_reject_with_the_25_listed() -> None:
    call, overrides = chain("What was Tesla's revenue in 2025?", "AAPL", 2025)
    assert call is None and overrides[-1].check == "company"
    assert len(overrides[-1].options) == 25


def test_probe_apple_fiscal_2023_is_a_year_reject_with_the_pinned_years() -> None:
    call, overrides = chain("What was Apple's revenue in fiscal 2023?", "AAPL", 2023)
    assert call is None and overrides[-1].check == "fiscal_year"
    assert overrides[-1].options == ["2024", "2025", "2026"]


def test_probe_costco_ebitda_is_a_metric_reject_with_the_13_metrics() -> None:
    call, overrides = chain("What is Costco's EBITDA for fiscal 2025?", "COST", 2025, "net_income")
    assert call is None and overrides[-1].check == "metric"
    assert len(overrides[-1].options) == 13


def test_probe_walmart_year_ended_jan_31_2026_is_fiscal_2026() -> None:
    question = "What was Walmart's revenue in the year ended January 31, 2026?"
    call, overrides = chain(question, "WMT", 2025)
    assert call is not None and call.arguments["fiscal_year"] == 2026
    assert [(o.check, o.outcome) for o in overrides if o.outcome != "pass"] == [
        ("fiscal_year", "repair")
    ]
    call, overrides = chain(question, "WMT", 2026)
    assert all(o.outcome == "pass" for o in overrides)


def test_probe_its_revenue_last_year_follows_the_page_filter() -> None:
    call, overrides = chain("What was its revenue last year?", "AAPL", 2025, page_ticker="WMT")
    assert call is not None
    assert (call.arguments["ticker"], call.arguments["fiscal_year"]) == ("WMT", 2026)
    assert [(o.check, o.outcome) for o in overrides if o.outcome != "pass"] == [
        ("company", "repair"),
        ("fiscal_year", "repair"),
    ]


def test_probe_apples_revenue_with_the_walmart_filter_is_rejected_with_both() -> None:
    call, overrides = chain("What was Apple's revenue last year?", "AAPL", 2026, page_ticker="WMT")
    assert call is None and overrides[-1].check == "company"
    assert overrides[-1].options == ["AAPL", "WMT"]


def test_probe_microsoft_calendar_2025_is_rejected_with_the_two_fiscal_years() -> None:
    call, overrides = chain("What was Microsoft's revenue in calendar 2025?", "MSFT", 2025)
    assert call is None and overrides[-1].check == "fiscal_year"
    assert overrides[-1].options == ["2025", "2026"]
    assert "ask the user which fiscal year" in overrides[-1].reason
    assert "Jul 1, 2024 to Jun 30, 2025" in overrides[-1].reason
    assert "Jul 1, 2025 to Jun 30, 2026" in overrides[-1].reason


def test_probe_the_company_that_makes_the_iphone_passes() -> None:
    _, overrides = chain(
        "What was the revenue in 2025 for the company that makes the iPhone?", "AAPL", 2025
    )
    assert all(o.outcome == "pass" for o in overrides)


def test_probe_two_sentences_pass_for_net_income_and_reject_the_quarterly_revenue() -> None:
    question = (
        "What was Apple's net income in fiscal 2025? Also, what did it report as revenue for "
        "the quarter?"
    )
    _, overrides = chain(question, "AAPL", 2025, "net_income")
    assert all(o.outcome == "pass" for o in overrides)
    call, overrides = chain(question, "AAPL", 2025, "revenue")
    assert call is None and overrides[-1].check == "metric"


# ---------------------------------------------------------------- the calendar rule, all companies


def test_a_december_company_reads_calendar_as_its_fiscal_year() -> None:
    call, overrides = chain("What was Coca-Cola's revenue in calendar 2025?", "KO", 2025)
    assert call is not None and all(o.outcome == "pass" for o in overrides)
    call, overrides = chain("What was Coca-Cola's revenue in calendar 2025?", "KO", 2024)
    assert call is not None and call.arguments["fiscal_year"] == 2025


def test_a_calendar_year_overlapping_one_pinned_year_offers_that_one() -> None:
    call, overrides = chain("What was Apple's revenue in calendar 2023?", "AAPL", 2024)
    assert call is None and overrides[-1].options == ["2024"]
    assert "fiscal 2023" in overrides[-1].reason  # the other overlapping year has no 10-K
