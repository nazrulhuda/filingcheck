"""Week 5 grader fixes: the abstain sentences the model writes, the strict clarify rule, the
unanswerable questions, and dagger citation markers."""

from typing import Any

import pytest

from filingcheck.answer.abstain import is_abstain
from filingcheck.eval.grade import grade
from filingcheck.eval.questions import Question

Q = chr(0x2019)  # the curly apostrophe the model writes
NB = chr(0x202F)  # the narrow no-break space it puts inside names and numbers
DASH = chr(0x2011)  # the non-breaking hyphen of "10-K"

# Every decline the model wrote in the stored rows (eval/results, eval/probes) that the exact
# abstain sentence missed, word for word.
SEEN = [
    f"I can{Q}t find a quarterly net revenue figure for Goldman{NB}Sachs in the filings I have.",
    f"I can{Q}t find this information in the filings I have.",
    f"I can{Q}t find a separate Converse revenue figure in the filings I have.",
    f"I{Q}m not able to locate a specific Converse revenue figure in the filings I have for fiscal "
    f"year{NB}2025. I couldn{Q}t find a line item that reports Converse revenue separately for "
    f"2025 or 2024, so I can{Q}t calculate the change.",
    f"I{Q}m sorry, but I can{Q}t find that information in the filings I have.",
    f"I can{Q}t find any reference in the 2025 10{DASH}K that specifies which framework "
    f"American{NB}Express management used to judge its internal controls.",
    f"I can{Q}t find any mention in the filings of a specific framework that American{NB}Express "
    "management used to judge its internal controls.",
    f"I can{Q}t find the specific Converse revenue figures in the filings I have.",
    f"I can{Q}t find Converse{Q}s revenue figures in the filings I have.",
]
# The wordings the spec names, with straight and curly apostrophes.
NAMED = [
    "I can't find any information in the filings about a quarterly figure.",
    "I couldn't find that in the filings I have.",
    f"I couldn{Q}t find a figure for that.",
    "The filings I have don't break out that number.",
    f"The filings I have don{Q}t say.",
]


@pytest.mark.parametrize("text", SEEN + NAMED)
def test_every_decline_the_model_writes_is_an_abstention(text: str) -> None:
    assert is_abstain(text)


@pytest.mark.parametrize(
    "text",
    [
        # Declines with something more: a figure, or what the filing does say.
        f"I can{Q}t find a specific figure for the fair value of Walmart{Q}s swaps in the 2024 "
        f"10{DASH}K. The filing describes the swaps, but does not give a dollar amount, so I "
        f"cannot calculate how a 10{NB}% dollar depreciation would affect it.",
        f"I can{Q}t find Coca{DASH}Cola{Q}s reasoning in the 2024 10{DASH}K. The filing only "
        "describes the refranchising as a structural change that affected revenue.",
        "I can't find the AWS figure, but AWS sales grew 20% in 2025.",
        "Revenue was $5 billion [1].",
        "I can't believe how much revenue grew.",
    ],
)
def test_a_decline_with_information_is_not_an_abstention(text: str) -> None:
    assert not is_abstain(text)


def question(**fields: Any) -> Question:
    base: dict[str, Any] = {
        "id": "dev-001",
        "set": "trap",
        "category": "lookalike_company",
        "question": "how much net revenue did morgan make in 2024",
        "company": None,
        "fiscal_year": 2024,
        "metric": "revenue",
        "expected_behavior": "clarify",
        "trap_note": "Morgan Stanley or JPMorgan Chase.",
    }
    return Question.model_validate(base | fields)


def outcomes(answer: str, **fields: Any) -> tuple[str, str | None]:
    result = grade({"answer": answer}, question(**fields))
    return result.outcome, result.lenient_outcome


@pytest.mark.parametrize(
    "answer",
    [
        "Do you mean Morgan Stanley or JPMorgan Chase?",
        "Which company do you mean?",
        "That could be JPMorgan Chase or Morgan Stanley; please say which.",
    ],
)
def test_a_clarify_answer_about_the_ambiguous_company_is_correct(answer: str) -> None:
    assert outcomes(answer) == ("correct", "correct")


@pytest.mark.parametrize(
    "answer",
    [
        "Which fiscal year do you mean?",
        "I can't find this in the filings I have.",
        "Could you specify the year?",
    ],
)
def test_a_clarify_answer_about_something_else_counts_only_under_the_lenient_rule(
    answer: str,
) -> None:
    assert outcomes(answer) == ("asked_about_another_thing", "correct")


def test_a_number_given_instead_of_asking_is_wrong_under_both_rules() -> None:
    answer = "Morgan Stanley's net revenues were $61,761 million in 2024."
    assert outcomes(answer) == ("answered_when_should_ask", "answered_when_should_ask")


YEAR = {
    "category": "wrong_fiscal_year",
    "question": "What was Costco's net income for calendar 2024?",
    "company": "COST",
    "fiscal_year": None,
    "metric": "net_income",
}


@pytest.mark.parametrize(
    "answer",
    [
        "Costco's fiscal years end around August 31. Do you mean fiscal 2024 or fiscal 2025?",
        "Which fiscal year do you mean?",
        "Which period should I use?",
    ],
)
def test_a_clarify_answer_about_the_ambiguous_year_is_correct(answer: str) -> None:
    assert outcomes(answer, **YEAR) == ("correct", "correct")


def test_asking_which_company_when_the_year_is_ambiguous_is_off_target() -> None:
    assert outcomes("Which company do you mean?", **YEAR) == (
        "asked_about_another_thing",
        "correct",
    )


def test_a_refuse_question_has_no_lenient_column() -> None:
    result = grade(
        {"answer": "I can't find this in the filings I have."},
        question(category="metric_not_supported", expected_behavior="refuse"),
    )
    assert (result.outcome, result.lenient_outcome) == ("correct", None)


UNANSWERABLE = {
    "id": "una-001",
    "category": "unanswerable_text",
    "question": "Why does Costco end its fiscal year in August?",
    "company": "COST",
    "fiscal_year": 2025,
    "metric": None,
    "expected_behavior": "refuse",
}


def test_an_unanswerable_question_is_graded_abstained_or_answered() -> None:
    declined = grade({"answer": "The filings I have don't say."}, question(**UNANSWERABLE))
    answered = grade(
        {"answer": "Costco wanted its year to end after the back-to-school season [1]."},
        question(**UNANSWERABLE),
    )
    assert (declined.outcome, answered.outcome) == ("abstained", "answered")


def test_the_numbers_inside_a_dagger_marker_are_not_read_as_figures() -> None:
    result = grade(
        {"answer": "$44 billion of its debt was fixed-rate【1†number=1】."},
        question(
            category="control",
            set="control",
            style="domain-relevant",
            company="UNH",
            expected_behavior="answer",
            gold_value=44000000000,
            gold_unit="USD",
            gold_source="hand",
        ),
    )
    assert result.numbers == ["44000000000"]


# Three rows of the Day 33 dry run the deterministic grader got wrong (the LLM grader did not).
NBSP = chr(0x202F)
HYPHEN = chr(0x2011)


def test_a_page_filter_company_means_the_year_is_the_ambiguity() -> None:
    """dev-025: company null, page filter KO fiscal 2023, the question says FY24; asking which year
    is what the trap wants, so the strict rule must read the company from the page filter."""
    q = question(
        category="wrong_fiscal_year",
        question="coke's FY24 bottom line?",
        company=None,
        fiscal_year=None,
        metric="net_income",
        expected_behavior="clarify",
        page_filter={"ticker": "KO", "fiscal_year": 2023},
    )
    answer = (
        f"I{Q}m not sure which fiscal year you{Q}re asking about. You indicated {chr(0x201C)}KO "
        f"and fiscal year{NBSP}2023,{chr(0x201D)} but then asked for Coke{Q}s FY24 bottom line. "
        f"Could you clarify whether you want the net income for fiscal year{NBSP}2023 or fiscal "
        f"year{NBSP}2024?"
    )
    assert grade({"id": "dev-025", "answer": answer}, q).outcome == "correct"


def test_asking_which_credit_card_company_asks_which_company() -> None:
    """dev-007: a word between "which" and "company", with a non-breaking hyphen."""
    q = question(
        category="lookalike_company",
        question="What was net income at the credit card company last year?",
        company=None,
        fiscal_year=None,
        metric="net_income",
        expected_behavior="clarify",
    )
    answer = (
        f"I{Q}m not sure which credit{HYPHEN}card company you{Q}re asking about. Could you specify "
        f"the ticker (e.g., AXP for American Express) and the fiscal year you{Q}re interested in?"
    )
    assert grade({"id": "dev-007", "answer": answer}, q).outcome == "correct"


def test_a_period_end_in_bold_still_states_the_year() -> None:
    """dev-028: "fiscal year ended **December 31, 2025**" is a period end."""
    q = question(
        category="relative_year",
        question="Latest total assets for Mastercard",
        company="MA",
        fiscal_year=2025,
        metric="total_assets",
        expected_behavior="answer",
        gold_value=54157000000,
        gold_unit="USD",
    )
    answer = (
        "The most recent annual filing for Mastercard (ticker **MA**) reports total assets of "
        "**$54,157,000,000**. This figure is for the fiscal year ended "
        f"**December{NBSP}31,{NBSP}2025** (instant value as of that date)【F1】."
    )
    assert grade({"id": "dev-028", "answer": answer}, q).outcome == "correct"
