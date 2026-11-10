"""`python -m filingcheck.eval`: the paths that need no database, model or network."""

import json
from pathlib import Path
from typing import Any

import pytest

import filingcheck.eval.__main__ as cli
import filingcheck.paths
from filingcheck.eval.grade import Grade
from tests.eval.test_run import questions_file


def graded_row(qid: str, outcome: str, checks: bool) -> dict[str, Any]:
    grade = Grade(outcome=outcome, numbers=[], matched=None, year_stated=True)  # type: ignore[arg-type]
    overrides = [{"check": "company", "outcome": "pass"}] if checks else []
    return {
        "id": qid,
        "repeat": 1,
        "cost_usd": 0.0001,
        "latency_ms": 1000.0,
        "checks": checks,
        "overrides": overrides,
        "grade": grade.model_dump(),
    }


def write(path: Path, rows: list[dict[str, Any]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    return path


def test_after_an_agent_run_the_comparison_is_written_when_the_other_arm_is_finished(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(cli, "REPO_ROOT", tmp_path)
    questions = questions_file(tmp_path)
    results = tmp_path / "eval" / "results"
    write(
        results / "2026-11-08_examples_agent-checks-off.jsonl",
        [graded_row("control-001", "abstained", False), graded_row("trap-001", "correct", False)],
    )
    on = write(
        results / "2026-11-09_examples_agent-checks-on.jsonl",
        [graded_row("control-001", "correct", True), graded_row("trap-001", "correct", True)],
    )
    cli._write_arms("examples", on, True, questions, 1)
    page = results / "2026-11-09_examples_agent-arms.md"
    text = page.read_text(encoding="utf-8")
    assert "| Checks off | 2 | 1 |" in text and "| Checks on | 2 | 2 |" in text
    assert "`2026-11-08_examples_agent-checks-off.jsonl`" in text
    assert "wrote eval" in capsys.readouterr().out


def test_without_a_finished_other_arm_no_comparison_is_written(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(cli, "REPO_ROOT", tmp_path)
    questions = questions_file(tmp_path)
    results = tmp_path / "eval" / "results"
    write(
        results / "2026-11-09_examples_agent-checks-on.jsonl",
        [graded_row("trap-001", "correct", True)],
    )
    off = write(
        results / "2026-11-09_examples_agent-checks-off.jsonl",
        [graded_row("control-001", "correct", False)],
    )
    cli._write_arms("examples", off, False, questions, 1)  # the checks-on file is unfinished
    assert not list(results.glob("*_agent-arms.md"))
    assert "no finished agent-checks-on file" in capsys.readouterr().out


def test_gate_fixture_needs_the_facts_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(filingcheck.paths, "DATA_DIR", tmp_path)  # no facts.jsonl here
    assert cli.main(["gate-fixture"]) == 1
    assert "no data/facts.jsonl" in capsys.readouterr().out


def test_checks_on_the_baseline_is_refused_before_anything_runs() -> None:
    with pytest.raises(SystemExit) as stopped:
        cli.main(["run", "--set", "examples", "--mode", "baseline", "--checks", "on"])
    assert stopped.value.code == 2
