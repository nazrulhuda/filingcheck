"""The retrieval eval: questions with a known answer chunk, and how a ranking is scored.

Every ranking is scored two ways. "Text found": the hit is from the question's company and
is the expected chunk or contains the question's `must_contain` phrase (so a neighbouring
chunk that overlaps the expected one also counts), in any fiscal year. "Right year": the
same, and the fiscal year matches too. About a quarter of the chunks have an identical copy
in another year's filing, and identical texts tie in a search without a year filter, so
the gap between the two scores is how often search alone cannot pick the year.
"""

import json
import re
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from filingcheck.eval.questions import QuestionFileError
from filingcheck.retrieval.models import Hit

WORD_RE = re.compile(r"[a-z0-9]+")


class RetrievalQuestion(BaseModel):
    """One question and where its answer is: a stable chunk key plus a phrase from it."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(pattern=r"^ret-\d{3}$")
    source: Literal["synthetic", "hand"]
    question: str = Field(min_length=10)
    ticker: str
    fiscal_year: int
    item: str
    accession: str
    chunk_index: int  # with accession and item, identifies the chunk across reloads
    must_contain: str = Field(min_length=8)
    expected_chunk_id: int | None = None  # the database id when the question was written


def load_retrieval_questions(path: Path, tickers: set[str]) -> list[RetrievalQuestion]:
    """Read and check the retrieval questions: valid rows, known companies, unique ids."""
    questions: list[RetrievalQuestion] = []
    seen: set[str] = set()
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        where = f"{path.name}:{number}"
        try:
            question = RetrievalQuestion.model_validate(json.loads(line))
        except (json.JSONDecodeError, ValidationError) as exc:
            raise QuestionFileError(f"{where}: {exc}") from exc
        if question.ticker not in tickers:
            raise QuestionFileError(f"{where}: unknown company {question.ticker}")
        if question.id in seen:
            raise QuestionFileError(f"{where}: id {question.id} is used twice")
        seen.add(question.id)
        questions.append(question)
    return questions


def _normal(text: str) -> str:
    return " ".join(text.split())


def is_hit(
    hit: Hit, question: RetrievalQuestion, expected_id: int | None, *, right_year: bool
) -> bool:
    """Whether a hit answers the question.

    "Text found" (`right_year=False`): the company matches, and the hit is the expected chunk
    or contains the phrase, in any fiscal year. "Right year" also needs the fiscal year.
    """
    if hit.ticker != question.ticker:
        return False
    if right_year and hit.fiscal_year != question.fiscal_year:
        return False
    return hit.chunk_id == expected_id or _normal(question.must_contain) in _normal(hit.text)


def recall_at(
    hits: list[Hit],
    question: RetrievalQuestion,
    expected_id: int | None,
    k: int,
    *,
    right_year: bool,
) -> float:
    """1.0 if a hit in the top k answers the question, else 0.0."""
    return (
        1.0
        if any(is_hit(h, question, expected_id, right_year=right_year) for h in hits[:k])
        else 0.0
    )


def reciprocal_rank(
    hits: list[Hit], question: RetrievalQuestion, expected_id: int | None, *, right_year: bool
) -> float:
    """1 / the rank of the first hit that answers the question, or 0.0."""
    for rank, hit in enumerate(hits, start=1):
        if is_hit(hit, question, expected_id, right_year=right_year):
            return 1.0 / rank
    return 0.0


def longest_shared_run(question: str, chunk_text: str) -> int:
    """The longest run of consecutive words the question shares with its chunk.

    Questions are written in a user's words; a long shared run would flatter keyword search.
    """
    a = WORD_RE.findall(question.lower())
    b = WORD_RE.findall(chunk_text.lower())
    best = 0
    previous = [0] * (len(b) + 1)
    for x in a:
        current = [0] * (len(b) + 1)
        for j, y in enumerate(b, start=1):
            if x == y:
                current[j] = previous[j - 1] + 1
                best = max(best, current[j])
        previous = current
    return best
