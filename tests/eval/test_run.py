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
    assert "| **All** | 4 | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |" in table
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


def test_a_row_whose_question_was_removed_is_kept_but_not_graded(tmp_path: Path) -> None:
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
    kept = [
        line
        for line in questions.read_text(encoding="utf-8").splitlines()
        if "trap-001" not in line
    ]
    questions.write_text("\n".join(kept) + "\n", encoding="utf-8")
    summary = run_eval(
        questions,
        mode="agent",
        repeats=1,
        model=FakeChat([]),
        deps=apple_deps(),
        out=out,
        settings="s",
    )
    rows = [json.loads(line) for line in out.read_text(encoding="utf-8").splitlines()]
    assert [(r["id"], r["grade"] is None) for r in rows] == [
        ("control-001", False),
        ("trap-001", True),
    ]
    table = summary.read_text(encoding="utf-8")
    assert "| **All** | 1 |" in table and "1 row whose question is no longer in" in table


def test_the_summary_title_counts_the_runs_in_the_file(tmp_path: Path) -> None:
    out = tmp_path / "run.jsonl"
    questions = questions_file(tmp_path)
    run_eval(
        questions,
        mode="agent",
        repeats=2,
        model=FakeChat(replies()),
        deps=apple_deps(),
        out=out,
        settings="s",
    )
    summary = run_eval(
        questions,
        mode="agent",
        repeats=1,
        model=FakeChat([]),
        deps=apple_deps(),
        out=out,
        settings="s",
    )
    assert "2 run(s) per question" in summary.read_text(encoding="utf-8")


def test_resuming_without_a_date_takes_the_date_of_the_unfinished_file(tmp_path: Path) -> None:
    from filingcheck.eval.run import choose_results_path

    results = tmp_path / "eval" / "results"
    results.mkdir(parents=True)
    unfinished = results / "2026-11-04_examples_agent.jsonl"
    unfinished.write_text('{"id": "q-1", "repeat": 1}\n', encoding="utf-8")
    pick = choose_results_path(tmp_path, "examples", "agent", expected_rows=4, today="2026-11-05")
    assert pick == unfinished
    # A finished file is not resumed: a new run gets today's date.
    unfinished.write_text(
        "".join(f'{{"id": "q-{i}", "repeat": 1}}\n' for i in range(4)), encoding="utf-8"
    )
    pick = choose_results_path(tmp_path, "examples", "agent", expected_rows=4, today="2026-11-05")
    assert pick == results / "2026-11-05_examples_agent.jsonl"
    # Another set or mode is never picked.
    (results / "2026-11-03_examples_baseline.jsonl").write_text('{"id": "q-1"}\n', encoding="utf-8")
    pick = choose_results_path(tmp_path, "examples", "agent", expected_rows=4, today="2026-11-05")
    assert pick == results / "2026-11-05_examples_agent.jsonl"
