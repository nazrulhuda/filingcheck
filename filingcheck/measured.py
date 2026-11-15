"""The measured system is pinned: `make verify-measured`.

The README's results describe the tagged commit `week6-measured`. Everything that could change
an answer or a reported number is listed here, in this one place:

- `PINNED`: the answering code, the grading and scoring code, the data pins, the pre-registration
  and the measured question sets, compared with the tag's commit `TAG_COMMIT` (recorded in full,
  so a tag moved onto another commit fails too);
- `ROWS`: the 50 final row and grade files, committed after the tag, compared with the commit
  that merged them, `ROWS_COMMIT`.

The check fails, naming each file, if any file under those paths differs from its commit,
whether a tracked change or a new file, or if the tag no longer points at its commit. What
moves the pin: a version 2 of the system, measured again on new sealed questions under a new
pre-registration, with its own tag. CI runs the check on every push (its checkout needs the
whole history, so the tag and both commits are there).
"""

import argparse
import subprocess
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

TAG = "week6-measured"
TAG_COMMIT = "da7a451e0a0ab872b2bc3f05a96699690b82d0eb"
PINNED: tuple[str, ...] = (
    # The answering code.
    "filingcheck/agent",
    "filingcheck/checks",
    "filingcheck/tools",
    "filingcheck/answer",
    "filingcheck/labels",
    "filingcheck/retrieval",
    "filingcheck/llm",
    "filingcheck/facts",
    # The grading and scoring code, and the LLM grader's prompt.
    "filingcheck/eval/grade.py",
    "filingcheck/eval/llm_grade.py",
    "filingcheck/eval/metrics.py",
    "filingcheck/eval/stats.py",
    "filingcheck/eval/questions.py",
    "eval/grader_prompt.md",
    # The data pins, the pre-registration and the measured question sets
    # (`page_examples.jsonl` is not pinned: the page's saved examples may grow).
    "data/companies.yaml",
    "data/manifest.json",
    "eval/PREREGISTRATION.md",
    "eval/questions/heldout_traps.jsonl",
    "eval/questions/heldout_traps_2.jsonl",
    "eval/questions/dev_traps.jsonl",
    "eval/questions/dev_unanswerable.jsonl",
    "eval/questions/control.jsonl",
)
# The final run's rows and grades (Day 40, merged as #79), unchanged since that merge.
ROWS_COMMIT = "4082c4e7ef6ba74a5acee0ad943fbdce06e77049"
ROWS: tuple[str, ...] = (
    "eval/results/2026-11-14_*-final.jsonl",
    "eval/results/2026-11-14_*-final_llm.jsonl",
)
REPO_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Pin:
    """Paths (git pathspecs) compared with one commit; `tag`, if given, must point at it."""

    commit: str
    paths: tuple[str, ...]
    tag: str | None = None


PINS: tuple[Pin, ...] = (Pin(TAG_COMMIT, PINNED, tag=TAG), Pin(ROWS_COMMIT, ROWS))


def _git(root: Path, *args: str) -> list[str]:
    done = subprocess.run(
        ["git", *args], cwd=root, capture_output=True, text=True, check=True, encoding="utf-8"
    )
    return [line for line in done.stdout.splitlines() if line.strip()]


def changed_files(root: Path, commit: str, paths: Sequence[str]) -> list[str]:
    """The files under `paths` that differ from `commit`: changed, deleted or new."""
    tracked = _git(root, "diff", "--name-only", "--no-renames", commit, "--", *paths)
    new = _git(root, "ls-files", "--others", "--exclude-standard", "--", *paths)
    return sorted(set(tracked) | set(new))


def problems(root: Path = REPO_ROOT, pins: Sequence[Pin] = PINS) -> list[str]:
    """Everything that breaks a pin, one line each; empty when the measured system is intact."""
    found: list[str] = []
    for pin in pins:
        if pin.tag is not None:
            points_to = _git(root, "rev-parse", f"{pin.tag}^{{commit}}")[0]
            if points_to != pin.commit:
                found.append(f"the tag {pin.tag} points to {points_to[:12]}, not {pin.commit[:12]}")
        found += [
            f"{name} differs from {pin.commit[:12]}"
            for name in changed_files(root, pin.commit, pin.paths)
        ]
    return found


def main(argv: Sequence[str] | None = None, pins: Sequence[Pin] = PINS) -> int:
    """Print the verdict; exit 1 when the measured system is not intact."""
    parser = argparse.ArgumentParser(prog="python -m filingcheck.measured")
    parser.add_argument("--root", type=Path, default=REPO_ROOT)
    args = parser.parse_args(argv)
    found = problems(args.root, pins)
    if not found:
        paths = sum(len(pin.paths) for pin in pins)
        commits = ", ".join(pin.commit[:12] for pin in pins)
        print(f"verify-measured: the {paths} pinned paths are unchanged since {commits}")
        return 0
    print(f"verify-measured: {len(found)} problem(s):")
    for line in found:
        print(f"  {line}")
    print("The measured system may not change; a version 2 gets its own tag and measurement.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
