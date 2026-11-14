"""Day 24: the agent with the checks off and on, side by side (fake chat and synthetic rows)."""

import json
from pathlib import Path
from typing import Any

import pytest

from filingcheck.checks import reference_data
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
from filingcheck.tools import ToolDeps
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
    deps = apple_deps()
    if checks:  # as make eval does: the checks read the company list and the manifest
        deps = ToolDeps(retriever=deps.retriever, facts=deps.facts, **reference_data())
    summary = run_eval(
        questions_file(tmp_path),
        mode="agent",
        repeats=1,
        model=FakeChat(replies()[:3]),
        deps=deps,
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
        lines[off] == "| Checks off | 6 | 2 | 0 | 2 | 0 | 0 | 0 | 1 | 0 | 1 | 0 | 0 | 0 | 2 "
        "| $0.000600 | 2.0 s |"
    )
    assert (
        lines[off + 1] == "| Checks on | 6 | 5 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 5 "
        "| $0.001200 | 4.0 s |"
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


def test_the_last_column_says_outcomes_differ_and_a_note_says_what_that_means() -> None:
    text = compare_arms(OFF, ON, set_name="examples", off_file="off.jsonl", on_file="on.jsonl")
    assert "| Question | Checks off | Checks on | What the checks did | Outcomes differ |" in text
    assert "| Changed |" not in text
    assert (
        "Outcomes can differ from model variance alone; a check changed an answer only where "
        '"What the checks did" shows a repair or a reject.' in text
    )
    table_end = text.rindex("| control-001 |")
    assert text.index("Outcomes can differ") > table_end  # the note sits under the table


def test_a_label_names_a_separate_run_of_the_same_arm() -> None:
    """A re-run after a change (the search-year check) gets its own files, both arms alike."""
    from filingcheck.eval.arms import arm_name

    assert arm_name("agent", True, label="search-year") == "agent-checks-on-search-year"
    assert arm_name("agent", False, label="search-year") == "agent-checks-off-search-year"
    assert arm_name("agent", True) == "agent-checks-on"
    assert arm_name("baseline", None, label="x") == "baseline-x"


def test_the_baselines_search_is_named_in_its_file() -> None:
    import pytest

    from filingcheck.eval.arms import arm_name

    assert arm_name("baseline", None, retriever="vector") == "baseline-vector"
    assert arm_name("baseline", None, retriever="hybrid") == "baseline"
    assert arm_name("baseline", None) == "baseline"
    with pytest.raises(ValueError, match="hybrid"):
        arm_name("agent", True, retriever="vector")  # the agent always searches hybrid


# ---------------------------------------------------------------- the prompt-rules arm (Day 39)


def test_the_prompt_rules_arm_is_named_and_has_the_checks_off() -> None:
    assert arm_name("agent", False, rules=True) == "agent-prompt-rules"
    assert arm_name("agent", False, "v2", rules=True) == "agent-prompt-rules-v2"
    with pytest.raises(ValueError, match="CHECKS=off"):
        arm_name("agent", True, rules=True)  # make eval's checks are on unless CHECKS=off
    with pytest.raises(ValueError, match="agent"):
        arm_name("baseline", None, rules=True)


def test_the_prompt_rules_arm_runs_with_the_block_in_the_prompt_and_the_checks_off(
    tmp_path: Path,
) -> None:
    from filingcheck.agent import SYSTEM_PROMPT

    out = tmp_path / f"2026-11-13_examples_{arm_name('agent', False, rules=True)}.jsonl"
    chat = FakeChat(replies()[:3])
    summary = run_eval(
        questions_file(tmp_path),
        mode="agent",
        repeats=1,
        model=chat,
        deps=apple_deps(),
        out=out,
        settings="s",
        checks=False,
        rules="THE BLOCK",
    )
    rows = [json.loads(line) for line in out.read_text(encoding="utf-8").splitlines()]
    assert {r["rules"] for r in rows} == {"prompt"}
    assert {r["checks"] for r in rows} == {False}
    assert all(r["overrides"] == [] for r in rows)
    assert {c["messages"][0]["content"] for c in chat.calls} == {SYSTEM_PROMPT + "\n\nTHE BLOCK"}
    assert "agent, checks off, the checks' rules in the prompt" in summary.read_text(
        encoding="utf-8"
    )


def test_rows_without_the_block_record_no_rules(tmp_path: Path) -> None:
    out = tmp_path / "2026-11-13_examples_agent-checks-off.jsonl"
    run_eval(
        questions_file(tmp_path),
        mode="agent",
        repeats=1,
        model=FakeChat(replies()[:3]),
        deps=apple_deps(),
        out=out,
        settings="s",
        checks=False,
    )
    rows = [json.loads(line) for line in out.read_text(encoding="utf-8").splitlines()]
    assert {r["rules"] for r in rows} == {None}


def test_make_eval_takes_rules_prompt() -> None:
    from filingcheck.eval.__main__ import build_parser

    args = build_parser().parse_args(
        ["run", "--set", "dev_traps", "--mode", "agent", "--checks", "off", "--rules", "prompt"]
    )
    assert args.rules == "prompt"
    assert build_parser().parse_args(["run", "--set", "x", "--mode", "agent"]).rules is None
    with pytest.raises(SystemExit):
        build_parser().parse_args(["run", "--set", "x", "--mode", "agent", "--rules", "other"])


def test_the_two_arm_page_is_for_the_checks_off_and_on_arms_only() -> None:
    """The prompt-rules arm has the checks off but is not the checks-off arm: no two-arm page."""
    from filingcheck.eval.arms import writes_two_arm_page

    assert writes_two_arm_page(True, rules=False)
    assert writes_two_arm_page(False, rules=False)
    assert not writes_two_arm_page(False, rules=True)
    assert not writes_two_arm_page(None, rules=False)  # the baseline
