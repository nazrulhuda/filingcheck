"""The batch runner: a question file through the baseline or the agent, one JSON line each.

Resumable: questions already in the output file are skipped, and a last line cut off by a
crash is dropped before the run goes on; any other line that is not a complete result stops
the run with its line number. A cut-off or empty answer is written with its error code and
what the run spent; any other provider failure stops the run (batch mode never falls back),
so it can be resumed later. This is the runner the evaluation uses; eval/README.md documents
the format.
"""

import json
import time
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from filingcheck.agent import RunLog, run_agent, total_usage
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


class BatchFileError(ValueError):
    """A results file has a line that is neither a complete result nor a cut-off last line."""


def read_done(out: Path) -> set[str]:
    """The ids already answered in `out`.

    A last line with no line end was cut off by a crash: it is removed and that question is
    asked again. Any other line that is not a JSON object with an `id` stops the run with its
    line number, and the file is left as it is for a person to look at.
    """
    if not out.exists():
        return set()
    lines = out.read_text(encoding="utf-8").splitlines(keepends=True)
    done: set[str] = set()
    for number, line in enumerate(lines, start=1):
        if number == len(lines) and not line.endswith("\n"):
            out.write_text("".join(lines[:-1]), encoding="utf-8", newline="")
            break
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            row = None
        if not isinstance(row, dict) or not isinstance(row.get("id"), str):
            raise BatchFileError(
                f"{out}, line {number}: not a complete result line; fix or remove it, then "
                "run the same command again"
            )
        done.add(row["id"])
    return done


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
        run_log = RunLog()
        started = time.perf_counter()
        try:
            if mode == "agent":
                answer = run_agent(question, model=model, deps=deps, run_log=run_log)
            else:
                answer = answer_question(
                    question, retriever=retriever or deps.retriever, model=model
                )
        except IncompleteAnswer as exc:
            completion = exc.completion
            # Everything the run spent: for the agent every model call before the cut-off one.
            completions = run_log.completions if mode == "agent" else [completion]
            usage, cost = total_usage(completions)
            row |= {
                "model": completion.model,
                "error": exc.log_code,
                "finish_reason": completion.finish_reason,
                "usage": usage,
                "cost_usd": cost,
                "latency_ms": (time.perf_counter() - started) * 1000,
                "model_calls": len(completions),
            }
            if mode == "agent":
                row |= {
                    "tool_calls": [json.loads(r.model_dump_json()) for r in run_log.tool_calls],
                    "facts_used": [json.loads(f.model_dump_json()) for f in run_log.facts],
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
