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
        "",
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
