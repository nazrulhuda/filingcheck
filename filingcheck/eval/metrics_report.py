"""The metrics report and the per-run CSV, written from scored runs (filingcheck/eval/metrics.py).

`render` lays out, per set and arm, the pre-registered metrics and, for the agent arms, the
paired comparison of checks on against checks off with its 95% bootstrap interval and McNemar's
test; the always-abstain floor; segment-refusal calls; false repairs on control questions; the
noise; and the graders' disagreements. `write_csv` writes one line per run in the
pre-registration's columns. Both read only scored runs; nothing here calls a model.
"""

import csv
import math
from collections import Counter
from collections.abc import Callable, Iterable, Sequence
from pathlib import Path

from filingcheck.eval.dryrun import percentile
from filingcheck.eval.metrics import (
    RunScore,
    deciding_outcome,
    error_share,
    noise,
    per_question,
    rate,
    runs_by_question,
)
from filingcheck.eval.stats import SEED, mcnemar, paired_bootstrap

CSV_COLUMNS = (
    "set",
    "id",
    "repeat",
    "arm",
    "category",
    "expected_behavior",
    "graded_by",
    "outcome",
    "llm_verdict",
    "correct",
    "confidently_wrong",
    "confidently_wrong_no_labels",
    "confidently_wrong_both_graders",
    "wrong_arg_ran",
    "wrong_arg_sent",
    "segment_total_calls",
    "calls_ran",
    "abstained",
    "false_repair",
    "latency_ms",
    "cost_usd",
    "error",
)
OFF, ON = "agent-checks-off", "agent-checks-on"
Value = Callable[[RunScore], float | bool | int]


def arm_sources(arms: str, *, date: str, label: str | None) -> list[tuple[str, str, str]]:
    """Each arm's name in the report, its run date and its file name part, from `--arms`.

    An entry is an arm (`agent-checks-on`: the given date and label, the arm named without the
    label), or an arm from another day (`agent-prompt-rules@2026-11-13`, no label), or one with
    its own label (`agent-prompt-rules@2026-11-13/v2`, named with it, so a second version is a
    row of its own). Day 39 reports the new arm next to the Week 5 arms, run the day before.
    """
    sources: list[tuple[str, str, str]] = []
    for entry in arms.split(","):
        arm, _, rest = entry.partition("@")
        if not rest:
            sources.append((arm, date, f"{arm}-{label}" if label else arm))
            continue
        day, _, own = rest.partition("/")
        name = f"{arm}-{own}" if own else arm
        sources.append((name, day, name))
    return sources


def write_csv(scores: Iterable[RunScore], path: Path) -> None:
    """One line per run, in the pre-registration's columns; empty cells for None."""
    with path.open("w", encoding="utf-8", newline="") as handle:
        out = csv.writer(handle, lineterminator="\n")
        out.writerow(CSV_COLUMNS)
        for s in scores:
            values = [
                s.set_name,
                s.id,
                s.repeat,
                s.arm,
                s.category,
                s.expected_behavior,
                s.graded_by,
                s.outcome,
                s.llm_verdict,
                s.correct,
                s.confidently_wrong,
                s.confidently_wrong_no_labels,
                s.confidently_wrong_both_graders,
                s.wrong_arg_ran,
                s.wrong_arg_sent,
                s.segment_total_calls,
                s.calls_ran,
                s.abstained,
                s.false_repair,
                s.latency_ms,
                s.cost_usd,
                s.error,
            ]
            out.writerow(["" if v is None else v for v in values])


def _pct(value: float) -> str:
    return "-" if math.isnan(value) else f"{100 * value:.1f}%"


def _per100(value: float) -> str:
    return "-" if math.isnan(value) else f"{100 * value:.1f}"


def _points(value: float) -> str:
    return "-" if math.isnan(value) else f"{100 * value:+.1f} points"


def _secs(values: list[float]) -> str:
    return "-" if not values else f"{percentile(values, 50) / 1000:.1f} s"


def _groups(scores: Sequence[RunScore]) -> dict[tuple[str, str], list[RunScore]]:
    groups: dict[tuple[str, str], list[RunScore]] = {}
    for s in scores:
        groups.setdefault((s.set_name, s.arm), []).append(s)
    return groups


def _comparison(
    set_name: str, label: str, off: list[RunScore], on: list[RunScore], value: Value, majority: bool
) -> str:
    a, b = per_question(off, value), per_question(on, value)
    shared = sorted(set(a) & set(b))
    a, b = {k: a[k] for k in shared}, {k: b[k] for k in shared}
    if not shared:
        return f"| {set_name} | {label} | - | - | - | - | - | - | - |"
    interval = paired_bootstrap(a, b)
    mean_a, mean_b = sum(a.values()) / len(a), sum(b.values()) / len(b)
    scale = (lambda v: f"{100 * v:.1f}") if "per 100" in label else _pct
    if "per 100" in label:
        diff = f"{100 * interval.estimate:+.1f}"
        span = f"{100 * interval.low:+.1f} to {100 * interval.high:+.1f}"
    else:
        diff = _points(interval.estimate)
        span = f"{100 * interval.low:+.1f} to {100 * interval.high:+.1f}"
    cells = f"| {set_name} | {label} | {scale(mean_a)} | {scale(mean_b)} | {diff} | {span} |"
    if majority:
        runs_a = runs_by_question(off, lambda s: bool(value(s)))
        runs_b = runs_by_question(on, lambda s: bool(value(s)))
        bb, cc, p = mcnemar({k: runs_a[k] for k in shared}, {k: runs_b[k] for k in shared})
        return f"{cells} {bb} | {cc} | {p:.4f} |"
    return f"{cells} - | - | - |"


def render(
    scores: Sequence[RunScore],
    *,
    floor: Sequence[RunScore],
    title: str,
    heading: str,
    notes: Sequence[str],
) -> str:
    """The report page (see the module docstring)."""
    groups = _groups(scores)
    lines = (
        [f"# {title}", "", heading, "", *notes, ""] if notes else [f"# {title}", "", heading, ""]
    )
    lines += [
        "## Per set and arm",
        "",
        "Rates are per question first, then the mean over the questions; questions marked not "
        "scored are left out. Error rows count in every rate: never correct, never confidently "
        "wrong.",
        "",
        "| Set | Arm | Questions | Runs | Error rows | Accuracy | Partly (text runs) | "
        "Confidently wrong | without the labels | both graders | Wrong-argument calls per 100 "
        "runs | per 100 calls that ran | Abstain rate | p50 | p95 | Cost "
        "| Cost per 100 questions |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for (set_name, arm), part in groups.items():
        scored = [s for s in part if s.scored]
        questions = len({s.id for s in scored})
        text = [s for s in scored if s.graded_by == "text"]
        partly = sum(1 for s in text if s.llm_verdict == "partly") / len(text) if text else math.nan
        calls = sum(s.calls_ran for s in scored)
        wrong = sum(s.wrong_arg_ran for s in scored)
        latencies = [s.latency_ms for s in part if s.latency_ms is not None]
        cost = sum(s.cost_usd for s in part)
        lines.append(
            f"| {set_name} | {arm} | {questions} | {len(part)} | "
            f"{sum(1 for s in part if s.error)} ({_pct(error_share(part))}) | "
            f"{_pct(rate(scored, lambda s: s.correct))} | {_pct(partly)} | "
            f"{_pct(rate(scored, lambda s: s.confidently_wrong))} | "
            f"{_pct(rate(scored, lambda s: s.confidently_wrong_no_labels))} | "
            f"{_pct(rate(scored, lambda s: s.confidently_wrong_both_graders))} | "
            f"{_per100(rate(scored, lambda s: s.wrong_arg_ran))} | "
            f"{_per100(wrong / calls) if calls else '-'} | "
            f"{_pct(rate(scored, lambda s: s.abstained))} | {_secs(latencies)} | "
            f"{'-' if not latencies else f'{percentile(latencies, 95) / 1000:.1f} s'} | "
            f"${cost:.4f} | ${100 * cost / questions if questions else 0:.4f} |"
        )
    if floor:
        lines += [
            "",
            "**The always-abstain floor** (the abstain sentence graded as the answer to "
            "every question by the same graders; its confidently-wrong rate is 0 by "
            "definition):",
            "",
            "| Set | Questions | Accuracy |",
            "|---|---:|---:|",
        ]
        for set_name in dict.fromkeys(s.set_name for s in floor):
            part = [s for s in floor if s.set_name == set_name and s.scored]
            lines.append(
                f"| {set_name} | {len({s.id for s in part})} | "
                f"{_pct(rate(part, lambda s: s.correct))} |"
            )
    lines += [
        "",
        "## Checks on against off",
        "",
        f"Paired by question: the difference is checks on minus checks off, with a 95% interval "
        f"from a bootstrap over questions (10,000 resamples, seed {SEED}); McNemar's exact test "
        "on each question's majority outcome (b: yes with the checks off and no with them on; "
        "c: the other way round). The wrong-argument rate falls partly by design: with the "
        "checks on, a stopped call never runs.",
        "",
        "| Set | Metric | Checks off | Checks on | Difference | 95% interval | b | c | p |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for set_name in dict.fromkeys(s.set_name for s in scores):
        off, on = groups.get((set_name, OFF)), groups.get((set_name, ON))
        if not off or not on:
            continue
        metrics: list[tuple[str, Value, bool]] = [
            ("accuracy", lambda s: s.correct, True),
            ("confidently wrong", lambda s: s.confidently_wrong, True),
            ("confidently wrong, both graders", lambda s: s.confidently_wrong_both_graders, True),
            (
                "confidently wrong, error rows counted as wrong",
                lambda s: s.confidently_wrong or bool(s.error),
                True,
            ),
            ("wrong-argument calls per 100 runs", lambda s: s.wrong_arg_ran, False),
        ]
        for label, value, majority in metrics:
            lines.append(_comparison(set_name, label, off, on, value, majority))
    segment = [s for s in scores if s.segment_total_calls is not None and s.scored]
    if segment:
        lines += [
            "",
            "## Segment refusals",
            "",
            "Calls for the company and metric of a segment_vs_total refusal that ran, per 100 "
            "runs (not counted as wrong-argument calls).",
            "",
            "| Set | Arm | Questions | Calls per 100 runs |",
            "|---|---|---:|---:|",
        ]
        for (set_name, arm), part in _groups(segment).items():
            lines.append(
                f"| {set_name} | {arm} | {len({s.id for s in part})} | "
                f"{_per100(rate(part, lambda s: s.segment_total_calls or 0))} |"
            )
    control = [s for s in scores if s.category == "control"]
    if control:
        false = [s for s in control if s.false_repair]
        lines += [
            "",
            "## False repairs on control questions",
            "",
            f"{len(false)} control run(s) of {len(control)} in which a check repaired or "
            "rejected a get_financial_fact call. The fiscal-year check's repairs on "
            f"search_filings, its design on a question that names no year, are counted apart: "
            f"{sum(s.search_repairs for s in control)}.",
        ]
        lines += [f"- {s.set_name} {s.arm} {s.id} run {s.repeat}" for s in false]
    lines += [
        "",
        "## Noise",
        "",
        "The share of questions whose 3 runs do not all get the same outcome (the deciding "
        "grader's).",
        "",
        "| Set | Arm | Questions | Not all the same |",
        "|---|---|---:|---:|",
    ]
    for (set_name, arm), part in groups.items():
        scored = [s for s in part if s.scored]
        lines.append(
            f"| {set_name} | {arm} | {len({s.id for s in scored})} | {_pct(noise(scored))} |"
        )
    unscored = {(s.id, s.not_scored_reason) for s in scores if not s.scored}
    if unscored:
        lines += ["", "## Questions not scored", "", "Run like the others, left out of every rate:"]
        lines += [""] + [f"- {qid}: {reason}" for qid, reason in sorted(unscored)]
    stopped = sum(s.stopped_calls for s in scores)
    unmatched = sum(max(0, s.stopped_calls - s.check_rejects) for s in scores)
    lines += [
        "",
        "## Stopped number-tool calls",
        "",
        f"Number-tool calls stored with status error: {stopped}; stopped without a check's "
        f"reject record: {unmatched}."
        + (
            " Those are not check rejects (an input validation error, or another kind): list "
            "them and ask before reporting."
            if unmatched
            else " Every stopped call is a check's reject."
        ),
    ]
    second = [s for s in scores if s.graded_by == "number" and s.llm_verdict and not s.error]
    det_passes = [s for s in second if s.outcome == "correct" and s.llm_verdict != "correct"]
    det_fails = [s for s in second if s.outcome != "correct" and s.llm_verdict == "correct"]
    pairs = Counter((s.outcome, str(s.llm_verdict)) for s in second)
    ungraded = [s for s in scores if s.text_ungraded]
    lines += [
        "",
        "## The graders",
        "",
        f"- Number-graded runs with an LLM second opinion: {len(second)}; where one grader "
        f"passes the run and the other fails it: {len(det_passes) + len(det_fails)} (the "
        f"deterministic grader passes and the LLM fails: {len(det_passes)}; the deterministic "
        f"grader fails and the LLM passes: {len(det_fails)}). Rows graded before the final run "
        "have a second opinion only on failed runs, so only the second direction can show there.",
        f"- Text-graded runs with no usable LLM verdict: {len(ungraded)}.",
        f"- Deciding outcomes seen: {', '.join(sorted({deciding_outcome(s) for s in scores}))}.",
        "",
        "Every pairing of the deterministic outcome and the LLM's second opinion:",
        "",
        "| Deterministic | LLM | Runs |",
        "|---|---|---:|",
    ]
    lines += [f"| {o} | {v} | {n} |" for (o, v), n in sorted(pairs.items(), key=lambda kv: -kv[1])]
    return "\n".join(lines) + "\n"
