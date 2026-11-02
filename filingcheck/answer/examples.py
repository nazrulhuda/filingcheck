"""`python -m filingcheck.answer.examples`: the 6 example questions through the baseline.

Batch mode, question text only (no ticker or year: the baseline has no company or year
resolver), so every answer comes from the primary model. Writes docs/baseline_examples.md.
"""

import json
import logging
import sys
from collections.abc import Callable
from datetime import date
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from filingcheck.answer.baseline import Answer, answer_question
from filingcheck.answer.run import (
    format_cost,
    format_incomplete,
    hybrid_retriever,
    settings_line,
)
from filingcheck.console import use_utf8_output
from filingcheck.db import connect
from filingcheck.llm import ChatModel, IncompleteAnswer, router_from_env
from filingcheck.paths import REPO_ROOT
from filingcheck.retrieval import Retriever

EXAMPLES_FILE = REPO_ROOT / "eval" / "questions" / "examples.jsonl"
OUTPUT = REPO_ROOT / "docs" / "baseline_examples.md"
HEADER = (
    "Week 2 baseline: plain RAG, no agent, no checks. "
    "These answers are not graded and may be wrong."
)


def render_examples(rows: list[tuple[str, str, Answer]], *, settings: str, run_date: date) -> str:
    """The examples file: the warning line, the date and settings, then each answer."""
    costs = [answer.cost_usd for _, _, answer in rows]
    total = None if any(c is None for c in costs) else sum(c for c in costs if c is not None)
    lines = [
        HEADER,
        "",
        f"Run on {run_date.isoformat()}. Settings: {settings}.",
        f"Total cost: {format_cost(total)} for {len(rows)} questions.",
    ]
    for question_id, question, answer in rows:
        lines += ["", f"## {question_id}: {question}", ""]
        lines += [f"> {line}" if line else ">" for line in answer.text.splitlines()]
        lines += ["", "Citations:", ""]
        lines += [
            f"- {c.ticker} FY{c.fiscal_year} Item {c.item}, chunk {c.chunk_id}: {c.source_url}"
            for c in answer.citations
        ] or ["- none"]
        lines += [
            "",
            f"Model used: {answer.model_used}. Tokens: prompt {answer.usage['prompt_tokens']}, "
            f"completion {answer.usage['completion_tokens']}. "
            f"Cost: {format_cost(answer.cost_usd)}. "
            f"finish_reason: {answer.finish_reason}. Abstained: {_yes(answer.abstained)}. "
            f"Uncited figures: {_yes(answer.has_uncited_claims)}. "
            f"Degraded: {_yes(answer.degraded)}.",
        ]
    return "\n".join(lines) + "\n"


def _yes(flag: bool) -> str:
    return "yes" if flag else "no"


def load_example_questions(path: Path) -> list[dict[str, Any]]:
    """The questions in a JSONL file; each line needs at least "id" and "question"."""
    return [
        json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()
    ]


def answer_examples(
    examples: list[dict[str, Any]],
    *,
    retriever: Retriever,
    model: ChatModel,
    out: Callable[[str], None] = print,
) -> list[tuple[str, str, Answer]] | None:
    """Every example's (id, question, answer), or None at the first degraded or cut-off one.

    A degraded answer came from keyword search alone (the question could not be embedded),
    and an incomplete one is not an answer, so neither may be saved as an example.
    """
    rows: list[tuple[str, str, Answer]] = []
    for example in examples:
        try:
            answer = answer_question(example["question"], retriever=retriever, model=model)
        except IncompleteAnswer as exc:
            out(f"{example['id']}: stopped, nothing saved")
            out(format_incomplete(exc))
            return None
        if answer.degraded:
            out(
                f"{example['id']}: degraded (keyword search answered alone because the question "
                "could not be embedded); stopped, nothing saved"
            )
            return None
        out(f"{example['id']}: {answer.model_used}, cost {format_cost(answer.cost_usd)}")
        rows.append((example["id"], example["question"], answer))
    return rows


def run_examples(
    examples: list[dict[str, Any]],
    *,
    retriever: Retriever,
    model: ChatModel,
    settings: str,
    output: Path,
    run_date: date,
    out: Callable[[str], None] = print,
) -> int:
    """Answer every example and write the file; stop without writing on a degraded answer."""
    rows = answer_examples(examples, retriever=retriever, model=model, out=out)
    if rows is None:
        return 1
    output.write_text(
        render_examples(rows, settings=settings, run_date=run_date),
        encoding="utf-8",
        newline="\n",
    )
    out(f"wrote {output}")
    return 0


def main() -> int:
    """Answer the 6 example questions in batch mode and write the examples file."""
    use_utf8_output()
    load_dotenv(REPO_ROOT / ".env")
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")
    router = router_from_env("batch")
    with connect() as conn:
        return run_examples(
            load_example_questions(EXAMPLES_FILE),
            retriever=hybrid_retriever(conn),
            model=router,
            settings=settings_line(router.primary.name, filters="no filters (question text only)"),
            output=OUTPUT,
            run_date=date.today(),
        )


if __name__ == "__main__":
    sys.exit(main())
