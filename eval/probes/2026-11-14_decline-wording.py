"""Day 39 probe: refusals the deterministic grader fails only for their wording.

The prompt-rules block (version 1) has the model reply in the checks' reason words ("Tesla is
not one of the 25 companies in the dataset"); the grader's decline phrases (`DECLINE_RE` in
`filingcheck/eval/grade.py`, frozen) do not include "is not one of the". This counts, per arm on
the development rows, the refuse runs graded `answered_when_should_ask` that give no amount and
say "is/are not one of the" or "not among the", using the grader's own number reader; then the
development table recomputed from the metrics CSV (not with `metrics.py`), as graded and with
those runs counted correct. The second table is a what-if: the grader does not change.
Block version 2 (the Day 39 review's one revision, the company line only) is counted the same
way; its rows are `agent-prompt-rules-v2`.

It describes the grader before the Nov 14 decline fix, so it grades under that rule
(`filingcheck/eval/regrade.py`, `previous_decline_rule`); the fix's own effect on every
stored row is `eval/results/regrade_2026-11-14/changes.md`.

Run from the repository root: uv run python eval/probes/2026-11-14_decline-wording.py
"""

import csv
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

from filingcheck.eval.grade import asks_or_declines, find_numbers
from filingcheck.eval.regrade import previous_decline_rule

R = Path("eval/results")
ARMS = {
    "agent-checks-off": "2026-11-12_{s}_agent-checks-off-search-year",
    "agent-checks-on": "2026-11-12_{s}_agent-checks-on-search-year",
    "agent-prompt-rules": "2026-11-14_{s}_agent-prompt-rules",
    "agent-prompt-rules-v2": "2026-11-14_{s}_agent-prompt-rules-v2",
}
NOT_ONE_OF = re.compile(r"\b(?:is|are) not (?:one of|among) the\b", re.IGNORECASE)
SETS = ("dev_traps", "control")


def wording_only(answer: str, expected: str, outcome: str) -> bool:
    """A refuse run failed only because "is not one of the ..." is not a decline phrase."""
    if expected != "refuse" or outcome != "answered_when_should_ask":
        return False
    no_amount = not [n for n in find_numbers(answer) if n.amount]
    with previous_decline_rule():  # the stored grade, from before the fix, holds
        assert not (no_amount and asks_or_declines(answer)), answer
    return no_amount and NOT_ONE_OF.search(answer) is not None


def main() -> None:
    """Print both tables (see the module docstring)."""
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    flagged: set[tuple[str, str, str, str]] = set()  # (set, arm, id, repeat)
    print("| Set | Arm | Refuse runs failed for the wording only | By question |")
    print("|---|---|---:|---|")
    for s in SETS:
        questions = {
            q["id"]: q
            for q in map(
                json.loads,
                Path(f"eval/questions/{s}.jsonl").read_text(encoding="utf-8").splitlines(),
            )
        }
        for arm, stem in ARMS.items():
            lines = (R / f"{stem.format(s=s)}.jsonl").read_text(encoding="utf-8").splitlines()
            hits = []
            for row in map(json.loads, lines):
                q = questions[row["id"]]
                if wording_only(
                    row["answer"] or "", q["expected_behavior"], row["grade"]["outcome"]
                ):
                    hits.append(row["id"])
                    flagged.add((s, arm, row["id"], str(row["repeat"])))
            by_q = ", ".join(f"{qid} x{hits.count(qid)}" for qid in sorted(set(hits))) or "-"
            print(f"| {s} | {arm} | {len(hits)} | {by_q} |")

    with (R / "2026-11-14_dev_agent-prompt-rules-v1-v2_metrics.csv").open(
        encoding="utf-8"
    ) as handle:
        rows = list(csv.DictReader(handle))
    flagged_cw = sum(
        r["confidently_wrong"] == "True"
        for r in rows
        if (r["set"], r["arm"], r["id"], r["repeat"]) in flagged
    )
    print(f"\nOf the {len(flagged)} runs, counted confidently wrong as graded: {flagged_cw}.\n")
    print(
        "| Set | Arm | Accuracy, as graded | Confidently wrong, as graded | Accuracy, what-if "
        "| Confidently wrong, what-if |"
    )
    print("|---|---|---:|---:|---:|---:|")
    groups: dict[tuple[str, str], dict[str, list[tuple[bool, bool, bool]]]] = defaultdict(
        lambda: defaultdict(list)
    )
    for r in rows:
        hit = (r["set"], r["arm"], r["id"], r["repeat"]) in flagged
        groups[(r["set"], r["arm"])][r["id"]].append(
            (r["correct"] == "True", r["confidently_wrong"] == "True", hit)
        )
    for (s, arm), by_question in groups.items():
        print(
            f"| {s} | {arm} | {_mean(by_question, 0, False):.1f}% | "
            f"{_mean(by_question, 1, False):.1f}% | {_mean(by_question, 0, True):.1f}% | "
            f"{_mean(by_question, 1, True):.1f}% |"
        )


def _mean(by_question: dict[str, list[tuple[bool, bool, bool]]], pick: int, what_if: bool) -> float:
    """Per question first, then the mean: correct (pick 0) or confidently wrong (pick 1)."""
    total = 0.0
    for runs in by_question.values():
        values = []
        for correct, cw, hit in runs:
            if what_if and hit:  # a wording-only refusal: correct, not confidently wrong
                correct, cw = True, False
            values.append(correct if pick == 0 else cw)
        total += sum(values) / len(values)
    return 100 * total / len(by_question)


if __name__ == "__main__":
    main()
