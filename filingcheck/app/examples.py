"""The cached example answers the page shows.

`python -m filingcheck.app.examples [--questions FILE]` refreshes them: batch mode, so every
answer comes from the primary model. The questions come from a JSONL file ("id", "question",
"ticker" and "fiscal_year" on each line; the search is narrowed to that company and year)
that can be swapped with `make examples EXAMPLES=path`. The cached answers are replaced only
when every answer is complete and not degraded.

`python -m filingcheck.app.examples --export FILE` writes the stored answers, unchanged
apart from each citation's passage number, to the JSON file the page builds in
(`make examples-export`); no model is called.
"""

import argparse
import json
import logging
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from filingcheck.answer.baseline import K
from filingcheck.answer.citations import cited_numbers
from filingcheck.answer.examples import EXAMPLES_FILE, answer_examples, load_example_questions
from filingcheck.answer.run import hybrid_retriever
from filingcheck.app.store import ExampleAnswer, PostgresStore, Store
from filingcheck.console import use_utf8_output
from filingcheck.db import connect
from filingcheck.llm import ChatModel, router_from_env
from filingcheck.paths import REPO_ROOT
from filingcheck.retrieval import Retriever

__all__ = ["export_examples", "load_example_questions", "refresh_examples"]
EXPORT_FILE = REPO_ROOT / "web" / "data" / "examples.json"


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


def with_citation_numbers(example: ExampleAnswer) -> dict[str, Any]:
    """The example as JSON, each citation carrying its passage number.

    Answers stored before citations had a `number` get it from their own text with the
    API's parser: the citations were built in the order of the numbers cited, so the two
    lists line up. If they do not have the same length, the example is refused.
    """
    answer = dict(example.answer)
    citations = [dict(c) for c in answer.get("citations", [])]
    if any("number" not in c for c in citations):
        numbers = cited_numbers(answer.get("text", ""), K)
        if len(numbers) != len(citations):
            raise ValueError(
                f"{example.question!r}: the text cites {len(numbers)} passages but the answer "
                f"has {len(citations)} citations"
            )
        for citation, number in zip(citations, numbers, strict=True):
            citation.setdefault("number", number)
    answer["citations"] = citations
    return {
        "question": example.question,
        "ticker": example.ticker,
        "fiscal_year": example.fiscal_year,
        "answer": answer,
    }


def export_examples(store: Store, path: Path) -> int:
    """Write every stored example answer to `path`; nothing is written if one is refused."""
    examples = [with_citation_numbers(e) for e in store.examples()]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(examples, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n"
    )
    return len(examples)


def main(argv: list[str] | None = None) -> int:
    """Refresh the cached example answers from a question file, or export them."""
    use_utf8_output()
    parser = argparse.ArgumentParser(prog="python -m filingcheck.app.examples")
    parser.add_argument("--questions", type=Path, default=EXAMPLES_FILE)
    parser.add_argument("--export", type=Path, help="write the stored answers to this file")
    args = parser.parse_args(argv)
    if args.export is not None:
        load_dotenv(REPO_ROOT / ".env")
        count = export_examples(PostgresStore(), args.export)
        print(f"wrote {count} example answers to {args.export}")
        return 0
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
