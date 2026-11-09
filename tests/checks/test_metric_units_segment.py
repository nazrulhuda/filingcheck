"""The metric-and-period, units and segment checks, and the order of the whole chain."""

from typing import Any

import pytest

from filingcheck.checks import CHECKS, CheckContext, CheckedCall, run_checks
from filingcheck.checks.metric import MetricCheck
from filingcheck.checks.segment import SegmentCheck
from filingcheck.checks.units import UnitsCheck
from filingcheck.facts.metrics import METRICS
from tests.checks.conftest import COMPANIES, MANIFEST, NOT_COVERED, run_check

METRIC, UNITS, SEGMENT = MetricCheck(), UnitsCheck(), SegmentCheck()


# ---------------------------------------------------------------- metric and period


@pytest.mark.parametrize(
    "question",
    [
        "What was Goldman Sachs's quarterly net revenue in Q3 2025?",
        "Goldman's Q4 revenue?",
        "Revenue in the third quarter of 2025?",
        "Revenue for the three months ended June 30, 2025?",
        "Revenue for the six months ended June 30?",
        "Nine months revenue?",
        "Revenue in the first half of 2025?",
        "Half-year revenue?",
        "H1 2025 revenue?",
        "H2 revenue?",
    ],
)
def test_quarter_words_are_rejected_before_the_tool_runs(question: str) -> None:
    result = run_check(METRIC, question, ticker="GS")
    assert result.outcome == "reject"
    assert result.override.reason.startswith("the dataset has annual figures only (10-K)")


@pytest.mark.parametrize(
    "question",
    [
        "What was Apple's EBITDA in fiscal 2025?",
        "Apple's free cash flow?",
        "Apple's gross margin?",
        "Apple's operating margin?",
        "Apple's market cap?",
        "Apple's share price?",
        "Apple's dividend?",
        "How many employees does Apple have?",
        "Apple's headcount?",
        "Apple's backlog?",
        "Microsoft's ARR?",
    ],
)
def test_unsupported_metrics_are_rejected_with_the_13_supported(question: str) -> None:
    result = run_check(METRIC, question, metric="net_income")
    assert result.outcome == "reject"
    assert result.override.options == sorted(METRICS)
    assert len(result.override.options) == 13


def test_an_unsupported_word_passes_when_the_question_also_names_the_argument_metric() -> None:
    question = "What were Apple's revenue and EBITDA in fiscal 2025?"
    assert run_check(METRIC, question, metric="revenue").outcome == "pass"
    assert run_check(METRIC, question, metric="net_income").outcome == "reject"


@pytest.mark.parametrize(
    ("question", "ticker"),
    [
        ("What was Apple's revenue in fiscal 2025?", "AAPL"),
        ("How much net revenue did JPMorgan report in 2025?", "JPM"),  # the bank rule
        ("Goldman's net revenues in 2025?", "GS"),
        ("What were Apple's total net sales in fiscal 2025?", "AAPL"),
        ("Apple's quartz revenue?", "AAPL"),  # 'quartz' is not a quarter word
    ],
)
def test_plain_annual_questions_pass(question: str, ticker: str) -> None:
    result = run_check(METRIC, question, ticker=ticker)
    assert result.outcome == "pass"
    assert result.override.check == "metric" and result.override.argument == "metric"


# ---------------------------------------------------------------- units


@pytest.mark.parametrize(
    ("question", "scale"),
    [
        ("Give Microsoft's FY2025 total assets in millions.", "millions"),
        ("Total assets in billions?", "billions"),
        ("Total assets in thousands?", "thousands"),
        ("Total assets in $M?", "millions"),
        ("Total assets in $B?", "billions"),
        ("Total assets ($ in millions)?", "millions"),
    ],
)
def test_a_requested_scale_passes_and_is_attached_for_the_tool_result(
    question: str, scale: str
) -> None:
    result = run_check(UNITS, question, ticker="MSFT", metric="total_assets")
    assert result.outcome == "pass"
    assert result.annotations == {"requested_scale": scale}
    assert result.arguments["metric"] == "total_assets"  # the stored value is never changed
    assert scale in result.override.reason


def test_no_scale_asked_for_attaches_nothing() -> None:
    result = run_check(UNITS, "Microsoft's FY2025 total assets?", ticker="MSFT")
    assert result.outcome == "pass" and result.annotations == {}


# ---------------------------------------------------------------- segments


@pytest.mark.parametrize(
    ("question", "ticker", "segment"),
    [
        ("What was AWS's operating income in 2025?", "AMZN", "AWS"),
        ("Amazon Web Services revenue in 2025?", "AMZN", "Amazon Web Services"),
        ("Amazon's North America revenue?", "AMZN", "North America"),
        ("Apple's iPhone revenue in fiscal 2025?", "AAPL", "iPhone"),
        ("Apple's Services revenue?", "AAPL", "Services"),
        ("Microsoft's Intelligent Cloud revenue?", "MSFT", "Intelligent Cloud"),
        ("Nvidia's Data Center revenue?", "NVDA", "Data Center"),
        ("Walmart's Sam's Club revenue?", "WMT", "Sam's Club"),
        ("Meta's Reality Labs loss?", "META", "Reality Labs"),
        ("JPMorgan's Consumer & Community Banking revenue?", "JPM", "Consumer & Community Banking"),
        ("Morgan Stanley's Wealth Management revenue?", "MS", "Wealth Management"),
    ],
)
def test_a_segment_question_is_rejected_with_the_segment_named(
    question: str, ticker: str, segment: str
) -> None:
    result = run_check(SEGMENT, question, ticker=ticker)
    assert result.outcome == "reject"
    assert f"segment figures ({segment})" in result.override.reason
    assert "company totals only" in result.override.reason


def test_a_question_about_the_total_that_mentions_a_segment_passes() -> None:
    result = run_check(SEGMENT, "Amazon's total revenue, including AWS, in 2025?", ticker="AMZN")
    assert result.outcome == "pass"
    assert "AWS" in result.override.reason


def test_segments_belong_to_the_argument_company_and_ordinary_words_are_not_segments() -> None:
    assert run_check(SEGMENT, "AWS revenue?", ticker="MSFT").outcome == "pass"
    assert (
        run_check(SEGMENT, "Apple's services and products revenue?", ticker="AAPL").outcome
        == "pass"
    )
    assert run_check(SEGMENT, "Apple's revenue in fiscal 2025?", ticker="AAPL").outcome == "pass"


def test_every_listed_segment_is_in_the_company_list() -> None:
    by_ticker = {c.ticker: c for c in COMPANIES}
    assert "AWS" in by_ticker["AMZN"].segments
    assert "Commercial & Investment Bank" in by_ticker["JPM"].segments
    assert by_ticker["NFLX"].segments == []


# ---------------------------------------------------------------- the chain


def chain(question: str, **arguments: Any) -> Any:
    call = CheckedCall(
        "get_financial_fact",
        {"ticker": "AAPL", "fiscal_year": 2025, "metric": "revenue", **arguments},
    )
    context = CheckContext(
        question=question,
        ticker=None,
        fiscal_year=None,
        companies=COMPANIES,
        not_covered=NOT_COVERED,
        manifest=MANIFEST,
    )
    return run_checks(call, context, CHECKS)


def test_the_checks_run_in_the_spec_order() -> None:
    assert [c.name for c in CHECKS] == ["company", "fiscal_year", "metric", "units", "segment"]
    call, overrides = chain("What were Apple's total net sales in fiscal 2025?")
    assert call is not None
    assert [(o.check, o.outcome) for o in overrides] == [
        ("company", "pass"),
        ("fiscal_year", "pass"),
        ("metric", "pass"),
        ("units", "pass"),
        ("segment", "pass"),
    ]


def test_a_company_reject_stops_the_chain() -> None:
    call, overrides = chain("How much net revenue did Morgan report in Q3 2025?", ticker="MS")
    assert call is None
    assert [o.check for o in overrides] == ["company"]


def test_a_repair_reaches_the_checks_after_it() -> None:
    # The company is repaired to WMT, so the year check reads Walmart's pinned years.
    call, overrides = chain("What was Walmart's revenue for 2025?", ticker="AAPL", fiscal_year=2026)
    assert call is not None and call.arguments["ticker"] == "WMT"
    assert call.arguments["fiscal_year"] == 2025
    assert "Feb 1, 2024 to Jan 31, 2025" in overrides[1].reason


def test_a_requested_scale_reaches_the_checked_call() -> None:
    call, _ = chain("Give Microsoft's FY2025 total assets in millions.", ticker="MSFT")
    assert call is not None and call.annotations == {"requested_scale": "millions"}


# ---------------------------------------------------------------- tie, including, sentences


def test_a_segments_own_total_is_still_a_segment_question() -> None:
    result = run_check(SEGMENT, "What was AWS's total revenue in 2025?", ticker="AMZN")
    assert result.outcome == "reject" and "AWS" in result.override.reason


def test_including_breaks_the_tie_and_excluding_keeps_it() -> None:
    included = "Microsoft's revenue in 2025, Office included?"
    assert run_check(SEGMENT, included, ticker="MSFT").outcome == "pass"
    including = "Amazon's total revenue, including AWS, in 2025?"
    assert run_check(SEGMENT, including, ticker="AMZN").outcome == "pass"
    excluding = "What was Amazon's revenue excluding AWS in 2025?"
    assert run_check(SEGMENT, excluding, ticker="AMZN").outcome == "reject"


def test_a_segment_far_from_the_metric_word_or_in_another_sentence_is_not_tied() -> None:
    far = "What was the revenue in 2025 for the company that makes the iPhone?"
    assert run_check(SEGMENT, far, ticker="AAPL").outcome == "pass"
    other = "What was Apple's revenue in fiscal 2025? Also, how did Services do?"
    assert run_check(SEGMENT, other, ticker="AAPL").outcome == "pass"
    text_only = "Which kinds of customers use Nvidia's data center platforms?"
    assert run_check(SEGMENT, text_only, ticker="NVDA").outcome == "pass"


def test_the_metric_check_looks_at_the_sentences_about_the_calls_metric() -> None:
    two = (
        "What was Apple's net income in fiscal 2025? Also, what did it report as revenue for "
        "the quarter?"
    )
    assert run_check(METRIC, two, metric="net_income").outcome == "pass"
    assert run_check(METRIC, two, metric="revenue").outcome == "reject"
    follow_up = "What was Goldman's net revenue in 2025? I mean for Q3."
    assert run_check(METRIC, follow_up, ticker="GS", metric="revenue").outcome == "reject"
    ebitda_too = "What was Apple's revenue in fiscal 2025? And what is its EBITDA?"
    assert run_check(METRIC, ebitda_too, metric="revenue").outcome == "pass"
    swapped = "What was Apple's revenue in fiscal 2025? What about net income in Q4?"
    assert run_check(METRIC, swapped, metric="revenue").outcome == "pass"
    assert run_check(METRIC, swapped, metric="net_income").outcome == "reject"
