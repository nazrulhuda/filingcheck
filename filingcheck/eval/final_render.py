"""The final report's pages: load the committed final rows and write each section.

The sections follow the Day 41 list, in its order, with the pre-registration's definitions
(`eval/PREREGISTRATION.md`) and rules (`filingcheck/eval/final_report.py`). Every number comes
from the committed rows and grades; nothing here calls a model.
"""

import json
import math
from collections import Counter, defaultdict
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any

from filingcheck.eval.dryrun import percentile
from filingcheck.eval.final_report import (
    Comparison,
    agree,
    claims_reduction,
    compare,
    confirmation_sentences,
    headline,
    s1_sentence,
)
from filingcheck.eval.grade import find_numbers, grade
from filingcheck.eval.llm_grade import LlmGrade
from filingcheck.eval.metrics import (
    NUMBER_TOOL,
    RunScore,
    deciding_outcome,
    noise,
    rate,
    score_run,
    sent_breakdown,
)
from filingcheck.eval.questions import Question

ARMS = ("baseline-vector", "baseline", "agent-checks-off", "agent-prompt-rules", "agent-checks-on")
AGENT_ARMS = ("agent-checks-off", "agent-prompt-rules", "agent-checks-on")
SETS = ("heldout_traps", "heldout_traps_2", "dev_traps", "dev_unanswerable", "control")
HELD = ("heldout_traps", "heldout_traps_2")
HELD_OUT = "held-out"  # both sealed files together
CALENDAR = ("held-006", "held-044", "held-049")
ONE_CANDIDATE = ("held-004", "held-032", "held-035")
OFF, ON, RULES = "agent-checks-off", "agent-checks-on", "agent-prompt-rules"
SLEPT = ("control", "baseline", "control-117", 1)  # the PC slept during this run (the record)
Value = Callable[[RunScore], float | bool | int]


def _cw(s: RunScore) -> bool:
    return s.confidently_wrong


def _acc(s: RunScore) -> bool:
    return s.correct


@dataclass
class Final:
    """The final run as committed: scores, the raw rows and the LLM grades, per set and arm."""

    scores: list[RunScore] = field(default_factory=list)
    rows: dict[tuple[str, str], list[dict[str, Any]]] = field(default_factory=dict)
    llm: dict[tuple[str, str], dict[tuple[str, int], LlmGrade]] = field(default_factory=dict)
    questions: dict[str, dict[str, Question]] = field(default_factory=dict)

    def part(self, sets: Sequence[str], arm: str) -> list[RunScore]:
        """The scores of these sets in one arm."""
        return [s for s in self.scores if s.set_name in sets and s.arm == arm]

    def question(self, qid: str) -> Question:
        """A question by id, from any set."""
        for by_id in self.questions.values():
            if qid in by_id:
                return by_id[qid]
        raise KeyError(qid)


def load(
    results: Path, questions: Mapping[str, dict[str, Question]], *, date: str, label: str
) -> Final:
    """Every final row of the five sets and five arms, scored, with its LLM grade."""
    final = Final(questions=dict(questions))
    for set_name in SETS:
        by_id = questions[set_name]
        for arm in ARMS:
            path = results / f"{date}_{set_name}_{arm}-{label}.jsonl"
            rows = [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x]
            grades: dict[tuple[str, int], LlmGrade] = {}
            for line in path.with_name(path.stem + "_llm.jsonl").read_text("utf-8").splitlines():
                if line:
                    parsed = LlmGrade.model_validate_json(line)
                    grades[(parsed.id, parsed.repeat)] = parsed
            final.rows[(set_name, arm)] = rows
            final.llm[(set_name, arm)] = grades
            for row in rows:
                g = grades.get((row["id"], row.get("repeat", 1)))
                final.scores.append(score_run(row, by_id[row["id"]], g, set_name=set_name, arm=arm))
    return final


# ---------------------------------------------------------------- formatting


def _pct(value: float) -> str:
    return "-" if math.isnan(value) else f"{100 * value:.1f}%"


def _per100(value: float) -> str:
    return "-" if math.isnan(value) else f"{100 * value:.1f}"


def _signed(value: float) -> str:
    return f"{100 * value:+.1f}"


def _secs(values: list[float], p: float) -> str:
    return "-" if not values else f"{percentile(values, p) / 1000:.1f} s"


def _set_title(sets: Sequence[str]) -> str:
    return HELD_OUT if tuple(sets) == HELD else ", ".join(sets)


def _comparison_row(name: str, what: str, c: Comparison, *, per100: bool = False) -> str:
    show = _per100 if per100 else _pct
    i = c.interval
    unit = "" if per100 else " points"
    tests = f"{c.b} | {c.c} | {c.p:.4f}" if c.p is not None else "- | - | -"
    return (
        f"| {name} | {what} | {c.questions} | {show(c.first)} | {show(c.second)} | "
        f"{_signed(i.estimate)}{unit} | {_signed(i.low)} to {_signed(i.high)} | {tests} |"
    )


COMPARISON_HEAD = [
    "| Set | Comparison | Questions | First | Second | Difference (second minus first) | 95% "
    "interval | b | c | p |",
    "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
]


# ---------------------------------------------------------------- 1. the headline


def headline_section(f: Final) -> list[str]:
    """The primary comparison, its two files apart, development, S1, pooling, confirmation."""
    held = compare(f.part(HELD, OFF), f.part(HELD, ON), _cw, majority=True)
    dev = compare(f.part(("dev_traps",), OFF), f.part(("dev_traps",), ON), _cw, majority=True)
    files = {s: compare(f.part((s,), OFF), f.part((s,), ON), _cw, majority=True) for s in HELD}
    s1 = compare(f.part(HELD, RULES), f.part(HELD, ON), _cw, majority=True)
    s1_acc = compare(f.part(HELD, RULES), f.part(HELD, ON), _acc, majority=True)
    lines = [
        "## 1. The headline",
        "",
        headline(held),
        "",
        "A reduction is claimed only if the 95% interval of the difference lies entirely below "
        f"zero. Here it {'does' if claims_reduction(held) else 'does not'}: "
        f"{'a reduction is claimed' if claims_reduction(held) else 'no reduction is claimed'}.",
        "",
        "Checks off is the first arm, checks on the second; b counts questions whose majority "
        "of runs is confidently wrong with the checks off and not with them on, c the other way "
        "round (McNemar's exact two-sided test).",
        "",
        *COMPARISON_HEAD,
        _comparison_row(HELD_OUT, "confidently wrong, off → on", held),
        _comparison_row(
            "heldout_traps (the first 28)", "confidently wrong, off → on", files[HELD[0]]
        ),
        _comparison_row(
            "heldout_traps_2 (the later 84)", "confidently wrong, off → on", files[HELD[1]]
        ),
        _comparison_row(
            "dev_traps (development: the checks were built while looking at these questions)",
            "confidently wrong, off → on",
            dev,
        ),
        "",
    ]
    a, b = files[HELD[0]].interval.estimate, files[HELD[1]].interval.estimate
    if a * b < 0:
        lines += [
            "**The two held-out files' differences point in opposite directions** "
            f"({_signed(a)} and {_signed(b)} points).",
            "",
        ]
    lines += [
        f"**The prompt-rules comparison (S1):** {s1_sentence(s1, s1_acc)} *(This sentence "
        "was first coded on confidently wrong alone; read against S1, which names confidently "
        "wrong and accuracy, it was changed after the results were seen, to judge both.)*",
        "",
    ]
    # The prompt-injection category, shown apart whichever way S1 comes out.
    cat = [s for s in f.scores if s.set_name in HELD and s.category == "prompt_injection"]
    if cat:
        pi_rules = [s for s in cat if s.arm == RULES]
        pi_on = [s for s in cat if s.arm == ON]
        lines += [
            "The prompt-injection questions apart (held-out): confidently wrong "
            f"{_pct(rate(pi_rules, _cw))} with the prompt rules, {_pct(rate(pi_on, _cw))} "
            f"with the checks on; accuracy {_pct(rate(pi_rules, _acc))} and "
            f"{_pct(rate(pi_on, _acc))}; {len({s.id for s in pi_on if s.scored})} questions.",
            "",
        ]
    if agree(held, dev):
        trap = (*HELD, "dev_traps")
        pooled = compare(f.part(trap, OFF), f.part(trap, ON), _cw, majority=True)
        lines += [
            "Held-out and development agree (the same sign, and each estimate inside the other's "
            "interval), so one pooled line follows; it does not replace the two:",
            "",
            *COMPARISON_HEAD,
            _comparison_row("all trap questions", "confidently wrong, off → on", pooled),
            "",
        ]
    else:
        h, d = held.interval, dev.interval
        failed = []
        if not (h.estimate * d.estimate > 0):
            failed.append("their differences do not have the same sign")
        if not d.low <= h.estimate <= d.high:
            failed.append(
                f"held-out's estimate ({_signed(h.estimate)}) is outside development's interval "
                f"({_signed(d.low)} to {_signed(d.high)})"
            )
        if not h.low <= d.estimate <= h.high:
            failed.append(
                f"development's estimate ({_signed(d.estimate)}) is outside held-out's interval "
                f"({_signed(h.low)} to {_signed(h.high)})"
            )
        lines += [
            "No pooled line: held-out and development agree only with the same sign and each "
            "estimate inside the other's interval, and here " + "; ".join(failed) + ".",
            "",
        ]
    lines += confirmation_sentences(held, dev) and [
        *[f"- {s}" for s in confirmation_sentences(held, dev)],
        "",
    ]
    return lines


# ---------------------------------------------------------------- 2. the ablation table


def _no_labels(scores: Sequence[RunScore]) -> list[RunScore]:
    """The same runs with confidently wrong counted as if no figure carried a label."""
    return [replace(s, confidently_wrong=s.confidently_wrong_no_labels) for s in scores]


def _arm_line(name: str, part: Sequence[RunScore], *, tools: bool) -> str:
    scored = [s for s in part if s.scored]
    questions = len({s.id for s in scored})
    latencies = [s.latency_ms for s in part if s.latency_ms is not None]
    cost = sum(s.cost_usd for s in part)
    wrong = _per100(rate(scored, lambda s: s.wrong_arg_ran)) if tools else "n/a"
    return (
        f"| {name} | {questions} | {len(part)} | {_pct(rate(scored, _acc))} | "
        f"{_pct(rate(scored, _cw))} | {wrong} | {_pct(rate(scored, lambda s: s.abstained))} | "
        f"{_secs(latencies, 50)} | {_secs(latencies, 95)} | ${cost:.4f} | "
        f"${100 * cost / questions if questions else 0:.4f} |"
    )


ABLATION_SETS: tuple[tuple[str, ...], ...] = (
    HELD,
    (HELD[0],),
    (HELD[1],),
    ("dev_traps",),
    ("dev_unanswerable",),
    ("control",),
)
STEPS = (
    ("baseline-vector → baseline", "baseline-vector", "baseline"),
    ("baseline → agent-checks-off", "baseline", OFF),
    ("agent-checks-off → agent-prompt-rules", OFF, RULES),
    ("agent-checks-off → agent-checks-on", OFF, ON),
)


def ablation_section(f: Final, floor: Sequence[RunScore], live: Sequence[str] = ()) -> list[str]:
    """Per set: the five arms, each agent arm without the labels, the floor; then the steps."""
    lines = [
        "## 2. The ablation table, per set",
        "",
        "Rates per question first, then the mean over the scored questions; error rows count "
        "in every rate (never correct, never confidently wrong). Wrong-argument calls are "
        "`get_financial_fact` calls that ran with the wrong company or year, per 100 runs; with "
        "the checks on a stopped call never runs, so that rate falls partly by design. The "
        "baselines make no tool calls (n/a). Latency is p50 and p95 of each run's time; cost is "
        "the answers' recorded cost (the grader's is in section 11).",
        "",
    ]
    for sets in ABLATION_SETS:
        title = _set_title(sets)
        lines += [
            f"### {title}",
            "",
            "| Arm | Questions | Runs | Accuracy | Confidently wrong | Wrong-argument calls per "
            "100 runs | Abstain rate | p50 | p95 | Cost | Cost per 100 questions |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
        for arm in ARMS:
            lines.append(_arm_line(arm, f.part(sets, arm), tools=arm in AGENT_ARMS))
        for arm in AGENT_ARMS:
            part = [s for s in f.part(sets, arm) if s.scored]
            lines.append(
                f"| {arm}, without the number labels | {len({s.id for s in part})} | - | - | "
                f"{_pct(rate(part, lambda s: s.confidently_wrong_no_labels))} | - | - | - | - | "
                "- | - |"
            )
        part_floor = [s for s in floor if s.set_name in sets and s.scored]
        lines += [
            f"| always abstain (floor) | {len({s.id for s in part_floor})} | - | "
            f"{_pct(rate(part_floor, _acc))} | 0.0% | - | - | - | - | - | - |",
            "",
            "Step by step (paired, 95% interval, descriptive):",
            "",
            *COMPARISON_HEAD,
        ]
        for label, first, second in STEPS:
            a, b = f.part(sets, first), f.part(sets, second)
            for what, value in (("accuracy", _acc), ("confidently wrong", _cw)):
                c = compare(a, b, value, majority=True)
                lines.append(_comparison_row(title, f"{label}: {what}", c))
        on = f.part(sets, ON)
        c = compare(_no_labels(on), on, _cw, majority=True)
        lines += [
            _comparison_row(
                title, "agent-checks-on without the labels → with them: confidently wrong", c
            ),
            "",
        ]
    base = [s for s in f.part(("control",), "baseline") if (s.id, s.repeat) != SLEPT[2:]]
    latencies = [s.latency_ms for s in base if s.latency_ms is not None]
    lines += [
        "*Added after the results:* the PC slept from 07:58:29 to 17:53:51 UTC during the "
        f"baseline arm, and one run ({SLEPT[2]} run {SLEPT[3]}, control) was in flight, so its "
        "time includes the sleep (`eval/results/2026-11-14_final-run_record.md`). It is the "
        "slowest of the baseline's 150 control runs and counts like any other above. Without "
        f"it, the baseline's control p50 is {_secs(latencies, 50)} and p95 "
        f"{_secs(latencies, 95)}. No means are given.",
        "",
        *live,
    ]
    return lines


# ---------------------------------------------------------------- 3. the secondary comparisons

SECONDARY: tuple[tuple[str, str, str, Value, bool, bool], ...] = (
    ("(S1) agent-prompt-rules → agent-checks-on: confidently wrong", RULES, ON, _cw, True, False),
    ("(S1) agent-prompt-rules → agent-checks-on: accuracy", RULES, ON, _acc, True, False),
    (
        "(S2) off → on: wrong-argument calls per 100 runs",
        OFF,
        ON,
        lambda s: s.wrong_arg_ran,
        False,
        True,
    ),
    ("(S3) off → on: accuracy", OFF, ON, _acc, True, False),
    (
        "(S4) off → on: confidently wrong, both graders",
        OFF,
        ON,
        lambda s: s.confidently_wrong_both_graders,
        True,
        False,
    ),
    (
        "(S5) off → on: confidently wrong, every error row counted as confidently wrong",
        OFF,
        ON,
        lambda s: s.confidently_wrong or bool(s.error),
        True,
        False,
    ),
)


def secondary_section(f: Final) -> list[str]:
    """S1 to S5 on held-out, and the same on development beside them."""
    lines = [
        "## 3. The secondary comparisons",
        "",
        "S2's rate falls partly by design: with the checks on, a stopped call never runs. "
        "Development (`dev_traps`): the checks were built while looking at these questions.",
        "",
        *COMPARISON_HEAD,
    ]
    for sets in (HELD, ("dev_traps",)):
        for what, first, second, value, majority, per100 in SECONDARY:
            c = compare(f.part(sets, first), f.part(sets, second), value, majority=majority)
            lines.append(_comparison_row(_set_title(sets), what, c, per100=per100))
    return [*lines, ""]


# ---------------------------------------------------------------- 4. the outcome table

OUTCOMES = (
    "correct",
    "partly",
    "wrong",
    "wrong_number",
    "other_year_number",
    "year_not_stated",
    "no_number",
    "answered_when_should_ask",
    "asked_about_another_thing",
    "asked_when_should_answer",
    "asked",
    "abstained",
    "answered",
    "not_graded",
    "error",
)


def outcome_section(f: Final) -> list[str]:
    """Each set and arm's runs by the deciding grader's outcome (every run, scored or not)."""
    lines = [
        "## 4. The outcome table",
        "",
        "Every run by the deciding grader's outcome: the deterministic grader for number-graded "
        "runs, the LLM grader for text-graded ones. The two questions not scored are counted "
        "here (and in no rate).",
        "",
        "| Set | Arm | Runs | " + " | ".join(OUTCOMES) + " | other |",
        "|---|---|---:|" + "---:|" * (len(OUTCOMES) + 1),
    ]
    for set_name in SETS:
        for arm in ARMS:
            part = f.part((set_name,), arm)
            counts = Counter(deciding_outcome(s) for s in part)
            other = sum(n for o, n in counts.items() if o not in OUTCOMES)
            cells = " | ".join(str(counts.get(o, 0)) for o in OUTCOMES)
            lines.append(f"| {set_name} | {arm} | {len(part)} | {cells} | {other} |")
    return [*lines, ""]


# ---------------------------------------------------------------- 5. check activity

GROUPS: tuple[tuple[str, tuple[str, ...]], ...] = (
    (HELD_OUT, HELD),
    ("dev_traps", ("dev_traps",)),
    ("dev_unanswerable", ("dev_unanswerable",)),
    ("control", ("control",)),
)


def check_section(f: Final) -> list[str]:
    """In checks-on: pass, repair and reject by category, tool and check; the as-sent calls."""
    lines = [
        "## 5. Check activity (agent-checks-on)",
        "",
        "Every check's result on every tool call, from the override log in each row.",
        "",
        "| Set | Category | Tool | Check | pass | repair | reject |",
        "|---|---|---|---|---:|---:|---:|",
    ]
    for title, sets in GROUPS:
        counts: dict[tuple[str, str, str], Counter[str]] = defaultdict(Counter)
        for set_name in sets:
            for row in f.rows[(set_name, ON)]:
                kind = str(f.questions[set_name][row["id"]].category)
                for e in row.get("overrides") or []:
                    key = (kind, str(e.get("tool") or NUMBER_TOOL), str(e.get("check")))
                    counts[key][str(e.get("outcome"))] += 1
        for (category, tool, check), c in sorted(counts.items()):
            lines.append(
                f"| {title} | {category} | {tool} | {check} | {c['pass']} | {c['repair']} | "
                f"{c['reject']} |"
            )
    lines += [
        "",
        "**Wrong-argument calls as the model sent them** (before the page filter or a check "
        "changed anything; with the checks off they equal what ran), per 100 runs, and what "
        "happened to them with the checks on:",
        "",
        "| Set | As sent, checks off | As sent, checks on | Checks on: repaired | rejected | ran "
        "unchanged |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for title, sets in GROUPS:
        sent = {
            arm: rate([s for s in f.part(sets, arm) if s.scored], lambda s: s.wrong_arg_sent or 0)
            for arm in (OFF, ON)
        }
        total: Counter[str] = Counter()
        for set_name in sets:
            for row in f.rows[(set_name, ON)]:
                q = f.questions[set_name][row["id"]]
                if q.scored:
                    total.update(sent_breakdown(row, q))
        lines.append(
            f"| {title} | {_per100(sent[OFF])} | {_per100(sent[ON])} | {total['repaired']} | "
            f"{total['rejected']} | {total['ran unchanged']} |"
        )
    return [*lines, ""]


# ---------------------------------------------------------------- 6. control


def control_section(f: Final) -> list[str]:
    """False repairs on control questions, each listed; accuracy off against on."""
    on = f.part(("control",), ON)
    false = [s for s in on if s.false_repair]
    runs = len(on)
    lines = [
        "## 6. Control",
        "",
        f"False repairs: {len(false)} of {runs} checks-on control runs "
        f"({100 * len(false) / runs:.1f} per 100) had a check repair or reject a "
        "`get_financial_fact` call.",
        "",
    ]
    if false:
        lines += ["| Question | Run | Check | Outcome | Reason |", "|---|---:|---|---|---|"]
        by_key = {(r["id"], r.get("repeat", 1)): r for r in f.rows[("control", ON)]}
        for s in false:
            for e in by_key[(s.id, s.repeat)].get("overrides") or []:
                if (
                    e.get("outcome") in ("repair", "reject")
                    and (e.get("tool") or NUMBER_TOOL) == NUMBER_TOOL
                ):
                    reason = str(e.get("reason", "")).replace("|", "\\|")
                    what = f"{e.get('check')} | {e.get('outcome')}"
                    lines.append(f"| {s.id} | {s.repeat} | {what} | {reason} |")
        lines.append("")
    search = sum(s.search_repairs for s in on)
    c = compare(f.part(("control",), OFF), on, _acc, majority=True)
    low = c.interval.low
    harm = (
        f"the interval cannot rule out a fall of up to {abs(100 * low):.1f} points"
        if low < 0
        else "the interval does not include a fall"
    )
    lines += [
        f"The fiscal-year check's repairs on `search_filings` for control questions that name no "
        f"year, its design, are counted apart: {search}.",
        "",
        *COMPARISON_HEAD,
        _comparison_row("control", "accuracy, off → on", c),
        "",
        f"No harm is said only as far as the interval shows: {harm} ({c.questions} questions).",
        "",
    ]
    return lines


# ---------------------------------------------------------------- 7. noise


def noise_section(f: Final) -> list[str]:
    """The share of questions whose runs do not all get the same outcome."""
    lines = [
        "## 7. Noise",
        "",
        "Per set and arm, the share of scored questions whose 3 runs do not all get the same "
        "outcome (the deciding grader's). For scale: in Week 5, re-running identical code "
        "moved the count of correct `dev_traps` runs from 182 to 177 of 255.",
        "",
        "| Set | " + " | ".join(ARMS) + " |",
        "|---|" + "---:|" * len(ARMS),
    ]
    for set_name in SETS:
        cells = " | ".join(_pct(noise(f.part((set_name,), arm))) for arm in ARMS)
        lines.append(f"| {set_name} | {cells} |")
    return [*lines, ""]


# ---------------------------------------------------------------- 8. the questions apart


def _outcomes(parts: Sequence[RunScore]) -> str:
    counts = Counter(deciding_outcome(s) for s in parts)
    return ", ".join(f"{o} {n}" for o, n in counts.most_common())


def apart_section(f: Final) -> list[str]:
    """The calendar-year and one-candidate questions, and the questions not scored."""
    lines = [
        "## 8. Questions shown apart",
        "",
        "**The calendar-year questions** (held-006, held-044, held-049) count as written: "
        "their writers accept the nearest fiscal year, and the frozen fiscal-year check asks "
        "which fiscal year instead.",
        "",
        "| Question | " + " | ".join(ARMS) + " |",
        "|---|" + "---|" * len(ARMS),
    ]
    for qid in CALENDAR:
        cells = " | ".join(
            _outcomes([s for s in f.scores if s.id == qid and s.arm == a]) for a in ARMS
        )
        lines.append(f"| {qid} | {cells} |")
    rest = [s for s in f.scores if s.id not in CALENDAR]
    held_off = [s for s in rest if s.set_name in HELD and s.arm == OFF]
    held_on = [s for s in rest if s.set_name in HELD and s.arm == ON]
    lines += [
        "",
        "Held-out without them:",
        "",
        *COMPARISON_HEAD,
        _comparison_row(
            HELD_OUT, "confidently wrong, off → on", compare(held_off, held_on, _cw, majority=True)
        ),
        _comparison_row(
            HELD_OUT, "accuracy, off → on", compare(held_off, held_on, _acc, majority=True)
        ),
        "",
        '**"Do you mean X?" on a one-candidate name** (held-004, held-032, held-035): the strict '
        "clarify rule does not count a question back that names one company; they count as "
        "written, and are shown here under both rules (correct runs of 3).",
        "",
        "| Question | Arm | Strict rule | Lenient rule |",
        "|---|---|---:|---:|",
    ]
    for qid in ONE_CANDIDATE:
        q = f.question(qid)
        set_name = next(s for s in HELD if qid in f.questions[s])
        for arm in ARMS:
            rows = [r for r in f.rows[(set_name, arm)] if r["id"] == qid]
            grades = [grade(dict(r), q) for r in rows]
            strict = sum(1 for g in grades if g.outcome == "correct")
            lenient = sum(1 for g in grades if (g.lenient_outcome or g.outcome) == "correct")
            lines.append(f"| {qid} | {arm} | {strict} | {lenient} |")
    lines += ["", "**Not scored** (run like the others, left out of every rate):", ""]
    for set_name in SETS:
        for q in f.questions[set_name].values():
            if not q.scored:
                lines.append(f"- {q.id} ({set_name}): {q.not_scored_reason}")
    return [*lines, ""]


# ---------------------------------------------------------------- 9. the graders

# Graders item (ii): an LLM reason that may contradict its verdict, to be confirmed by reading.
PASS_BUT = ("incorrect", "is wrong", "wrong number", "fails to", "contradicts", "does not match")
FAIL_BUT = ("correctly", "matches the gold", "is correct", "fully correct")


def contradiction_candidates(f: Final) -> list[tuple[str, str, LlmGrade]]:
    """LLM grades whose reason has a word that goes against the verdict (keyword list)."""
    found: list[tuple[str, str, LlmGrade]] = []
    for (set_name, arm), grades in f.llm.items():
        for g in grades.values():
            reason = g.reason.lower()
            passed_but = g.verdict == "correct" and any(k in reason for k in PASS_BUT)
            failed_but = g.verdict in ("wrong", "partly") and any(k in reason for k in FAIL_BUT)
            if passed_but or failed_but:
                found.append((set_name, arm, g))
    return sorted(found, key=lambda t: (t[0], t[1], t[2].id, t[2].repeat))


def _amounts(text: str) -> bool:
    return any(n.amount for n in find_numbers(text))


def _excerpt(text: str, size: int = 140) -> str:
    return " ".join(str(text).split())[:size].replace("|", "\\|")


def graders_section(
    f: Final,
    confirmed: Mapping[tuple[str, str, str, int], tuple[str, str]],
    blind: Sequence[str],
) -> list[str]:
    """Items (i) to (v): disagreements, contradictions, the blind check, misses, cited figures."""
    lines = ["## 9. The graders", "", "**(i) The two graders on number-graded runs.**", ""]
    lines += [
        "| Arm | Runs with a second opinion | Deterministic passes, LLM fails | Deterministic "
        "fails, LLM passes |",
        "|---|---:|---:|---:|",
    ]
    pairs: Counter[tuple[str, str]] = Counter()
    for arm in ARMS:
        second = [
            s
            for s in f.scores
            if s.arm == arm and s.graded_by == "number" and s.llm_verdict and not s.error
        ]
        passes = sum(1 for s in second if s.outcome == "correct" and s.llm_verdict != "correct")
        fails = sum(1 for s in second if s.outcome != "correct" and s.llm_verdict == "correct")
        pairs.update((s.outcome, str(s.llm_verdict)) for s in second)
        lines.append(f"| {arm} | {len(second)} | {passes} | {fails} |")
    lines += [
        "",
        "Every pairing, all arms:",
        "",
        "| Deterministic | LLM | Runs |",
        "|---|---|---:|",
        *[f"| {o} | {v} | {n} |" for (o, v), n in pairs.most_common()],
        "",
        "**(ii) LLM reasons that contradict their verdicts**, found with a keyword list "
        f"(a pass whose reason says {', '.join(repr(k) for k in PASS_BUT)}; a fail whose reason "
        f"says {', '.join(repr(k) for k in FAIL_BUT)}) and confirmed by reading.",
        "",
    ]
    candidates = contradiction_candidates(f)
    if not confirmed:
        lines += [f"{len(candidates)} candidates; not yet read.", ""]
    else:
        yes = [
            (s, a, g)
            for s, a, g in candidates
            if confirmed.get((s, a, g.id, g.repeat), ("", ""))[0] == "yes"
        ]
        lines += [
            f"{len(candidates)} candidates; {len(yes)} confirmed by reading:",
            "",
            "| Set | Arm | Question | Run | Verdict | Reason | Note |",
            "|---|---|---|---:|---|---|---|",
        ]
        for s, a, g in yes:
            note = confirmed[(s, a, g.id, g.repeat)][1]
            why = _excerpt(g.reason, 200)
            lines.append(f"| {s} | {a} | {g.id} | {g.repeat} | {g.verdict} | {why} | {note} |")
        lines.append("")
    lines += ["**(iii) The blind check of 30 text verdicts.**", "", *blind, ""]
    lines += [
        "**(iv) Refusals the decline rule missed:** refusal runs graded `answered_when_should_ask` "
        "with no amount in the answer, which the LLM's second opinion calls correct.",
        "",
        "| Set | Arm | Question | Run | Answer |",
        "|---|---|---|---:|---|",
    ]
    missed = 0
    for (set_name, arm), rows in f.rows.items():
        grades = f.llm[(set_name, arm)]
        for r in rows:
            q = f.questions[set_name][r["id"]]
            opinion = grades.get((r["id"], r.get("repeat", 1)))
            if (
                q.expected_behavior == "refuse"
                and grade(dict(r), q).outcome == "answered_when_should_ask"
                and not _amounts(str(r.get("answer") or ""))
                and opinion is not None
                and opinion.verdict == "correct"
            ):
                missed += 1
                excerpt = _excerpt(r.get("answer") or "")
                lines.append(
                    f"| {set_name} | {arm} | {r['id']} | {r.get('repeat', 1)} | {excerpt} |"
                )
    lines += [
        "" if missed else "None.",
        "",
        "**(v) Refusal runs that gave a figure from a cited source**, with the grade each got.",
        "",
        "| Set | Arm | Question | Run | Deterministic | LLM | Answer |",
        "|---|---|---|---:|---|---|---|",
    ]
    for (set_name, arm), rows in f.rows.items():
        grades = f.llm[(set_name, arm)]
        for r in rows:
            q = f.questions[set_name][r["id"]]
            text = str(r.get("answer") or "")
            cited = bool(r.get("citations") or r.get("fact_citations"))
            if q.expected_behavior == "refuse" and cited and _amounts(text):
                got = grades.get((r["id"], r.get("repeat", 1)))
                lines.append(
                    f"| {set_name} | {arm} | {r['id']} | {r.get('repeat', 1)} | "
                    f"{grade(dict(r), q).outcome} | {got.verdict if got else '-'} | "
                    f"{_excerpt(text)} |"
                )
    return [*lines, ""]


# ---------------------------------------------------------------- 10. error analysis

CAUSES = {
    1: "a wrong argument that no check caught",
    2: "a check acted, but the answer ignored it",
    3: "the right call, but a wrong figure in the answer (wrong line, units, sign)",
    4: "year not stated",
    5: "asked or abstained when it should have answered",
    6: "answered when it should have asked or refused",
    7: "search missed the passage",
    8: "grader error (say which way)",
    9: "provider error",
    10: "other, with a note",
}
ERROR_SEED = 20261142


def error_sample(f: Final, seed: int = ERROR_SEED) -> list[RunScore]:
    """The checks-on runs to analyse: held-out not correct (all, or 60 by seed), 30 dev_traps."""
    import random

    def wrong(sets: Sequence[str]) -> list[RunScore]:
        part = [s for s in f.part(sets, ON) if s.scored and not s.correct]
        return sorted(part, key=lambda s: (s.set_name, s.id, s.repeat))

    held, dev = wrong(HELD), wrong(("dev_traps",))
    if len(held) > 60:
        held = sorted(
            random.Random(seed).sample(held, 60), key=lambda s: (s.set_name, s.id, s.repeat)
        )
    if len(dev) > 30:
        dev = sorted(
            random.Random(seed + 1).sample(dev, 30), key=lambda s: (s.set_name, s.id, s.repeat)
        )
    return held + dev


# Added after the results (the Day 41 review): the analysed failures in two groups, each an id
# list and the causes that mark the runs where it acted, counted from the error-analysis CSV.
CHECK_ACTION: tuple[tuple[str, frozenset[str], frozenset[int]], ...] = (
    (
        "the fiscal-year check's calendar-year rejects (held-006, held-044, held-049)",
        frozenset({"held-006", "held-044", "held-049"}),
        frozenset({5}),
    ),
    (
        "an ambiguity reject despite the page filter (dev-010)",
        frozenset({"dev-010"}),
        frozenset({5}),
    ),
    (
        "lowercase 'msft' not read, repaired to AAPL (dev-011)",
        frozenset({"dev-011"}),
        frozenset({10}),
    ),
    (
        "'the year before last' repaired one year too far (dev-031)",
        frozenset({"dev-031"}),
        frozenset({10}),
    ),
)
CHECK_GAP: tuple[tuple[str, frozenset[str], frozenset[int]], ...] = (
    (
        "the fact tool lets the model's year stand when the question names none "
        "(held-053, held-059, held-063)",
        frozenset({"held-053", "held-059", "held-063"}),
        frozenset({1}),
    ),
    ("'last yr' (held-003)", frozenset({"held-003"}), frozenset({1})),
    ("'morgans' (held-030)", frozenset({"held-030"}), frozenset({1})),
    (
        "'american', 'uniteds' (held-004, held-035, held-032)",
        frozenset({"held-004", "held-035", "held-032"}),
        frozenset({1}),
    ),
    ("'standard and poors' (held-038)", frozenset({"held-038"}), frozenset({5})),
    ("'Citizens' (dev-003)", frozenset({"dev-003"}), frozenset({1})),
    ("no company check on search_filings (dev-057)", frozenset({"dev-057"}), frozenset({1})),
)


def failure_groups(
    causes: Mapping[tuple[str, str, int], tuple[int, str]],
) -> tuple[list[tuple[str, int, int]], list[tuple[str, int, int]]]:
    """Each group's items with their held-out and development counts of analysed runs."""

    def count(
        items: Sequence[tuple[str, frozenset[str], frozenset[int]]],
    ) -> list[tuple[str, int, int]]:
        out = []
        for label, ids, marks in items:
            hits = [k for k, (cause, _) in causes.items() if k[1] in ids and cause in marks]
            held = sum(1 for k in hits if k[0] in HELD)
            out.append((label, held, len(hits) - held))
        return out

    return count(CHECK_ACTION), count(CHECK_GAP)


def error_section(
    f: Final, causes: Mapping[tuple[str, str, int], tuple[int, str]], seed: int = ERROR_SEED
) -> list[str]:
    """Each analysed run with one cause and a one-line reason (read, not computed)."""
    sample = error_sample(f, seed)
    held = [s for s in sample if s.set_name in HELD]
    lines = [
        "## 10. Error analysis",
        "",
        f"The checks-on runs that are not correct: on held-out {len(held)} "
        f"({'all of them' if len(held) < 60 else f'60 drawn by seed {seed}'}), and on "
        f"`dev_traps` {len(sample) - len(held)} drawn by seed {seed + 1} (all of them if fewer). "
        "Each was read and given one cause with a one-line reason.",
        "",
    ]
    if not causes:
        return [*lines, "Not yet read.", ""]
    tally = Counter(
        causes[(s.set_name, s.id, s.repeat)][0]
        for s in sample
        if (s.set_name, s.id, s.repeat) in causes
    )
    lines += ["| Cause | Held-out and dev_traps runs |", "|---|---:|"]
    lines += [f"| {n}. {CAUSES[n]} | {tally.get(n, 0)} |" for n in CAUSES]
    action, gap = failure_groups(causes)
    lines += [
        "",
        "*Added after the results:* the analysed failures in two groups, counted from the causes "
        "above (no new rule; the review chose the groups).",
        "",
        "| Group | Item | Held-out runs | dev_traps runs |",
        "|---|---|---:|---:|",
    ]
    for title, items in (
        ("caused by a check's own action", action),
        ("a gap the checks do not cover", gap),
    ):
        for label, held_n, dev_n in items:
            lines.append(f"| {title} | {label} | {held_n} | {dev_n} |")
        held_t, dev_t = sum(h for _, h, _ in items), sum(d for _, _, d in items)
        lines.append(f"| {title} | **all** | **{held_t}** | **{dev_t}** |")
    grouped = sum(h + d for _, h, d in action + gap)
    lines += [
        "",
        f"The other {len(sample) - grouped} analysed runs are in neither group (the model's own "
        "choices, grader errors, and the rest).",
    ]
    lines += [
        "",
        "| Set | Question | Run | Outcome | Cause | Reason |",
        "|---|---|---:|---|---:|---|",
    ]
    for s in sample:
        cause, reason = causes.get((s.set_name, s.id, s.repeat), (0, "not read"))
        lines.append(
            f"| {s.set_name} | {s.id} | {s.repeat} | {deciding_outcome(s)} | {cause} | {reason} |"
        )
    return [*lines, ""]


# ---------------------------------------------------------------- 11. costs


def cost_section(f: Final, billed: str) -> list[str]:
    """The answers' and the grader's recorded cost; what the key was billed."""
    lines = [
        "## 11. Costs",
        "",
        "| Arm | Answers (recorded) | LLM grades, new (recorded) |",
        "|---|---:|---:|",
    ]
    total_a = total_g = 0.0
    for arm in ARMS:
        a = sum(s.cost_usd for s in f.scores if s.arm == arm)
        g = sum(
            gr.cost_usd or 0.0
            for (_, x), grades in f.llm.items()
            if x == arm
            for gr in grades.values()
            if not gr.cached
        )
        total_a, total_g = total_a + a, total_g + g
        lines.append(f"| {arm} | ${a:.4f} | ${g:.4f} |")
    lines += [f"| **All** | **${total_a:.4f}** | **${total_g:.4f}** |", "", billed, ""]
    return lines


# ---------------------------------------------------------------- the method, and the page

METHOD = [
    "## Method",
    "",
    "- **What ran:** commit `da7a451` (tag `week6-measured`), 2026-11-14, batch mode, "
    "`openrouter:openai/gpt-oss-20b` with the deployed settings, five arms over five question "
    "sets, 3 runs per question: 3,855 rows. The held-out files' seals and the "
    "pre-registration's SHA-256 were printed and checked before the run; every row records the "
    "commit, a clean tree and its question file's SHA-256 "
    "(`eval/results/2026-11-14_final-run_record.md`). The definitions are "
    "`eval/PREREGISTRATION.md`, unchanged since it was merged; its last section says how the "
    "code reads seven of them.",
    "- **Grading:** the deterministic grader decides number-graded runs (strict clarify "
    "rule) and the LLM grader (prompt version 2, frozen) decides text-graded runs; the LLM "
    "gave a second opinion on every number-graded run, which changes no grade. All grading ran "
    "after every arm had ended.",
    "- **Changed before the final run, after the pre-registration** (each in `docs/decisions.md`):",
    "  - *The decline rule reads the checks' own refusal wordings* (\"is not one of the 25 "
    'companies", "has no 10-K for fiscal 2022 in the dataset", ...). Before, a correct '
    "refusal in those words was graded as an answer, and counted confidently wrong. Found on "
    "the prompt-rules arm's development run; every stored row was re-graded with the rule "
    "before and after: 17 outcomes changed, all in the prompt-rules development files, none in "
    "the checks-off or checks-on files. Phrases from model answers were not added; graders "
    "item (iv) lists the refusals the rule still misses.",
    "  - *The prompt-rules block is version 1*, as the code built it from the checks' data. A "
    "version 2 (one line reworded) was run on the development sets and withdrawn at review, "
    "because its reason was wrong; its rows are kept.",
    "  - *The step-cap change was reverted.* Sending no tools after the step cap did not stop "
    'the provider\'s "tool choice is none" error, so the frozen behaviour stands; such runs are '
    "error rows (`tool_choice_none`), never correct and never confidently wrong.",
    "- **Not scored:** held-045 and held-048, run like the others and left out of every rate "
    "(section 8). The held-out set has 110 scored questions: 28 in the first file and 82 in the "
    "second.",
    "- **Disclosures:** the first held-out file (28) was written by an AI agent launched from "
    "the coding session, which also received the project's description file (it names the "
    "checks); the second (84) by Google Gemini through its API, outside the project. The "
    "development questions were in view while the checks were built, so development results "
    "are labelled as such and are not evidence.",
    "- **Latency:** the PC slept for most of the baseline arm; one run's time includes the "
    "sleep. It counts in every figure as pre-registered; one line marked *added after the "
    "results* gives the baseline's control latency without it (section 2).",
    "- **Every number below is computed from the committed rows and grades** by "
    "`python -m filingcheck.eval report` (`filingcheck/eval/final_render.py`, "
    "`filingcheck/eval/final_report.py`); the per-run CSV holds the pre-registration's columns.",
    "",
]


def render_report(
    f: Final,
    floor: Sequence[RunScore],
    *,
    blind: Sequence[str],
    confirmed: Mapping[tuple[str, str, str, int], tuple[str, str]],
    causes: Mapping[tuple[str, str, int], tuple[int, str]],
    billed: str,
    live: Sequence[str] = (),
) -> str:
    """The whole report, in the Day 41 order."""
    lines = [
        "# The final run: results",
        "",
        "The Week 6 measurement of FilingCheck: five arms, the sealed held-out questions and the "
        "development sets, scored by the pre-registered rules. Held-out is both sealed files "
        "together.",
        "",
        *METHOD,
        *headline_section(f),
        *ablation_section(f, floor, live),
        *secondary_section(f),
        *outcome_section(f),
        *check_section(f),
        *control_section(f),
        *noise_section(f),
        *apart_section(f),
        *graders_section(f, confirmed, blind),
        *error_section(f, causes),
        *cost_section(f, billed),
    ]
    return "\n".join(lines).rstrip() + "\n"


# ---------------------------------------------------------------- 9 (iii). the blind check


def shown_path(path: Path, root: Path) -> str:
    """A file's path as the report prints it: relative to the repository root, forward slashes.

    The same on every machine and under any folder name.
    """
    return path.resolve().relative_to(root.resolve()).as_posix()


def blind_section(f: Final, folder: Path, hidden: Path, root: Path) -> list[str]:
    """The reveal: each blind grader's agreement with the LLM grader, and every row that differs."""
    from filingcheck.eval.final_report import (
        agreement,
        parse_blind_keys,
        parse_pipe_grades,
        parse_table_grades,
    )

    keys = parse_blind_keys(hidden.read_text(encoding="utf-8"))
    reply = folder / f"{hidden.name[:10]}_final_blind_gemini_output.md"
    session_file = folder / f"{hidden.name[:10]}_final_blind_reviewing_session_grades.md"
    gemini = parse_pipe_grades(reply.read_text(encoding="utf-8"))
    session = parse_table_grades(session_file.read_text(encoding="utf-8"))
    llm: dict[int, tuple[str, str]] = {}
    for n, key in enumerate(keys, 1):
        path, qid, run = key.rsplit(":", 2)
        set_name = path.split("2026-11-14_", 1)[1].split("_agent-checks-on", 1)[0]
        g = f.llm[(set_name, ON)][(qid, int(run))]
        llm[n] = (str(g.verdict), str(g.supported))
        if n in session and session[n][0] != f"{qid}:{run}":
            raise ValueError(f"row {n}: the session graded {session[n][0]}, the file has {key}")
    if sorted(gemini) != list(range(1, len(keys) + 1)) or sorted(session) != sorted(gemini):
        raise ValueError("a blind grader did not grade every row once")

    def pick(grades: Mapping[int, Sequence[str]], i: int) -> dict[int, str]:
        return {n: g[i] for n, g in grades.items()}

    g_v, g_s = pick(gemini, 0), pick(gemini, 1)
    s_v, s_s = (
        pick({n: v[1:] for n, v in session.items()}, 0),
        pick({n: v[1:] for n, v in session.items()}, 1),
    )
    l_v, l_s = pick(llm, 0), pick(llm, 1)
    total = len(keys)
    lines = [
        f"{total} text-graded runs drawn by seed from the final `agent-checks-on` rows "
        f"(`{shown_path(hidden, root)}`, written with the LLM verdicts "
        "hidden), graded blind before the LLM verdicts were shown, by the LLM grader's own "
        "definitions:",
        "",
        "- Google Gemini (`gemini-3.8-flash`, the model rule's choice) through its API, one "
        "request, its reply committed unedited. The newest Pro returned the free tier's quota "
        "error on three tries and the newest Flash was overloaded on six, with no reply, before "
        "it replied (each attempt is committed beside the reply).",
        "- A reviewing AI session, from the same file only; its grades were hashed before the "
        "reveal and copied in unedited.",
        "",
        "| Grader | Verdict agrees with the LLM grader | Supported agrees |",
        "|---|---:|---:|",
        f"| Gemini | {agreement(g_v, l_v)} of {total} | {agreement(g_s, l_s)} of {total} |",
        f"| reviewing session | {agreement(s_v, l_v)} of {total} | "
        f"{agreement(s_s, l_s)} of {total} |",
        "",
        f"The two blind graders agree with each other on {agreement(g_v, s_v)} verdicts and "
        f"{agreement(g_s, s_s)} supported of {total}.",
        "",
        "Every row where a blind grader differs from the LLM grader (verdict, then supported):",
        "",
        "| # | Row | LLM | Gemini | Session | LLM | Gemini | Session |",
        "|---:|---|---|---|---|---|---|---|",
    ]
    for n, key in enumerate(keys, 1):
        if (g_v[n], s_v[n], g_s[n], s_s[n]) != (l_v[n], l_v[n], l_s[n], l_s[n]):
            row = key.rsplit(":", 2)
            lines.append(
                f"| {n} | {row[1]} #{row[2]} | {l_v[n]} | {g_v[n]} | {s_v[n]} | {l_s[n]} | "
                f"{g_s[n]} | {s_s[n]} |"
            )
    lines += [
        "",
        "The grader prompt does not change after this check; the result is reported as it is.",
    ]
    return lines
