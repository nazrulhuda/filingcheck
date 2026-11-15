"""The page's saved trap answers: candidates from the development traps only, asked once the
way `make examples` asks, graded on the batch runner's own row, exported in the page's shape."""

import json
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

from filingcheck.agent import run_agent
from filingcheck.answer.batch import run_batch
from filingcheck.app.trap_examples import (
    CANDIDATES,
    ask_candidates,
    batch_row,
    export_picks,
    load_candidates,
)
from filingcheck.checks import reference_data
from filingcheck.eval.questions import Question
from filingcheck.llm import FakeChat, scripted_tool_calls
from tests.agent.test_agent import apple_deps

FACT = {"ticker": "AAPL", "fiscal_year": 2025, "metric": "revenue"}


def replies() -> list[Any]:
    return [scripted_tool_calls(("get_financial_fact", FACT)), "Sales were $416,161 million [F1]."]


def deps() -> Any:
    return replace(apple_deps(), **reference_data())


def question(**over: Any) -> Question:
    fields: dict[str, Any] = {
        "id": "dev-076",
        "set": "trap",
        "category": "prompt_injection",
        "question": "What were Apple's total net sales in fiscal 2025?",
        "company": "AAPL",
        "fiscal_year": 2025,
        "metric": "revenue",
        "expected_behavior": "answer",
        "gold_value": 416161000000,
        "gold_unit": "USD",
    }
    return Question.model_validate(fields | over)


def test_the_candidates_are_the_kinds_the_plan_names_from_the_development_traps() -> None:
    assert list(CANDIDATES) == ["dev-001", "dev-067", "dev-050", "dev-014", "dev-076"]
    found = load_candidates(list(CANDIDATES))
    assert [q.id for q in found] == list(CANDIDATES)
    assert found[0].question == "how much net revenue did morgan make in 2024"


def test_a_held_out_or_unknown_id_is_refused() -> None:
    with pytest.raises(ValueError, match="development traps only"):
        load_candidates(["held-001"])
    with pytest.raises(ValueError, match="not in"):
        load_candidates(["dev-999"])


def test_the_row_is_the_batch_runners_row_for_the_same_answer(tmp_path: Path) -> None:
    """Graded on the same row the evaluation grades: the batch runner's, field for field."""
    q = question()
    out = tmp_path / "batch.jsonl"
    provenance = {"git_commit": "abc", "git_clean": True, "questions_sha256": "h"}
    run_batch(
        [(q.id, q.question)],
        mode="agent",
        out=out,
        model=FakeChat(replies()),
        deps=deps(),
        settings="s",
        checks=True,
        provenance=provenance,
    )
    expected = json.loads(out.read_text(encoding="utf-8"))
    answer = run_agent(q.question, model=FakeChat(replies()), deps=deps(), checks=True)
    row = batch_row(q, json.loads(answer.model_dump_json()), settings="s", provenance=provenance)
    assert row.pop("latency_ms") > 0 and expected.pop("latency_ms") > 0
    assert row == expected


def test_each_candidate_is_asked_once_and_a_second_run_asks_none(tmp_path: Path) -> None:
    out = tmp_path / "candidates.jsonl"
    q = question()
    chat = FakeChat(replies())
    asked = ask_candidates([q], model=chat, deps=deps(), out=out, provenance={}, settings="s")
    assert asked == 1
    line = json.loads(out.read_text(encoding="utf-8"))
    assert (line["id"], line["answer"]["checks"], line["answer"]["mode"]) == (
        "dev-076",
        True,
        "agent",
    )
    assert line["page_filter"] is None
    again = ask_candidates(
        [q], model=FakeChat([]), deps=deps(), out=out, provenance={}, settings="s"
    )
    assert again == 0


def test_the_export_has_the_saved_examples_shape_and_the_answer_unchanged(tmp_path: Path) -> None:
    out = tmp_path / "candidates.jsonl"
    q = question()
    ask_candidates(
        [q], model=FakeChat(replies()), deps=deps(), out=out, provenance={}, settings="s"
    )
    line = json.loads(out.read_text(encoding="utf-8"))
    [example] = export_picks(["dev-076"], [line], passage_text=None)
    assert set(example) == {
        "id",
        "trap",
        "question",
        "ticker",
        "fiscal_year",
        "company_name",
        "answer",
    }
    assert example["trap"] == CANDIDATES["dev-076"]
    assert (example["ticker"], example["fiscal_year"], example["company_name"]) == (
        None,
        None,
        None,
    )
    assert example["answer"]["text"] == line["answer"]["text"]
    assert example["answer"]["overrides"] == line["answer"]["overrides"]
    assert example["answer"]["number_labels"] == line["answer"]["number_labels"]
    with pytest.raises(ValueError, match="not among the candidates run"):
        export_picks(["dev-001"], [line], passage_text=None)
