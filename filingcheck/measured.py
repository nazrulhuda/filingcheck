"""The measured system is pinned to the tag `week6-measured`: `make verify-measured`.

The README's results describe that tagged commit. Everything that could change an answer or a
reported number is listed in `PINNED`, in this one place; the check fails, naming the files,
if any file under those paths differs from the tag, whether a tracked change or a new file.
What moves the pin: a version 2 of the system, measured again on new sealed questions under a
new pre-registration, with its own tag. CI runs the check on every push (its checkout needs
the tags).
"""

import argparse
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path

TAG = "week6-measured"
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
REPO_ROOT = Path(__file__).resolve().parents[1]


def _git(root: Path, *args: str) -> list[str]:
    done = subprocess.run(
        ["git", *args], cwd=root, capture_output=True, text=True, check=True, encoding="utf-8"
    )
    return [line for line in done.stdout.splitlines() if line.strip()]


def changed_files(
    root: Path = REPO_ROOT, tag: str = TAG, *, pinned: Sequence[str] = PINNED
) -> list[str]:
    """The files under the pinned paths that differ from the tag: changed, deleted or new."""
    tracked = _git(root, "diff", "--name-only", "--no-renames", tag, "--", *pinned)
    new = _git(root, "ls-files", "--others", "--exclude-standard", "--", *pinned)
    return sorted(set(tracked) | set(new))


def main(argv: Sequence[str] | None = None) -> int:
    """Print the verdict; exit 1 when a pinned file differs from the tag."""
    parser = argparse.ArgumentParser(prog="python -m filingcheck.measured")
    parser.add_argument("--root", type=Path, default=REPO_ROOT)
    parser.add_argument("--tag", default=TAG)
    parser.add_argument("--pinned", nargs="+", default=list(PINNED), help="paths to pin")
    args = parser.parse_args(argv)
    changed = changed_files(args.root, args.tag, pinned=args.pinned)
    if not changed:
        print(
            f"verify-measured: the {len(args.pinned)} pinned paths are unchanged since {args.tag}"
        )
        return 0
    print(f"verify-measured: {len(changed)} file(s) under the pinned paths differ from {args.tag}:")
    for name in changed:
        print(f"  {name}")
    print("The measured system may not change; a version 2 gets its own tag and measurement.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
