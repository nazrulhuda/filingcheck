"""The Day 36 live check of the step-cap change: re-ask the dry-run runs that hit the step cap.

In the Week 5 search-year re-run, 8 runs stopped at the model-call cap (7 with the checks on).
This script asks each of those questions 3 more times in the same arm with the current code,
where the final request carries no tools, and writes the rows to `eval/probes/` and a page that
puts each new run's ending and grade next to the old run's.

Run: `uv run python eval/step_cap_check.py` (needs the local database and the OpenRouter key; a
few cents).
"""

import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from dotenv import load_dotenv  # noqa: E402

from filingcheck.answer.batch import run_batch  # noqa: E402
from filingcheck.answer.run import hybrid_retriever, settings_line  # noqa: E402
from filingcheck.checks import reference_data  # noqa: E402
from filingcheck.db import connect  # noqa: E402
from filingcheck.eval.__main__ import sources_reader  # noqa: E402
from filingcheck.eval.grade import grade  # noqa: E402
from filingcheck.eval.llm_grade import GRADER_MODEL, GradeCache, llm_grade, needs_llm  # noqa: E402
from filingcheck.eval.run import read_questions  # noqa: E402
from filingcheck.facts.lookup import PostgresFacts  # noqa: E402
from filingcheck.llm import router_from_env  # noqa: E402
from filingcheck.llm.registry import make_chat  # noqa: E402
from filingcheck.tools import ToolDeps  # noqa: E402

RESULTS = REPO / "eval" / "results"
DRY_RUN = "2026-11-12"
SETS = ("dev_traps", "dev_unanswerable", "control")
REPEATS = 3


def capped_runs() -> list[dict[str, Any]]:
    """The search-year re-run's rows that stopped at the step cap, with their file and arm."""
    found = []
    for set_name in SETS:
        for arm in ("agent-checks-off", "agent-checks-on"):
            path = RESULTS / f"{DRY_RUN}_{set_name}_{arm}-search-year.jsonl"
            for line in path.read_text(encoding="utf-8").splitlines():
                row = json.loads(line)
                if row.get("stopped_by"):
                    found.append({"set": set_name, "arm": arm, "row": row})
    return found


def main() -> int:
    """Re-ask each capped question 3 times in its arm, grade the runs, write the rows and page."""
    load_dotenv(REPO / ".env")
    today = datetime.now(UTC).date().isoformat()
    capped = capped_runs()
    pairs = list(dict.fromkeys((c["set"], c["arm"], c["row"]["id"]) for c in capped))
    questions = {
        s: {q.id: q for q in read_questions(REPO / "eval" / "questions" / f"{s}.jsonl")}
        for s in SETS
    }
    router = router_from_env("batch")
    settings = settings_line(router.primary.name, filters="question text only, no filters")
    grader = make_chat(GRADER_MODEL, mode="batch")
    cache = GradeCache(REPO / "eval" / "llm_grades" / "cache.jsonl")
    lines_out: list[dict[str, Any]] = []
    with connect() as conn:
        extra = reference_data()
        sources_for = sources_reader(conn)
        for arm in ("agent-checks-off", "agent-checks-on"):
            checks = arm == "agent-checks-on"
            asked = [(s, qid) for s, a, qid in pairs if a == arm]
            if not asked:
                continue
            out = REPO / "eval" / "probes" / f"{today}_step-cap-check_{arm}.jsonl"
            deps = ToolDeps(
                retriever=hybrid_retriever(conn),
                facts=PostgresFacts(conn),
                **(extra if checks else {}),
            )
            filters = {
                qid: (q.page_filter.ticker, q.page_filter.fiscal_year)
                for s, qid in asked
                if (q := questions[s][qid]).page_filter is not None
            }
            run_batch(
                [(qid, questions[s][qid].question) for s, qid in asked],
                mode="agent",
                out=out,
                model=router,
                deps=deps,
                settings=settings,
                repeats=REPEATS,
                checks=checks,
                filters=filters,
            )
            set_of = {qid: s for s, qid in asked}
            for line in out.read_text(encoding="utf-8").splitlines():
                row = json.loads(line)
                question = questions[set_of[row["id"]]][row["id"]]
                det = grade(row, question)
                verdict = None
                if row.get("answer") and needs_llm(question, det) == "text":
                    passages, facts = sources_for(row)
                    g = llm_grade(
                        question, row, passages=passages, facts=facts, model=grader, cache=cache
                    )
                    verdict = g.verdict
                lines_out.append({"arm": arm, "row": row, "outcome": det.outcome, "llm": verdict})
    page = [
        f"# The step-cap change, checked live ({today})",
        "",
        "The 8 runs of the Week 5 search-year re-run that stopped at the model-call cap (7 with "
        "the checks on), each question asked 3 more times in the same arm with the current code, "
        "where the final request carries no tools instead of `tool_choice: none`. Rows: "
        f"`eval/probes/{today}_step-cap-check_*.jsonl`. Written by `eval/step_cap_check.py`.",
        "",
        "## The old runs",
        "",
        "| Arm | Question | Run | Ended by | Error | Deterministic | Answer |",
        "|---|---|---:|---|---|---|---|",
    ]
    for c in capped:
        r = c["row"]
        answer = str(r.get("answer") or "").replace("\n", " ").replace("|", "\\|")[:160]
        page.append(
            f"| {c['arm']} | {r['id']} | {r['repeat']} | {r.get('stopped_by') or 'answer'} | "
            f"{r.get('error') or 'none'} | {r['grade']['outcome']} | {answer} |"
        )
    page += [
        "",
        "## The new runs",
        "",
        "| Arm | Question | Run | Ended by | Error | Deterministic | LLM (text) | Answer |",
        "|---|---|---:|---|---|---|---|---|",
    ]
    for item in lines_out:
        r = item["row"]
        answer = str(r.get("answer") or "").replace("\n", " ").replace("|", "\\|")[:160]
        page.append(
            f"| {item['arm']} | {r['id']} | {r['repeat']} | {r.get('stopped_by') or 'answer'} | "
            f"{r.get('error') or 'none'} | {item['outcome']} | {item['llm'] or '-'} | {answer} |"
        )
    errors = sum(1 for item in lines_out if item["row"].get("error"))
    capped_again = sum(1 for item in lines_out if item["row"].get("stopped_by"))
    page += [
        "",
        f"{len(lines_out)} new runs: {errors} with a provider error, {capped_again} stopped by "
        "the step cap again (each of those ended with a final request that carried no tools).",
    ]
    target = REPO / "eval" / "probes" / f"{today}_step-cap-check.md"
    target.write_text("\n".join(page) + "\n", encoding="utf-8", newline="\n")
    print("\n".join(page[-1:]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
