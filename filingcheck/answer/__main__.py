"""The answer command line: one question, or a question file in batch mode.

`python -m filingcheck.answer "question" [--mode agent] [--checks on|off] [--ticker T]
[--year Y] [--live]` answers one question.

`python -m filingcheck.answer batch --mode agent --questions FILE --out FILE` runs a question
file in batch mode (see filingcheck/answer/batch.py and eval/README.md).
"""

import argparse
import logging
import sys
from pathlib import Path

import psycopg
from dotenv import load_dotenv

from filingcheck.answer.baseline import MAX_TOKENS, answer_question
from filingcheck.answer.run import (
    format_agent_answer,
    format_answer,
    format_incomplete,
    format_tool_call,
    hybrid_retriever,
    retriever_for,
    settings_line,
)
from filingcheck.checks import reference_data
from filingcheck.console import use_utf8_output
from filingcheck.db import connect
from filingcheck.llm import IncompleteAnswer, ModelRouter, router_from_env
from filingcheck.paths import REPO_ROOT

CHECK_CHOICES = ("on", "off", "1", "0")


def checks_on(value: str) -> bool:
    """The --checks flag as a switch: on or 1 is on."""
    return value in ("on", "1")


def answer_parser() -> argparse.ArgumentParser:
    """The options of one question (`make ask`)."""
    parser = argparse.ArgumentParser(prog="python -m filingcheck.answer")
    parser.add_argument("question")
    parser.add_argument("--mode", choices=["baseline", "agent"], default="baseline")
    parser.add_argument(
        "--retriever",
        choices=["hybrid", "vector"],
        default="hybrid",
        help="the baseline's search (the agent always searches hybrid)",
    )
    parser.add_argument("--ticker")
    parser.add_argument("--year", type=int)
    parser.add_argument(
        "--live", action="store_true", help="live mode: short waits, fall back to other models"
    )
    parser.add_argument(
        "--max-tokens", type=int, default=MAX_TOKENS, help="token limit sent to the model"
    )
    parser.add_argument(
        "--checks",
        choices=CHECK_CHOICES,
        default="on",
        help="agent mode: run the skeptical checks before get_financial_fact (default on)",
    )
    return parser


def batch_parser() -> argparse.ArgumentParser:
    """The options of a batch run."""
    parser = argparse.ArgumentParser(prog="python -m filingcheck.answer batch")
    parser.add_argument("--mode", choices=["baseline", "agent"], required=True)
    parser.add_argument("--questions", type=Path, required=True, help="a .jsonl question file")
    parser.add_argument("--out", type=Path, required=True, help="the .jsonl results file")
    parser.add_argument("--repeats", type=int, default=1, help="runs per question (default 1)")
    parser.add_argument(
        "--checks",
        choices=CHECK_CHOICES,
        default="on",
        help="agent mode: run the skeptical checks (default on); recorded in every row",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Answer one question with the baseline or the agent; print the answer and its cost."""
    use_utf8_output()
    argv = sys.argv[1:] if argv is None else argv
    if argv[:1] == ["batch"]:
        return batch_main(argv[1:])
    parser = answer_parser()
    args = parser.parse_args(argv)
    if not args.question.strip():
        parser.error('give a question: make ask Q="..."')
    # load_dotenv keeps variables already set, so GROQ_API_KEY=invalid on the command line wins.
    load_dotenv(REPO_ROOT / ".env")
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")
    router = router_from_env("live" if args.live else "batch")
    filters = (
        f"ticker {args.ticker or '-'}, year {args.year or '-'}"
        if args.ticker or args.year
        else "no filters"
    )
    if args.mode == "agent" and args.retriever != "hybrid":
        parser.error("the agent always searches hybrid; --retriever is the baseline's")
    settings = settings_line(
        router.primary.name, filters=filters, max_tokens=args.max_tokens, retriever=args.retriever
    )
    checks_line = f"; checks: {args.checks}" if args.mode == "agent" else ""
    print(f"mode: {router.mode}, {args.mode}{checks_line}; {settings}\n")
    with connect() as conn:
        if args.mode == "agent":
            return _ask_agent(args, router, conn)
        try:
            answer = answer_question(
                args.question,
                retriever=retriever_for(conn, args.retriever),
                model=router,
                ticker=args.ticker,
                fiscal_year=args.year,
                max_tokens=args.max_tokens,
            )
        except IncompleteAnswer as exc:
            print(format_incomplete(exc))
            return 1
    print(format_answer(answer, router.last_completion))
    return 0


def _ask_agent(args: argparse.Namespace, router: ModelRouter, conn: psycopg.Connection) -> int:
    """Run the agent, printing each tool call as it happens, then the answer.

    With --live, a provider failure restarts the question with the next model, as the API
    does; a run is never handed half-finished to another model.
    """
    from filingcheck.agent import run_agent_with_fallbacks
    from filingcheck.facts.lookup import PostgresFacts
    from filingcheck.tools import ToolDeps

    try:
        answer = run_agent_with_fallbacks(
            args.question,
            models=router.in_turn(),
            deps=ToolDeps(
                retriever=hybrid_retriever(conn), facts=PostgresFacts(conn), **reference_data()
            ),
            ticker=args.ticker,
            fiscal_year=args.year,
            max_tokens=args.max_tokens,
            on_tool_call=lambda record: print(format_tool_call(record), flush=True),
            checks=checks_on(args.checks),
        )
    except IncompleteAnswer as exc:
        print(format_incomplete(exc))
        return 1
    print()
    print(format_agent_answer(answer))
    return 0


def batch_main(argv: list[str]) -> int:
    """Run a question file through one mode in batch mode, resumably."""
    import json

    from filingcheck.answer.batch import BatchFileError, run_batch
    from filingcheck.facts.lookup import PostgresFacts
    from filingcheck.tools import ToolDeps

    parser = batch_parser()
    args = parser.parse_args(argv)
    load_dotenv(REPO_ROOT / ".env")
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")
    router = router_from_env("batch")
    questions = [
        (row["id"], row["question"])
        for row in (
            json.loads(line)
            for line in args.questions.read_text(encoding="utf-8").splitlines()
            if line.strip()
        )
    ]
    settings = settings_line(router.primary.name, filters="question text only, no filters")
    checks_line = f"; checks: {args.checks}" if args.mode == "agent" else ""
    print(f"mode: batch, {args.mode}{checks_line}; {settings}")
    with connect() as conn:
        deps = ToolDeps(
            retriever=hybrid_retriever(conn), facts=PostgresFacts(conn), **reference_data()
        )
        try:
            written = run_batch(
                questions,
                mode=args.mode,
                out=args.out,
                model=router,
                deps=deps,
                settings=settings,
                repeats=args.repeats,
                checks=checks_on(args.checks),
            )
        except BatchFileError as exc:
            print(f"ERROR: {exc}")
            return 1
    total = len(questions) * args.repeats
    print(f"{written} answers written; {total - written} already in {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
