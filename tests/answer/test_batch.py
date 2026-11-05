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
    assert read_done(out) == {("q-1", 1)}
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


def test_a_cut_off_agent_answer_records_everything_the_run_spent(tmp_path: Path) -> None:
    from tests.agent.test_agent import cut_off

    out = tmp_path / "run.jsonl"
    model = FakeChat([scripted_tool_calls(("get_financial_fact", FACT)), cut_off()])
    run_batch(QUESTIONS[:1], mode="agent", out=out, model=model, deps=apple_deps(), settings="s")
    (row,) = lines(out)
    assert row["error"] == "fake - incomplete_length" and row["answer"] is None
    assert row["usage"] == {"prompt_tokens": 107, "completion_tokens": 23}  # both calls
    assert row["cost_usd"] == pytest.approx(0.001)
    assert row["model_calls"] == 2
    assert [c["name"] for c in row["tool_calls"]] == ["get_financial_fact"]
    assert row["facts_used"][0]["value"] == "416161000000"
    assert row["latency_ms"] is not None and row["finish_reason"] == "length"


def test_a_cut_off_baseline_answer_records_its_one_call(tmp_path: Path) -> None:
    from tests.agent.test_agent import cut_off

    out = tmp_path / "base.jsonl"
    run_batch(
        QUESTIONS[:1],
        mode="baseline",
        out=out,
        model=FakeChat([cut_off()]),
        deps=apple_deps(),
        settings="s",
        retriever=FakeRetriever(),
    )
    (row,) = lines(out)
    assert (row["model_calls"], row["usage"]["prompt_tokens"]) == (1, 7)
    assert row["latency_ms"] is not None


def test_a_corrupt_line_before_the_last_stops_the_runner_with_its_line_number(
    tmp_path: Path,
) -> None:
    from filingcheck.answer.batch import BatchFileError

    out = tmp_path / "run.jsonl"
    out.write_text(
        '{"id": "q-1"}\nnot json\n{"id": "q-3"}\n',
        encoding="utf-8",
    )
    with pytest.raises(BatchFileError, match="line 2"):
        read_done(out)
    with pytest.raises(BatchFileError, match="line 2"):
        run_batch(
            QUESTIONS, mode="agent", out=out, model=FakeChat([]), deps=apple_deps(), settings="s"
        )
    # Nothing is removed: the file is left for a person to look at.
    assert out.read_text(encoding="utf-8").count("\n") == 3


def test_a_complete_last_line_that_is_not_json_is_corrupt_too(tmp_path: Path) -> None:
    from filingcheck.answer.batch import BatchFileError

    out = tmp_path / "run.jsonl"
    out.write_text('{"id": "q-1"}\nnot json\n', encoding="utf-8")
    with pytest.raises(BatchFileError, match="line 2"):
        read_done(out)


def test_a_line_without_an_id_is_corrupt(tmp_path: Path) -> None:
    from filingcheck.answer.batch import BatchFileError

    out = tmp_path / "run.jsonl"
    out.write_text('{"id": "q-1"}\n{"answer": "x"}\n', encoding="utf-8")
    with pytest.raises(BatchFileError, match="line 2"):
        read_done(out)


def test_each_question_is_asked_repeats_times_and_each_row_says_which(tmp_path: Path) -> None:
    out = tmp_path / "run.jsonl"
    written = run_batch(
        QUESTIONS[:2],
        mode="agent",
        out=out,
        model=FakeChat(agent_replies(6)),
        deps=apple_deps(),
        settings="s",
        repeats=3,
    )
    assert written == 6
    # One full pass over the questions, then the next, so a stopped run has whole passes.
    assert [(r["id"], r["repeat"]) for r in lines(out)] == [
        ("q-1", 1),
        ("q-2", 1),
        ("q-1", 2),
        ("q-2", 2),
        ("q-1", 3),
        ("q-2", 3),
    ]


def test_repeats_resume_by_question_and_repeat(tmp_path: Path) -> None:
    out = tmp_path / "run.jsonl"
    run_batch(
        QUESTIONS[:1],
        mode="agent",
        out=out,
        model=FakeChat(agent_replies(1)),
        deps=apple_deps(),
        settings="s",
        repeats=1,
    )
    model = FakeChat(agent_replies(2))
    written = run_batch(
        QUESTIONS[:1],
        mode="agent",
        out=out,
        model=model,
        deps=apple_deps(),
        settings="s",
        repeats=3,
    )
    assert written == 2 and model.replies == []
    assert [r["repeat"] for r in lines(out)] == [1, 2, 3]


def test_a_row_written_before_repeats_counts_as_repeat_1(tmp_path: Path) -> None:
    out = tmp_path / "run.jsonl"
    out.write_text('{"id": "q-1"}\n', encoding="utf-8")
    assert read_done(out) == {("q-1", 1)}


def test_a_blank_line_in_a_results_file_is_skipped_not_corrupt(tmp_path: Path) -> None:
    out = tmp_path / "run.jsonl"
    out.write_text('{"id": "q-1", "repeat": 1}\n\n{"id": "q-2", "repeat": 1}\n', encoding="utf-8")
    assert read_done(out) == {("q-1", 1), ("q-2", 1)}
