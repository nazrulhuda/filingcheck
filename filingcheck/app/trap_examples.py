"""Saved answers to development trap questions, for the page's "Try a trap question".

`python -m filingcheck.app.trap_examples run` asks each candidate once, as `make examples`
asks (batch mode, the agent with its checks on, the question's page filter if it has one),
and appends the answers to `eval/results/<date>_page_trap_candidates.jsonl`; a candidate
already in the file is not asked again, and the stored example answers are not touched. It
then grades every candidate as the final run was graded: the batch runner's row, the
deterministic grader, the LLM grader on the rows that need it (every number-graded row
gets the second opinion) and the pre-registered scoring; and writes the table to the `.md`
file next to it. The LLM grades come from the shared cache when the inputs were graded before.

`python -m filingcheck.app.trap_examples export --pick ID,ID` writes the picked answers to
`web/data/trap_examples.json` in the shape of `web/data/examples.json`; no model is called.

Candidates come from the development traps only, never the held-out questions.
"""

import argparse
import json
import sys
from collections.abc import Callable, Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from filingcheck.agent import run_agent
from filingcheck.answer.batch import BATCH_FIELDS
from filingcheck.app.examples import _mark_standard_labels, with_citation_numbers
from filingcheck.app.store import ExampleAnswer
from filingcheck.console import use_utf8_output
from filingcheck.eval.questions import Question
from filingcheck.llm import ChatModel, IncompleteAnswer
from filingcheck.paths import REPO_ROOT
from filingcheck.tools import ToolDeps

DEV_TRAPS = REPO_ROOT / "eval" / "questions" / "dev_traps.jsonl"
RESULTS = REPO_ROOT / "eval" / "results"
EXPORT_FILE = REPO_ROOT / "web" / "data" / "trap_examples.json"
SET_NAME, ARM = "dev_traps", "agent-checks-on"

# The plan's kinds of trap, one development question each (the first of its kind in the file
# for the calendar year); the relative year is the Nike example the page already holds.
CANDIDATES: dict[str, str] = {
    "dev-001": "An ambiguous company name",
    "dev-067": "A company that is not covered",
    "dev-050": "A part of a company",
    "dev-014": "A calendar year for a company whose fiscal year ends in another month",
    "dev-076": "An instruction to ignore the rules",
}


def load_candidates(ids: Sequence[str], path: Path = DEV_TRAPS) -> list[Question]:
    """The questions with these ids from the development traps, in the order given."""
    if any(not i.startswith("dev-") for i in ids):
        raise ValueError("trap examples come from the development traps only")
    by_id = {
        q.id: q
        for q in (
            Question.model_validate_json(line)
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        )
    }
    missing = [i for i in ids if i not in by_id]
    if missing:
        raise ValueError(f"{', '.join(missing)} not in {path.name}")
    return [by_id[i] for i in ids]


def _filter(question: Question) -> tuple[str | None, int | None]:
    """The page filter a question is asked with; a year counts only with a company."""
    page = question.page_filter
    if page is None or page.ticker is None:
        return None, None
    return page.ticker, page.fiscal_year


def batch_row(
    question: Question, answer: Mapping[str, Any], *, settings: str, provenance: Mapping[str, Any]
) -> dict[str, Any]:
    """The row the batch runner writes for this completed agent answer, checks on, repeat 1."""
    row: dict[str, Any] = dict.fromkeys(BATCH_FIELDS) | {
        "id": question.id,
        "repeat": 1,
        "mode": "agent",
        "question": question.question,
        "settings": settings,
        "citations": [],
        "fact_citations": [],
        "tool_calls": [],
        "facts_used": [],
        "overrides": [],
        "number_labels": [],
    }
    row |= dict(provenance)
    if question.page_filter is not None:
        ticker, fiscal_year = _filter(question)
        row["page_filter"] = {"ticker": ticker, "fiscal_year": fiscal_year}
    row |= {"checks": True, "rules": None}
    row |= {
        "model": answer["model_used"],
        "answer": answer["text"],
        "citations": answer["citations"],
        "usage": answer["usage"],
        "cost_usd": answer["cost_usd"],
        "latency_ms": answer["latency_ms"],
        "finish_reason": answer["finish_reason"],
        "abstained": answer["abstained"],
        "has_uncited_claims": answer["has_uncited_claims"],
        "model_calls": answer.get("model_calls", 1),
        "number_labels": answer["number_labels"],
        "fact_citations": answer["fact_citations"],
        "tool_calls": answer["tool_calls"],
        "facts_used": answer["facts_used"],
        "stopped_by": answer["stopped_by"],
        "overrides": answer["overrides"],
    }
    return row


def read_lines(path: Path) -> list[dict[str, Any]]:
    """The candidates file's lines."""
    if not path.exists():
        return []
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]


def ask_candidates(
    questions: Sequence[Question],
    *,
    model: ChatModel,
    deps: ToolDeps,
    out: Path,
    provenance: Mapping[str, Any],
    settings: str,
    echo: Callable[[str], None] = print,
) -> int:
    """Ask each candidate not yet in `out` once, checks on; return how many were asked.

    A cut-off or degraded answer stops the run with nothing written for that candidate, as
    `make examples` does; run again to go on.
    """
    done = {line["id"] for line in read_lines(out)}
    asked = 0
    for q in questions:
        if q.id in done:
            continue
        ticker, fiscal_year = _filter(q)
        try:
            answer = run_agent(
                q.question,
                model=model,
                deps=deps,
                ticker=ticker,
                fiscal_year=fiscal_year,
                checks=True,
            )
        except IncompleteAnswer:
            echo(f"{q.id}: cut off; stopped, nothing written for it")
            return asked
        if answer.degraded:
            echo(f"{q.id}: degraded (keyword search only); stopped, nothing written for it")
            return asked
        line = {
            "id": q.id,
            "question": q.question,
            "page_filter": (
                None if q.page_filter is None else {"ticker": ticker, "fiscal_year": fiscal_year}
            ),
            "settings": settings,
            **provenance,
            "answer": json.loads(answer.model_dump_json()),
        }
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(line, ensure_ascii=False) + "\n")
        asked += 1
        echo(f"{q.id}: {answer.model_used}, {len(answer.tool_calls)} tool calls")
    return asked


def row_of(line: Mapping[str, Any], question: Question) -> dict[str, Any]:
    """A candidates-file line as the batch runner's row."""
    provenance = {k: line[k] for k in ("git_commit", "git_clean", "questions_sha256") if k in line}
    return batch_row(question, line["answer"], settings=line["settings"], provenance=provenance)


def _checks_did(answer: Mapping[str, Any]) -> str:
    """What the checks did, in the order of the log: every repair and reject, then the passes."""
    log = answer.get("overrides") or []
    acted = [f"{o['check']} {o['outcome']}: {o['reason']}" for o in log if o["outcome"] != "pass"]
    passes = sum(1 for o in log if o["outcome"] == "pass")
    calls = ", ".join(
        f"{c['name']}({json.dumps(c.get('arguments'), ensure_ascii=False)})"
        for c in answer.get("tool_calls") or []
    )
    return f"Calls: {calls or 'none'}. " + (
        "; ".join(acted) + f"; {passes} passes"
        if acted
        else f"No repair or reject; {passes} passes"
    )


def _cell(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ")


def render_table(lines: Sequence[Mapping[str, Any]], scores: Mapping[str, Any]) -> str:
    """The candidates as a page: what each asked, what the checks did, the answer, the grade."""
    out = [
        "# Trap candidates for the page",
        "",
        "Each asked once, as `make examples` asks (batch mode, the agent with its checks on); "
        "graded as the final run was (the deterministic grader, the LLM grader, the "
        "pre-registered scoring). Written by `python -m filingcheck.app.trap_examples run`.",
        "",
        "| Candidate | Kind | Question | Asked with | What the checks did | Answer | Grade |",
        "|---|---|---|---|---|---|---|",
    ]
    for line in lines:
        s = scores[line["id"]]
        grade = (
            f"{'correct' if s.correct else 'not correct'}"
            f"{', confidently wrong' if s.confidently_wrong else ''} "
            f"(deterministic: {s.outcome}; LLM: {s.llm_verdict or 'not asked'})"
        )
        page = line.get("page_filter")
        asked = (
            "no filters" if not page else f"{page['ticker']} · {page['fiscal_year'] or 'any year'}"
        )
        out.append(
            "| "
            + " | ".join(
                _cell(x)
                for x in (
                    line["id"],
                    CANDIDATES.get(line["id"], ""),
                    line["question"],
                    asked,
                    _checks_did(line["answer"]),
                    line["answer"]["text"],
                    grade,
                )
            )
            + " |"
        )
    return "\n".join(out) + "\n"


def export_picks(
    ids: Sequence[str],
    lines: Sequence[Mapping[str, Any]],
    *,
    passage_text: Callable[[list[int]], dict[int, str]] | None,
) -> list[dict[str, Any]]:
    """The picked candidates in the saved examples' shape, each answer as it was stored.

    As for the saved examples, each citation carries its passage number and, when stored
    without it, its passage's text; each fact citation says whether its line label is the
    standard name. Nothing in the answer's text, labels or log changes.
    """
    by_id = {line["id"]: line for line in lines}
    missing = [i for i in ids if i not in by_id]
    if missing:
        raise ValueError(f"{', '.join(missing)} not among the candidates run")
    picks = []
    for i in ids:
        line = by_id[i]
        page = line.get("page_filter") or {}
        example = with_citation_numbers(
            ExampleAnswer(
                question=line["question"],
                ticker=page.get("ticker"),
                fiscal_year=page.get("fiscal_year"),
                answer=dict(line["answer"]),
            )
        )
        answer = example["answer"]
        _mark_standard_labels(answer)
        missing_text = [c for c in answer.get("citations", []) if not c.get("text")]
        if passage_text is not None and missing_text:
            texts = passage_text([c["chunk_id"] for c in missing_text])
            for citation in missing_text:
                citation["text"] = texts.get(citation["chunk_id"], citation.get("quote", ""))
        picks.append({"id": i, "trap": CANDIDATES[i], **example})
    return picks


def candidates_path(day: str) -> Path:
    """Where one day's candidate answers go."""
    return RESULTS / f"{day}_page_trap_candidates.jsonl"


def _newest() -> Path:
    found = sorted(RESULTS.glob("*_page_trap_candidates.jsonl"))
    if not found:
        raise SystemExit("no candidates file: run `python -m filingcheck.app.trap_examples run`")
    return found[-1]


def run_main(day: str, cap: float) -> int:
    """Ask the candidates not yet asked, then grade them all and write the table."""
    from filingcheck.answer.run import hybrid_retriever, settings_line
    from filingcheck.checks import reference_data
    from filingcheck.db import connect
    from filingcheck.eval.__main__ import sources_reader
    from filingcheck.eval.llm_grade import GRADER_MODEL, GradeCache, grade_rows
    from filingcheck.eval.metrics import score_run
    from filingcheck.eval.run import provenance
    from filingcheck.facts.lookup import PostgresFacts
    from filingcheck.llm import router_from_env
    from filingcheck.llm.registry import make_chat

    load_dotenv(REPO_ROOT / ".env")
    questions = load_candidates(list(CANDIDATES))
    out = candidates_path(day)
    router = router_from_env("batch")
    settings = settings_line(router.primary.name, filters="the question's page filter, if any")
    with connect() as conn:
        deps = ToolDeps(
            retriever=hybrid_retriever(conn), facts=PostgresFacts(conn), **reference_data()
        )
        ask_candidates(
            questions,
            model=router,
            deps=deps,
            out=out,
            provenance=provenance(DEV_TRAPS),
            settings=settings,
        )
        by_id = {q.id: q for q in questions}
        lines = [line for line in read_lines(out) if line["id"] in by_id]
        rows = [row_of(line, by_id[line["id"]]) for line in lines]
        grades, stopped = grade_rows(
            rows,
            by_id,
            sources_for=sources_reader(conn),
            model=make_chat(GRADER_MODEL, mode="batch"),
            cache=GradeCache(REPO_ROOT / "eval" / "llm_grades" / "cache.jsonl"),
            cap_usd=cap,
            every_number=True,
        )
    by_row = {(g.id, g.repeat): g for g in grades}
    scores = {
        r["id"]: score_run(r, by_id[r["id"]], by_row.get((r["id"], 1)), set_name=SET_NAME, arm=ARM)
        for r in rows
    }
    out.with_name(out.stem + "_llm.jsonl").write_text(
        "".join(g.model_dump_json() + "\n" for g in grades), encoding="utf-8", newline="\n"
    )
    table = render_table(lines, scores)
    out.with_suffix(".md").write_text(table, encoding="utf-8", newline="\n")
    print(table)
    spent = sum(line["answer"]["cost_usd"] or 0 for line in lines)
    print(f"answers: ${spent:.6f}; LLM grades: ${sum(g.cost_usd or 0 for g in grades):.6f}")
    return 1 if stopped else 0


def export_main(ids: list[str], path: Path, out: Path) -> int:
    """Write the picked candidates to the page's file; the passages' text comes from the DB."""
    from filingcheck.app.examples import chunk_texts
    from filingcheck.db import connect

    load_dotenv(REPO_ROOT / ".env")
    with connect() as conn:
        picks = export_picks(ids, read_lines(path), passage_text=chunk_texts(conn))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(picks, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n"
    )
    print(f"wrote {len(picks)} trap examples to {out.relative_to(REPO_ROOT).as_posix()}")
    return 0


def main(argv: list[str] | None = None) -> int:
    """Run and grade the candidates, or export the picked ones."""
    use_utf8_output()
    parser = argparse.ArgumentParser(prog="python -m filingcheck.app.trap_examples")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run", help="ask the candidates once each and grade them (costs money)")
    run.add_argument("--date", default=datetime.now(UTC).strftime("%Y-%m-%d"))
    run.add_argument("--cap", type=float, default=0.25, help="the LLM grader's spend cap, USD")
    export = sub.add_parser("export", help="write the picked answers for the page; no model call")
    export.add_argument("--pick", required=True, help="candidate ids, comma-separated")
    export.add_argument("--from", dest="source", type=Path, help="the candidates file")
    export.add_argument("--out", type=Path, default=EXPORT_FILE)
    args = parser.parse_args(argv)
    if args.command == "run":
        return run_main(args.date, args.cap)
    ids = [i.strip() for i in args.pick.split(",") if i.strip()]
    load_candidates(ids)  # refuses a held-out or unknown id
    return export_main(ids, args.source or _newest(), args.out)


if __name__ == "__main__":
    sys.exit(main())
