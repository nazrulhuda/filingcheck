"""Citations in an answer, and whether any figure in it goes uncited."""

import re

from pydantic import BaseModel

from filingcheck.retrieval import Hit

QUOTE_CHARS = 200
# Parsing reads a copy of the answer with these mapped; the answer itself is kept as returned.
# Hyphen, non-breaking hyphen, figure dash, en dash and minus sign become "-". The em dash
# separates words, so it becomes a space: as "-" it would glue "grew" to "12%" and hide
# the figure. No-break, figure, thin and narrow no-break spaces become a plain space. The
# lenticular brackets gpt-oss sometimes writes around citations become square brackets.
NORMALIZE = str.maketrans(
    dict.fromkeys((0x2010, 0x2011, 0x2012, 0x2013, 0x2212), "-")
    | dict.fromkeys((0x2014, 0x00A0, 0x2007, 0x2009, 0x202F), " ")
    | {0x3010: "[", 0x3011: "]"}
)
# One citation bracket: passages as [1], [1, 3] or [1-3], and the agent's facts from
# get_financial_fact as [F1] or [F1, F2]; one bracket may hold both ([1, F2]), and each part
# is read as written, so in [F1, 2] the 2 is passage 2. [1][3] is two matches.
_PART = r"F?\d+(?:\s*-\s*\d+)?"
CITATION_RE = re.compile(r"\[\s*(" + _PART + r"(?:\s*,\s*" + _PART + r")*)\s*\]")
RANGE_RE = re.compile(r"\s*-\s*")


def _parts(text: str, *, facts: bool) -> list[tuple[int, int]]:
    """The (low, high) bounds of each cited part: fact parts ([Fn]) or passage parts ([n])."""
    bounds: list[tuple[int, int]] = []
    for match in CITATION_RE.finditer(normalize_text(text)):
        for part in match.group(1).split(","):
            part = part.strip()
            if part.startswith("F") != facts:
                continue
            numbers = [int(n) for n in RANGE_RE.split(part.removeprefix("F"))]
            bounds.append((min(numbers), max(numbers)))
    return bounds


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
        r"\b(?:Items?|Notes?)\s+\d+[A-Z]?(?:\s*(?:,|and|or|&|-|through|to)\s*\d+[A-Z]?)*\b",
        re.IGNORECASE,
    ),
    re.compile(r"\b[A-Za-z]+-?\d[\w-]*"),  # digits glued to letters: Q3, FY2025, COVID-19
    re.compile(r"\b\d+(?:st|nd|rd|th)\b"),  # ordinals
    re.compile(r"(?<![\d$.,])(?:199\d|20[0-3]\d)(?![\d%]|[.,]\d)"),  # a year standing alone
]
DIGIT_RE = re.compile(r"\d")


def normalize_text(text: str) -> str:
    """A copy of the text with Unicode dashes and spaces mapped for parsing (see NORMALIZE)."""
    return text.translate(NORMALIZE)


class Citation(BaseModel):
    """A passage the answer cites, with where it came from.

    `number` is the passage's number in the prompt, the n of the answer's [n] markers.
    """

    number: int
    chunk_id: int
    ticker: str
    fiscal_year: int
    item: str
    source_url: str
    quote: str  # the passage's first 200 characters


def cited_numbers(text: str, passages: int) -> list[int]:
    """The passage numbers cited in the text, in first-cited order, within 1..passages."""
    numbers: list[int] = []
    for low, high in _parts(text, facts=False):
        numbers.extend(range(max(low, 1), min(high, passages) + 1))
    return list(dict.fromkeys(numbers))


def parse_fact_citations(text: str, facts: int) -> list[int]:
    """The fact numbers cited as [Fn] in the text, in first-cited order, within 1..facts."""
    numbers: list[int] = []
    for low, high in _parts(text, facts=True):
        numbers.extend(range(max(low, 1), min(high, facts) + 1))
    return list(dict.fromkeys(numbers))


def parse_citations(text: str, hits: list[Hit]) -> list[Citation]:
    """Citations for the passages the text cites; numbers that point to no passage are dropped."""
    return [
        Citation(
            number=n,
            chunk_id=hit.chunk_id,
            ticker=hit.ticker,
            fiscal_year=hit.fiscal_year,
            item=hit.item,
            source_url=hit.source_url,
            quote=hit.text[:QUOTE_CHARS],
        )
        for n, hit in ((n, hits[n - 1]) for n in cited_numbers(text, len(hits)))
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


def _cites_something(sentence: str, passages: int | None, facts: int | None) -> bool:
    """True if a citation in the sentence points to a passage or fact that exists.

    Without the counts any citation mark counts; with them, [9] among 4 passages or [F3]
    among 1 fact is no citation.
    """
    for low, high in _parts(sentence, facts=False):
        if passages is None or any(1 <= n <= passages for n in range(low, high + 1)):
            return True
    for low, high in _parts(sentence, facts=True):
        if facts is None or any(1 <= n <= facts for n in range(low, high + 1)):
            return True
    return False


def has_uncited_claims(text: str, *, passages: int | None = None, facts: int | None = None) -> bool:
    """True if any sentence states a figure without a citation ([n] or [Fn]) in that sentence.

    Given the number of passages and facts the answer could cite, a mark that points to
    none of them is no citation, so its figure is uncited.
    """
    return any(
        has_figure(s) and not _cites_something(s, passages, facts)
        for s in sentences(normalize_text(text))
    )
