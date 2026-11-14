"""The metrics report and its per-run CSV (the pre-registration's columns, in its order)."""

import csv
from pathlib import Path

from filingcheck.eval.metrics import score_run
from filingcheck.eval.metrics_report import CSV_COLUMNS, render, write_csv
from tests.eval.test_metrics import question, row

SPEC_COLUMNS = (
    "set, id, repeat, arm, category, expected_behavior, graded_by, outcome, llm_verdict, correct, "
    "confidently_wrong, confidently_wrong_no_labels, confidently_wrong_both_graders, "
    "wrong_arg_ran, wrong_arg_sent, segment_total_calls, calls_ran, abstained, false_repair, "
    "latency_ms, cost_usd, error"
)
RIGHT = "Apple's fiscal 2025 revenue was $416.2 billion."
WRONG = "Apple's fiscal 2025 revenue was $5 billion."


def scores() -> list:  # type: ignore[type-arg]
    out = []
    for arm, answers in (
        ("agent-checks-off", [WRONG, WRONG, RIGHT]),
        ("agent-checks-on", [RIGHT] * 3),
    ):
        for n, answer in enumerate(answers, 1):
            out.append(
                score_run(row(answer, repeat=n), question(), None, set_name="dev_traps", arm=arm)
            )
    return out


def test_the_csv_has_the_preregistered_columns_in_order(tmp_path: Path) -> None:
    assert ", ".join(CSV_COLUMNS) == SPEC_COLUMNS
    out = tmp_path / "runs.csv"
    write_csv(scores(), out)
    with out.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert list(rows[0]) == list(CSV_COLUMNS) and len(rows) == 6
    assert (rows[0]["set"], rows[0]["arm"], rows[0]["correct"], rows[0]["wrong_arg_sent"]) == (
        "dev_traps",
        "agent-checks-off",
        "False",
        "0",  # no number-tool call: none wrong as sent (blank only when a call lacks the record)
    )


def test_the_report_carries_its_heading_and_the_comparison() -> None:
    page = render(
        scores(),
        floor=[],
        title="Metrics demo",
        heading="Development rows from the Week 5 dry run; a check of the code, not a result.",
        notes=[],
    )
    assert page.startswith("# Metrics demo\n\nDevelopment rows from the Week 5 dry run; a check")
    assert "## Checks on against off" in page
    assert "| dev_traps | accuracy | 33.3% | 100.0% | +66.7 points |" in page


def test_the_report_lists_the_questions_not_scored_with_their_reasons() -> None:
    from filingcheck.eval.metrics import score_run

    q = question(id="held-948", scored=False, not_scored_reason="it repeats dev-017")
    s = [
        score_run(
            row(RIGHT, id="held-948"), q, None, set_name="heldout_traps_2", arm="agent-checks-on"
        )
    ]
    page = render(s, floor=[], title="T", heading="H", notes=[])
    assert "## Questions not scored" in page and "held-948: it repeats dev-017" in page


def test_the_graders_disagree_when_one_passes_what_the_other_fails_and_pairings_show() -> None:
    from filingcheck.eval.metrics import score_run
    from tests.eval.test_metrics import REFUSE, llm

    answer = "iPhone net sales for fiscal 2025 were $416,161,000,000."
    s = [
        score_run(
            row(answer, repeat=1),
            REFUSE,
            llm("correct", "second opinion"),
            set_name="dev_traps",
            arm="agent-checks-on",
        ),
        score_run(
            row(answer, repeat=2),
            REFUSE,
            llm("wrong", "second opinion"),
            set_name="dev_traps",
            arm="agent-checks-on",
        ),
        score_run(
            row("Which year?", repeat=3),
            question(),
            llm("wrong", "second opinion"),
            set_name="dev_traps",
            arm="agent-checks-on",
        ),
    ]
    page = render(s, floor=[], title="T", heading="H", notes=[])
    assert "where one grader passes the run and the other fails it: 1" in page
    assert "| answered_when_should_ask | correct | 1 |" in page
    assert "| asked_when_should_answer | wrong | 1 |" in page


def test_a_stopped_number_call_without_a_checks_reject_record_is_flagged() -> None:
    from filingcheck.eval.metrics import score_run

    call = {"name": "get_financial_fact", "arguments": {"ticker": "Apple"}, "status": "error"}
    checked = score_run(
        row("x", tool_calls=[call], overrides=[{"check": "company", "outcome": "reject"}]),
        question(),
        None,
        set_name="dev_traps",
        arm="agent-checks-on",
    )
    unchecked = score_run(
        row("x", tool_calls=[call], repeat=2),
        question(),
        None,
        set_name="dev_traps",
        arm="agent-checks-off",
    )
    assert (checked.stopped_calls, checked.check_rejects) == (1, 1)
    page = render([checked, unchecked], floor=[], title="T", heading="H", notes=[])
    assert "stopped without a check's reject record: 1" in page and "list them and ask" in page


def test_the_graders_disagreement_is_counted_in_each_direction() -> None:
    from filingcheck.eval.metrics import score_run
    from tests.eval.test_metrics import llm

    passed_by_both = score_run(
        row(RIGHT, repeat=1),
        question(),
        llm("correct", "second opinion"),
        set_name="d",
        arm="agent-checks-on",
    )
    det_passes = score_run(
        row(RIGHT, repeat=2),
        question(),
        llm("wrong", "second opinion"),
        set_name="d",
        arm="agent-checks-on",
    )
    det_fails = score_run(
        row(WRONG, repeat=3),
        question(),
        llm("correct", "second opinion"),
        set_name="d",
        arm="agent-checks-on",
    )
    page = render(
        [passed_by_both, det_passes, det_fails], floor=[], title="T", heading="H", notes=[]
    )
    assert "the deterministic grader passes and the LLM fails: 1" in page
    assert "the deterministic grader fails and the LLM passes: 1" in page
