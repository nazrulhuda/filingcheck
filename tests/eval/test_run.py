"""`make eval`: the batch runner, then the grader, then a one-table summary (fake chat only)."""

import json
from pathlib import Path
from typing import Any

from filingcheck.eval.run import results_path, run_eval
from filingcheck.llm import FakeChat, scripted_tool_calls
from tests.agent.test_agent import apple_deps
from tests.eval.test_gold import row

FACT = {"ticker": "AAPL", "fiscal_year": 2025, "metric": "revenue"}


def questions_file(tmp_path: Path) -> Path:
    path = tmp_path / "examples.jsonl"
    rows = [
        row(gold_value=416161000000, gold_source="facts"),
        row(
            id="trap-001",
            set="trap",
            category="lookalike_company",
            question="How much net revenue did Morgan report last year?",
            company=None,
            fiscal_year=None,
            expected_behavior="clarify",
            style=None,
        ),
    ]
    path.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    return path


def replies() -> list[Any]:
    one_pass: list[Any] = [
        scripted_tool_calls(("get_financial_fact", FACT)),
        "Apple's fiscal 2025 total net sales were $416,161 million [F1].",
        "Do you mean Morgan Stanley or JPMorgan Chase?",
    ]
    return one_pass * 2


def test_the_results_file_is_named_by_date_set_and_mode() -> None:
    assert results_path("examples", "agent", "2026-11-04") == Path(
        "eval/results/2026-11-04_examples_agent.jsonl"
    )


def test_an_eval_run_writes_graded_rows_and_a_summary(tmp_path: Path) -> None:
    out = tmp_path / "2026-11-04_examples_agent.jsonl"
    summary = run_eval(
        questions_file(tmp_path),
        mode="agent",
        repeats=2,
        model=FakeChat(replies()),
        deps=apple_deps(),
        out=out,
        settings="fake settings",
    )
    rows = [json.loads(line) for line in out.read_text(encoding="utf-8").splitlines()]
    assert [(r["id"], r["repeat"]) for r in rows] == [
        ("control-001", 1),
        ("trap-001", 1),
        ("control-001", 2),
        ("trap-001", 2),
    ]
    assert [r["grade"]["outcome"] for r in rows] == ["correct"] * 4
    assert rows[0]["grade"]["matched"] == "416161000000"
    assert summary == out.with_suffix(".md")
    table = summary.read_text(encoding="utf-8")
    assert "| **All** | 4 | 4 | 0 | 0 | 0 | 0 | 0 |" in table
    assert "agent" in table and "fake settings" in table


def test_grading_again_after_a_resumed_run_grades_every_row(tmp_path: Path) -> None:
    out = tmp_path / "run.jsonl"
    questions = questions_file(tmp_path)
    run_eval(
        questions,
        mode="agent",
        repeats=1,
        model=FakeChat(replies()[:3]),
        deps=apple_deps(),
        out=out,
        settings="s",
    )
    run_eval(
        questions,
        mode="agent",
        repeats=2,
        model=FakeChat(replies()[3:]),
        deps=apple_deps(),
        out=out,
        settings="s",
    )
    rows = [json.loads(line) for line in out.read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 4 and all(r["grade"]["outcome"] == "correct" for r in rows)
