"""Day 37: does the refusal note work? Grade two stored rows as if their question carried it.

The note lets the LLM grader accept a refusal question's answer that gives the figure from the
filing's text or tables with a citation, as long as it does not present a company total as the
part or another metric under the asked name. Two stored development rows test it (the
development file itself does not change):
- dev-072, checks on, run 1 of the search-year re-run: Coca-Cola's dividend, quoted from the
  filing's text (the note should accept it);
- dev-051, checks off, run 1: Apple's total net sales given as iPhone sales (it should not).

dev-072 turned out not to be a clean accept case (it asks for next quarter's dividend), so two
hand-made answers to held-022 ("how many people work at amazon") test the grader too; they test
the grader, not the system, and are written to `eval/probes/<date>_refusal-note-handmade.jsonl`
marked `hand_made: true`:
- (a) quotes chunk 1256 (Amazon FY2025, Item 1, Human Capital: "approximately 1,576,000
  full-time and part-time employees" as of December 31, 2025) with a citation: must be accepted;
- (b) the same citation with a figure the passage does not state: must be rejected. The first (b)
  used 1,600,000 and was accepted as "that figure rounded"; it was a bad case (1,600,000 is a fair
  rounding of 1,576,000, "about 1.6 million") and is withdrawn but kept here with its verdict. (b)
  was run once more with 1,250,000, nothing else changed, its verdict final (decisions,
  2026-11-13).

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
AMAZON_CHUNK = 1256  # Amazon FY2025 10-K, Item 1, "Human Capital"
HAND_MADE = (
    (
        "held-022-a",
        "As of December 31, 2025, Amazon employed approximately 1,576,000 full-time and part-time "
        "employees [1].",
        "accept",
    ),
    (
        "held-022-b (first; withdrawn: a fair rounding)",
        "As of December 31, 2025, Amazon employed approximately 1,600,000 full-time and part-time "
        "employees [1].",
        "reject",
    ),
    (
        "held-022-b (re-run, final)",
        "As of December 31, 2025, Amazon employed approximately 1,250,000 full-time and part-time "
        "employees [1].",
        "reject",
    ),
)


def main() -> int:
    """Grade the two rows with the note attached and write the page."""
    load_dotenv(REPO / ".env")
    questions = {q.id: q for q in read_questions(REPO / "eval" / "questions" / "dev_traps.jsonl")}
    heldout = {q.id: q for q in read_questions(REPO / "eval" / "questions" / "heldout_traps.jsonl")}
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
        today = datetime.now(UTC).date().isoformat()
        held = heldout["held-022"].model_copy(update={"also_accept": AlsoAccept(note=NOTE)})
        made_rows = []
        for label, text, expected in HAND_MADE:
            row = {
                "id": "held-022",
                "repeat": 1,
                "hand_made": True,
                "label": label,
                "expected": expected,
                "question": held.question,
                "answer": text,
                "citations": [{"number": 1, "chunk_id": AMAZON_CHUNK}],
                "tool_calls": [],
                "facts_used": [],
            }
            made_rows.append(row)
            det = grade(row, held)
            use = needs_llm(held, det) or "-"
            passages, facts = sources_for(row)
            g = llm_grade(
                held,
                row,
                passages=passages,
                facts=facts,
                model=grader,
                cache=cache,
                use=use,
            )
            reason = g.reason.replace("|", "\\|")
            lines.append(
                f"| {label} (hand-made, must {expected}) | {det.outcome} | {use} | {g.verdict} | "
                f"{g.supported} | {reason} | {text} |"
            )
        (REPO / "eval" / "probes" / f"{today}_refusal-note-handmade.jsonl").write_text(
            "".join(json.dumps(r) + "\n" for r in made_rows), encoding="utf-8", newline="\n"
        )
    out = REPO / "eval" / "probes" / f"{datetime.now(UTC).date().isoformat()}_refusal-note-check.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print("\n".join(lines[-2:]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
