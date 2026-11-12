"""Check the Week 5 question sets against every older question.

Run: `uv run python eval/check_overlap.py`.

The older questions: the six examples, the page examples, the retrieval set, every question in
`eval/probes/` and `eval/results/`, the gate scenarios, the Day 18 scripted scenarios, and the
Day 23 phrasing matrices and review probes (generated from their test templates). A new question
whose word overlap with any of them is above 0.6 is printed with its closest match.
"""

import importlib
import json
import sys
from pathlib import Path
from typing import Any

import yaml

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from filingcheck.eval.overlap import flagged  # noqa: E402

NEW_SETS = ("dev_traps.jsonl", "dev_unanswerable.jsonl", "control.jsonl")
THRESHOLD = 0.6


def references() -> dict[str, str]:
    """Every older question, mapped to where it comes from."""
    refs: dict[str, str] = {}

    def add(text: Any, source: str) -> None:
        if isinstance(text, str) and len(text.split()) >= 2:
            refs.setdefault(text.strip(), source)

    for name in ("examples.jsonl", "page_examples.jsonl", "retrieval.jsonl"):
        for line in (REPO / "eval/questions" / name).read_text(encoding="utf-8").splitlines():
            if line.strip():
                add(json.loads(line)["question"], name)
    for folder in ("eval/probes", "eval/results"):
        for path in sorted((REPO / folder).glob("*.jsonl")):
            for line in path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    add(json.loads(line).get("question"), path.name)
    gate = yaml.safe_load((REPO / "tests/eval_gate/scenarios.yaml").read_text(encoding="utf-8"))
    for scenario in gate if isinstance(gate, list) else gate.get("scenarios", []):
        add(scenario.get("question"), "gate scenarios")
    day18 = importlib.import_module("tests.agent.test_agent_checks")
    for case in day18.day18_scenarios():
        add(case.values[0], "Day 18 scenarios")
    years = importlib.import_module("tests.checks.test_year_matrix")
    for build in (years.strong_cases, years.relative_cases, years.weak_cases):
        for case in build():
            add(case.values[0], "Day 23 year matrix")
    segments = importlib.import_module("tests.checks.test_segment_matrix")
    for case in [
        *segments.cases(segments.TIED),
        *segments.cases(segments.NOT_TIED),
        *segments.lower_cases(segments.LOWER_TIED),
        *segments.lower_cases(segments.LOWER_LOOSE),
        *segments.exclude_cases(),
    ]:
        add(case.values[0], "Day 23 segment matrix")
    real = importlib.import_module("tests.checks.test_real_questions")
    for case in real.real_questions():
        add(case.values[0], "Day 23 real questions")
    probes = (REPO / "tests/checks/test_real_questions.py").read_text(encoding="utf-8")
    for line in probes.splitlines():
        if 'chain("' in line:
            add(line.split('chain("', 1)[1].split('"', 1)[0], "Day 23 review probes")
    return refs


def main() -> int:
    """Print the flagged questions and a one-line count; exit 1 if any is flagged."""
    refs = references()
    new: dict[str, str] = {}
    for name in NEW_SETS:
        for line in (REPO / "eval/questions" / name).read_text(encoding="utf-8").splitlines():
            if line.strip():
                row = json.loads(line)
                new[row["id"]] = row["question"]
    flags = flagged(new, refs, THRESHOLD)
    for flag in flags:
        print(f"{flag.id} ({flag.score}): {flag.question!r} ~ {flag.reference!r} [{flag.source}]")
    print(
        f"{len(new)} new questions against {len(refs)} older ones: {len(flags)} above {THRESHOLD}"
    )
    return 1 if flags else 0


if __name__ == "__main__":
    sys.exit(main())
