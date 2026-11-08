"""A generated matrix for the segment tie: a segment name within three words of a metric word,
in one sentence, is a segment question and is rejected; "including" or "included" breaks the
tie; "excluding" keeps it; a segment far from any metric word, in another sentence, or of
another company, is not a segment question."""

import itertools

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


def cases(templates: list[str]) -> list[object]:
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
