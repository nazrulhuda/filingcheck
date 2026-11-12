"""The dry-run report: each table is computed from result rows, their grades and the LLM grades."""

from typing import Any

from filingcheck.eval.dryrun import (
    arm_summary,
    check_activity,
    disagreements,
    false_repairs,
    label_shares,
    no_tool_call_rows,
    percentile,
    report,
    text_support,
)
from filingcheck.eval.grade import Grade
from filingcheck.eval.llm_grade import LlmGrade
from filingcheck.eval.questions import Question


def question(qid: str, category: str, **over: Any) -> Question:
    fields: dict[str, Any] = {
        "id": qid,
        "set": "control" if category == "control" else "trap",
        "category": category,
        "question": "What was Apple's revenue in fiscal 2025?",
        "company": "AAPL",
        "fiscal_year": 2025,
        "metric": "revenue",
        "expected_behavior": "answer",
        "gold_value": 416161000000,
        "gold_unit": "USD",
        "style": "metrics-generated" if category == "control" else None,
    }
    return Question.model_validate(fields | over)


def row(qid: str, repeat: int = 1, **over: Any) -> dict[str, Any]:
    fields: dict[str, Any] = {
        "id": qid,
        "repeat": repeat,
        "answer": "Apple's fiscal 2025 revenue was $416.2 billion [F1].",
        "cost_usd": 0.0003,
        "latency_ms": 1000.0,
        "tool_calls": [{"name": "get_financial_fact", "status": "ok"}],
        "overrides": [{"check": "company", "outcome": "pass"}],
        "number_labels": [{"figure": "$416.2 billion", "label": "verified"}],
    }
    return fields | over


def graded(outcome: str, **over: Any) -> Grade:
    return Grade(outcome=outcome, numbers=[], matched=None, year_stated=True, **over)  # type: ignore[arg-type]


def llm(qid: str, repeat: int, use: str, verdict: str | None, supported: str | None) -> LlmGrade:
    return LlmGrade(
        id=qid,
        repeat=repeat,
        use=use,
        verdict=verdict,  # type: ignore[arg-type]
        supported=supported,  # type: ignore[arg-type]
        reason="because",
        evidence="",
        model="fake",
        prompt_version="2-abc",
        cost_usd=0.0002,
        cached=False,
    )


QUESTIONS = {
    "control-101": question("control-101", "control"),
    "dev-026": question("dev-026", "relative_year"),
    "dev-013": question("dev-013", "wrong_fiscal_year"),
}


def test_percentiles_use_the_nearest_rank() -> None:
    values = [100.0, 200.0, 300.0, 400.0, 500.0, 600.0, 700.0, 800.0, 900.0, 1000.0]
    assert percentile(values, 50) == 500.0
    assert percentile(values, 95) == 1000.0
    assert percentile([250.0], 95) == 250.0


def test_the_arm_summary_counts_outcomes_verdicts_abstains_cost_and_latency() -> None:
    rows = [
        (row("control-101", 1), graded("correct")),
        (
            row(
                "control-101",
                2,
                latency_ms=3000.0,
                answer="I can't find this in the filings I have.",
            ),
            graded("abstained"),
        ),
        (
            row("dev-026", 1, latency_ms=2000.0),
            graded("asked_when_should_answer", lenient_outcome=None),
        ),
    ]
    grades = {("control-101", 2): llm("control-101", 2, "second opinion", "abstained", "n/a")}
    summary = arm_summary(rows, grades)
    assert summary["runs"] == 3
    assert summary["outcomes"]["correct"] == 1 and summary["outcomes"]["abstained"] == 1
    assert summary["abstained"] == 1 and summary["abstain_rate"] == 1 / 3
    assert summary["verdicts"]["abstained"] == 1
    assert summary["cost_usd"] == 0.0009
    assert (summary["p50_ms"], summary["p95_ms"]) == (2000.0, 3000.0)


def test_check_activity_counts_passes_repairs_and_rejects_per_category() -> None:
    rows = [
        row(
            "dev-013",
            overrides=[
                {"check": "fiscal_year", "outcome": "repair"},
                {"check": "company", "outcome": "pass"},
            ],
        ),
        row("dev-013", 2, overrides=[{"check": "company", "outcome": "reject"}]),
        row("control-101", overrides=[]),  # no fact call: counts nothing
    ]
    activity = check_activity(rows, QUESTIONS)
    assert activity[("wrong_fiscal_year", "get_financial_fact")] == {
        "pass": 1,
        "repair": 1,
        "reject": 1,
    }
    assert not [key for key in activity if key[0] == "control"]


def test_a_repair_or_reject_on_a_control_question_is_a_false_repair() -> None:
    rows = [
        row("control-101", 1),
        row("control-101", 2, overrides=[{"check": "units", "outcome": "repair", "reason": "x"}]),
        row("dev-013", 1, overrides=[{"check": "fiscal_year", "outcome": "reject"}]),
    ]
    found = false_repairs(rows, QUESTIONS)
    assert [(r["id"], r["repeat"]) for r in found] == [("control-101", 2)]


def test_label_shares_split_correct_and_wrong_number_answers() -> None:
    rows = [
        (row("control-101", 1), graded("correct")),
        (
            row(
                "control-101",
                2,
                number_labels=[
                    {"figure": "$5 billion", "label": "unverified"},
                    {"figure": "$416.2 billion", "label": "verified"},
                    {"figure": "$3", "label": "conflict"},
                ],
            ),
            graded("wrong_number"),
        ),
    ]
    shares = label_shares(rows)
    assert shares["correct"] == {"figures": 1, "verified": 1}
    assert shares["wrong_number"] == {"figures": 3, "verified": 1, "conflict": 1, "unverified": 1}
    assert shares["verified_in_wrong"] == [("control-101", 2, "$416.2 billion")]


def test_text_support_counts_no_and_partly_among_text_answers() -> None:
    grades = [
        llm("control-131", 1, "text", "correct", "yes"),
        llm("control-131", 2, "text", "correct", "partly"),
        llm("control-132", 1, "text", "wrong", "no"),
        llm("dev-013", 1, "second opinion", "wrong", "yes"),  # not a text answer
    ]
    assert text_support(grades) == {
        "text_answers": 3,
        "no": 1,
        "partly": 1,
        "unsupported_rate": 2 / 3,
    }


def test_disagreements_list_every_row_where_the_two_grades_do_not_agree() -> None:
    rows = [
        (row("dev-013", 1), graded("wrong_number")),
        (row("dev-013", 2), graded("abstained")),
        (row("dev-026", 1), graded("asked_when_should_answer")),
        (row("dev-026", 2), graded("other_year_number")),
    ]
    grades = {
        ("dev-013", 1): llm("dev-013", 1, "second opinion", "correct", "yes"),  # the LLM passes it
        ("dev-013", 2): llm("dev-013", 2, "second opinion", "abstained", "n/a"),  # agree
        ("dev-026", 1): llm("dev-026", 1, "second opinion", "asked", "n/a"),  # agree
        ("dev-026", 2): llm("dev-026", 2, "second opinion", "partly", "yes"),  # wrong-ish: agree
    }
    found = disagreements(rows, grades)
    assert [(r["id"], r["repeat"], kind) for r, _, _, kind in found] == [
        ("dev-013", 1, "the LLM grader passes a row the deterministic grader failed")
    ]


def test_relative_year_rows_with_no_tool_call_are_listed() -> None:
    rows = [
        row("dev-026", 1, tool_calls=[]),
        row("dev-026", 2),
        row("dev-013", 1, tool_calls=[]),  # not relative_year
    ]
    found = no_tool_call_rows(rows, QUESTIONS, category="relative_year")
    assert [(r["id"], r["repeat"]) for r in found] == [("dev-026", 1)]


def test_the_report_has_the_dry_run_heading_and_every_section() -> None:
    arms: dict[str, dict[str, tuple[Any, Any]]] = {
        "dev_traps": {
            "checks off": ([(row("dev-013", 1), graded("wrong_number"))], {}),
            "checks on": ([(row("dev-013", 1), graded("correct"))], {}),
        }
    }
    page = report(arms, QUESTIONS, date="2026-11-12")
    assert page.startswith("# Dry run: pipeline check, not results")
    for heading in (
        "## Per set and arm",
        "## Check activity",
        "## False repairs on control questions",
        "## Labels",
        "## Text support",
        "## Grader disagreements",
        "## Relative-year runs with no tool call",
    ):
        assert heading in page, heading


def test_search_years_compare_the_year_sent_with_the_years_the_company_holds() -> None:
    from filingcheck.eval.dryrun import search_years

    text = question(
        "control-131", "control", gold_value=None, gold_unit=None, gold_text="Beaverton"
    )
    questions = {"control-131": text, "control-101": question("control-101", "control")}
    held = {"AAPL": {2024, 2025, 2026}}

    def call(year: int | None, ticker: str = "AAPL") -> dict[str, Any]:
        return {"name": "search_filings", "arguments": {"ticker": ticker, "fiscal_year": year}}

    rows = [
        row("control-131", 1, tool_calls=[call(2026), call(2023)]),  # latest; not held
        row("control-131", 2, tool_calls=[call(2024), call(None)]),  # earlier held year; no year
        row("control-131", 3, tool_calls=[{"name": "get_financial_fact", "arguments": {}}]),
        row("control-101", 1, tool_calls=[call(2023)]),  # a number question: not counted
    ]
    table = search_years(rows, questions, held)
    assert table["calls"] == 4
    assert table["by_year"] == {2026: 1, 2024: 1, 2023: 1, None: 1}
    assert (table["latest"], table["earlier_held"], table["not_held"], table["no_year"]) == (
        1,
        1,
        1,
        1,
    )


def test_false_repairs_count_the_number_tool_only_and_search_repairs_are_listed_apart() -> None:
    """The search-year check repairs by design on a control question that names no year."""
    from filingcheck.eval.dryrun import search_repairs

    rows = [
        row(
            "control-101",
            1,
            overrides=[{"check": "fiscal_year", "outcome": "repair", "tool": "search_filings"}],
        ),
        row(
            "control-101",
            2,
            overrides=[{"check": "units", "outcome": "repair", "tool": "get_financial_fact"}],
        ),
        row(
            "control-101", 3, overrides=[{"check": "company", "outcome": "reject"}]
        ),  # an old row: no tool
    ]
    assert [(r["repeat"]) for r in false_repairs(rows, QUESTIONS)] == [2, 3]
    assert search_repairs(rows, QUESTIONS) == {"repair": 1, "reject": 0}


def test_check_activity_tells_the_two_tools_apart() -> None:
    rows = [
        row(
            "dev-013",
            overrides=[
                {"check": "fiscal_year", "outcome": "repair", "tool": "search_filings"},
                {"check": "company", "outcome": "pass", "tool": "get_financial_fact"},
            ],
        ),
        row(
            "dev-013", 2, overrides=[{"check": "company", "outcome": "reject"}]
        ),  # an old row counts as the number tool
    ]
    activity = check_activity(rows, QUESTIONS)
    assert activity[("wrong_fiscal_year", "get_financial_fact")] == {"pass": 1, "reject": 1}
    assert activity[("wrong_fiscal_year", "search_filings")] == {"repair": 1}
