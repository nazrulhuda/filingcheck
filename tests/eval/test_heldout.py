"""The held-out trap set: the writer's words kept, and the alternatives its notes accept."""

import re
from pathlib import Path

from filingcheck.eval.run import read_questions

REPO = Path(__file__).resolve().parents[2]
SOURCE = REPO / "eval" / "questions" / "heldout_source" / "2026-11-12_heldout_agent_output.md"
HELDOUT = {q.id: q for q in read_questions(REPO / "eval" / "questions" / "heldout_traps.jsonl")}


def test_every_question_and_note_is_the_writers_word_for_word() -> None:
    lines = re.findall(r"^\s*[1-7]\s*\|\s*(.+?)\s*\|\s*(.+?)\s*$", SOURCE.read_text("utf-8"), re.M)
    assert [(q.question, q.trap_note) for q in HELDOUT.values()] == lines
    assert len(HELDOUT) == 28


def test_the_alternatives_follow_the_writers_notes() -> None:
    with_alternative = {qid for qid, q in HELDOUT.items() if q.also_accept is not None}
    assert with_alternative == {"held-002", "held-007", "held-017", "held-028"}
    united, nvidia, youtube, spgi = (
        HELDOUT[i].also_accept for i in ("held-002", "held-007", "held-017", "held-028")
    )
    assert united is not None and united.expected_behavior == "clarify"
    assert spgi is not None and spgi.expected_behavior == "refuse"
    assert nvidia is not None and (nvidia.fiscal_year, nvidia.gold_source) == (2026, "facts")
    assert nvidia.gold_value == HELDOUT["held-007"].gold_other_years[2026]  # type: ignore[index]
    assert youtube is not None and youtube.note and youtube.expected_behavior is None
    assert HELDOUT["held-017"].expected_behavior == "refuse"


def test_the_held_out_file_is_sealed() -> None:
    """The SHA-256 recorded in docs/decisions.md on 2026-11-12; any edit to the file fails here."""
    import hashlib

    digest = hashlib.sha256(
        (REPO / "eval" / "questions" / "heldout_traps.jsonl").read_bytes()
    ).hexdigest()
    assert digest == "456723d5ca80eece53af096cc0516b6105e09772c8c52b45e4e1e5f7b72ec014"
