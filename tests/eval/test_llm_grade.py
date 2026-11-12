"""The LLM grader, with the fake model: its prompt, inputs, verdict, cache and cost cap."""

import json
from pathlib import Path
from typing import Any

from filingcheck.eval.grade import grade
from filingcheck.eval.llm_grade import (
    PROMPT_FILE,
    VERDICT_SCHEMA,
    GradeCache,
    build_messages,
    grade_rows,
    llm_grade,
    load_prompt,
    needs_llm,
)
from filingcheck.eval.questions import Question
from filingcheck.llm import Completion, FakeChat

NUMBER = Question.model_validate(
    {
        "id": "control-101",
        "set": "control",
        "category": "control",
        "style": "metrics-generated",
        "question": "how much did Amazon make in revenue for 2023",
        "company": "AMZN",
        "fiscal_year": 2023,
        "metric": "revenue",
        "expected_behavior": "answer",
        "gold_value": 574785000000,
        "gold_unit": "USD",
        "gold_source": "facts",
        "gold_period_start": "2023-01-01",
        "gold_period_end": "2023-12-31",
    }
)
TEXT = Question.model_validate(
    {
        "id": "control-131",
        "set": "control",
        "category": "control",
        "style": "domain-relevant",
        "question": "Where is Nike headquartered?",
        "company": "NKE",
        "fiscal_year": 2025,
        "metric": None,
        "expected_behavior": "answer",
        "gold_text": "Beaverton, Oregon (One Bowerman Drive).",
        "trap_note": "Key phrase in Item 1.",
    }
)
UNANSWERABLE = Question.model_validate(
    {
        "id": "una-004",
        "set": "trap",
        "category": "unanswerable_text",
        "question": "how many iphones did apple sell in fiscal 2025",
        "company": "AAPL",
        "fiscal_year": 2025,
        "metric": None,
        "expected_behavior": "refuse",
        "trap_note": "Apple does not disclose unit sales. Searched: unit sales.",
    }
)
VERDICT = {
    "verdict": "correct",
    "supported": "yes",
    "reason": "It names Beaverton.",
    "evidence": "Beaverton, Oregon",
}
PASSAGES = [(2, "NIKE Investor Relations, One Bowerman Drive, Beaverton, Oregon 97005-6453.")]
FACTS = [
    {
        "concept": "us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax",
        "value": "574785000000",
        "unit": "USD",
        "period_start": "2023-01-01",
        "period_end": "2023-12-31",
        "instant": None,
    }
]


def reply(payload: dict[str, Any], cost: float = 0.001) -> Completion:
    return Completion(
        text=json.dumps(payload),
        prompt_tokens=900,
        completion_tokens=60,
        model="fake:chat",
        latency_ms=5.0,
        cost_usd=cost,
        finish_reason="stop",
    )


def test_the_prompt_is_a_versioned_file_with_the_any_year_rule() -> None:
    text, version = load_prompt()
    assert Path(__file__).resolve().parents[2] / "eval" / "grader_prompt.md" == PROMPT_FILE
    assert text.startswith("Version: 1") and version.startswith("1-") and len(version) == 14
    assert "Text questions name no year" in text


def test_the_grader_sees_the_question_the_reference_the_answer_and_its_sources() -> None:
    prompt, _ = load_prompt()
    system, user = build_messages(
        NUMBER,
        "Revenue was $574.8 billion in 2023 [F1].",
        passages=PASSAGES,
        facts=FACTS,
        prompt=prompt,
    )
    assert (system["role"], system["content"]) == ("system", prompt)
    content = user["content"]
    for part in (
        "how much did Amazon make in revenue for 2023",
        "Expected behavior: answer",
        "574785000000 USD",
        "2023-01-01 to 2023-12-31",
        "Revenue was $574.8 billion in 2023 [F1].",
        "[2] NIKE Investor Relations",
        "F1: us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax = 574785000000 USD",
    ):
        assert part in content, part
    _, text_user = build_messages(TEXT, "Beaverton.", passages=[], facts=[], prompt=prompt)
    assert "Beaverton, Oregon (One Bowerman Drive)." in text_user["content"]
    assert "Key phrase in Item 1." in text_user["content"]


def test_a_verdict_is_read_from_the_models_json(tmp_path: Path) -> None:
    model = FakeChat([reply(VERDICT)])
    result = llm_grade(
        TEXT,
        {"id": "control-131", "repeat": 1, "answer": "Beaverton, Oregon [2]."},
        passages=PASSAGES,
        facts=[],
        model=model,
        cache=GradeCache(tmp_path / "cache.jsonl"),
    )
    assert (result.verdict, result.supported, result.cached, result.error) == (
        "correct",
        "yes",
        False,
        None,
    )
    assert result.cost_usd == 0.001 and result.prompt_version.startswith("1-")
    call = model.calls[0]
    assert call["json_schema"] == VERDICT_SCHEMA and call["temperature"] is None


def test_the_same_inputs_are_graded_once_and_then_read_from_the_cache(tmp_path: Path) -> None:
    cache = GradeCache(tmp_path / "cache.jsonl")
    row = {"id": "control-131", "repeat": 1, "answer": "Beaverton, Oregon [2]."}
    first = llm_grade(
        TEXT, row, passages=PASSAGES, facts=[], model=FakeChat([reply(VERDICT)]), cache=cache
    )
    again = llm_grade(
        TEXT,
        row,
        passages=PASSAGES,
        facts=[],
        model=FakeChat([]),
        cache=GradeCache(tmp_path / "cache.jsonl"),
    )
    assert (again.verdict, again.cached, again.cost_usd) == (first.verdict, True, 0.0)


def test_a_reply_that_is_not_a_valid_verdict_is_recorded_as_an_error(tmp_path: Path) -> None:
    model = FakeChat(
        [reply({"verdict": "great", "supported": "yes", "reason": "", "evidence": ""})]
    )
    result = llm_grade(
        TEXT,
        {"id": "control-131", "repeat": 1, "answer": "Beaverton."},
        passages=[],
        facts=[],
        model=model,
        cache=GradeCache(tmp_path / "cache.jsonl"),
    )
    assert (result.verdict, result.error) == (None, "invalid verdict")


def test_which_rows_the_llm_grader_reads() -> None:
    correct = grade({"answer": "Revenue was $574,785 million in fiscal 2023."}, NUMBER)
    wrong = grade({"answer": "Revenue was $1 billion in fiscal 2023."}, NUMBER)
    assert needs_llm(NUMBER, correct) is None
    assert needs_llm(NUMBER, wrong) == "second opinion"
    assert needs_llm(TEXT, grade({"answer": "Beaverton."}, TEXT)) == "text"
    assert needs_llm(UNANSWERABLE, grade({"answer": "I can't find that."}, UNANSWERABLE)) == "text"


def test_grading_stops_once_the_cost_cap_is_passed(tmp_path: Path) -> None:
    rows = [{"id": "control-131", "repeat": r, "answer": f"Beaverton {r}."} for r in (1, 2, 3)]
    model = FakeChat([reply(VERDICT, cost=0.6) for _ in rows])
    grades, stopped = grade_rows(
        rows,
        {"control-131": TEXT},
        sources_for=lambda row: ([], []),
        model=model,
        cache=GradeCache(tmp_path / "cache.jsonl"),
        cap_usd=1.0,
    )
    assert stopped and len(grades) == 2 and len(model.calls) == 2
