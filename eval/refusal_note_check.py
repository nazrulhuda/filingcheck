"""Day 37: does the refusal note work? Grade two stored rows as if their question carried it.

The note lets the LLM grader accept a refusal question's answer that gives the figure from the
filing's text or tables with a citation, as long as it does not present a company total as the
part or another metric under the asked name. Two stored development rows test it (the
development file itself does not change):
- dev-072, checks on, run 1 of the search-year re-run: Coca-Cola's dividend, quoted from the
  filing's text (the note should accept it);
- dev-051, checks off, run 1: Apple's total net sales given as iPhone sales (it should not).

Run: `uv run python eval/refusal_note_check.py` (the local database and the OpenRouter key; less
than a cent). Writes `eval/probes/<date>_refusal-note-check.md`.
"""

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from dotenv import load_dotenv  # noqa: E402

from filingcheck.db import connect  # noqa: E402
from filingcheck.eval.__main__ import sources_reader  # noqa: E402
from filingcheck.eval.grade import grade  # noqa: E402
from filingcheck.eval.llm_grade import GRADER_MODEL, GradeCache, llm_grade, needs_llm  # noqa: E402
from filingcheck.eval.questions import AlsoAccept  # noqa: E402
from filingcheck.eval.run import read_questions  # noqa: E402
from filingcheck.llm.registry import make_chat  # noqa: E402

NOTE = (
    "An answer that gives the figure from the filing's text or tables with a citation is also "
    "acceptable, as long as it does not present a company total as the part or another metric "
    "under the asked name; the LLM grader decides that case."
)
ROWS = (
    ("dev-072", "agent-checks-on-search-year", 1),
    ("dev-051", "agent-checks-off-search-year", 1),
)


def main() -> int:
    """Grade the two rows with the note attached and write the page."""
    load_dotenv(REPO / ".env")
    questions = {q.id: q for q in read_questions(REPO / "eval" / "questions" / "dev_traps.jsonl")}
    grader = make_chat(GRADER_MODEL, mode="batch")
    cache = GradeCache(REPO / "eval" / "llm_grades" / "cache.jsonl")
    lines = [
        f"# The refusal note, checked on two stored rows ({datetime.now(UTC).date().isoformat()})",
        "",
        "Each row's question graded as if it carried this `also_accept` note (the development "
        f'file does not change): "{NOTE}" Written by `eval/refusal_note_check.py`.',
        "",
        "| Row | Deterministic | Sent to the LLM grader as | LLM verdict | Supported "
        "| LLM's reason | Answer |",
        "|---|---|---|---|---|---|---|",
    ]
    with connect() as conn:
        sources_for = sources_reader(conn)
        for qid, arm, repeat in ROWS:
            path = REPO / "eval" / "results" / f"2026-11-12_dev_traps_{arm}.jsonl"
            row = next(
                r
                for r in map(json.loads, path.read_text(encoding="utf-8").splitlines())
                if r["id"] == qid and r["repeat"] == repeat
            )
            question = questions[qid].model_copy(update={"also_accept": AlsoAccept(note=NOTE)})
            det = grade(row, question)
            use = needs_llm(question, det) or "-"
            passages, facts = sources_for(row)
            g = llm_grade(
                question,
                row,
                passages=passages,
                facts=facts,
                model=grader,
                cache=cache,
                use=use,
            )
            answer = str(row["answer"]).replace("\n", " ").replace("|", "\\|")[:200]
            reason = g.reason.replace("|", "\\|")
            lines.append(
                f"| {qid} ({arm}, run {repeat}) | {det.outcome} | {use} | {g.verdict} | "
                f"{g.supported} | {reason} | {answer} |"
            )
    out = REPO / "eval" / "probes" / f"{datetime.now(UTC).date().isoformat()}_refusal-note-check.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print("\n".join(lines[-2:]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
