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
    assert grade(row("Sales were $416.2 billion [F1]."), q).outcome == "year_not_stated"
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
    # Correct, year not stated, other year, wrong number, no number, asked back, answered
    # when it should have asked, abstained, errors, not graded.
    assert "| control-001 | 3 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 |" in table
    assert "| **All** | 3 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 |" in table
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


def test_narrow_and_no_break_spaces_between_digit_groups_are_thousands_separators() -> None:
    for space in (0x202F, 0x00A0, 0x2009):  # narrow no-break, no-break, thin
        text = "Revenue was $680" + chr(space) + "985" + chr(space) + "000" + chr(space) + "000."
        assert values(text) == [Decimal("680985000000")], hex(space)
    # A plain space still separates two numbers.
    assert values("Segments 680 985 were listed.") == [Decimal("680"), Decimal("985")]


# ---------------------------------------------------------------- fixes after the Day 20 review

EN_DASH = chr(0x2013)
KO = {"id": "control-001", "company": "KO", "fiscal_year": 2024, "metric": "net_income"}
NVDA_2026 = {
    "id": "trap-003",
    "set": "trap",
    "category": "relative_year",
    "question": "What was Nvidia's net income last year?",
    "company": "NVDA",
    "fiscal_year": 2026,
    "metric": "net_income",
    "gold_value": 120067000000,
    "gold_other_years": {"2024": 29760000000, "2025": 72880000000},
    "style": None,
}
CLARIFY = {
    "id": "trap-001",
    "set": "trap",
    "category": "lookalike_company",
    "company": None,
    "fiscal_year": None,
    "expected_behavior": "clarify",
    "gold_value": None,
    "style": None,
}
REFUSE = {
    "id": "trap-005",
    "set": "trap",
    "category": "metric_not_supported",
    "company": "GS",
    "expected_behavior": "refuse",
    "gold_value": None,
    "style": None,
}


def test_a_wrong_sign_is_not_the_positive_gold_value() -> None:
    q = question(**KO, gold_value=10631000000)
    assert grade(
        row("Coca-Cola reported a net loss of $10.6 billion in fiscal 2024."), q
    ).outcome == ("wrong_number")
    assert grade(row("Coca-Cola's fiscal 2024 net income was ($10,631 million)."), q).outcome == (
        "wrong_number"
    )
    assert grade(row("Coca-Cola's fiscal 2024 net income was $10.6 billion."), q).outcome == (
        "correct"
    )


def test_an_amount_in_parentheses_keeps_its_minus_sign() -> None:
    assert values("($1.2 billion)") == [Decimal("-1200000000")]
    assert values("($10,631 million)") == [Decimal("-10631000000")]
    q = question(metric="net_income", gold_value=-1200000000)
    assert grade(row("Net income in fiscal 2025 was ($1.2 billion)."), q).outcome == "correct"


def test_a_range_is_two_positive_numbers_with_the_scale_of_the_second() -> None:
    assert values("$680.9" + EN_DASH + "681.0 billion") == [
        Decimal("680900000000"),
        Decimal("681000000000"),
    ]
    assert [(n.value, n.percent) for n in find_numbers("Margins were 10-12%.")] == [
        (Decimal("10"), True),
        (Decimal("12"), True),
    ]
    q = question(id="trap-002", company="WMT", fiscal_year=2025, gold_value=680985000000)
    text = "Walmart's fiscal 2025 revenue was $680.9" + EN_DASH + "681.0 billion."
    assert grade(row(text), q).outcome == "correct"


def test_an_explicit_fiscal_year_phrase_wins_over_a_period_end_date() -> None:
    q = question(**NVDA_2026)
    text = (
        "Nvidia's net income for fiscal 2025 (the year ended January 25, 2026) was $120.1 billion."
    )
    assert grade(row(text), q).outcome == "year_not_stated"
    assert not states_year(text, 2026)
    assert states_year("Net income for fiscal 2026 was $120.1 billion.", 2026)
    assert states_year("Net income for fiscal '26 was $120.1 billion.", 2026)


def test_a_period_end_date_counts_when_no_fiscal_phrase_contradicts_it() -> None:
    assert states_year("Net income for the year ended January 25, 2026 was $120.1 billion.", 2026)
    assert states_year("Total assets as of June 30, 2025 were $619,003 million.", 2025)
    assert states_year("For the period 2025-01-27 to 2026-01-25 net income was $120.1B.", 2026)
    # The same date with a fiscal phrase that agrees still counts.
    assert states_year("Fiscal 2026 (ended January 25, 2026) net income was $120.1B.", 2026)


def test_a_bare_year_inside_any_other_date_counts_for_nothing() -> None:
    assert not states_year("In its 10-K filed in February 2026, net income was $120.1B.", 2026)
    assert not states_year("In its 10-K filed on February 25, 2026, net income was $120.1B.", 2026)
    assert not states_year("From January 27, 2025, net income was $120.1B.", 2025)


def test_harmless_numbers_do_not_spoil_a_clarify_or_refuse_answer() -> None:
    refuse = question(**REFUSE)
    for text in (
        "I can't answer that: the 3 months ended September 30, 2025 are in a 10-Q filing, "
        "which is not loaded.",
        "I can't give a quarter: the fiscal year ended Dec. 31, 2025, and quarterly figures are "
        "in 10-Q filings.",
    ):
        assert grade(row(text), refuse).outcome == "correct", text
    clarify = question(**CLARIFY)
    for text in (
        "Did you mean Morgan Stanley or JPMorgan Chase? Both are among the 25 companies covered.",
        "Do you mean Morgan Stanley (1) or JPMorgan Chase (2)?",
    ):
        assert grade(row(text), clarify).outcome == "correct", text
    # An amount still spoils it, a per-share figure included.
    assert grade(row("I can't answer, but diluted EPS was 8.98."), refuse).outcome == (
        "answered_when_should_ask"
    )


def test_a_footnote_marker_is_not_a_negative_number() -> None:
    assert values("Revenue grew (1).") == [Decimal("1")]


def test_cannot_in_an_ordinary_sentence_is_not_declining() -> None:
    text = "Morgan's net revenue grew strongly last year, though segments cannot be compared."
    assert not asks_or_declines(text)
    assert grade(row(text), question(**CLARIFY)).outcome == "answered_when_should_ask"


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Revenue was $681.0 B.", Decimal("681000000000")),
        ("Revenue was $681.0b.", Decimal("681000000000")),
        ("The fee was $416k.", Decimal("416000")),
        ("Revenue was $416 mm.", Decimal("416000000")),
        ("Revenue was $681-billion.", Decimal("681000000000")),
        ("Revenue was $.5 billion.", Decimal("500000000")),
        ("Revenue was $416.2\nbillion.", Decimal("416200000000")),
    ],
)
def test_more_ways_of_writing_a_scale_are_read(text: str, expected: Decimal) -> None:
    assert values(text) == [expected]


def test_a_question_asked_back_on_a_number_question_is_its_own_outcome() -> None:
    rsq = chr(0x2019)  # the curly apostrophe gpt-oss writes
    text = (
        f"I{rsq}m not sure which fiscal year you{rsq}re referring to. Could you specify the year "
        "(e.g., 2024, 2023, etc.)?"
    )
    assert grade(row(text), question(**NVDA_2026)).outcome == "asked_when_should_answer"
    assert grade(row(ABSTAIN), question(**NVDA_2026)).outcome == "abstained"


def test_another_pinned_years_value_is_its_own_outcome() -> None:
    q = question(**NVDA_2026)
    # The stored agent answer, with its curly apostrophe and lenticular citation brackets.
    text = f"Nvidia{chr(0x2019)}s net income for fiscal 2025 was **$72,880,000,000**"
    text += chr(0x3010) + "F1" + chr(0x3011) + "."
    result = grade(row(text), q)
    assert (result.outcome, result.other_year, result.matched) == (
        "other_year_number",
        2025,
        "72880000000",
    )
    assert grade(row("Fiscal 2024 net income was $114 million."), q).outcome == "wrong_number"
    # The gold year wins when a number fits both.
    both = question(**{**NVDA_2026, "gold_other_years": {"2025": 120000000000}})
    assert grade(row("Fiscal 2026 net income was $120.1 billion."), both).outcome == "correct"


def test_a_number_goes_to_the_years_value_it_is_closest_to() -> None:
    # Coca-Cola's net income: FY2024 10,631 million (gold), FY2023 10,714 million, 0.8% apart,
    # so both are inside the 1% tolerance of the other.
    q = question(**KO, gold_value=10631000000, gold_other_years={"2023": 10714000000})
    result = grade(row("Coca-Cola's fiscal 2023 net income was $10,714 million."), q)
    assert (result.outcome, result.other_year) == ("other_year_number", 2023)
    result = grade(row("Coca-Cola's fiscal 2024 net income was $10,631 million."), q)
    assert result.outcome == "correct"
    result = grade(row("Coca-Cola's fiscal 2024 net income was $10.6 billion."), q)
    assert result.outcome == "correct"


# ---------------------------------------------------------------- fixes after the second review


def test_no_number_and_a_decline_in_other_words_are_their_own_outcomes() -> None:
    q = question(**NVDA_2026)
    assert (
        grade(row("Nvidia reports its net income in Item 8 of its 10-K [1]."), q).outcome
        == "no_number"
    )
    assert (
        grade(row("I couldn't find Nvidia's net income in the filings I have."), q).outcome
        == "abstained"
    )
    assert (
        grade(row("That figure isn't available in the filings I have."), q).outcome == "abstained"
    )


def test_a_spaced_dash_is_not_a_minus_sign() -> None:
    assert values(f"Total revenues {EN_DASH} $681.0 billion [2]") == [Decimal("681000000000")]
    assert values("Walmart fiscal 2025 revenue - $681.0 billion.") == [Decimal("681000000000")]
    assert values(f"$680.9 {EN_DASH} $681.0 billion") == [
        Decimal("680900000000"),
        Decimal("681000000000"),
    ]
    assert [str(n.value) for n in find_numbers("5% - 6%")] == ["5", "6"]
    assert values("(713,163,000,000 - 680,985,000,000) / 680,985,000,000") == [
        Decimal("713163000000"),
        Decimal("680985000000"),
        Decimal("680985000000"),
    ]
    assert values("Net loss was -$1.2 billion.") == [
        Decimal("-1200000000")
    ]  # attached: still a sign


def test_each_number_goes_to_its_own_nearest_year() -> None:
    q = question(
        id="trap-002",
        company="WMT",
        fiscal_year=2025,
        gold_value=680985000000,
        gold_other_years={"2024": 648125000000, "2026": 713163000000},
    )
    text = "Fiscal 2025 revenue was $681.0 billion, up from $648,125 million in fiscal 2024."
    assert grade(row(text), q).outcome == "correct"
    q = question(**NVDA_2026)
    text = (
        "Nvidia's net income was $120.1 billion in fiscal 2026, up from $72.9 billion in "
        "fiscal 2025."
    )
    assert grade(row(text), q).outcome == "correct"
    assert (
        grade(row("Nvidia's fiscal 2025 net income was $72.9 billion."), q).outcome
        == "other_year_number"
    )


def test_the_loss_label_and_other_clauses_do_not_flip_a_sign() -> None:
    assert values("Net income (loss) was $5.0 billion.") == [Decimal("5000000000")]
    assert values("Operating income (loss): $5 billion.") == [Decimal("5000000000")]
    assert values("Despite the loss, net income was $5 billion.") == [Decimal("5000000000")]
    assert values("Income before losses was $4 billion.") == [Decimal("4000000000")]
    assert values("Loss before income taxes of $3 billion.") == [Decimal("-3000000000")]
    assert values("The net loss for fiscal 2025 was $45 million.") == [Decimal("-45000000")]


def test_more_fiscal_year_phrasings() -> None:
    assert states_year("Revenue in fiscal years 2024 and 2025 was $648B and $681B.", 2025)
    assert states_year(f"Revenue in fiscal 2024{EN_DASH}2025 rose.", 2025)
    assert states_year(
        "Revenue for the fiscal 52-week year ended January 31, 2025 was $681B.", 2025
    )
    assert not states_year(
        "The fiscal 52-week year ended January 31, 2025 had sales of $681B.", 2052
    )
    assert states_year("Total assets on June 30, 2025 were $619B.", 2025)
    assert not states_year("The 10-K filed on February 25, 2026 reports $120B.", 2026)
    assert states_year("Net income for 2024-01-29 " + chr(0x2014) + " 2025-01-26 was $72.9B.", 2025)


def test_more_ways_of_declining() -> None:
    for text in (
        "I could not find a quarterly figure in the filings.",
        "That figure isn't available in the 10-K filings I have.",
        "I can't help with quarterly figures.",
        "The dataset does not include quarterly reports.",
        "The filings I have don't cover the third quarter.",
    ):
        assert asks_or_declines(text), text
