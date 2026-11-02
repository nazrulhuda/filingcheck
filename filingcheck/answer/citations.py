"""Citations in an answer, and whether any figure in it goes uncited."""

import re

from pydantic import BaseModel

from filingcheck.retrieval import Hit

QUOTE_CHARS = 200
# [1], [1, 3], [1-3] and the same with an en dash; [1][3] is two matches.
CITATION_RE = re.compile(r"\[\s*(\d+(?:\s*[,\-\u2013]\s*\d+)*)\s*\]")
RANGE_RE = re.compile(r"\s*[\-\u2013]\s*")

# Abbreviations whose period never ends a sentence.
ABBREVIATIONS = (
    "U.S.",
    "U.K.",
    "Inc.",
    "Corp.",
    "Co.",
    "Ltd.",
    "No.",
    "e.g.",
    "i.e.",
    "approx.",
    "vs.",
)
ABBREVIATION_RE = re.compile(
    r"(?<![A-Za-z])(?:" + "|".join(re.escape(a) for a in ABBREVIATIONS) + ")", re.IGNORECASE
)
PROTECTED_PERIOD = "\x00"
# A sentence ends at . ! or ? followed by space, unless a citation follows ("$2 billion. [3]").
SENTENCE_END_RE = re.compile(r"(?<=[.!?])\s+(?!\[)")
# "1.", "2)", "(a)", "a)" or a bullet at the start of a line.
LIST_MARKER_RE = re.compile(r"^\s*(?:[-*+•]\s+)?(?:(?:\d{1,3}[.)]|\(\w{1,4}\)|[A-Za-z][.)])\s+)?")
MONTH = (
    r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|June?|July?|Aug(?:ust)?"
    r"|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
)
# Numbers that are not figures, removed in this order before looking for digits.
NOT_FIGURES = [
    CITATION_RE,
    re.compile(MONTH + r"\.?\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4}\b"),  # January 31, 2025
    re.compile(r"\b\d{4}-\d{2}-\d{2}\b"),  # 2025-01-31
    re.compile(r"\b\d{1,2}/\d{1,2}/\d{2,4}\b"),  # 1/31/2025
    re.compile(r"\b(?:10-K|10-Q|8-K)(?:/A)?\b"),  # SEC form names
    re.compile(  # Item 7, Items 1A and 7A, Note 8
        r"\b(?:Items?|Notes?)\s+\d+[A-Z]?(?:\s*(?:,|and|or|&|-|\u2013|through|to)\s*\d+[A-Z]?)*\b",
        re.IGNORECASE,
    ),
    re.compile(r"\b[A-Za-z]+-?\d[\w-]*"),  # digits glued to letters: Q3, FY2025, COVID-19
    re.compile(r"\b\d+(?:st|nd|rd|th)\b"),  # ordinals
    re.compile(r"(?<![\d$.,])(?:199\d|20[0-3]\d)(?![\d%]|[.,]\d)"),  # a year standing alone
]
DIGIT_RE = re.compile(r"\d")


class Citation(BaseModel):
    """A passage the answer cites, with where it came from."""

    chunk_id: int
    ticker: str
    fiscal_year: int
    item: str
    source_url: str
    quote: str  # the passage's first 200 characters


def cited_numbers(text: str, passages: int) -> list[int]:
    """The passage numbers cited in the text, in first-cited order, within 1..passages."""
    numbers: list[int] = []
    for match in CITATION_RE.finditer(text):
        for part in match.group(1).split(","):
            bounds = [int(n) for n in RANGE_RE.split(part.strip())]
            low, high = min(bounds), max(bounds)
            numbers.extend(range(max(low, 1), min(high, passages) + 1))
    return list(dict.fromkeys(numbers))


def parse_citations(text: str, hits: list[Hit]) -> list[Citation]:
    """Citations for the passages the text cites; numbers that point to no passage are dropped."""
    return [
        Citation(
            chunk_id=hit.chunk_id,
            ticker=hit.ticker,
            fiscal_year=hit.fiscal_year,
            item=hit.item,
            source_url=hit.source_url,
            quote=hit.text[:QUOTE_CHARS],
        )
        for hit in (hits[n - 1] for n in cited_numbers(text, len(hits)))
    ]


def sentences(text: str) -> list[str]:
    """Each line split into sentences, list markers removed; abbreviations never end one."""
    result: list[str] = []
    for line in text.splitlines():
        line = LIST_MARKER_RE.sub("", line, count=1)
        line = ABBREVIATION_RE.sub(lambda m: m.group(0).replace(".", PROTECTED_PERIOD), line)
        result.extend(
            s.replace(PROTECTED_PERIOD, ".") for s in SENTENCE_END_RE.split(line) if s.strip()
        )
    return result


def has_figure(sentence: str) -> bool:
    """True if the sentence has a number that is not a year, date, form, label or the like."""
    for pattern in NOT_FIGURES:
        sentence = pattern.sub(" ", sentence)
    return DIGIT_RE.search(sentence) is not None


def has_uncited_claims(text: str) -> bool:
    """True if any sentence states a figure without a citation in that sentence."""
    return any(has_figure(s) and not CITATION_RE.search(s) for s in sentences(text))
