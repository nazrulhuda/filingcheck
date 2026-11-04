"""The batch runner: a question file through the baseline or the agent, one JSON line each.

Resumable: questions already in the output file are skipped, and a last line cut off by a
crash is dropped before the run goes on. A cut-off or empty answer is written with its error
code; any other provider failure stops the run (batch mode never falls back), so it can be
resumed later. This is the runner the evaluation uses; eval/README.md documents the format.
"""

import json
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from filingcheck.agent import run_agent
from filingcheck.answer.baseline import Answer, answer_question
from filingcheck.llm import ChatModel, IncompleteAnswer
from filingcheck.retrieval import Retriever
from filingcheck.tools import ToolDeps

BATCH_FIELDS = (
    "id",
    "mode",
    "question",
    "model",
    "settings",
    "answer",
    "citations",
    "fact_citations",
    "tool_calls",
    "facts_used",
    "usage",
    "cost_usd",
    "latency_ms",
    "finish_reason",
    "abstained",
    "has_uncited_claims",
    "model_calls",
    "stopped_by",
    "error",
)


def read_done(out: Path) -> set[str]:
    """The ids already answered in `out`; a last line cut off by a crash is removed."""
    if not out.exists():
        return set()
    lines = out.read_text(encoding="utf-8").splitlines(keepends=True)
    kept: list[str] = []
    for line in lines:
        try:
            json.loads(line)
        except json.JSONDecodeError:
            break  # only the last line can be cut off; nothing after it is trusted
        if not line.endswith("\n"):
            break
        kept.append(line)
    if len(kept) != len(lines):
        out.write_text("".join(kept), encoding="utf-8", newline="")
    return {json.loads(line)["id"] for line in kept}


def _row(qid: str, mode: str, question: str, settings: str) -> dict[str, Any]:
    return dict.fromkeys(BATCH_FIELDS) | {
        "id": qid,
        "mode": mode,
        "question": question,
        "settings": settings,
        "citations": [],
        "fact_citations": [],
        "tool_calls": [],
        "facts_used": [],
    }


def run_batch(
    questions: Iterable[tuple[str, str]],
    *,
    mode: str,
    out: Path,
    model: ChatModel,
    deps: ToolDeps,
    settings: str,
    retriever: Retriever | None = None,
) -> int:
    """Answer every question not yet in `out` and append its line; return how many were written.

    Questions are asked as text only, with no company or year filter. The baseline searches
    with `retriever` (the tools' retriever when none is given).
    """
    done = read_done(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    written = 0
    for qid, question in questions:
        if qid in done:
            continue
        row = _row(qid, mode, question, settings)
        answer: Answer
        try:
            if mode == "agent":
                answer = run_agent(question, model=model, deps=deps)
            else:
                answer = answer_question(
                    question, retriever=retriever or deps.retriever, model=model
                )
        except IncompleteAnswer as exc:
            completion = exc.completion
            row |= {
                "model": completion.model,
                "error": exc.log_code,
                "finish_reason": completion.finish_reason,
                "usage": {
                    "prompt_tokens": completion.prompt_tokens,
                    "completion_tokens": completion.completion_tokens,
                },
                "cost_usd": completion.cost_usd,
            }
        else:
            data = json.loads(answer.model_dump_json())
            row |= {
                "model": data["model_used"],
                "answer": data["text"],
                "citations": data["citations"],
                "usage": data["usage"],
                "cost_usd": data["cost_usd"],
                "latency_ms": data["latency_ms"],
                "finish_reason": data["finish_reason"],
                "abstained": data["abstained"],
                "has_uncited_claims": data["has_uncited_claims"],
                "model_calls": data.get("model_calls", 1),
            }
            if mode == "agent":
                row |= {
                    "fact_citations": data["fact_citations"],
                    "tool_calls": data["tool_calls"],
                    "facts_used": data["facts_used"],
                    "stopped_by": data["stopped_by"],
                }
        with out.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(row) + "\n")
        written += 1
    return written
