"""Day 24: the agent with the checks off and on, side by side.

Each arm is a `make eval` run whose file name carries it (`<date>_<set>_agent-checks-on.jsonl`,
`..._agent-checks-off.jsonl`; Day 20's `..._agent.jsonl` predates the checks). After an
agent run, when a finished file of the other arm exists, `make eval` writes
`<date>_<set>_agent-arms.md`: the two arms as two rows one under the other, then each
question with both arms' outcomes, what the checks did and whether the outcomes differ. A
handful of questions shows that the layer works and is logged; it measures nothing (Week 6).
"""

import json
from collections import Counter
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from filingcheck.eval.grade import LABELS, OUTCOMES, Grade, summary_header, summary_row
from filingcheck.eval.run import DATED

Graded = Sequence[tuple[dict[str, Any], Grade]]
ON_WORDS = {"on", "1", "true", "yes"}
OFF_WORDS = {"off", "0", "false", "no"}


def arm_name(
    mode: str,
    checks: bool | None,
    label: str | None = None,
    *,
    retriever: str = "hybrid",
    rules: bool = False,
) -> str:
    """The run's name in its file name, as in 'baseline-vector' or 'agent-checks-on'.

    The baselines are 'baseline' (hybrid search) and 'baseline-vector'; the agent arms are
    'agent-checks-on' and 'agent-checks-off'. A `label` names a separate run of the same arm
    ('agent-checks-on-search-year'): a re-run after a change, kept apart from the day's earlier
    files. `rules` is the prompt-rules arm (Week 6): 'agent-prompt-rules', the agent with
    the checks off and the checks' rules in its prompt.
    """
    if rules and mode != "agent":
        raise ValueError("the prompt-rules arm is an agent arm: MODE=agent")
    if rules and checks:
        raise ValueError("the prompt-rules arm has the checks off: add CHECKS=off")
    if mode != "agent":
        if checks is not None:
            raise ValueError("the checks apply to the agent only")
        name = mode if retriever == "hybrid" else f"{mode}-{retriever}"
    else:
        if retriever != "hybrid":
            raise ValueError("the agent always searches hybrid; RETRIEVER is the baseline's")
        name = "agent-checks-on" if checks else "agent-checks-off"
        if rules:
            name = "agent-prompt-rules"
    return f"{name}-{label}" if label else name


def checks_argument(mode: str, value: str | None) -> bool | None:
    """`--checks on|off` for `make eval`: on by default for the agent, as everywhere else."""
    if mode != "agent":
        if value is not None:
            raise ValueError("--checks applies to the agent only")
        return None
    if value is None or value.lower() in ON_WORDS:
        return True
    if value.lower() in OFF_WORDS:
        return False
    raise ValueError(f"--checks must be on or off, not {value!r}")


def arms_path(set_name: str, day: str) -> Path:
    """Where the comparison goes, relative to the repository root."""
    return Path("eval") / "results" / f"{day}_{set_name}_agent-arms.md"


def finished_arm(
    root: Path, set_name: str, name: str, *, expected_rows: int, question_ids: set[str]
) -> Path | None:
    """The newest results file of this set and arm with a row for every (question, repeat)."""
    for path in sorted((root / "eval" / "results").glob(f"{DATED}_{set_name}_{name}.jsonl"))[::-1]:
        rows = [
            json.loads(line)
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        if len([r for r in rows if r.get("id") in question_ids]) >= expected_rows:
            return path
    return None


def _outcomes(part: Graded) -> str:
    counts = Counter(grade.outcome for _, grade in part)
    return ", ".join(f"{LABELS[o]} x{counts[o]}" for o in OUTCOMES if counts[o])


def _did(row: dict[str, Any]) -> str:
    """What the checks did in one run: the non-pass outcomes, 'pass', or 'no fact call'."""
    overrides = row.get("overrides") or []
    odd = [f"{o['check']} {o['outcome']}" for o in overrides if o.get("outcome") != "pass"]
    if odd:
        return " + ".join(odd)
    return "pass" if overrides else "no fact call"


def _what_the_checks_did(part: Graded) -> str:
    counts = Counter(_did(row) for row, _ in part)  # in the order first seen
    return ", ".join(f"{what} x{n}" for what, n in counts.items())


def compare_arms(off: Graded, on: Graded, *, set_name: str, off_file: str, on_file: str) -> str:
    """The comparison page: the two arms' rows, then each question in both arms."""
    ids = list(dict.fromkeys([row["id"] for row, _ in off] + [row["id"] for row, _ in on]))
    runs = max((row.get("repeat", 1) for row, _ in [*off, *on]), default=0)
    lines = [
        f"# The two arms: {set_name}, the agent with the checks off and on",
        "",
        f"Checks off: `{off_file}`; checks on: `{on_file}`; {runs} run(s) per question. Graded by "
        "the deterministic number grader (`filingcheck/eval/grade.py`). Written by `make eval`.",
        "",
        f"**{len(ids)} questions prove nothing about accuracy.** This page shows that the checks "
        "layer works and is logged; the measurement with intervals is Week 6's.",
        "",
        *summary_header("Arm"),
        summary_row("Checks off", off),
        summary_row("Checks on", on),
        "",
        "## Each question",
        "",
        "| Question | Checks off | Checks on | What the checks did | Outcomes differ |",
        "|---|---|---|---|---|",
    ]
    for qid in ids:
        off_part = [(r, g) for r, g in off if r["id"] == qid]
        on_part = [(r, g) for r, g in on if r["id"] == qid]
        off_cell = _outcomes(off_part) if off_part else "not run"
        on_cell = _outcomes(on_part) if on_part else "not run"
        did = _what_the_checks_did(on_part) if on_part else "-"
        if off_part and on_part:
            same = Counter(g.outcome for _, g in off_part) == Counter(g.outcome for _, g in on_part)
            changed = "no" if same else "yes"
        else:
            changed = "-"
        lines.append(f"| {qid} | {off_cell} | {on_cell} | {did} | {changed} |")
    lines += [
        "",
        "Outcomes can differ from model variance alone; a check changed an answer only where "
        '"What the checks did" shows a repair or a reject.',
    ]
    return "\n".join(lines) + "\n"
