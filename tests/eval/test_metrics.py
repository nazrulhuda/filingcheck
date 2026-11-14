"""The pre-registered metrics (eval/PREREGISTRATION.md), one test per rule, on synthetic rows."""

from typing import Any

import pytest

from filingcheck.answer.baseline import ABSTAIN
from filingcheck.eval.llm_grade import LlmGrade
from filingcheck.eval.metrics import (
    always_abstain,
    error_share,
    noise,
    rate,
    score_run,
    sent_breakdown,
)
from filingcheck.eval.questions import Question


def question(**over: Any) -> Question:
    fields: dict[str, Any] = {
        "id": "held-900",
        "set": "trap",
        "category": "wrong_fiscal_year",
        "question": "What was Apple's revenue in fiscal 2025?",
        "company": "AAPL",
        "fiscal_year": 2025,
        "metric": "revenue",
        "expected_behavior": "answer",
        "gold_value": 416161000000,
        "gold_unit": "USD",
        "gold_other_years": {2024: 391035000000},
    }
    return Question.model_validate(fields | over)


def row(answer: str | None, **over: Any) -> dict[str, Any]:
    fields: dict[str, Any] = {
        "id": "held-900",
        "repeat": 1,
        "answer": answer,
        "number_labels": [],
        "tool_calls": [],
        "overrides": [],
        "latency_ms": 1000.0,
        "cost_usd": 0.0003,
        "error": None,
    }
    return fields | over


def label(value: str, kind: str, percent: bool = False) -> dict[str, Any]:
    return {"figure": value, "value": value, "percent": percent, "label": kind}


def llm(verdict: str, use: str = "text") -> LlmGrade:
    return LlmGrade(
        id="held-900",
        repeat=1,
        use=use,
        verdict=verdict,  # type: ignore[arg-type]
        supported="yes",
        reason="because",
        evidence="",
        model="fake",
        prompt_version="2-abc",
        cost_usd=0.0,
        cached=True,
    )


def fact_call(
    ticker: str, year: int, metric: str = "revenue", status: str = "ok", **more: Any
) -> dict[str, Any]:
    return {
        "name": "get_financial_fact",
        "arguments": {"ticker": ticker, "fiscal_year": year, "metric": metric},
        "status": status,
        "defaults_applied": [],
    } | more


def score(
    r: dict[str, Any], q: Question, grade: LlmGrade | None = None, arm: str = "agent-checks-on"
) -> Any:
    return score_run(r, q, grade, set_name="heldout_traps", arm=arm)


# ---------------------------------------------------------------- which grader decides, accuracy


def test_a_number_question_is_decided_by_the_deterministic_grader() -> None:
    right = score(row("Apple's fiscal 2025 revenue was $416.2 billion."), question())
    assert (right.graded_by, right.outcome, right.correct) == ("number", "correct", True)
    # The LLM's second opinion never changes a number grade.
    wrong = score(
        row("Apple's fiscal 2025 revenue was $5 billion."),
        question(),
        llm("correct", "second opinion"),
    )
    assert (wrong.correct, wrong.llm_verdict) == (False, "correct")


def test_text_questions_unanswerable_ones_and_llm_decides_rows_are_decided_by_the_llm() -> None:
    text = question(
        category="control",
        set="control",
        style="domain-relevant",
        metric=None,
        gold_value=None,
        gold_unit=None,
        gold_other_years=None,
        gold_text="Beaverton",
    )
    assert score(row("Beaverton, Oregon [1]."), text, llm("correct")).correct is True
    assert (
        score(row("Beaverton, Oregon [1]."), text, llm("partly")).correct is False
    )  # partly apart
    una = question(
        category="unanswerable_text",
        expected_behavior="refuse",
        metric=None,
        gold_value=None,
        gold_unit=None,
        gold_other_years=None,
    )
    s = score(row("The filing does not say why."), una, llm("correct"))
    assert (s.graded_by, s.correct) == ("text", True)
    noted = question(
        category="segment_vs_total",
        expected_behavior="refuse",
        gold_value=None,
        gold_unit=None,
        gold_other_years=None,
        also_accept={"note": "A cited figure from the filing is also acceptable."},
    )
    cited = score(
        row("iPhone net sales were $209.6 billion [1]."), noted, llm("correct", "also accept")
    )
    assert (cited.graded_by, cited.correct) == ("text", True)


def test_an_also_accept_alternative_counts_as_correct() -> None:
    q = question(also_accept={"fiscal_year": 2024, "gold_value": 391035000000, "gold_unit": "USD"})
    assert score(row("Apple's fiscal 2024 revenue was $391.0 billion."), q).correct is True


def test_an_error_row_is_never_correct_and_never_confidently_wrong() -> None:
    s = score(row(None, error="openrouter 200 502"), question(), llm("wrong", "second opinion"))
    assert (s.correct, s.confidently_wrong, s.confidently_wrong_no_labels, s.error) == (
        False,
        False,
        False,
        "openrouter 200 502",
    )


# ---------------------------------------------------------------- confidently wrong


REFUSE = question(
    category="segment_vs_total",
    expected_behavior="refuse",
    gold_value=None,
    gold_unit=None,
    gold_other_years=None,
)


def test_a_wrong_answer_whose_key_figure_carries_no_warning_is_confidently_wrong() -> None:
    answer = "iPhone net sales for fiscal 2025 were $416,161,000,000 [F1]."
    verified = score(row(answer, number_labels=[label("416161000000", "verified")]), REFUSE)
    assert (verified.outcome, verified.confidently_wrong) == ("answered_when_should_ask", True)
    unlabeled = score(row(answer), REFUSE)  # a figure with no label carries no warning
    assert unlabeled.confidently_wrong is True


def test_a_wrong_answer_whose_every_key_figure_is_warned_is_not_confidently_wrong() -> None:
    answer = "iPhone net sales for fiscal 2025 were $416,161,000,000."
    for kind in ("unverified", "conflict"):
        s = score(row(answer, number_labels=[label("416161000000", kind)]), REFUSE)
        assert (s.confidently_wrong, s.confidently_wrong_no_labels) == (False, True), kind


def test_one_unwarned_key_figure_among_several_is_enough() -> None:
    answer = "Sales were $416,161,000,000 and units grew 5%."
    labels = [label("416161000000", "unverified"), label("5", "verified", percent=True)]
    assert score(row(answer, number_labels=labels), REFUSE).confidently_wrong is True


def test_for_another_years_number_the_key_figure_is_the_one_the_grader_matched() -> None:
    answer = "Apple's revenue was $391,035,000,000, up from $1 billion."
    s = score(
        row(
            answer,
            number_labels=[label("391035000000", "unverified"), label("1000000000", "verified")],
        ),
        question(),
    )
    assert (s.outcome, s.confidently_wrong) == (
        "other_year_number",
        False,
    )  # the matched one is warned
    s = score(row(answer, number_labels=[label("391035000000", "verified")]), question())
    assert s.confidently_wrong is True


def test_a_wrong_text_answer_with_no_figure_is_confidently_wrong() -> None:
    una = question(
        category="unanswerable_text",
        expected_behavior="refuse",
        metric=None,
        gold_value=None,
        gold_unit=None,
        gold_other_years=None,
    )
    s = score(row("Goldman narrowed it because of regulation."), una, llm("wrong"))
    assert s.confidently_wrong is True  # labels cover figures, not sentences


@pytest.mark.parametrize(
    "answer",
    [
        ABSTAIN,  # abstained
        "Which fiscal year do you mean?",  # asked
        "Apple's revenue was $416.2 billion.",  # year not stated
    ],
)
def test_abstains_asks_and_unstated_years_are_not_confidently_wrong(answer: str) -> None:
    assert score(row(answer), question()).confidently_wrong is False


def test_the_both_graders_line_needs_the_llms_second_opinion_to_say_wrong_too() -> None:
    answer = "iPhone net sales for fiscal 2025 were $416,161,000,000."
    agree = score(row(answer), REFUSE, llm("wrong", "second opinion"))
    differ = score(row(answer), REFUSE, llm("correct", "second opinion"))
    assert (agree.confidently_wrong_both_graders, differ.confidently_wrong_both_graders) == (
        True,
        False,
    )


# ---------------------------------------------------------------- wrong-argument calls


def test_an_answer_question_counts_calls_for_another_company_or_year_that_ran() -> None:
    calls = [
        fact_call("AAPL", 2025),  # right
        fact_call("AAPL", 2025, "net_income"),  # another metric: not compared
        fact_call("MSFT", 2025),  # wrong company
        fact_call("AAPL", 2024),  # wrong year
        fact_call("AAPL", 2023, status="error"),  # stopped by a check: did not run
    ]
    s = score(row("Apple's fiscal 2025 revenue was $416.2 billion.", tool_calls=calls), question())
    assert (s.wrong_arg_ran, s.calls_ran) == (2, 4)


def test_an_also_accept_year_is_a_right_year_too() -> None:
    q = question(also_accept={"fiscal_year": 2024, "gold_value": 391035000000, "gold_unit": "USD"})
    s = score(row("x", tool_calls=[fact_call("AAPL", 2024)]), q)
    assert s.wrong_arg_ran == 0


def test_a_clarify_or_refuse_question_with_no_company_counts_every_call_that_ran() -> None:
    q = question(
        category="lookalike_company",
        company=None,
        fiscal_year=2024,
        expected_behavior="clarify",
        gold_value=None,
        gold_unit=None,
        gold_other_years=None,
    )
    s = score(row("x", tool_calls=[fact_call("MS", 2024), fact_call("JPM", 2024)]), q)
    assert s.wrong_arg_ran == 2


def test_with_a_page_filter_no_call_is_counted() -> None:
    q = question(
        category="lookalike_company",
        company=None,
        fiscal_year=2025,
        expected_behavior="clarify",
        gold_value=None,
        gold_unit=None,
        gold_other_years=None,
        page_filter={"ticker": "AAPL", "fiscal_year": None},
    )
    assert score(row("x", tool_calls=[fact_call("AAPL", 2025)]), q).wrong_arg_ran == 0


def test_a_clarify_question_that_names_its_company_counts_calls_for_another_company() -> None:
    q = question(
        category="relative_year",
        fiscal_year=None,
        expected_behavior="clarify",
        gold_value=None,
        gold_unit=None,
        gold_other_years=None,
    )
    s = score(row("x", tool_calls=[fact_call("AAPL", 2024), fact_call("MSFT", 2025)]), q)
    assert s.wrong_arg_ran == 1


def test_a_refusal_that_names_its_company_counts_no_call_but_segment_calls_are_reported() -> None:
    calls = [fact_call("AAPL", 2025), fact_call("AAPL", 2025, "net_income")]
    s = score(row("x", tool_calls=calls), REFUSE)
    assert (s.wrong_arg_ran, s.segment_total_calls) == (0, 1)
    assert score(row("x"), question()).segment_total_calls is None  # not a segment refusal


def test_the_count_as_sent_uses_the_models_own_arguments_and_the_breakdown() -> None:
    calls = [
        fact_call(
            "AAPL",
            2025,
            sent_arguments={"ticker": "MSFT", "fiscal_year": 2025, "metric": "revenue"},
        ),  # repaired
        fact_call(
            "AAPL",
            2024,
            status="error",
            sent_arguments={"ticker": "AAPL", "fiscal_year": 2024, "metric": "revenue"},
        ),  # rejected
        fact_call(
            "AAPL",
            2023,
            sent_arguments={"ticker": "AAPL", "fiscal_year": 2023, "metric": "revenue"},
        ),  # ran unchanged
        fact_call(
            "AAPL",
            2025,
            sent_arguments={"metric": "revenue"},
            defaults_applied=["ticker", "fiscal_year"],
        ),  # page filter: right
    ]
    s = score(row("x", tool_calls=calls), question())
    assert (s.wrong_arg_ran, s.wrong_arg_sent) == (1, 3)
    assert sent_breakdown(row("x", tool_calls=calls), question()) == {
        "repaired": 1,
        "rejected": 1,
        "ran unchanged": 1,
    }
    assert (
        score(row("x", tool_calls=[fact_call("AAPL", 2024)]), question()).wrong_arg_sent is None
    )  # not recorded


# ---------------------------------------------------------------- abstains, false repairs


def test_the_abstain_rate_counts_abstained_outcomes() -> None:
    assert score(row(ABSTAIN), question()).abstained is True
    assert score(row("Which fiscal year do you mean?"), question()).abstained is False


def test_a_false_repair_is_a_number_tool_repair_or_reject_on_a_control_question() -> None:
    control = question(category="control", set="control", style="metrics-generated")
    fact = [{"check": "units", "outcome": "repair", "tool": "get_financial_fact"}]
    old = [{"check": "company", "outcome": "reject"}]  # rows before 2026-11-13 name no tool
    search = [{"check": "fiscal_year", "outcome": "repair", "tool": "search_filings"}]
    assert score(row("x", overrides=fact), control).false_repair is True
    assert score(row("x", overrides=old), control).false_repair is True
    s = score(row("x", overrides=search), control)
    assert (s.false_repair, s.search_repairs) == (False, 1)  # listed apart: its design
    assert (
        score(row("x", overrides=fact), question()).false_repair is False
    )  # not a control question


# ---------------------------------------------------------------- rates, not scored, errors, noise


def scores_for(outcomes: dict[str, list[str]], scored: dict[str, bool] | None = None) -> list[Any]:
    out = []
    for qid, answers in outcomes.items():
        reason = None if (scored or {}).get(qid, True) else "a repeat"
        q = question(id=qid, scored=reason is None, not_scored_reason=reason)
        for n, answer in enumerate(answers, 1):
            out.append(score(row(answer, id=qid, repeat=n), q))
    return out


RIGHT = "Apple's fiscal 2025 revenue was $416.2 billion."


def test_a_rate_is_per_question_first_then_averaged() -> None:
    s = scores_for({"held-901": [RIGHT, RIGHT, RIGHT], "held-902": [RIGHT, ABSTAIN, ABSTAIN]})
    assert rate(s, lambda r: r.correct) == pytest.approx((1 + 1 / 3) / 2)
    assert rate(s, lambda r: r.abstained) == pytest.approx((0 + 2 / 3) / 2)


def test_a_question_not_scored_is_left_out_of_every_rate() -> None:
    s = scores_for(
        {"held-901": [RIGHT, RIGHT, RIGHT], "held-902": [ABSTAIN, ABSTAIN, ABSTAIN]},
        scored={"held-902": False},
    )
    assert rate(s, lambda r: r.correct) == 1.0
    assert rate(s, lambda r: r.abstained) == 0.0


def test_the_error_share_counts_error_rows() -> None:
    s = scores_for({"held-901": [RIGHT, RIGHT, RIGHT]})
    s.append(score(row(None, id="held-902", error="x"), question(id="held-902")))
    assert error_share(s) == 0.25


def test_noise_is_the_share_of_questions_whose_runs_do_not_all_agree() -> None:
    s = scores_for({"held-901": [RIGHT, RIGHT, RIGHT], "held-902": [RIGHT, ABSTAIN, RIGHT]})
    assert noise(s) == 0.5


# ---------------------------------------------------------------- the always-abstain floor


def test_the_floor_grades_the_abstain_sentence_and_is_never_confidently_wrong() -> None:
    assert always_abstain(question(), None, set_name="heldout_traps").correct is False
    assert always_abstain(REFUSE, None, set_name="heldout_traps").correct is True  # a refusal fits
    una = question(
        category="unanswerable_text",
        expected_behavior="refuse",
        metric=None,
        gold_value=None,
        gold_unit=None,
        gold_other_years=None,
    )
    s = always_abstain(una, llm("correct"), set_name="dev_unanswerable")
    assert (s.correct, s.confidently_wrong, s.arm) == (True, False, "always-abstain")
