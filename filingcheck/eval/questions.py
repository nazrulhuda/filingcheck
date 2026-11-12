"""The evaluation question format, and a validator for the JSONL question files.

Question files live in `eval/questions/*.jsonl`, one question per line. Run
`make validate-questions` to check them all.
"""

import argparse
import json
import sys
from datetime import date
from pathlib import Path
from typing import Literal, Self, get_args

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from filingcheck.facts.metrics import Metric
from filingcheck.paths import DATA_DIR, REPO_ROOT

# The metric names come from the one metric map (13 metrics, with pretax_income).
Category = Literal[
    "lookalike_company",  # "Morgan": Morgan Stanley or JPMorgan?
    "wrong_fiscal_year",  # a calendar year that is not the company's fiscal year
    "relative_year",  # "last year" with no year given
    "units_scale",  # thousands vs millions vs billions
    "segment_vs_total",  # one segment's figure vs the company total
    "metric_not_supported",  # a metric or period outside the dataset, such as a quarter
    "prompt_injection",  # the question tries to change the agent's rules
    "unanswerable_text",  # the filings do not say: a reason, a forecast, an undisclosed detail
    "control",  # a normal, clean question
]
QuestionSet = Literal["trap", "control"]
# FinanceBench's three question styles; control questions are written in one of them.
Style = Literal["metrics-generated", "domain-relevant", "novel-generated"]
Behavior = Literal["answer", "clarify", "refuse"]
# Where a gold value came from: the filing's XBRL facts through the lookup
# (`python -m filingcheck.eval gold`), or a person; a person's value is never overwritten.
GoldSource = Literal["facts", "hand"]

METRICS: tuple[str, ...] = get_args(Metric)
CATEGORIES: tuple[str, ...] = get_args(Category)
QUESTIONS_DIR = REPO_ROOT / "eval" / "questions"


class PageFilter(BaseModel):
    """The company and fiscal year a question is asked with, as the page's filters send them."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    ticker: str | None = None
    fiscal_year: int | None = Field(default=None, ge=1990, le=2100)

    @model_validator(mode="after")
    def _year_needs_company(self) -> Self:
        # The page lists the chosen company's years, so it never sends a year on its own.
        if self.fiscal_year is not None and self.ticker is None:
            raise ValueError("a page filter's fiscal year needs a company, as on the page")
        return self


class AlsoAccept(BaseModel):
    """A second answer a question accepts, when its writer's note accepts two.

    An alternative behavior (`refuse` where the main one is `answer`), an alternative gold value
    with its own fiscal year (filled from the facts like the main one), or a `note` describing an
    acceptable answer the deterministic grader cannot check, which the LLM grader decides.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    expected_behavior: Behavior | None = None
    fiscal_year: int | None = Field(default=None, ge=1990, le=2100)
    gold_value: int | float | None = None
    gold_unit: str | None = None
    gold_source: GoldSource | None = None
    gold_concept: str | None = None
    gold_accession: str | None = None
    gold_period_start: date | None = None
    gold_period_end: date | None = None
    gold_instant: date | None = None
    note: str | None = None

    @model_validator(mode="after")
    def _says_something(self) -> Self:
        if self.expected_behavior is None and self.fiscal_year is None and not self.note:
            raise ValueError("also_accept needs a behavior, a fiscal year or a note")
        if self.gold_value is not None and (self.fiscal_year is None or not self.gold_unit):
            raise ValueError("an also_accept gold value needs its fiscal year and unit")
        if self.gold_source is not None and self.gold_value is None:
            raise ValueError("also_accept gold_source is set but gold_value is not")
        return self


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
    gold_source: GoldSource | None = None
    # Filled with a value from the facts: the fact's tag, filing and period.
    gold_concept: str | None = None
    gold_accession: str | None = None
    gold_period_start: date | None = None
    gold_period_end: date | None = None
    gold_instant: date | None = None
    # The same metric for the company's other pinned years, so the grader can tell a
    # number from another year (other_year_number) from a wrong one.
    gold_other_years: dict[int, int | float] | None = None
    tolerance_pct: float = Field(default=1.0, ge=0)
    gold_text: str | None = None
    trap_note: str | None = None
    style: Style | None = None  # control questions only
    page_filter: PageFilter | None = None  # asked with these page filters (the batch runner too)
    also_accept: AlsoAccept | None = None  # a second answer the writer's note accepts

    @model_validator(mode="after")
    def _consistent(self) -> Self:
        if self.gold_value is not None and not self.gold_unit:
            raise ValueError("gold_unit is required when gold_value is set")
        if self.gold_source is not None and self.gold_value is None:
            raise ValueError("gold_source is set but gold_value is not")
        if (self.category == "control") != (self.set == "control"):
            raise ValueError("a control question has set 'control' and category 'control'")
        if (self.style is not None) != (self.set == "control"):
            raise ValueError("style is required for control questions and not allowed otherwise")
        also = self.also_accept
        if also is not None and also.expected_behavior == self.expected_behavior:
            raise ValueError("also_accept's behavior is the same as the main one")
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
        page = question.page_filter
        if page is not None and page.ticker is not None and page.ticker not in tickers:
            raise QuestionFileError(f"{where}: unknown page filter company {page.ticker}")
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
    from filingcheck.eval.retrieval import load_retrieval_questions

    paths = sorted(args.dir.glob("*.jsonl"))
    retrieval = [p for p in paths if p.name.startswith("retrieval")]  # their own format
    paths = [p for p in paths if not p.name.startswith("page_")]  # the page examples, not eval
    try:
        counts = validate_files([p for p in paths if p not in retrieval], tickers)
        for path in retrieval:
            counts[path.name] = len(load_retrieval_questions(path, tickers))
    except QuestionFileError as exc:
        print(f"invalid: {exc}")
        return 1
    for name, count in counts.items():
        print(f"{name}: {count} questions")
    print(f"{sum(counts.values())} questions in {len(counts)} files, all valid")
    return 0


if __name__ == "__main__":
    sys.exit(main())
