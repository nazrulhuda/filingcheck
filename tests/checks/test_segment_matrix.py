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
    "What was {c}'s total {m}, including {seg} {m}, in 2025?",
    "What was {c}'s total {m} in 2025, including the {seg} {m}?",
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
    "What was {c}'s total {m} in 2025, including {low} {m}?",
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


# ------------------------------------------------------------ an exclusion word before a segment
# "Amazon's revenue in fiscal 2024, excluding AWS" asks for a figure the 10-K data does not
# hold (the total less a segment), so it rejects at any distance from the metric word: a rule
# separate from the tie window. Each case runs with the call's metric matching its words.

EXCLUSIONS = [
    "excluding",
    "without",
    "not counting",
    "not including",
    "minus",
    "other than",
    "except",
    "ex-",
    "apart from",
    "aside from",
]
EXCLUDE_SHAPES = [
    "What was {c}'s {m} in fiscal 2024, {x}{seg}?",
    "What was {c}'s {m} in fiscal 2024 {x}{seg}?",
    "What was {c}'s {m} in 2024, {x}{seg}?",
    "What was {c}'s {m}, {x}{seg}, in fiscal 2024?",
    "What was {c}'s {m} {x}{seg} in fiscal 2024?",
    "{X}{seg}, what was {c}'s {m} in 2024?",
]
CALL_METRIC = {
    "revenue": "revenue",
    "operating income": "operating_income",
    "net income": "net_income",
}


def exclusion(word: str) -> str:
    return word if word.endswith("-") else word + " "


def exclude_cases() -> list[Any]:
    out = []
    for (ticker, company, segment), metric, word, shape in itertools.product(
        SEGMENTS, METRICS, EXCLUSIONS, EXCLUDE_SHAPES
    ):
        x = exclusion(word)
        question = shape.format(c=company, m=metric, seg=segment, x=x, X=x[0].upper() + x[1:])
        out.append(
            pytest.param(
                question,
                ticker,
                segment,
                CALL_METRIC[metric],
                id=f"{segment}-{metric}-{word}-{EXCLUDE_SHAPES.index(shape)}",
            )
        )
    return out


@pytest.mark.parametrize(("question", "ticker", "segment", "metric"), exclude_cases())
def test_an_exclusion_word_before_a_segment_rejects_at_any_distance(
    question: str, ticker: str, segment: str, metric: str
) -> None:
    result = run_check(CHECK, question, ticker=ticker, metric=metric)
    assert result.outcome == "reject", question
    assert segment in result.override.reason


@pytest.mark.parametrize(
    "question",
    [
        "What was Amazon's revenue in fiscal 2024, excluding AWS?",
        "What was Amazon's revenue in 2024, not counting AWS?",
        "What was Apple's revenue in fiscal 2024, excluding services?",
        "What was Microsoft's revenue in fiscal 2024 without office?",
        "What was Amazon's revenue in 2024 apart from AWS?",
        "What was Amazon's revenue in 2024 aside from AWS?",
    ],
)
def test_the_review_examples_and_lower_case_words_after_an_exclusion_reject(question: str) -> None:
    ticker = {"Amazon": "AMZN", "Apple": "AAPL", "Microsoft": "MSFT"}[question.split()[2][:-2]]
    assert run_check(CHECK, question, ticker=ticker).outcome == "reject", question


@pytest.mark.parametrize(
    ("question", "ticker"),
    [
        ("What was Amazon's revenue in fiscal 2024, excluding taxes?", "AMZN"),
        ("Besides AWS, what does Amazon sell? What was its revenue in 2024?", "AMZN"),
        ("What was Coca-Cola's revenue in fiscal 2024, excluding AWS?", "KO"),
        ("Without counting on AWS, Amazon grew. What was its net income in 2024?", "AMZN"),
    ],
)
def test_an_exclusion_without_a_segment_of_the_company_in_the_metric_sentence_passes(
    question: str, ticker: str
) -> None:
    metric = "net_income" if "net income" in question else "revenue"
    assert run_check(CHECK, question, ticker=ticker, metric=metric).outcome == "pass", question
