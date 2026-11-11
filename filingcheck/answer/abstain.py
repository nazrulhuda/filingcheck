"""The abstain sentence the prompts ask for, and whether an answer is that sentence.

Kept apart from the baseline so the grader and the number labeler can read it without
importing the answering code.
"""

import re

from filingcheck.answer.citations import normalize_text

ABSTAIN = "I can't find this in the filings I have."
QUOTES = str.maketrans({"\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"'})
EMPHASIS_RE = re.compile(r"[*_`]")


def _normalize(text: str) -> str:
    text = EMPHASIS_RE.sub("", normalize_text(text).translate(QUOTES))
    return " ".join(text.split()).lower().rstrip(".!?").strip()


def is_abstain(text: str) -> bool:
    """True if the answer is the abstain sentence and nothing else, whatever its formatting."""
    return _normalize(text) == _normalize(ABSTAIN)
