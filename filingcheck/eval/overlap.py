"""Word overlap between questions, so new evaluation questions do not copy old ones.

Overlap is the share of distinct words two questions have in common (Jaccard): the shared
words over all the words of either. Words are compared lower-case, without punctuation or a
possessive "'s". A new question is flagged when its overlap with any older question is above
the threshold (0.6 for the Week 5 sets); `eval/check_overlap.py` gathers the older questions.
"""

import re
from collections.abc import Mapping

from pydantic import BaseModel

APOSTROPHES = str.maketrans({chr(0x2019): "'", chr(0x2018): "'"})  # curly to straight
WORD_RE = re.compile(r"[a-z0-9&]+(?:'[a-z]+)?")


class Flag(BaseModel):
    """A new question too close to an older one."""

    id: str
    question: str
    reference: str  # the closest older question
    source: str  # where the older question comes from
    score: float


def words(text: str) -> set[str]:
    """The question's distinct words: lower-case, no punctuation, no possessive "'s"."""
    found = WORD_RE.findall(text.translate(APOSTROPHES).lower())
    return {w.removesuffix("'s") for w in found}


def overlap(a: str, b: str) -> float:
    """Shared distinct words over all distinct words of either question."""
    left, right = words(a), words(b)
    union = left | right
    return len(left & right) / len(union) if union else 0.0


def flagged(
    new: Mapping[str, str], references: Mapping[str, str], threshold: float = 0.6
) -> list[Flag]:
    """Each new question (id to text) whose closest older question overlaps above `threshold`."""
    flags: list[Flag] = []
    for qid, question in new.items():
        best = max(
            ((overlap(question, ref), ref) for ref in references),
            default=(0.0, ""),
            key=lambda x: x[0],
        )
        if best[0] > threshold:
            flags.append(
                Flag(
                    id=qid,
                    question=question,
                    reference=best[1],
                    source=references[best[1]],
                    score=round(best[0], 3),
                )
            )
    return flags
