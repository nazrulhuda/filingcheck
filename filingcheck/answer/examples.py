"""`python -m filingcheck.answer.examples`: the 6 example questions through the baseline.

Batch mode, question text only (no ticker or year: the baseline has no company or year
resolver), so every answer comes from the primary model. Writes docs/baseline_examples.md.
"""

import json
import logging
import sys
from datetime import date

from dotenv import load_dotenv

from filingcheck.answer.baseline import Answer, answer_question
from filingcheck.answer.run import format_cost, hybrid_retriever, settings_line
from filingcheck.db import connect
from filingcheck.llm import router_from_env
from filingcheck.paths import REPO_ROOT

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


def main() -> int:
    """Answer the 6 example questions in batch mode and write the examples file."""
    load_dotenv(REPO_ROOT / ".env")
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")
    router = router_from_env("batch")
    examples = [
        json.loads(line)
        for line in EXAMPLES_FILE.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    rows: list[tuple[str, str, Answer]] = []
    with connect() as conn:
        retriever = hybrid_retriever(conn)
        for example in examples:
            answer = answer_question(example["question"], retriever=retriever, model=router)
            print(f"{example['id']}: {answer.model_used}, cost {format_cost(answer.cost_usd)}")
            rows.append((example["id"], example["question"], answer))
    settings = settings_line(router.primary.name, filters="no filters (question text only)")
    OUTPUT.write_text(
        render_examples(rows, settings=settings, run_date=date.today()),
        encoding="utf-8",
        newline="\n",
    )
    print(f"wrote {OUTPUT.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
