"""The abstain sentence the prompts ask for, and whether an answer is that sentence.

Kept apart from the baseline so the grader and the number labeler can read it without
importing the answering code.
"""

import re

from filingcheck.answer.citations import has_figure, normalize_text, sentences

ABSTAIN = "I can't find this in the filings I have."
QUOTES = str.maketrans({"\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"'})
EMPHASIS_RE = re.compile(r"[*_`]")


def _normalize(text: str) -> str:
    text = EMPHASIS_RE.sub("", normalize_text(text).translate(QUOTES))
    return " ".join(text.split()).lower().rstrip(".!?").strip()


# A sentence that says the answer is not there, in the words the model writes: "I can't find
# ...", "I couldn't find ...", "I'm not able to locate ...", "The filings I have don't say".
DECLINE_SENTENCE_RE = re.compile(
    r"\b(?:can't|cannot|can not|couldn't|could not|unable to|not able to|wasn't able to)\s+"
    r"(?:\w+\s+){0,2}?(?:find|locate|calculate|determine|provide|give|answer)\b"
    r"|\bfilings?(?: i have)? (?:don't|do not|doesn't|does not) (?:\w+ )?"
    r"(?:include|contain|provide|report|say|give|show|break out|state|mention|disclose)\b",
    re.IGNORECASE,
)


def is_abstain(text: str) -> bool:
    """True if the answer only says it cannot find the answer.

    That is the abstain sentence, whatever its formatting, or an answer every sentence of which
    is a decline in the model's own words ("I can't find this information in the filings I
    have.") with no figure in it. A decline followed by what the filing does say, or by a
    figure, is not an abstention.
    """
    if _normalize(text) == _normalize(ABSTAIN):
        return True
    parts = sentences(normalize_text(text).translate(QUOTES))
    if not parts or any(has_figure(part) for part in parts):
        return False
    return all(DECLINE_SENTENCE_RE.search(part) for part in parts)
