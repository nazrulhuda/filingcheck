import json
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from filingcheck.eval.questions import (
    CATEGORIES,
    METRICS,
    Question,
    QuestionFileError,
    load_questions,
    main,
    validate_files,
)

REPO = Path(__file__).resolve().parents[2]
TICKERS = {"AAPL", "WMT", "NVDA", "MSFT", "GS", "KO", "JPM", "MS"}

BASE: dict[str, Any] = {
    "id": "trap-001",
    "set": "trap",
    "category": "wrong_fiscal_year",
    "question": "What was Apple's total revenue in 2025?",
    "company": "AAPL",
    "fiscal_year": 2025,
    "metric": "revenue",
    "expected_behavior": "answer",
    "gold_value": None,
    "gold_unit": "USD",
    "tolerance_pct": 1.0,
    "gold_text": None,
    "trap_note": "Apple's FY2025 ended in late September 2025.",
}


def write(tmp_path: Path, rows: list[dict[str, Any]], name: str = "q.jsonl") -> Path:
    path = tmp_path / name
    path.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    return path


def test_the_twelve_metrics_and_all_categories_are_allowed() -> None:
    assert len(METRICS) == 12
    assert "stockholders_equity" in METRICS and "shares_outstanding" in METRICS
    assert {"prompt_injection", "control", "lookalike_company", "units_scale"} <= set(CATEGORIES)


def test_a_valid_question_loads() -> None:
    question = Question.model_validate(BASE)
    assert (question.company, question.fiscal_year, question.metric) == ("AAPL", 2025, "revenue")


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("category", "made_up_category"),
        ("metric", "ebitda"),
        ("set", "practice"),
        ("expected_behavior", "guess"),
        ("tolerance_pct", -1),
        ("id", "Trap 1"),
    ],
)
def test_values_outside_the_allowed_lists_are_rejected(field: str, value: object) -> None:
    with pytest.raises(ValidationError):
        Question.model_validate(dict(BASE, **{field: value}))


def test_a_gold_value_needs_a_unit() -> None:
    with pytest.raises(ValidationError, match="gold_unit"):
        Question.model_validate(dict(BASE, gold_value=391_035_000_000, gold_unit=None))


def test_a_control_question_belongs_to_the_control_set() -> None:
    with pytest.raises(ValidationError, match="control"):
        Question.model_validate(dict(BASE, category="control", set="trap"))


def test_load_questions_reports_the_line_of_a_bad_row(tmp_path: Path) -> None:
    path = write(tmp_path, [BASE, dict(BASE, id="trap-002", metric="ebitda")])
    with pytest.raises(QuestionFileError, match=r"q\.jsonl:2"):
        load_questions(path, TICKERS)


def test_an_unknown_company_is_rejected(tmp_path: Path) -> None:
    path = write(tmp_path, [dict(BASE, company="TSLA")])
    with pytest.raises(QuestionFileError, match="TSLA"):
        load_questions(path, TICKERS)


def test_ids_must_be_unique_across_files(tmp_path: Path) -> None:
    write(tmp_path, [BASE], "a.jsonl")
    write(tmp_path, [BASE], "b.jsonl")
    with pytest.raises(QuestionFileError, match="trap-001"):
        validate_files(sorted(tmp_path.glob("*.jsonl")), TICKERS)


def test_the_example_file_is_valid() -> None:
    files = sorted((REPO / "eval" / "questions").glob("*.jsonl"))
    assert files, "eval/questions has no .jsonl files"
    counts = validate_files(files, TICKERS | {"KO"})
    assert counts["examples.jsonl"] == 6


def test_the_examples_cover_the_categories_they_should() -> None:
    rows = load_questions(REPO / "eval" / "questions" / "examples.jsonl", TICKERS)
    assert {q.category for q in rows} == {
        "lookalike_company",
        "wrong_fiscal_year",
        "relative_year",
        "units_scale",
        "metric_not_supported",
        "control",
    }


def test_the_command_line_validates_the_real_files(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["validate"]) == 0
    assert "examples.jsonl: 6 questions" in capsys.readouterr().out


def test_the_command_line_fails_on_a_bad_file(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    write(tmp_path, [dict(BASE, metric="ebitda")])
    assert main(["validate", "--dir", str(tmp_path)]) == 1
    assert "q.jsonl:1" in capsys.readouterr().out
