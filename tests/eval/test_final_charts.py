"""The README's summary chart: held-out only, four rows with plain names, drawn from the same
scores as the full chart (the same bootstrap interval per arm), with its CSV."""

import csv
from pathlib import Path

from filingcheck.eval.final_charts import SUMMARY_PANELS, SUMMARY_ROWS, chart_summary
from filingcheck.eval.final_render import HELD, OFF, ON, RULES, Final
from filingcheck.eval.final_report import rate_interval
from filingcheck.eval.metrics import RunScore, score_run
from tests.eval.test_metrics import question, row

RIGHT = "Apple's fiscal 2025 revenue was $416.2 billion."
WRONG = "Apple's fiscal 2025 revenue was $5 billion."


def scores(set_name: str, arm: str, answers: list[str]) -> list[RunScore]:
    out: list[RunScore] = []
    for n, answer in enumerate(answers, 1):
        q = question(id=f"{set_name}-{n:03d}")
        out += [
            score_run(row(answer, id=q.id, repeat=r), q, None, set_name=set_name, arm=arm)
            for r in (1, 2, 3)
        ]
    return out


def final() -> Final:
    """Five arms on both held-out files, and a development set that must not count."""
    f = Final()
    for arm, right in (("baseline-vector", 1), ("baseline", 2), (OFF, 4), (RULES, 6), (ON, 5)):
        for set_name in HELD:
            f.scores += scores(set_name, arm, [RIGHT] * right + [WRONG] * (8 - right))
        f.scores += scores("dev_traps", arm, [WRONG] * 8)
    return f


def test_the_summary_chart_has_four_plain_named_rows_from_the_held_out_scores(
    tmp_path: Path,
) -> None:
    f = final()
    chart_summary(f, tmp_path)
    assert (tmp_path / "final_summary.png").exists()
    with (tmp_path / "final_summary.csv").open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    arms = [arm for arm, _ in SUMMARY_ROWS]
    assert arms == ["baseline", OFF, RULES, ON]  # no vector baseline: four rows
    assert [name for _, name in SUMMARY_ROWS] == [
        "search only, no agent (the hybrid baseline)",
        "agent, no checks",
        "agent, rules in the prompt",
        "agent, server checks",
    ]
    assert [title for title, _ in SUMMARY_PANELS] == [
        "Correct answers (higher is better)",
        "Confidently wrong answers (lower is better)",
    ]
    assert [r["arm"] for r in rows] == arms * 2
    assert [r["metric"] for r in rows] == [SUMMARY_PANELS[0][0]] * 4 + [SUMMARY_PANELS[1][0]] * 4
    assert [r["row"] for r in rows][:4] == [name for _, name in SUMMARY_ROWS]

    # The same number as the full chart: rate_interval over the held-out scores of that arm.
    for r in rows:
        value = dict(SUMMARY_PANELS)[r["metric"]]
        i = rate_interval(f.part(HELD, r["arm"]), value)
        assert (float(r["estimate"]), float(r["low"]), float(r["high"])) == (
            i.estimate,
            i.low,
            i.high,
        )
    # Held-out only: with the development set counted, checks off would be 4 of 16, not 4 of 8.
    off_accuracy = next(r for r in rows if r["arm"] == OFF)
    assert float(off_accuracy["estimate"]) == 0.5
