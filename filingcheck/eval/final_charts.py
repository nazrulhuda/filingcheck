"""The final report's charts (matplotlib PNGs in docs/results/), each with the CSV it is drawn from.

(a) accuracy and confidently wrong per arm, per set, with 95% interval whiskers; (b) the
checks-off → on difference per set with its interval, held-out first; (c) check activity by
question category. Plain dots and bars, axis labels in words, the set size in each title.
"""

import csv
from collections import Counter
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from filingcheck.eval.final_render import (
    ARMS,
    HELD,
    HELD_OUT,
    OFF,
    ON,
    Final,
    _acc,
    _cw,
)
from filingcheck.eval.final_report import compare, rate_interval

PANEL_SETS: tuple[tuple[str, tuple[str, ...]], ...] = (
    (HELD_OUT, HELD),
    ("dev_traps", ("dev_traps",)),
    ("dev_unanswerable", ("dev_unanswerable",)),
    ("control", ("control",)),
)
DIFF_SETS: tuple[tuple[str, tuple[str, ...]], ...] = (
    (HELD_OUT, HELD),
    ("heldout_traps", (HELD[0],)),
    ("heldout_traps_2", (HELD[1],)),
    ("dev_traps", ("dev_traps",)),
    ("dev_unanswerable", ("dev_unanswerable",)),
    ("control", ("control",)),
)


def _questions(f: Final, sets: tuple[str, ...]) -> int:
    return len({s.id for s in f.part(sets, ON) if s.scored})


def _write(path: Path, header: list[str], rows: list[list[object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        out = csv.writer(handle, lineterminator="\n")
        out.writerow(header)
        out.writerows(rows)


def chart_rates(f: Final, out: Path) -> None:
    """(a) Each arm's accuracy and confidently-wrong rate, per set, with 95% whiskers."""
    rows: list[list[object]] = []
    fig, axes = plt.subplots(2, len(PANEL_SETS), figsize=(16, 7), sharey=True)
    for col, (title, sets) in enumerate(PANEL_SETS):
        for row, (name, value) in enumerate((("Accuracy", _acc), ("Confidently wrong", _cw))):
            ax = axes[row][col]
            for y, arm in enumerate(ARMS):
                i = rate_interval(f.part(sets, arm), value)
                rows.append([title, arm, name, i.estimate, i.low, i.high])
                ax.errorbar(
                    100 * i.estimate,
                    y,
                    xerr=[[100 * (i.estimate - i.low)], [100 * (i.high - i.estimate)]],
                    fmt="o",
                    color="black",
                    capsize=3,
                )
            ax.set_yticks(range(len(ARMS)), ARMS)
            ax.set_xlim(0, 100)
            ax.set_xlabel(f"{name}, % of runs (per question first)")
            ax.set_title(f"{title} ({_questions(f, sets)} questions)")
            ax.grid(axis="x", linewidth=0.3)
    fig.suptitle("Accuracy and confidently wrong per arm, with 95% intervals (3 runs per question)")
    fig.tight_layout()
    fig.savefig(out / "final_rates.png", dpi=120)
    plt.close(fig)
    _write(out / "final_rates.csv", ["set", "arm", "metric", "estimate", "low", "high"], rows)


def chart_difference(f: Final, out: Path) -> None:
    """(b) Checks on minus checks off per set, with its paired 95% interval, held-out first."""
    rows: list[list[object]] = []
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.5), sharey=True)
    labels = [f"{title} ({_questions(f, sets)} questions)" for title, sets in DIFF_SETS]
    for ax, (name, value) in zip(
        axes, (("Confidently wrong", _cw), ("Accuracy", _acc)), strict=True
    ):
        for n, (title, sets) in enumerate(DIFF_SETS):
            y = len(DIFF_SETS) - 1 - n  # held-out first, at the top
            c = compare(f.part(sets, OFF), f.part(sets, ON), value, majority=False)
            i = c.interval
            rows.append([title, name, i.estimate, i.low, i.high, c.questions])
            ax.errorbar(
                100 * i.estimate,
                y,
                xerr=[[100 * (i.estimate - i.low)], [100 * (i.high - i.estimate)]],
                fmt="o",
                color="black",
                capsize=3,
            )
        ax.axvline(0, color="grey", linewidth=0.8)
        ax.set_yticks(range(len(DIFF_SETS)), labels[::-1])
        ax.set_xlabel(f"{name}: checks on minus checks off, percentage points")
        ax.grid(axis="x", linewidth=0.3)
    fig.suptitle("Turning the checks on, per set, with paired 95% intervals")
    fig.tight_layout()
    fig.savefig(out / "final_difference.png", dpi=120)
    plt.close(fig)
    _write(
        out / "final_difference.csv",
        ["set", "metric", "difference", "low", "high", "questions"],
        rows,
    )


def chart_activity(f: Final, out: Path) -> None:
    """(c) In checks-on, the checks' repairs and rejects by question category (every set)."""
    counts: dict[str, Counter[str]] = {}
    for (set_name, arm), part in f.rows.items():
        if arm != ON:
            continue
        for row in part:
            category = str(f.questions[set_name][row["id"]].category)
            bucket = counts.setdefault(category, Counter())
            for e in row.get("overrides") or []:
                bucket[str(e.get("outcome"))] += 1
    categories = sorted(counts)
    repairs = [counts[c]["repair"] for c in categories]
    rejects = [counts[c]["reject"] for c in categories]
    fig, ax = plt.subplots(figsize=(11, 4.5))
    xs = range(len(categories))
    ax.bar([x - 0.2 for x in xs], repairs, width=0.4, color="grey", label="repair")
    ax.bar([x + 0.2 for x in xs], rejects, width=0.4, color="black", label="reject")
    ax.set_xticks(list(xs), categories, rotation=30, ha="right")
    ax.set_ylabel("Check results (one per check per tool call)")
    runs = sum(len(p) for (s, a), p in f.rows.items() if a == ON)
    ax.set_title(f"Check activity with the checks on, by question category ({runs} runs, all sets)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out / "final_check_activity.png", dpi=120)
    plt.close(fig)
    _write(
        out / "final_check_activity.csv",
        ["category", "repair", "reject", "pass"],
        [[c, counts[c]["repair"], counts[c]["reject"], counts[c]["pass"]] for c in categories],
    )


def write_charts(f: Final, out: Path) -> list[Path]:
    """All three charts and their CSVs; returns the PNGs written."""
    out.mkdir(parents=True, exist_ok=True)
    chart_rates(f, out)
    chart_difference(f, out)
    chart_activity(f, out)
    return [
        out / n for n in ("final_rates.png", "final_difference.png", "final_check_activity.png")
    ]
