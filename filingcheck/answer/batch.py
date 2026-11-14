"""The batch runner: a question file through the baseline or the agent, one JSON line each.

Resumable: questions already in the output file are skipped, and a last line cut off by a
crash is dropped before the run goes on; any other line that is not a complete result stops
the run with its line number. A cut-off or empty answer is written with its error code and
what the run spent. A provider failure on one row (after the client's own retries; batch mode
never falls back) is written as an error row too, and the run goes on; a resume does not ask
that row again (delete its line to retry it). Three failures in a row look like an outage: the
run stops before writing the third, so it can be resumed later. This is the runner the
evaluation uses; eval/README.md documents the format.
"""

import json
import time
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from filingcheck.agent import RunLog, run_agent, total_usage
from filingcheck.answer.baseline import Answer, answer_question
from filingcheck.llm import ChatModel, IncompleteAnswer, ProviderError
from filingcheck.llm.chat import error_kind
from filingcheck.retrieval import Retriever
from filingcheck.tools import ToolDeps

# Provider failures on this many rows in a row stop the run: an outage, not one bad row.
MAX_CONSECUTIVE_FAILURES = 3
BATCH_FIELDS = (
    "id",
    "repeat",
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
    "checks",
    "rules",
    "overrides",
    "number_labels",
    "page_filter",
    "error",
    "error_kind",
    "git_commit",
    "git_clean",
    "questions_sha256",
)


class BatchFileError(ValueError):
    """A results file has a line that is neither a complete result nor a cut-off last line."""


def read_done(out: Path) -> set[tuple[str, int]]:
    """The (id, repeat) pairs already answered in `out`; a row with no repeat is repeat 1.

    A last line with no line end was cut off by a crash: it is removed and that question is
    asked again. Any other line that is not a JSON object with an `id` stops the run with its
    line number, and the file is left as it is for a person to look at.
    """
    if not out.exists():
        return set()
    lines = out.read_text(encoding="utf-8").splitlines(keepends=True)
    done: set[tuple[str, int]] = set()
    for number, line in enumerate(lines, start=1):
        if number == len(lines) and not line.endswith("\n"):
            out.write_text("".join(lines[:-1]), encoding="utf-8", newline="")
            break
        if not line.strip():
            continue  # a blank line is not a result and not a fault
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            row = None
        if (
            not isinstance(row, dict)
            or not isinstance(row.get("id"), str)
            or not isinstance(row.get("repeat", 1), int)
        ):
            raise BatchFileError(
                f"{out}, line {number}: not a complete result line; fix or remove it, then "
                "run the same command again"
            )
        done.add((row["id"], row.get("repeat", 1)))
    return done


def _row(qid: str, repeat: int, mode: str, question: str, settings: str) -> dict[str, Any]:
    return dict.fromkeys(BATCH_FIELDS) | {
        "id": qid,
        "repeat": repeat,
        "mode": mode,
        "question": question,
        "settings": settings,
        "citations": [],
        "fact_citations": [],
        "tool_calls": [],
        "facts_used": [],
        "overrides": [],
        "number_labels": [],
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
    repeats: int = 1,
    checks: bool = False,
    filters: dict[str, tuple[str | None, int | None]] | None = None,
    provenance: dict[str, Any] | None = None,
    rules: str | None = None,
) -> int:
    """Answer every question not yet in `out` and append its line; return how many were written.

    Questions are asked as text only, unless `filters` gives them page filters. The baseline
    searches with `retriever` (the tools' retriever when none is given). With `repeats`, each
    question is asked that many times, one whole pass over the file after another, and
    each row records its `repeat` (1, 2, ...). `checks` switches the agent's skeptical
    checks on; every agent row records it, and its override log, as `checks` and `overrides`.
    `filters` gives a question's page filters (company, fiscal year) by id; it is asked with
    them as the page asks, and its row records them as `page_filter`. `provenance` (the commit,
    whether the tree was clean, the question file's SHA-256) goes into every row.
    `rules` is the prompt-rules arm's block (Week 6): the agent, with the checks off,
    gets it after the frozen system prompt, and its rows record `rules` as "prompt".
    """
    if rules is not None and mode != "agent":
        raise ValueError("the rules block is for the agent only")
    if rules is not None and checks:
        raise ValueError("the prompt-rules arm runs with the checks off")
    questions = list(questions)
    done = read_done(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    written = 0
    failures = 0  # provider failures in a row
    for repeat in range(1, repeats + 1):
        for qid, question in questions:
            if (qid, repeat) in done:
                continue
            row = _row(qid, repeat, mode, question, settings) | dict(provenance or {})
            ticker, fiscal_year = (filters or {}).get(qid, (None, None))
            if ticker is None:
                fiscal_year = None  # as on the page: a year counts only with a company
            if qid in (filters or {}):
                row["page_filter"] = {"ticker": ticker, "fiscal_year": fiscal_year}
            if mode == "agent":
                row["checks"] = checks
                row["rules"] = "prompt" if rules is not None else None
            answer: Answer
            run_log = RunLog()
            started = time.perf_counter()
            try:
                if mode == "agent":
                    answer = run_agent(
                        question,
                        model=model,
                        deps=deps,
                        run_log=run_log,
                        checks=checks,
                        ticker=ticker,
                        fiscal_year=fiscal_year,
                        rules=rules,
                    )
                else:
                    answer = answer_question(
                        question,
                        retriever=retriever or deps.retriever,
                        model=model,
                        ticker=ticker,
                        fiscal_year=fiscal_year,
                    )
            except IncompleteAnswer as exc:
                failures = 0
                completion = exc.completion
                # Everything the run spent: for the agent every model call before the cut-off one.
                completions = run_log.completions if mode == "agent" else [completion]
                usage, cost = total_usage(completions)
                row |= {
                    "model": completion.model,
                    "error": exc.log_code,
                    "error_kind": error_kind(exc),
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
                        "overrides": [json.loads(o.model_dump_json()) for o in run_log.overrides],
                    }
            except ProviderError as exc:
                failures += 1
                if failures >= MAX_CONSECUTIVE_FAILURES:
                    raise
                completions = run_log.completions if mode == "agent" else []
                usage, cost = total_usage(completions)
                row |= {
                    "model": model.name,
                    "error": exc.log_code,
                    "error_kind": error_kind(exc),
                    "usage": usage,
                    "cost_usd": cost,
                    "latency_ms": (time.perf_counter() - started) * 1000,
                    "model_calls": len(completions),
                }
                if mode == "agent":
                    row |= {
                        "tool_calls": [json.loads(r.model_dump_json()) for r in run_log.tool_calls],
                        "facts_used": [json.loads(f.model_dump_json()) for f in run_log.facts],
                        "overrides": [json.loads(o.model_dump_json()) for o in run_log.overrides],
                    }
            else:
                failures = 0
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
                    "number_labels": data["number_labels"],
                }
                if mode == "agent":
                    row |= {
                        "fact_citations": data["fact_citations"],
                        "tool_calls": data["tool_calls"],
                        "facts_used": data["facts_used"],
                        "stopped_by": data["stopped_by"],
                        "overrides": data["overrides"],
                    }
            with out.open("a", encoding="utf-8", newline="\n") as handle:
                handle.write(json.dumps(row) + "\n")
            written += 1
    return written
