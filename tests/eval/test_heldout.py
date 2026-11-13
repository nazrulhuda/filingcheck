"""The held-out trap sets: the writers' words kept, and the alternatives their notes accept."""

import hashlib
import re
from pathlib import Path

from filingcheck.eval.run import read_questions

REPO = Path(__file__).resolve().parents[2]
SOURCES = REPO / "eval" / "questions" / "heldout_source"
SOURCE = SOURCES / "2026-11-12_heldout_agent_output.md"
SOURCE_2 = SOURCES / "2026-11-13_heldout2_gemini_output.md"
HELDOUT = {q.id: q for q in read_questions(REPO / "eval" / "questions" / "heldout_traps.jsonl")}
HELDOUT_2 = {q.id: q for q in read_questions(REPO / "eval" / "questions" / "heldout_traps_2.jsonl")}
LINE = r"^\s*[1-7]\s*\|\s*(.+?)\s*\|\s*(.+?)\s*$"
REFUSAL_NOTE = (
    "An answer that gives the figure from the filing's text or tables with a citation is also "
    "acceptable, as long as it does not present a company total as the part or another metric "
    "under the asked name; the LLM grader decides that case."
)


def test_every_question_and_note_is_the_writers_word_for_word() -> None:
    lines = re.findall(LINE, SOURCE.read_text("utf-8"), re.M)
    assert [(q.question, q.trap_note) for q in HELDOUT.values()] == lines
    assert len(HELDOUT) == 28


def test_the_second_files_questions_and_notes_are_geminis_word_for_word() -> None:
    lines = re.findall(LINE, SOURCE_2.read_text("utf-8"), re.M)
    assert [(q.question, q.trap_note) for q in HELDOUT_2.values()] == lines
    assert list(HELDOUT_2) == [f"held-{n:03d}" for n in range(29, 113)]
    assert not set(HELDOUT) & set(HELDOUT_2)


def test_the_alternatives_follow_the_writers_notes() -> None:
    with_alternative = {qid for qid, q in HELDOUT.items() if q.also_accept is not None}
    assert with_alternative == {
        "held-002",
        "held-007",
        "held-017",
        "held-018",
        "held-019",
        "held-021",
        "held-022",
        "held-028",
    }
    united, nvidia, youtube, spgi = (
        HELDOUT[i].also_accept for i in ("held-002", "held-007", "held-017", "held-028")
    )
    assert united is not None and united.expected_behavior == "clarify"
    assert spgi is not None and spgi.expected_behavior == "refuse"
    assert nvidia is not None and (nvidia.fiscal_year, nvidia.gold_source) == (2026, "facts")
    assert nvidia.gold_value == HELDOUT["held-007"].gold_other_years[2026]  # type: ignore[index]
    assert youtube is not None and youtube.note and youtube.expected_behavior is None
    assert HELDOUT["held-017"].expected_behavior == "refuse"


def test_the_refusal_note_sits_only_on_refusal_questions_and_is_the_tested_wording() -> None:
    noted = {
        qid: q
        for qid, q in {**HELDOUT, **HELDOUT_2}.items()
        if q.also_accept is not None and q.also_accept.note == REFUSAL_NOTE
    }
    assert set(noted) == {
        "held-018",
        "held-019",
        "held-021",
        "held-022",
        "held-077",
        "held-079",
        "held-082",
        "held-083",
        "held-087",
        "held-088",
        "held-091",
        "held-094",
        "held-097",
        "held-100",
    }
    assert all(q.expected_behavior == "refuse" and q.company for q in noted.values())
    assert all(q.also_accept and q.also_accept.expected_behavior is None for q in noted.values())


def test_the_held_out_file_is_sealed() -> None:
    """The SHA-256 recorded in docs/decisions.md; any edit to the file fails here.

    The seal of 2026-11-12 was 456723d5ca80eece53af096cc0516b6105e09772c8c52b45e4e1e5f7b72ec014;
    the file changed on 2026-11-13 only by four refusal notes, before any held-out run.
    """
    digest = hashlib.sha256((REPO / "eval" / "questions" / "heldout_traps.jsonl").read_bytes())
    assert digest.hexdigest() == "b295c38f60fcecce687f70b43520726cb0bfef3c1e616d4bd2835aeb85f343a5"
