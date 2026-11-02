"""`python -m filingcheck.app.examples [--questions FILE]`: refresh the cached example answers.

Batch mode, so every answer comes from the primary model. The questions come from a JSONL
file ("id", "question", "ticker" and "fiscal_year" on each line; the search is narrowed to
that company and year) that can be swapped with `make examples EXAMPLES=path`. The cached
answers are replaced only when every answer is complete and not degraded.
"""

import argparse
import logging
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from filingcheck.answer.examples import EXAMPLES_FILE, answer_examples, load_example_questions
from filingcheck.answer.run import hybrid_retriever
from filingcheck.app.store import ExampleAnswer, PostgresStore, Store
from filingcheck.console import use_utf8_output
from filingcheck.db import connect
from filingcheck.llm import ChatModel, router_from_env
from filingcheck.paths import REPO_ROOT
from filingcheck.retrieval import Retriever

__all__ = ["load_example_questions", "refresh_examples"]


def refresh_examples(
    examples: list[dict[str, Any]],
    *,
    retriever: Retriever,
    model: ChatModel,
    store: Store,
    out: Callable[[str], None] = print,
) -> int:
    """Answer every example and replace the cached answers; keep the old ones on a failure."""
    rows = answer_examples(examples, retriever=retriever, model=model, use_filters=True, out=out)
    if rows is None:
        return 1
    by_id = {example["id"]: example for example in examples}
    store.replace_examples(
        [
            ExampleAnswer(
                question=question,
                ticker=by_id[example_id].get("ticker"),
                fiscal_year=by_id[example_id].get("fiscal_year"),
                answer=answer.model_dump(),
            )
            for example_id, question, answer in rows
        ]
    )
    out(f"saved {len(rows)} example answers")
    return 0


def main(argv: list[str] | None = None) -> int:
    """Refresh the cached example answers from a question file."""
    use_utf8_output()
    parser = argparse.ArgumentParser(prog="python -m filingcheck.app.examples")
    parser.add_argument("--questions", type=Path, default=EXAMPLES_FILE)
    args = parser.parse_args(argv)
    load_dotenv(REPO_ROOT / ".env")
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")
    router = router_from_env("batch")
    with connect() as conn:
        return refresh_examples(
            load_example_questions(args.questions),
            retriever=hybrid_retriever(conn),
            model=router,
            store=PostgresStore(),
        )


if __name__ == "__main__":
    sys.exit(main())
