"""`python -m filingcheck.eval gold` and `python -m filingcheck.eval run` (`make eval`).

gold: fill the gold values of a question file from the facts table (filingcheck/eval/gold.py).
run:  a question set through one mode in batch mode, graded (filingcheck/eval/run.py).
"""

import argparse
import json
import logging
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from filingcheck.console import use_utf8_output
from filingcheck.paths import REPO_ROOT

QUESTIONS_DIR = REPO_ROOT / "eval" / "questions"


def gold_main(args: argparse.Namespace) -> int:
    """Fill the gold values from the facts table, through the agent's own lookup."""
    from filingcheck.db import connect
    from filingcheck.eval.gold import fill_gold_file
    from filingcheck.facts.lookup import PostgresFacts

    with connect() as conn:
        report = fill_gold_file(args.questions, PostgresFacts(conn))
    for qid, action, detail in report:
        print(f"{qid}: {action}" + (f" ({detail})" if detail else ""))
    return 0


def run_main(args: argparse.Namespace) -> int:
    """Ask, grade and summarize one question set in one mode (batch mode, no fallback)."""
    from filingcheck.answer.batch import BatchFileError
    from filingcheck.answer.run import hybrid_retriever, settings_line
    from filingcheck.checks import reference_data
    from filingcheck.db import connect
    from filingcheck.eval.arms import arm_name
    from filingcheck.eval.run import choose_results_path, read_questions, results_path, run_eval
    from filingcheck.facts.lookup import PostgresFacts
    from filingcheck.llm import router_from_env
    from filingcheck.tools import ToolDeps

    questions = QUESTIONS_DIR / f"{args.set}.jsonl"
    if not questions.exists():
        print(f"ERROR: no question file {questions.relative_to(REPO_ROOT)}")
        return 1
    name = arm_name(args.mode, args.checks)
    if args.date:
        out = REPO_ROOT / results_path(args.set, name, args.date)
    else:
        today = datetime.now(UTC).date().isoformat()
        ids = {q.id for q in read_questions(questions)}
        out = choose_results_path(
            REPO_ROOT,
            args.set,
            name,
            expected_rows=len(ids) * args.repeats,
            today=today,
            question_ids=ids,
        )
        if not out.name.startswith(today):
            print(f"resuming the unfinished {out.relative_to(REPO_ROOT)}")
    out.parent.mkdir(parents=True, exist_ok=True)
    router = router_from_env("batch")
    settings = settings_line(router.primary.name, filters="question text only, no filters")
    print(f"mode: batch, {name}; {args.repeats} run(s) per question; {settings}")
    with connect() as conn:
        extra = reference_data() if args.checks else {}
        deps = ToolDeps(retriever=hybrid_retriever(conn), facts=PostgresFacts(conn), **extra)
        try:
            summary = run_eval(
                questions,
                mode=args.mode,
                repeats=args.repeats,
                model=router,
                deps=deps,
                out=out,
                settings=settings,
                checks=args.checks,
            )
        except BatchFileError as exc:
            print(f"ERROR: {exc}")
            return 1
    print(summary.read_text(encoding="utf-8"))
    print(f"wrote {out.relative_to(REPO_ROOT)} and {summary.relative_to(REPO_ROOT)}")
    if args.checks is not None:
        _write_arms(args.set, out, args.checks, questions, args.repeats)
    return 0


def _write_arms(set_name: str, out: Path, checks: bool, questions: Path, repeats: int) -> None:
    """After an agent run: the comparison with the newest finished file of the other arm."""
    from filingcheck.eval.arms import arm_name, arms_path, compare_arms, finished_arm
    from filingcheck.eval.grade import Grade
    from filingcheck.eval.run import read_questions

    ids = {q.id for q in read_questions(questions)}
    other = finished_arm(
        REPO_ROOT,
        set_name,
        arm_name("agent", not checks),
        expected_rows=len(ids) * repeats,
        question_ids=ids,
    )
    if other is None:
        print(f"no finished {arm_name('agent', not checks)} file for {set_name} yet: no comparison")
        return

    def graded(path: Path) -> list[tuple[dict[str, Any], Grade]]:
        rows = [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]
        return [(r, Grade.model_validate(r["grade"])) for r in rows if r.get("grade")]

    off, on = (other, out) if checks else (out, other)
    text = compare_arms(
        graded(off), graded(on), set_name=set_name, off_file=off.name, on_file=on.name
    )
    page = REPO_ROOT / arms_path(set_name, out.name[:10])
    page.write_text(text, encoding="utf-8", newline="\n")
    print(text)
    print(f"wrote {page.relative_to(REPO_ROOT)}")


def main(argv: list[str] | None = None) -> int:
    """Parse the command and run it."""
    use_utf8_output()
    parser = argparse.ArgumentParser(prog="python -m filingcheck.eval")
    commands = parser.add_subparsers(dest="command", required=True)
    gold = commands.add_parser("gold", help="fill gold values from the facts table")
    gold.add_argument("--questions", type=Path, default=QUESTIONS_DIR / "examples.jsonl")
    run = commands.add_parser("run", help="ask and grade a question set in one mode")
    run.add_argument("--set", required=True, help="a question file in eval/questions/, no .jsonl")
    run.add_argument("--mode", choices=["baseline", "agent"], required=True)
    run.add_argument("--repeats", type=int, default=1, help="runs per question (default 1)")
    run.add_argument(
        "--date", help="the results file date (default: an unfinished file's, else today UTC)"
    )
    run.add_argument("--checks", help="agent only: on (default) or off; the file name says which")
    args = parser.parse_args(argv)
    load_dotenv(REPO_ROOT / ".env")
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")
    if args.command == "gold":
        return gold_main(args)
    if args.repeats < 1:
        parser.error("--repeats must be 1 or more")
    from filingcheck.eval.arms import checks_argument

    try:
        args.checks = checks_argument(args.mode, args.checks)
    except ValueError as exc:
        parser.error(str(exc))
    return run_main(args)


if __name__ == "__main__":
    sys.exit(main())
