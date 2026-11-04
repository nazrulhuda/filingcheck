"""The batch runner: a question file through either mode, one JSON line each, resumable."""

import json
from pathlib import Path
from typing import Any

import pytest

from filingcheck.answer.batch import BATCH_FIELDS, read_done, run_batch
from filingcheck.llm import FakeChat, IncompleteAnswer, ProviderError, scripted_tool_calls
from tests.agent.test_agent import apple_deps
from tests.answer.test_baseline import FakeRetriever

QUESTIONS = [
    ("q-1", "What were Apple's total net sales in fiscal 2025?"),
    ("q-2", "What are Apple's main risks?"),
    ("q-3", "What was Apple's net income in fiscal 2025?"),
]
FACT = {"ticker": "AAPL", "fiscal_year": 2025, "metric": "revenue"}


def lines(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def agent_replies(n: int) -> list[Any]:
    replies: list[Any] = []
    for _ in range(n):
        replies += [
            scripted_tool_calls(("get_financial_fact", FACT)),
            "Sales were $416,161 million [F1].",
        ]
    return replies


def test_the_agent_mode_writes_one_line_per_question_with_every_field(tmp_path: Path) -> None:
    out = tmp_path / "run.jsonl"
    written = run_batch(
        QUESTIONS,
        mode="agent",
        out=out,
        model=FakeChat(agent_replies(3)),
        deps=apple_deps(),
        settings="fake settings",
    )
    assert written == 3
    rows = lines(out)
    assert [r["id"] for r in rows] == ["q-1", "q-2", "q-3"]
    first = rows[0]
    assert set(first) == set(BATCH_FIELDS)
    assert (first["mode"], first["model"], first["settings"]) == (
        "agent",
        "fake:chat",
        "fake settings",
    )
    assert first["answer"] == "Sales were $416,161 million [F1]."
    assert first["tool_calls"][0]["name"] == "get_financial_fact"
    assert first["facts_used"][0]["value"] == "416161000000"
    assert first["fact_citations"][0]["number"] == 1
    assert first["usage"] == {"prompt_tokens": 200, "completion_tokens": 40}
    assert first["error"] is None and first["finish_reason"] == "stop"


def test_the_baseline_mode_writes_the_same_fields(tmp_path: Path) -> None:
    out = tmp_path / "base.jsonl"
    run_batch(
        QUESTIONS[:1],
        mode="baseline",
        out=out,
        model=FakeChat(["Risk [1]."]),
        deps=apple_deps(),
        settings="s",
        retriever=FakeRetriever(),
    )
    (row,) = lines(out)
    assert set(row) == set(BATCH_FIELDS)
    assert (row["mode"], row["tool_calls"], row["facts_used"]) == ("baseline", [], [])
    assert row["citations"][0]["number"] == 1


def test_a_run_resumes_after_a_crash_from_the_next_question(tmp_path: Path) -> None:
    out = tmp_path / "run.jsonl"
    run_batch(
        QUESTIONS[:1],
        mode="agent",
        out=out,
        model=FakeChat(agent_replies(1)),
        deps=apple_deps(),
        settings="s",
    )
    with out.open("a", encoding="utf-8") as handle:
        handle.write('{"id": "q-2", "mode": "agent", "answ')  # a line cut off by the crash
    assert read_done(out) == {"q-1"}
    model = FakeChat(agent_replies(2))
    written = run_batch(
        QUESTIONS, mode="agent", out=out, model=model, deps=apple_deps(), settings="s"
    )
    assert written == 2  # q-2 and q-3; q-1 was done
    assert [r["id"] for r in lines(out)] == ["q-1", "q-2", "q-3"]
    assert model.replies == []


def test_a_cut_off_answer_is_written_with_its_error_and_the_run_goes_on(tmp_path: Path) -> None:
    from filingcheck.llm import Completion

    cut = IncompleteAnswer(
        "fake: cut off",
        Completion(
            text="Sales were",
            prompt_tokens=1,
            completion_tokens=1,
            model="fake:chat",
            latency_ms=0.0,
            cost_usd=0.0,
            finish_reason="length",
        ),
        provider="fake",
        code="incomplete_length",
    )
    out = tmp_path / "run.jsonl"
    model = FakeChat([cut, *agent_replies(1)])
    run_batch(QUESTIONS[:2], mode="agent", out=out, model=model, deps=apple_deps(), settings="s")
    first, second = lines(out)
    assert (first["error"], first["answer"]) == ("fake - incomplete_length", None)
    assert second["error"] is None


def test_a_provider_failure_stops_the_run_so_it_can_be_resumed(tmp_path: Path) -> None:
    out = tmp_path / "run.jsonl"
    model = FakeChat([*agent_replies(1), ProviderError("down", provider="fake", status=500)])
    with pytest.raises(ProviderError):
        run_batch(QUESTIONS, mode="agent", out=out, model=model, deps=apple_deps(), settings="s")
    assert [r["id"] for r in lines(out)] == ["q-1"]
