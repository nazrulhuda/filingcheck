"""The retrieval eval: questions with a known answer chunk, and how a ranking is scored.

A hit counts only if its company and fiscal year are the question's, and then if it is the
expected chunk or contains the question's `must_contain` phrase (so a neighbouring chunk
that overlaps the expected one also counts). Many chunk texts repeat word for word from
one year to the next, so without the company-and-year test a FY2023 chunk could "answer"
a FY2024 question.
"""

import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

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


def _normal(text: str) -> str:
    return " ".join(text.split())


def is_hit(hit: Hit, question: RetrievalQuestion, expected_id: int | None) -> bool:
    """Whether a hit answers the question (same company and year, right chunk or phrase)."""
    if (hit.ticker, hit.fiscal_year) != (question.ticker, question.fiscal_year):
        return False
    return hit.chunk_id == expected_id or _normal(question.must_contain) in _normal(hit.text)


def recall_at(
    hits: list[Hit], question: RetrievalQuestion, expected_id: int | None, k: int
) -> float:
    """1.0 if a hit in the top k answers the question, else 0.0."""
    return 1.0 if any(is_hit(h, question, expected_id) for h in hits[:k]) else 0.0


def reciprocal_rank(hits: list[Hit], question: RetrievalQuestion, expected_id: int | None) -> float:
    """1 / the rank of the first hit that answers the question, or 0.0."""
    for rank, hit in enumerate(hits, start=1):
        if is_hit(hit, question, expected_id):
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
