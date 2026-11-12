"""The Day 33 dry-run report: a pipeline check over the development sets, not results.

Every table is computed from the stored result rows (`eval/results/<date>_<set>_<arm>.jsonl`),
their deterministic grades and the LLM grades (`<file>_llm.jsonl`). No intervals and no claims:
those are Week 6's. `python -m filingcheck.eval dry-run` writes `eval/results/<date>_dry-run.md`.
"""

import math
from collections import Counter
from collections.abc import Iterable, Mapping
from typing import Any

from filingcheck.eval.grade import LABELS, OUTCOMES, Grade
from filingcheck.eval.llm_grade import VERDICTS, LlmGrade
from filingcheck.eval.questions import Question

Graded = list[tuple[dict[str, Any], Grade]]
LlmGrades = Mapping[tuple[str, int], LlmGrade]
# The LLM verdict each deterministic outcome amounts to, for the disagreement list.
AGREES: dict[str, set[str]] = {
    "correct": {"correct"},
    "abstained": {"abstained"},
    "asked_when_should_answer": {"asked"},
    "answered": {"correct", "wrong", "partly"},  # unanswerable_text: the LLM grade is the grade
}
FAILED_VERDICTS = {"wrong", "partly"}
PASSES = "the LLM grader passes a row the deterministic grader failed"
DIFFERS = "the two grades differ"
NO_TOOL_CALL = "## Relative-year runs with no tool call"


def percentile(values: list[float], p: float) -> float:
    """The nearest-rank percentile: the value at rank ceil(p/100 * n), so always one seen."""
    if not values:
        return math.nan
    ordered = sorted(values)
    rank = max(1, math.ceil(p / 100 * len(ordered)))
    return ordered[rank - 1]


def _repeat(row: Mapping[str, Any]) -> int:
    return int(row.get("repeat", 1))


def arm_summary(graded: Graded, llm: LlmGrades) -> dict[str, Any]:
    """One set and arm: runs, outcomes, lenient-correct, LLM verdicts, abstains, cost, latency."""
    outcomes = Counter(g.outcome for _, g in graded)
    lenient = sum(1 for _, g in graded if (g.lenient_outcome or g.outcome) == "correct")
    verdicts = Counter(
        llm[(r["id"], _repeat(r))].verdict
        for r, _ in graded
        if (r["id"], _repeat(r)) in llm and llm[(r["id"], _repeat(r))].verdict
    )
    abstained = outcomes["abstained"]
    latencies = [float(r["latency_ms"]) for r, _ in graded if r.get("latency_ms") is not None]
    return {
        "runs": len(graded),
        "outcomes": outcomes,
        "lenient_correct": lenient,
        "verdicts": verdicts,
        "abstained": abstained,
        "abstain_rate": abstained / len(graded) if graded else math.nan,
        "cost_usd": round(sum(float(r.get("cost_usd") or 0.0) for r, _ in graded), 6),
        "p50_ms": percentile(latencies, 50),
        "p95_ms": percentile(latencies, 95),
    }


def check_activity(
    rows: Iterable[Mapping[str, Any]], questions: Mapping[str, Question]
) -> dict[str, Counter[str]]:
    """Passes, repairs and rejects per question category, from the rows' override logs."""
    activity: dict[str, Counter[str]] = {}
    for row in rows:
        question = questions.get(row["id"])
        if question is None:
            continue
        for entry in row.get("overrides") or []:
            activity.setdefault(question.category, Counter())[entry["outcome"]] += 1
    return {category: counts for category, counts in activity.items() if counts}


def false_repairs(
    rows: Iterable[Mapping[str, Any]], questions: Mapping[str, Question]
) -> list[dict[str, Any]]:
    """Control rows where a check repaired or rejected a call the question did not call for."""
    found = []
    for row in rows:
        question = questions.get(row["id"])
        if question is None or question.category != "control":
            continue
        if any(e.get("outcome") in ("repair", "reject") for e in row.get("overrides") or []):
            found.append(dict(row))
    return found


def label_shares(graded: Graded) -> dict[str, Any]:
    """Label counts of the figures in correct answers and in wrong-number answers.

    Of figures in correct answers, how many are Verified; of figures in wrong-number answers, how
    many are Verified, Conflict and Unverified, with every Verified one listed.
    """
    correct: Counter[str] = Counter()
    wrong: Counter[str] = Counter()
    verified_in_wrong: list[tuple[str, int, str]] = []
    for row, grade in graded:
        labels = row.get("number_labels") or []
        if grade.outcome == "correct":
            correct["figures"] += len(labels)
            correct["verified"] += sum(1 for n in labels if n["label"] == "verified")
        elif grade.outcome == "wrong_number":
            wrong["figures"] += len(labels)
            for n in labels:
                wrong[n["label"]] += 1
                if n["label"] == "verified":
                    verified_in_wrong.append((row["id"], _repeat(row), n["figure"]))
    return {
        "correct": {"figures": correct["figures"], "verified": correct["verified"]},
        "wrong_number": {
            "figures": wrong["figures"],
            "verified": wrong["verified"],
            "conflict": wrong["conflict"],
            "unverified": wrong["unverified"],
        },
        "verified_in_wrong": verified_in_wrong,
    }


def text_support(grades: Iterable[LlmGrade]) -> dict[str, Any]:
    """The share of text answers the LLM grader marks `supported: no` or `partly`."""
    text = [g for g in grades if g.use == "text" and g.supported]
    no = sum(1 for g in text if g.supported == "no")
    partly = sum(1 for g in text if g.supported == "partly")
    return {
        "text_answers": len(text),
        "no": no,
        "partly": partly,
        "unsupported_rate": (no + partly) / len(text) if text else math.nan,
    }


def disagreements(
    graded: Graded, llm: LlmGrades
) -> list[tuple[dict[str, Any], Grade, LlmGrade, str]]:
    """Every row where the deterministic grade and the LLM's second opinion do not agree.

    A failing deterministic outcome agrees with `wrong` or `partly`; `correct`, `abstained` and
    `asked_when_should_answer` agree with their own verdict. An LLM `correct` on a failed row is
    the disagreement the spec lists for a person; any other mismatch is listed as differing.
    """
    found = []
    for row, grade in graded:
        verdict_row = llm.get((row["id"], _repeat(row)))
        if verdict_row is None or verdict_row.use != "second opinion" or not verdict_row.verdict:
            continue
        agrees = AGREES.get(grade.outcome, FAILED_VERDICTS)
        if verdict_row.verdict in agrees:
            continue
        kind = PASSES if verdict_row.verdict == "correct" else DIFFERS
        found.append((dict(row), grade, verdict_row, kind))
    return found


def no_tool_call_rows(
    rows: Iterable[Mapping[str, Any]], questions: Mapping[str, Question], *, category: str
) -> list[dict[str, Any]]:
    """Rows of one category whose run made no tool call at all."""
    return [
        dict(row)
        for row in rows
        if (q := questions.get(row["id"])) is not None
        and q.category == category
        and not (row.get("tool_calls") or [])
    ]


def _ms(value: float) -> str:
    return "-" if math.isnan(value) else f"{value / 1000:.1f} s"


def _rate(value: float) -> str:
    return "-" if math.isnan(value) else f"{100 * value:.0f}%"


def _row_label(row: Mapping[str, Any]) -> str:
    return f"{row['id']} #{_repeat(row)}"


def report(
    arms: Mapping[str, Mapping[str, tuple[Graded, LlmGrades]]],
    questions: Mapping[str, Question],
    *,
    date: str,
) -> str:
    """The dry-run page. `arms[set][arm] = (graded rows, LLM grades by (id, repeat))`."""
    lines = [
        "# Dry run: pipeline check, not results",
        "",
        f"The development sets through both arms on {date}, 3 runs per question, graded by the "
        "deterministic grader and the LLM grader. This page checks that every stage works and "
        "is logged. No confidence intervals and no claims: those are Week 6's, on the held-out "
        "set.",
        "",
        "## Per set and arm",
        "",
    ]
    shown = [o for o in OUTCOMES if o not in ("error", "not_graded")]
    lines += [
        "| Set | Arm | Runs | "
        + " | ".join(LABELS[o] for o in shown)
        + " | Correct, lenient | "
        + " | ".join(f"LLM {v}" for v in VERDICTS)
        + " | Abstain rate | Cost | p50 | p95 |",
        "|---|---|" + "---:|" * (len(shown) + len(VERDICTS) + 6),
    ]
    for set_name, by_arm in arms.items():
        for arm, (graded, llm) in by_arm.items():
            s = arm_summary(graded, llm)
            lines.append(
                f"| {set_name} | {arm} | {s['runs']} | "
                + " | ".join(str(s["outcomes"][o]) for o in shown)
                + f" | {s['lenient_correct']} | "
                + " | ".join(str(s["verdicts"][v]) for v in VERDICTS)
                + f" | {_rate(s['abstain_rate'])} | ${s['cost_usd']:.4f} | {_ms(s['p50_ms'])} "
                f"| {_ms(s['p95_ms'])} |"
            )
    lines += [
        "",
        "## Check activity",
        "",
        "Passes, repairs and rejects per question category, in the checks-on arm.",
        "",
        "| Set | Category | Pass | Repair | Reject |",
        "|---|---|---:|---:|---:|",
    ]
    for set_name, by_arm in arms.items():
        for arm, (graded, _) in by_arm.items():
            if "on" not in arm:
                continue
            for category, counts in sorted(
                check_activity([r for r, _ in graded], questions).items()
            ):
                lines.append(
                    f"| {set_name} | {category} | {counts['pass']} | {counts['repair']} | "
                    f"{counts['reject']} |"
                )
    lines += ["", "## False repairs on control questions", ""]
    false = [
        (set_name, arm, row)
        for set_name, by_arm in arms.items()
        for arm, (graded, _) in by_arm.items()
        for row in false_repairs([r for r, _ in graded], questions)
    ]
    lines.append(
        f"{len(false)} control run(s) where a check repaired or rejected a call that the question "
        "did not call for."
    )
    if false:
        lines += ["", "| Set | Arm | Row | What the checks did |", "|---|---|---|---|"]
        for set_name, arm, row in false:
            did = "; ".join(
                f"{e['check']} {e['outcome']}: {e.get('reason', '')}"
                for e in row.get("overrides") or []
                if e.get("outcome") != "pass"
            )
            lines.append(f"| {set_name} | {arm} | {_row_label(row)} | {did} |")
    lines += [
        "",
        "## Labels",
        "",
        "| Set | Arm | Figures in correct answers | Verified | Figures in wrong-number answers | "
        "Verified | Conflict | Unverified |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    verified_in_wrong = []
    for set_name, by_arm in arms.items():
        for arm, (graded, _) in by_arm.items():
            sh = label_shares(graded)
            c, w = sh["correct"], sh["wrong_number"]
            lines.append(
                f"| {set_name} | {arm} | {c['figures']} | {c['verified']} | {w['figures']} | "
                f"{w['verified']} | {w['conflict']} | {w['unverified']} |"
            )
            verified_in_wrong += [(set_name, arm, *v) for v in sh["verified_in_wrong"]]
    lines += [
        "",
        f"Verified figures in wrong-number answers: {len(verified_in_wrong)}. A Verified figure "
        "is in a cited source; it can still be the wrong number for the question.",
    ]
    if verified_in_wrong:
        lines += ["", "| Set | Arm | Row | Figure |", "|---|---|---|---|"]
        lines += [
            f"| {s} | {a} | {qid} #{rep} | {fig} |" for s, a, qid, rep, fig in verified_in_wrong
        ]
    lines += [
        "",
        "## Text support",
        "",
        "| Set | Arm | Text answers | supported: no | supported: partly | Unsupported share |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for set_name, by_arm in arms.items():
        for arm, (_, llm) in by_arm.items():
            t = text_support(llm.values())
            if t["text_answers"]:
                lines.append(
                    f"| {set_name} | {arm} | {t['text_answers']} | {t['no']} | {t['partly']} | "
                    f"{_rate(t['unsupported_rate'])} |"
                )
    lines += ["", "## Grader disagreements", ""]
    found = [
        (set_name, arm, *d)
        for set_name, by_arm in arms.items()
        for arm, (graded, llm) in by_arm.items()
        for d in disagreements(graded, llm)
    ]
    passes = [f for f in found if f[-1] == PASSES]
    lines.append(
        f"{len(passes)} row(s) the deterministic grader failed that the LLM grader calls correct; "
        f"{len(found) - len(passes)} other row(s) where the two grades differ. The deterministic "
        "grade stays the main one for numbers."
    )
    if found:
        lines += [
            "",
            "| Set | Arm | Row | Deterministic | LLM | LLM's reason | Kind |",
            "|---|---|---|---|---|---|---|",
        ]
        for set_name, arm, row, grade, verdict_row, kind in found:
            reason = verdict_row.reason.replace("|", "\\|")
            lines.append(
                f"| {set_name} | {arm} | {_row_label(row)} | {grade.outcome} | "
                f"{verdict_row.verdict} / {verdict_row.supported} | {reason} | {kind} |"
            )
    lines += ["", NO_TOOL_CALL, ""]
    quiet = [
        (set_name, arm, row)
        for set_name, by_arm in arms.items()
        for arm, (graded, _) in by_arm.items()
        for row in no_tool_call_rows([r for r, _ in graded], questions, category="relative_year")
    ]
    lines.append(
        f"{len(quiet)} relative_year run(s) made no tool call: the model answered or asked from "
        "the question alone, so no check could run."
    )
    if quiet:
        lines += ["", "| Set | Arm | Row | Answer |", "|---|---|---|---|"]
        for set_name, arm, row in quiet:
            answer = str(row.get("answer") or "").replace("\n", " ").replace("|", "\\|")[:160]
            lines.append(f"| {set_name} | {arm} | {_row_label(row)} | {answer} |")
    return "\n".join(lines) + "\n"
