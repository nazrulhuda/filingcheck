"""`python -m filingcheck.answer "question" [--ticker WMT] [--year 2025] [--live]`."""

import argparse
import logging
import sys

from dotenv import load_dotenv

from filingcheck.answer.baseline import answer_question
from filingcheck.answer.run import format_answer, format_cost, hybrid_retriever, settings_line
from filingcheck.db import connect
from filingcheck.llm import IncompleteAnswer, router_from_env
from filingcheck.paths import REPO_ROOT


def main(argv: list[str] | None = None) -> int:
    """Answer one question with the baseline and print the answer, citations and cost."""
    parser = argparse.ArgumentParser(prog="python -m filingcheck.answer")
    parser.add_argument("question")
    parser.add_argument("--ticker")
    parser.add_argument("--year", type=int)
    parser.add_argument(
        "--live", action="store_true", help="live mode: short waits, fall back to other models"
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
    print(f"mode: {router.mode}; {settings_line(router.primary.name, filters=filters)}\n")
    with connect() as conn:
        try:
            answer = answer_question(
                args.question,
                retriever=hybrid_retriever(conn),
                model=router,
                ticker=args.ticker,
                fiscal_year=args.year,
            )
        except IncompleteAnswer as exc:
            c = exc.completion
            print(f"error: {exc}")
            print(f"text so far: {c.text!r}")
            print(f"tokens: prompt {c.prompt_tokens}, completion {c.completion_tokens}")
            print(f"cost: {format_cost(c.cost_usd)}; usage as sent: {c.usage}")
            return 1
    print(format_answer(answer, router.last_completion))
    return 0


if __name__ == "__main__":
    sys.exit(main())
