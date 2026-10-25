"""The evaluation question format, and a validator for the JSONL question files.

Question files live in `eval/questions/*.jsonl`, one question per line. Run
`make validate-questions` to check them all.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Literal, Self, get_args

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from filingcheck.paths import DATA_DIR, REPO_ROOT

Metric = Literal[
    "revenue",
    "net_income",
    "diluted_eps",
    "operating_income",
    "total_assets",
    "total_liabilities",
    "stockholders_equity",
    "operating_cash_flow",
    "capital_expenditures",
    "cash_and_equivalents",
    "long_term_debt",
    "shares_outstanding",
]
Category = Literal[
    "lookalike_company",  # "Morgan": Morgan Stanley or JPMorgan?
    "wrong_fiscal_year",  # a calendar year that is not the company's fiscal year
    "relative_year",  # "last year" with no year given
    "units_scale",  # thousands vs millions vs billions
    "segment_vs_total",  # one segment's figure vs the company total
    "metric_not_supported",  # a metric or period outside the dataset, such as a quarter
    "prompt_injection",  # the question tries to change the agent's rules
    "control",  # a normal, clean question
]
QuestionSet = Literal["trap", "control", "financebench"]
Behavior = Literal["answer", "clarify", "refuse"]

METRICS: tuple[str, ...] = get_args(Metric)
CATEGORIES: tuple[str, ...] = get_args(Category)
QUESTIONS_DIR = REPO_ROOT / "eval" / "questions"


class Question(BaseModel):
    """One evaluation question and what a correct answer looks like."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(pattern=r"^[a-z]+-\d{3,}$")
    set: QuestionSet
    category: Category
    question: str = Field(min_length=10)
    company: str | None  # the ticker the question should resolve to; null if ambiguous on purpose
    fiscal_year: int | None = Field(ge=1990, le=2100)
    metric: Metric | None
    expected_behavior: Behavior
    gold_value: int | float | None = None  # raw units, as filed (dollars, not millions)
    gold_unit: str | None = None
    tolerance_pct: float = Field(default=1.0, ge=0)
    gold_text: str | None = None
    trap_note: str | None = None

    @model_validator(mode="after")
    def _consistent(self) -> Self:
        if self.gold_value is not None and not self.gold_unit:
            raise ValueError("gold_unit is required when gold_value is set")
        if (self.category == "control") != (self.set == "control"):
            raise ValueError("a control question has set 'control' and category 'control'")
        return self


class QuestionFileError(ValueError):
    """A question file has a bad line; the message names the file and line."""


def load_questions(path: Path, tickers: set[str]) -> list[Question]:
    """Read and validate one JSONL question file; companies must be in the dataset."""
    questions: list[Question] = []
    lines = path.read_text(encoding="utf-8").splitlines()
    for number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        where = f"{path.name}:{number}"
        try:
            question = Question.model_validate(json.loads(line))
        except (json.JSONDecodeError, ValidationError) as exc:
            raise QuestionFileError(f"{where}: {exc}") from exc
        if question.company is not None and question.company not in tickers:
            raise QuestionFileError(f"{where}: unknown company {question.company}")
        questions.append(question)
    return questions


def validate_files(paths: list[Path], tickers: set[str]) -> dict[str, int]:
    """Validate every file and check ids are unique across them; return questions per file."""
    counts: dict[str, int] = {}
    seen: dict[str, str] = {}
    for path in paths:
        questions = load_questions(path, tickers)
        for question in questions:
            if question.id in seen:
                raise QuestionFileError(
                    f"{path.name}: id {question.id} is already used in {seen[question.id]}"
                )
            seen[question.id] = path.name
        counts[path.name] = len(questions)
    return counts


def main(argv: list[str] | None = None) -> int:
    """`python -m filingcheck.eval.questions validate`: check every question file."""
    from filingcheck.ingest.companies import load_companies

    parser = argparse.ArgumentParser(prog="python -m filingcheck.eval.questions")
    commands = parser.add_subparsers(dest="command", required=True)
    validate = commands.add_parser("validate", help="check every .jsonl question file")
    validate.add_argument("--dir", type=Path, default=QUESTIONS_DIR)
    args = parser.parse_args(argv)
    tickers = {c.ticker for c in load_companies(DATA_DIR / "companies.yaml")}
    paths = sorted(args.dir.glob("*.jsonl"))
    try:
        counts = validate_files(paths, tickers)
    except QuestionFileError as exc:
        print(f"invalid: {exc}")
        return 1
    for name, count in counts.items():
        print(f"{name}: {count} questions")
    print(f"{sum(counts.values())} questions in {len(counts)} files, all valid")
    return 0


if __name__ == "__main__":
    sys.exit(main())
