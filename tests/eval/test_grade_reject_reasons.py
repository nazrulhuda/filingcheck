"""The grader reads a refusal written in a check's own reject words (the Day 39 review).

Every reject reason in `filingcheck/checks/` is produced here by running the check itself, and
marked as a refusal (the data does not hold it), an ask (the user must choose) or a retry (the
model must call again with a valid argument; not a reply). A refusal must be read as a decline;
an ask or a retry must not. The reject call sites are counted in the source, so a reject added
later without a case here fails the count.
"""

import ast
from pathlib import Path
from typing import Any, Literal

import pytest

from filingcheck.checks.company import CompanyCheck
from filingcheck.checks.fiscal_year import FiscalYearCheck
from filingcheck.checks.metric import MetricCheck
from filingcheck.checks.segment import SegmentCheck
from filingcheck.eval.grade import declines, grade
from tests.checks.conftest import run_check
from tests.eval.test_grade import question, row

Kind = Literal["refusal", "ask", "retry"]
CHECKS_DIR = Path("filingcheck/checks")
# (module, kind, check, question, run_check arguments, a fixed part of the reason)
CASES: list[tuple[str, Kind, Any, str, dict[str, Any], str]] = [
    (
        "company",
        "refusal",
        CompanyCheck(),
        "What was Tesla's revenue in 2024?",
        {},
        "is not one of the 25 companies in the dataset",
    ),
    (
        "company",
        "refusal",
        CompanyCheck(),
        "Compare Tesla and Visa revenue in 2024.",
        {},
        "are not among the 25 companies in the dataset",
    ),
    (
        "company",
        "ask",
        CompanyCheck(),
        "What was Microsoft's revenue in fiscal 2025?",
        {"ticker": "MSFT", "page_ticker": "AAPL"},
        "but the page filter is",
    ),
    (
        "company",
        "ask",
        CompanyCheck(),
        "What was Morgan's revenue in 2024?",
        {"ticker": "JPM"},
        "the question's company is ambiguous",
    ),
    (
        "company",
        "retry",
        CompanyCheck(),
        "Compare Apple and Microsoft revenue in fiscal 2025.",
        {"ticker": "GOOGL"},
        "which the question does not name",
    ),
    (
        "fiscal_year",
        "refusal",
        FiscalYearCheck(),
        "What was Apple's revenue in fiscal 2022?",
        {"fiscal_year": 2022},
        "AAPL has no 10-K for fiscal 2022 in the dataset",
    ),
    (
        "fiscal_year",
        "refusal",
        FiscalYearCheck(),
        "What was Walmart's revenue for the year ended December 31, 2025?",
        {"ticker": "WMT"},
        "no fiscal year of WMT ends on Dec 31, 2025; the 10-K data has annual figures only",
    ),
    (
        "fiscal_year",
        "refusal",
        FiscalYearCheck(),
        "What was Walmart's revenue from January 1, 2025 to June 30, 2025?",
        {"ticker": "WMT"},
        "is not one of WMT's fiscal years; the 10-K data has annual figures only",
    ),
    (
        "fiscal_year",
        "ask",
        FiscalYearCheck(),
        "What was Apple's revenue in calendar 2025?",
        {},
        "calendar 2025 is not one of AAPL's fiscal years",
    ),
    (
        "fiscal_year",
        "ask",
        FiscalYearCheck(),
        "What was Apple's revenue in fiscal 2025?",
        {"page_year": 2024},
        "but the page filter is fiscal 2024",
    ),
    (
        "fiscal_year",
        "retry",
        FiscalYearCheck(),
        "Compare Apple's revenue in fiscal 2024 and fiscal 2025.",
        {"fiscal_year": 2026},
        "the model sent 2026",
    ),
    (
        "fiscal_year",
        "retry",
        FiscalYearCheck(),
        "What was Apple's revenue?",
        {"fiscal_year": None},
        "no year in the question and none sent",
    ),
    (
        "metric",
        "refusal",
        MetricCheck(),
        "What was Apple's revenue in Q3 2025?",
        {},
        "the dataset has annual figures only (10-K); no quarterly periods",
    ),
    (
        "metric",
        "refusal",
        MetricCheck(),
        "What was Apple's EBITDA in fiscal 2025?",
        {},
        "is not one of the 13 metrics the data holds",
    ),
    (
        "segment",
        "refusal",
        SegmentCheck(),
        "What was AWS revenue in fiscal 2025?",
        {"ticker": "AMZN"},
        "segment figures (AWS) are not supported",
    ),
]
# The reject call sites each module has (`CheckResult.rejected(...)` and the fiscal-year
# check's `reject(...)` helper, whose own body is one more), and the cases that reach them.
SITES = {"company": 4, "fiscal_year": 7, "metric": 2, "segment": 1, "units": 0}
CASE_SITES = {"company": 4, "fiscal_year": 6 + 1, "metric": 2, "segment": 1, "units": 0}


def reason(case: tuple[str, Kind, Any, str, dict[str, Any], str]) -> str:
    _, _, check, text, kwargs, _ = case
    result = run_check(check, text, **kwargs)
    assert result.outcome == "reject", (text, result.override.reason)
    return result.override.reason


def test_every_reject_site_in_the_checks_has_a_case() -> None:
    """A reject added to a check later fails here until it has a case and a kind."""
    for path in sorted(CHECKS_DIR.glob("*.py")):
        if path.stem in ("__init__", "base"):
            continue
        calls = [
            node
            for node in ast.walk(ast.parse(path.read_text(encoding="utf-8")))
            if isinstance(node, ast.Call)
            and (
                (isinstance(node.func, ast.Attribute) and node.func.attr == "rejected")
                or (isinstance(node.func, ast.Name) and node.func.id == "reject")
            )
        ]
        assert len(calls) == SITES[path.stem], (path.stem, len(calls))
    assert SITES == CASE_SITES
    # fiscal_year: unpinned, odd date or range (one site), calendar, page filter, two named,
    # none sent, and the helper's body; the odd period has two wordings, so two cases.
    assert sum(1 for c in CASES if c[0] == "fiscal_year") == 7


@pytest.mark.parametrize("case", CASES, ids=[f"{c[0]}-{c[1]}-{i}" for i, c in enumerate(CASES)])
def test_each_reject_reason_is_its_branch(case: tuple[Any, ...]) -> None:
    assert case[5] in reason(case)


@pytest.mark.parametrize("case", [c for c in CASES if c[1] == "refusal"], ids=lambda c: c[3])
def test_a_refusal_in_a_checks_reject_words_is_a_decline(case: tuple[Any, ...]) -> None:
    text = reason(case)
    assert declines(text), text
    refuse = question(
        id="trap-001",
        set="trap",
        category="metric_not_supported",
        expected_behavior="refuse",
        style=None,
    )
    assert grade(row(text[0].upper() + text[1:] + "."), refuse).outcome == "correct"


@pytest.mark.parametrize("case", [c for c in CASES if c[1] != "refusal"], ids=lambda c: c[3])
def test_an_ask_or_a_retry_is_not_a_decline(case: tuple[Any, ...]) -> None:
    text = reason(case)
    assert not declines(text), text
