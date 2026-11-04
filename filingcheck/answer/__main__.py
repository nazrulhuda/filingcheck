"""`python -m filingcheck.answer "question" [--mode agent] [--ticker T] [--year Y] [--live]`.

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
    settings_line,
)
from filingcheck.console import use_utf8_output
from filingcheck.db import connect
from filingcheck.llm import IncompleteAnswer, ModelRouter, router_from_env
from filingcheck.paths import REPO_ROOT


def main(argv: list[str] | None = None) -> int:
    """Answer one question with the baseline or the agent; print the answer and its cost."""
    use_utf8_output()
    argv = sys.argv[1:] if argv is None else argv
    if argv[:1] == ["batch"]:
        return batch_main(argv[1:])
    parser = argparse.ArgumentParser(prog="python -m filingcheck.answer")
    parser.add_argument("question")
    parser.add_argument("--mode", choices=["baseline", "agent"], default="baseline")
    parser.add_argument("--ticker")
    parser.add_argument("--year", type=int)
    parser.add_argument(
        "--live", action="store_true", help="live mode: short waits, fall back to other models"
    )
    parser.add_argument(
        "--max-tokens", type=int, default=MAX_TOKENS, help="token limit sent to the model"
    )
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
    settings = settings_line(router.primary.name, filters=filters, max_tokens=args.max_tokens)
    print(f"mode: {router.mode}, {args.mode}; {settings}\n")
    with connect() as conn:
        if args.mode == "agent":
            return _ask_agent(args, router, conn)
        try:
            answer = answer_question(
                args.question,
                retriever=hybrid_retriever(conn),
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
    """Run the agent, printing each tool call as it happens, then the answer."""
    from filingcheck.agent import run_agent
    from filingcheck.facts.lookup import PostgresFacts
    from filingcheck.tools import ToolDeps

    try:
        answer = run_agent(
            args.question,
            model=router,
            deps=ToolDeps(retriever=hybrid_retriever(conn), facts=PostgresFacts(conn)),
            ticker=args.ticker,
            fiscal_year=args.year,
            max_tokens=args.max_tokens,
            on_tool_call=lambda record: print(format_tool_call(record), flush=True),
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

    from filingcheck.answer.batch import run_batch
    from filingcheck.facts.lookup import PostgresFacts
    from filingcheck.tools import ToolDeps

    parser = argparse.ArgumentParser(prog="python -m filingcheck.answer batch")
    parser.add_argument("--mode", choices=["baseline", "agent"], required=True)
    parser.add_argument("--questions", type=Path, required=True, help="a .jsonl question file")
    parser.add_argument("--out", type=Path, required=True, help="the .jsonl results file")
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
    print(f"mode: batch, {args.mode}; {settings}")
    with connect() as conn:
        deps = ToolDeps(retriever=hybrid_retriever(conn), facts=PostgresFacts(conn))
        written = run_batch(
            questions, mode=args.mode, out=args.out, model=router, deps=deps, settings=settings
        )
    print(f"{written} questions answered; {len(questions) - written} already in {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
