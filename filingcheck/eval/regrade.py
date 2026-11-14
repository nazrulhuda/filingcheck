"""Re-grade stored rows after a grader change, and list every outcome that changes.

The Day 39 review added the company and metric checks' reject wordings to the decline rule
(`grade.CHECK_REJECT_DECLINES`). This grades each stored row twice with the current question
file, with the rule as it was before the fix and as it is now, so a change is the fix's alone
and not an older grader change or a question edit. The stored grade is kept beside both, and
the count of stored grades that differ from the "before" grade is shown apart. No row is
edited: the new grades go to new files.
"""

import re
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any

from filingcheck.eval import grade as grader
from filingcheck.eval.grade import CHECK_REJECT_DECLINES, Grade
from filingcheck.eval.questions import Question

ANSWER_CHARS = 140  # of the answer shown beside a change


@contextmanager
def previous_decline_rule() -> Iterator[None]:
    """The grader with the decline rule as it was before the Nov 14 fix, then put back."""
    current = grader.DECLINE_RE
    pattern = current.pattern.replace(CHECK_REJECT_DECLINES, "", 1)
    if pattern == current.pattern:
        raise ValueError("the decline rule does not hold the fix's wordings")
    grader.DECLINE_RE = re.compile(pattern, current.flags)
    try:
        yield
    finally:
        grader.DECLINE_RE = current


@dataclass(frozen=True)
class Regraded:
    """One stored row graded before and after the fix."""

    id: str
    repeat: int
    answer: str
    stored: str | None  # the outcome stored in the row, if any
    before: str  # the outcome with the decline rule before the fix
    before_lenient: str | None
    after: Grade

    @property
    def changed(self) -> bool:
        """Whether the fix changes the outcome or the lenient clarify outcome."""
        return (self.before, self.before_lenient) != (
            self.after.outcome,
            self.after.lenient_outcome,
        )


def set_for(file_name: str, set_names: Sequence[str]) -> str | None:
    """The question set of a results file (`<date>_<set>_<arm>.jsonl`), longest name first."""
    rest = file_name.split("_", 1)[1] if "_" in file_name else ""
    for name in sorted(set_names, key=len, reverse=True):
        if rest.startswith(f"{name}_"):
            return name
    return None


def regrade_rows(
    rows: Sequence[Mapping[str, Any]], questions: Mapping[str, Question]
) -> tuple[list[Regraded], int]:
    """Each row whose question is still in the file, graded before and after; and how many not."""
    out: list[Regraded] = []
    skipped = 0
    for row in rows:
        question = questions.get(row["id"])
        if question is None:
            skipped += 1
            continue
        with previous_decline_rule():
            before = grader.grade(dict(row), question)
        after = grader.grade(dict(row), question)
        stored = (row.get("grade") or {}).get("outcome")
        out.append(
            Regraded(
                id=row["id"],
                repeat=row.get("repeat", 1),
                answer=row.get("answer") or "",
                stored=stored,
                before=before.outcome,
                before_lenient=before.lenient_outcome,
                after=after,
            )
        )
    return out, skipped


def _cell(text: str) -> str:
    short = " ".join(text.split())[:ANSWER_CHARS]
    return short.replace("|", "\\|")


def render_changes(by_file: Mapping[str, Sequence[Regraded]], *, skipped: int) -> str:
    """The page: every row whose outcome the fix changes, with the totals."""
    rows = [r for part in by_file.values() for r in part]
    changes = [(name, r) for name, part in by_file.items() for r in part if r.changed]
    stale = sum(1 for r in rows if r.stored is not None and r.stored != r.before)
    lines = [
        "# Re-grade after the decline fix (Day 39 review)",
        "",
        "Every stored row in `eval/results/` graded with the current question files, by the "
        "deterministic grader with the decline rule before the fix and after it "
        "(`filingcheck/eval/regrade.py`); the new grades are in this folder, one file per "
        "results file. No stored row is edited.",
        "",
        f"{len(changes)} outcome(s) change, in {len(changes)} of {len(rows)} row(s), "
        f"{len(by_file)} file(s). Rows whose question is no longer in its file: {skipped}. "
        f"Stored grades that differ from the grade before the fix (older grader or question "
        f"changes, not this fix): {stale}.",
        "",
        "| File | Question | Run | Before | After | Answer |",
        "|---|---|---:|---|---|---|",
    ]
    lines += [
        f"| {name} | {r.id} | {r.repeat} | {r.before} | {r.after.outcome} | {_cell(r.answer)} |"
        for name, r in changes
    ]
    return "\n".join(lines) + "\n"
