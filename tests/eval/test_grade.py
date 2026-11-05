"""The deterministic number grader: the number finder, the tolerance rule, the behaviour rules."""

from decimal import Decimal
from typing import Any

import pytest

from filingcheck.answer.baseline import ABSTAIN
from filingcheck.eval.grade import (
    asks_or_declines,
    find_numbers,
    grade,
    states_year,
    summary_table,
)
from filingcheck.eval.questions import Question


def values(text: str) -> list[Decimal]:
    return [n.value for n in find_numbers(text)]


# ---------------------------------------------------------------- the number finder


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Total net sales were $416.2 billion.", [Decimal("416200000000")]),
        ("Total net sales were $416,161 million.", [Decimal("416161000000")]),
        ("Total net sales were 416,161,000,000 dollars.", [Decimal("416161000000")]),
        ("Diluted EPS was 8.98.", [Decimal("8.98")]),
        ("Diluted EPS was $6.08 per share.", [Decimal("6.08")]),
        ("It reported $416,161M in sales.", [Decimal("416161000000")]),
        ("Sales were $416.2B.", [Decimal("416200000000")]),
        ("Revenue of $1.3 billion came from Mexico in the year.", [Decimal("1300000000")]),
        ("The company had 15.2 billion shares outstanding.", [Decimal("15200000000")]),
        ("Net loss was -$1.2 billion.", [Decimal("-1200000000")]),
        ("Net loss was $(1.2) billion.", [Decimal("-1200000000")]),
        ("Operating income was (1,234) million.", [Decimal("-1234000000")]),
        ("Net loss was " + chr(0x2212) + "$45 million.", [Decimal("-45000000")]),  # minus sign
    ],
)
def test_numbers_are_found_and_converted_to_raw_units(text: str, expected: list[Decimal]) -> None:
    assert values(text) == expected


def test_percentages_are_found_as_percentages() -> None:
    [growth] = find_numbers("Revenue grew 4.5% from fiscal 2025 to fiscal 2026.")
    assert (growth.value, growth.percent) == (Decimal("4.5"), True)
    [decline] = find_numbers("It fell -3.2 percent.")
    assert (decline.value, decline.percent) == (Decimal("-3.2"), True)


@pytest.mark.parametrize(
    "text",
    [
        "In fiscal 2025 the company grew.",
        "In FY2025 the company grew.",
        "The year ended September 27, 2025.",
        "The period was 2024-09-29 to 2025-09-27.",
        "See Item 7 and Note 8 of the 10-K [1] [F1] [2, F3].",
        "In Q3 2025 it reported results.",
        "1. Revenue is discussed in the filing.",
    ],
)
def test_years_dates_citations_and_labels_are_not_values(text: str) -> None:
    assert values(text) == []


# ---------------------------------------------------------------- rules


def question(**over: Any) -> Question:
    fields: dict[str, Any] = {
        "id": "control-001",
        "set": "control",
        "category": "control",
        "question": "What were Apple's total net sales in fiscal 2025?",
        "company": "AAPL",
        "fiscal_year": 2025,
        "metric": "revenue",
        "expected_behavior": "answer",
        "gold_value": 416161000000,
        "gold_unit": "USD",
        "tolerance_pct": 1.0,
        "style": "metrics-generated",
    }
    fields.update(over)
    return Question.model_validate(fields)


def row(answer: str | None, **over: Any) -> dict[str, Any]:
    fields: dict[str, Any] = {
        "id": "control-001",
        "repeat": 1,
        "answer": answer,
        "abstained": answer == ABSTAIN,
        "error": None,
        "cost_usd": 0.0002,
        "latency_ms": 1000.0,
    }
    fields.update(over)
    return fields


def test_the_fiscal_year_must_be_stated() -> None:
    assert states_year("Sales in fiscal 2025 were $416.2 billion.", 2025)
    assert states_year("FY2025 sales were $416.2 billion.", 2025)
    assert states_year("FY25 sales were $416.2 billion.", 2025)
    assert not states_year("Sales were $416.2 billion.", 2025)
    assert not states_year("Sales in fiscal 2026 were $416.2 billion.", 2025)


def test_a_number_within_the_tolerance_and_the_year_stated_is_correct() -> None:
    q = question()
    assert grade(row("Fiscal 2025 total net sales were $416.2 billion [F1]."), q).outcome == (
        "correct"
    )
    assert grade(row("In fiscal 2025 sales were $412.5 billion."), q).outcome == "correct"  # 0.9%
    assert grade(row("In fiscal 2025 sales were $410 billion."), q).outcome == "wrong_number"
    assert grade(row("Sales were $416.2 billion [F1]."), q).outcome == "wrong_year"
    assert grade(row("Sales grew 6.4% in fiscal 2025."), q).outcome == "wrong_number"


def test_a_tolerance_of_zero_needs_the_exact_value() -> None:
    q = question(tolerance_pct=0.0)
    assert grade(row("In fiscal 2025 sales were $416,161 million."), q).outcome == "correct"
    assert grade(row("In fiscal 2025 sales were $416.2 billion."), q).outcome == "wrong_number"


def test_the_grade_records_what_it_found() -> None:
    result = grade(row("In fiscal 2025 sales were $416.2 billion, up 6.4% [F1]."), question())
    assert result.matched == "416200000000"
    assert result.numbers == ["416200000000", "6.4%"]
    assert result.year_stated


def test_an_abstention_and_an_error_are_their_own_outcomes() -> None:
    assert grade(row(ABSTAIN), question()).outcome == "abstained"
    assert grade(row(None, error="openrouter - incomplete_length"), question()).outcome == "error"


@pytest.mark.parametrize(
    "text",
    [
        "Do you mean Morgan Stanley or JPMorgan Chase?",
        '"Morgan" is ambiguous: which company do you mean, Morgan Stanley or JPMorgan Chase?',
        ABSTAIN,
        "I can't answer that: only annual 10-K filings are loaded, and quarterly figures are "
        "in 10-Q filings.",
    ],
)
def test_asking_or_declining_is_recognised(text: str) -> None:
    assert asks_or_declines(text)


def test_a_plain_answer_neither_asks_nor_declines() -> None:
    assert not asks_or_declines("Morgan Stanley's net revenue was $61.8 billion in fiscal 2024.")


def test_a_clarify_or_refuse_question_is_correct_only_without_numbers_and_with_a_question() -> None:
    clarify = question(
        id="trap-001",
        set="trap",
        category="lookalike_company",
        company=None,
        fiscal_year=None,
        expected_behavior="clarify",
        gold_value=None,
        style=None,
    )
    assert grade(row("Do you mean Morgan Stanley or JPMorgan Chase?"), clarify).outcome == (
        "correct"
    )
    answered = row("Morgan Stanley's net revenue in fiscal 2025 was $61.8 billion [F1].")
    assert grade(answered, clarify).outcome == "answered_when_should_ask"
    asked_but_answered = row("Do you mean Morgan Stanley? Its revenue was $61.8 billion.")
    assert grade(asked_but_answered, clarify).outcome == "answered_when_should_ask"
    no_number_no_question = row("Morgan Stanley reports net revenue in its 10-K [1].")
    assert grade(no_number_no_question, clarify).outcome == "answered_when_should_ask"
    refuse = question(
        id="trap-005",
        set="trap",
        category="metric_not_supported",
        expected_behavior="refuse",
        style=None,
    )
    declined = row("I can't answer that: quarterly figures are in 10-Q filings, not loaded here.")
    assert grade(declined, refuse).outcome == "correct"
    assert grade(row(ABSTAIN), refuse).outcome == "correct"


# ---------------------------------------------------------------- the summary


def test_the_summary_table_counts_each_outcome_per_question_and_in_total() -> None:
    q = question()
    rows = [
        row("In fiscal 2025 sales were $416.2 billion.", repeat=1),
        row("Sales were $416.2 billion.", repeat=2),
        row(ABSTAIN, repeat=3),
    ]
    graded = [(r, grade(r, q)) for r in rows]
    table = summary_table(graded, mode="agent")
    assert "| control-001 | 3 | 1 | 0 | 1 | 0 | 1 | 0 |" in table
    assert "| **All** | 3 | 1 | 0 | 1 | 0 | 1 | 0 |" in table
    assert "$0.000600" in table


def test_a_loss_written_as_a_positive_amount_matches_a_negative_gold_value() -> None:
    q = question(metric="net_income", gold_value=-1200000000)
    assert grade(row("In fiscal 2025 the net loss was $1.2 billion."), q).outcome == "correct"
    assert grade(row("In fiscal 2025 net income was -$1.2 billion."), q).outcome == "correct"
    # Without a word for a loss, a positive amount is not the negative gold value.
    assert grade(row("In fiscal 2025 net income was $1.2 billion."), q).outcome == "wrong_number"


def test_an_answer_question_without_a_gold_value_is_not_graded() -> None:
    q = question(gold_value=None)
    assert grade(row("In fiscal 2025 sales were $416.2 billion."), q).outcome == "not_graded"
