"""A generated matrix for the segment tie: a segment name within three words of a metric word,
in one sentence, is a segment question and is rejected; "including" or "included" breaks the
tie; "excluding" keeps it; a segment far from any metric word, in another sentence, or of
another company, is not a segment question. A single ordinary word ("Services", "Office")
also counts in lower case when it sits directly before the metric word ("services revenue"),
and only there."""

import itertools
from typing import Any

import pytest

from filingcheck.checks.segment import SegmentCheck
from tests.checks.conftest import run_check

SEGMENTS = [
    ("AMZN", "Amazon", "AWS"),
    ("AMZN", "Amazon", "Amazon Web Services"),
    ("AAPL", "Apple", "iPhone"),
    ("AAPL", "Apple", "Services"),
    ("MSFT", "Microsoft", "Intelligent Cloud"),
    ("MSFT", "Microsoft", "Office"),
    ("NVDA", "Nvidia", "Data Center"),
    ("WMT", "Walmart", "Sam's Club"),
    ("JPM", "JPMorgan", "Commercial & Investment Bank"),
    ("MS", "Morgan Stanley", "Wealth Management"),
]
METRICS = ["revenue", "operating income", "net income"]
TIED = [
    "What was {seg} {m} in 2025?",
    "What was {seg}'s {m} in 2025?",
    "How much {m} did {seg} make in 2025?",
    "What was the {m} of {seg} in 2025?",
    "What was {c}'s {m} from {seg} in 2025?",
    "What was {m} in the {seg} segment in 2025?",
    "What was {c}'s {m} excluding {seg}?",
    "What was {seg}'s total {m} in 2025?",
]
NOT_TIED = [
    "What was {c}'s total {m}, including {seg}, in 2025?",
    "What was {c}'s {m} in 2025, {seg} included?",
    "What was the {m} in 2025 for the company that makes the {seg}?",
    "What was {c}'s {m} in fiscal 2025? Also, how did {seg} do?",
    "Which customers use {c}'s {seg} products? Give {c}'s {m} too.",
]
CHECK = SegmentCheck()


def cases(templates: list[str]) -> list[Any]:
    out = []
    for (ticker, company, segment), metric, template in itertools.product(
        SEGMENTS, METRICS, templates
    ):
        question = template.format(c=company, seg=segment, m=metric)
        out.append(
            pytest.param(
                question, ticker, segment, id=f"{segment}-{metric}-{templates.index(template)}"
            )
        )
    return out


@pytest.mark.parametrize(("question", "ticker", "segment"), cases(TIED))
def test_a_segment_tied_to_the_number_is_rejected(question: str, ticker: str, segment: str) -> None:
    result = run_check(CHECK, question, ticker=ticker)
    assert result.outcome == "reject", question
    assert segment in result.override.reason


@pytest.mark.parametrize(("question", "ticker", "segment"), cases(NOT_TIED))
def test_a_segment_not_tied_to_the_number_passes(question: str, ticker: str, segment: str) -> None:
    result = run_check(CHECK, question, ticker=ticker)
    assert result.outcome == "pass", question


@pytest.mark.parametrize(("question", "ticker", "segment"), cases(TIED[:3]))
def test_another_companys_segment_is_not_a_segment(
    question: str, ticker: str, segment: str
) -> None:
    other = "KO" if ticker != "KO" else "PFE"
    assert run_check(CHECK, question, ticker=other).outcome == "pass", question


# A single ordinary word in lower case: tied only directly before the metric word.
AS_WRITTEN = [(t, c, seg) for t, c, seg in SEGMENTS if " " not in seg and not seg.isupper()]
LOWER_TIED = [
    "What was {c}'s {low} {m} in 2025?",
    "How much {low} {m} did {c} report in 2025?",
]
LOWER_LOOSE = [
    "What was {c}'s {m} from products and {low} in 2025?",
    "What was {c}'s {m} in 2025? Its {low} business grew.",
    "Which {low} does {c} sell, and what was its {m} in 2025?",
]


def lower_cases(templates: list[str]) -> list[Any]:
    out = []
    for (ticker, company, segment), metric, template in itertools.product(
        AS_WRITTEN, METRICS, templates
    ):
        question = template.format(c=company, low=segment.lower(), m=metric)
        out.append(
            pytest.param(
                question, ticker, segment, id=f"low-{segment}-{metric}-{templates.index(template)}"
            )
        )
    return out


def test_the_lower_case_matrix_covers_the_single_ordinary_words() -> None:
    assert sorted(seg for _, _, seg in AS_WRITTEN) == ["Office", "Services", "iPhone"]


@pytest.mark.parametrize(("question", "ticker", "segment"), lower_cases(LOWER_TIED))
def test_a_lower_case_segment_word_before_the_metric_is_rejected(
    question: str, ticker: str, segment: str
) -> None:
    result = run_check(CHECK, question, ticker=ticker)
    assert result.outcome == "reject", question
    assert segment in result.override.reason


@pytest.mark.parametrize(("question", "ticker", "segment"), lower_cases(LOWER_LOOSE))
def test_a_lower_case_segment_word_elsewhere_passes(
    question: str, ticker: str, segment: str
) -> None:
    assert run_check(CHECK, question, ticker=ticker).outcome == "pass", question
