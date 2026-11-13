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
    assert "| **All** | 4 | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |" in table
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


def test_a_blank_line_in_a_results_file_is_skipped(tmp_path: Path) -> None:
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
    out.write_text(out.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    summary = run_eval(
        questions,
        mode="agent",
        repeats=1,
        model=FakeChat([]),
        deps=apple_deps(),
        out=out,
        settings="s",
    )
    assert "| **All** | 2 |" in summary.read_text(encoding="utf-8")


def test_stale_rows_do_not_make_an_unfinished_file_look_finished(tmp_path: Path) -> None:
    from filingcheck.eval.run import choose_results_path

    results = tmp_path / "eval" / "results"
    results.mkdir(parents=True)
    old = results / "2026-11-04_examples_agent.jsonl"
    old.write_text(
        '{"id": "gone-001", "repeat": 1}\n{"id": "control-001", "repeat": 1}\n', encoding="utf-8"
    )
    pick = choose_results_path(
        tmp_path,
        "examples",
        "agent",
        expected_rows=2,
        today="2026-11-05",
        question_ids={"control-001", "trap-001"},
    )
    assert pick == old  # only one of its two rows belongs to a current question


def test_a_question_with_a_page_filter_is_asked_with_it_like_the_page(tmp_path: Path) -> None:
    path = tmp_path / "dev.jsonl"
    filtered = row(
        id="dev-001",
        set="trap",
        category="relative_year",
        question="What was revenue last year?",
        company="AAPL",
        style=None,
        page_filter={"ticker": "AAPL", "fiscal_year": 2025},
    )
    path.write_text(json.dumps(filtered) + "\n", encoding="utf-8")
    chat = FakeChat(
        [scripted_tool_calls(("get_financial_fact", FACT)), "Sales were $416,161 million [F1]."]
    )
    out = tmp_path / "2026-11-12_dev_agent.jsonl"
    run_eval(path, mode="agent", repeats=1, model=chat, deps=apple_deps(), out=out, settings="s")
    user = chat.calls[0]["messages"][1]["content"]
    assert "AAPL" in user and "2025" in user
    (line,) = [json.loads(x) for x in out.read_text(encoding="utf-8").splitlines()]
    assert line["page_filter"] == {"ticker": "AAPL", "fiscal_year": 2025}


def test_several_sets_are_named_in_one_argument() -> None:
    from filingcheck.eval.run import set_names

    assert set_names("dev_traps,dev_unanswerable,control") == [
        "dev_traps",
        "dev_unanswerable",
        "control",
    ]
    assert set_names(" examples ") == ["examples"]
    assert set_names("a,,a") == ["a"]  # blanks dropped, repeats once


def test_the_run_record_names_the_commit_and_hashes_the_question_file(tmp_path: Path) -> None:
    import hashlib
    import re

    from filingcheck.eval.run import provenance

    questions = questions_file(tmp_path)
    record = provenance(questions)
    assert re.fullmatch(r"[0-9a-f]{40}", record["git_commit"] or "")
    assert isinstance(record["git_clean"], bool)
    assert record["questions_sha256"] == hashlib.sha256(questions.read_bytes()).hexdigest()


def test_an_eval_runs_rows_carry_the_run_record(tmp_path: Path) -> None:
    out = tmp_path / "2026-11-04_examples_agent.jsonl"
    run_eval(
        questions_file(tmp_path),
        mode="agent",
        repeats=1,
        model=FakeChat(replies()[: len(replies()) // 2]),
        deps=apple_deps(),
        out=out,
        settings="fake settings",
    )
    rows = [json.loads(line) for line in out.read_text(encoding="utf-8").splitlines()]
    assert all(len(r["questions_sha256"]) == 64 and r["git_commit"] for r in rows)


def test_a_new_results_file_does_not_make_the_tree_unclean_but_a_changed_file_does(
    tmp_path: Path,
) -> None:
    """In a run of several sets, the earlier sets' new result files must not count as changes."""
    import subprocess

    from filingcheck.eval.run import provenance

    def git(*args: str) -> None:
        subprocess.run(["git", *args], cwd=tmp_path, check=True, capture_output=True)

    git("init", "-q")
    git("config", "user.email", "test@example.com")
    git("config", "user.name", "test")
    questions = questions_file(tmp_path)
    git("add", ".")
    git("commit", "-q", "-m", "questions")
    (tmp_path / "2026-11-13_examples_agent.jsonl").write_text("{}\n", encoding="utf-8")
    assert provenance(questions, root=tmp_path)["git_clean"] is True  # a new, untracked file
    questions.write_text(questions.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    assert provenance(questions, root=tmp_path)["git_clean"] is False  # a tracked file changed
