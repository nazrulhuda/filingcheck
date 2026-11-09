"""Day 24: the agent with the checks off and on, side by side (fake chat and synthetic rows)."""

import json
from pathlib import Path
from typing import Any

import pytest

from filingcheck.eval.arms import (
    arm_name,
    arms_path,
    checks_argument,
    compare_arms,
    finished_arm,
)
from filingcheck.eval.grade import Grade
from filingcheck.eval.run import run_eval
from filingcheck.llm import FakeChat
from tests.agent.test_agent import apple_deps
from tests.eval.test_run import questions_file, replies

# ---------------------------------------------------------------- names and the switch


def test_the_arm_is_in_the_name() -> None:
    assert arm_name("agent", True) == "agent-checks-on"
    assert arm_name("agent", False) == "agent-checks-off"
    assert arm_name("baseline", None) == "baseline"


def test_the_baseline_has_no_checks_arm() -> None:
    with pytest.raises(ValueError, match="agent"):
        arm_name("baseline", True)


@pytest.mark.parametrize(
    ("mode", "value", "expected"),
    [
        ("agent", None, True),  # on by default, as in make ask, the batch command and the API
        ("agent", "on", True),
        ("agent", "1", True),
        ("agent", "off", False),
        ("agent", "0", False),
        ("baseline", None, None),
    ],
)
def test_the_checks_argument(mode: str, value: str | None, expected: bool | None) -> None:
    assert checks_argument(mode, value) is expected


def test_checks_on_the_baseline_is_an_error() -> None:
    with pytest.raises(ValueError, match="agent"):
        checks_argument("baseline", "on")


def test_the_comparison_file_is_named_by_date_and_set() -> None:
    assert arms_path("examples", "2026-11-09") == Path(
        "eval/results/2026-11-09_examples_agent-arms.md"
    )


# ---------------------------------------------------------------- run_eval with the switch


@pytest.mark.parametrize(("checks", "label"), [(True, "checks on"), (False, "checks off")])
def test_an_eval_run_passes_the_switch_and_names_the_arm(
    tmp_path: Path, checks: bool, label: str
) -> None:
    out = tmp_path / f"2026-11-09_examples_{arm_name('agent', checks)}.jsonl"
    summary = run_eval(
        questions_file(tmp_path),
        mode="agent",
        repeats=1,
        model=FakeChat(replies()[:3]),
        deps=apple_deps(),
        out=out,
        settings="s",
        checks=checks,
    )
    rows = [json.loads(line) for line in out.read_text(encoding="utf-8").splitlines()]
    assert {r["checks"] for r in rows} == {checks}
    fact_row = next(r for r in rows if r["id"] == "control-001")
    assert bool(fact_row["overrides"]) is checks  # the log is filled only with the checks on
    assert f"agent, {label}" in summary.read_text(encoding="utf-8")


# ---------------------------------------------------------------- finding the other arm


def write_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")


def test_the_newest_finished_file_of_an_arm_is_found(tmp_path: Path) -> None:
    results = tmp_path / "eval" / "results"
    ids = {"q-1", "q-2"}
    full = [{"id": i, "repeat": 1} for i in sorted(ids)]
    write_rows(results / "2026-11-07_examples_agent-checks-off.jsonl", full)
    write_rows(results / "2026-11-09_examples_agent-checks-off.jsonl", full[:1])  # unfinished
    write_rows(results / "2026-11-08_examples_agent-checks-on.jsonl", full)
    write_rows(results / "2026-11-08_examples_agent.jsonl", full)  # Day 20: no arm in the name
    found = finished_arm(
        tmp_path, "examples", "agent-checks-off", expected_rows=2, question_ids=ids
    )
    assert found == results / "2026-11-07_examples_agent-checks-off.jsonl"
    assert (
        finished_arm(tmp_path, "trap", "agent-checks-off", expected_rows=2, question_ids=ids)
        is None
    )


# ---------------------------------------------------------------- the comparison


def graded(
    qid: str,
    repeat: int,
    outcome: str,
    overrides: list[dict[str, Any]] | None,
    cost: float = 0.0001,
    ms: float = 2000.0,
) -> tuple[dict[str, Any], Grade]:
    row = {
        "id": qid,
        "repeat": repeat,
        "cost_usd": cost,
        "latency_ms": ms,
        "overrides": overrides,
        "tool_calls": [] if overrides is None else [{"name": "get_financial_fact"}],
    }
    grade = Grade(outcome=outcome, numbers=[], matched=None, year_stated=True)  # type: ignore[arg-type]
    return row, grade


def override(check: str, outcome: str) -> dict[str, Any]:
    return {"check": check, "outcome": outcome, "argument": None, "reason": "r"}


PASSES = [override(c, "pass") for c in ("company", "fiscal_year", "metric", "units", "segment")]
REPAIR = [
    override("company", "pass"),
    override("fiscal_year", "repair"),
    *[override(c, "pass") for c in ("metric", "units", "segment")],
]
REJECT = [override("company", "reject")]

OFF = [
    graded("trap-003", 1, "other_year_number", []),
    graded("trap-003", 2, "other_year_number", []),
    graded("trap-003", 3, "correct", []),
    graded("trap-001", 1, "answered_when_should_ask", []),
    graded("trap-001", 2, "abstained", None),
    graded("control-001", 1, "correct", []),
]
ON = [
    graded("trap-003", 1, "correct", REPAIR, cost=0.0002, ms=4000.0),
    graded("trap-003", 2, "correct", REPAIR, cost=0.0002, ms=4000.0),
    graded("trap-003", 3, "correct", REPAIR, cost=0.0002, ms=4000.0),
    graded("trap-001", 1, "correct", REJECT, cost=0.0002, ms=4000.0),
    graded("trap-001", 2, "abstained", None, cost=0.0002, ms=4000.0),
    graded("control-001", 1, "correct", PASSES, cost=0.0002, ms=4000.0),
]


def test_the_two_arms_are_two_rows_one_under_the_other() -> None:
    text = compare_arms(OFF, ON, set_name="examples", off_file="off.jsonl", on_file="on.jsonl")
    lines = text.splitlines()
    off = next(i for i, line in enumerate(lines) if line.startswith("| Checks off |"))
    assert lines[off + 1].startswith("| Checks on |")
    assert (
        lines[off]
        == "| Checks off | 6 | 2 | 0 | 2 | 0 | 0 | 0 | 1 | 1 | 0 | 0 | $0.000600 | 2.0 s |"
    )
    assert (
        lines[off + 1]
        == "| Checks on | 6 | 5 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | $0.001200 | 4.0 s |"
    )
    assert "`off.jsonl`" in text and "`on.jsonl`" in text


def test_each_question_shows_both_arms_what_the_checks_did_and_whether_it_changed() -> None:
    text = compare_arms(OFF, ON, set_name="examples", off_file="off.jsonl", on_file="on.jsonl")
    assert (
        "| trap-003 | Correct x1, Other year's number x2 | Correct x3 "
        "| fiscal_year repair x3 | yes |" in text
    )
    assert (
        "| trap-001 | Answered when it should have asked x1, Abstained x1 "
        "| Correct x1, Abstained x1 | company reject x1, no fact call x1 | yes |" in text
    )
    assert "| control-001 | Correct x1 | Correct x1 | pass x1 | no |" in text


def test_the_comparison_says_how_little_a_few_questions_prove() -> None:
    text = compare_arms(OFF, ON, set_name="examples", off_file="off.jsonl", on_file="on.jsonl")
    assert "3 questions" in text and "prove nothing" in text


def test_a_question_missing_from_one_arm_is_shown_as_not_run() -> None:
    text = compare_arms(OFF, ON[:3], set_name="examples", off_file="a", on_file="b")
    assert (
        "| trap-001 | Answered when it should have asked x1, Abstained x1 | not run | - | - |"
        in text
    )
