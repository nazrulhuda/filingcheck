"""Cut each 10-K Item into overlapping chunks for search, and drop chunks that are noise.

Chunks never cross Items. Character offsets point into the cleaned Item text saved under
`data/sections/`, so every chunk can be traced back to the exact place it came from.
"""

import re
from collections import Counter
from collections.abc import Sequence
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

CHUNK_SIZE = 1100  # characters: about one long paragraph
OVERLAP = 200  # characters repeated at the start of the next chunk
MIN_CHUNK_CHARS = 200
MAX_SYMBOL_SHARE = 0.5  # more digits and punctuation than letters: a table, not prose
TOC_MIN_LINES = 3
CONTENTS_MIN_LINES = 10  # a contents list without "Item" labels: page numbers on their own lines
CONTENTS_SHORT_SHARE = 0.4
REPEAT_MIN = 5  # a short line seen this often in one Item is a page header or footer
REPEAT_MAX_LEN = 120
# No-break, narrow no-break, thin and figure spaces become plain spaces; zero-width ones go.
SPACE_CHARS = str.maketrans(
    {chr(0xA0): " ", chr(0x202F): " ", chr(0x2009): " ", chr(0x2007): " ", chr(0x200B): ""}
)

TOC_LINE_RE = re.compile(
    r"^[ \t]*(?:part[ \t]+[ivx]+[ \t]*[,.]?[ \t]*)?item[ \t]+\d{1,2}[a-c]?\b.*?"
    r"[ \t](?:\d{1,3}|[ivx]{1,4})[ \t]*$",
    re.IGNORECASE | re.MULTILINE,
)
EDGE_NUMBERS_RE = re.compile(r"^[\s\d|.\-]+|[\s\d|.\-]+$")
BLANK_RUN_RE = re.compile(r"\n{3,}")
# Page furniture between paragraphs, removed before split sentences are rejoined.
PAGE_NUMBER_RE = re.compile(r"\d{1,3}")
TABLE_OF_CONTENTS_RE = re.compile(r"table of contents[:.]?", re.IGNORECASE)
# A sentence ends with . ? ! : or ;, possibly followed by a closing quote or bracket.
CLOSERS = "\"')]" + chr(0x201D) + chr(0x2019)
SENTENCE_END_RE = re.compile(r"[.?!:;][" + re.escape(CLOSERS) + r"]*$")
SENTENCE_MARK_RE = re.compile(r"[.,;:]")
SHORT_LINE = 80  # a single line this short with no punctuation may be a heading or label
LABEL_MAX_WORDS = 3  # "iPhone", "Total net sales": a label, not half a sentence
PAGE_FOOTER_RE = re.compile(r"\s\d{1,3}$")  # "2023 Annual Report  13"
FOOTNOTE_START_RE = re.compile(r"\(\d+\)|\*")  # "(3) As of end of period"
LETTER_RE = re.compile(r"[A-Za-z]")
ITEM_ORDER = ("1", "1A", "7", "7A", "8", "1-7A")  # "1-7A": Items not separable

Boundary = Literal["exact", "approximate"]
SharedSpan = tuple[int, int, list[str]]  # (start, end, other Items) in an Item's saved text


class Chunk(BaseModel):
    """One searchable piece of a 10-K Item."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    ticker: str
    cik: str
    fiscal_year: int
    accession: str
    item: str
    chunk_index: int
    char_start: int
    char_end: int
    text: str
    # Other Items of the same filing that contain this text; it is stored once, under `item`.
    also_in: list[str] = Field(default_factory=list)
    # "approximate" when the 10-K maps Items to pages through its own index, so the section's
    # edges are where those pages begin and end rather than at a heading.
    boundary: Boundary = "exact"


class TableChunk(BaseModel):
    """One number table set aside from the prose; kept for numbers XBRL does not have."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    ticker: str
    fiscal_year: int
    accession: str
    item: str | None  # None when the table is outside the Items that are kept
    table_index: int
    source_url: str  # the 10-K or the Exhibit 13 that holds the table
    position: int  # character offset of the table in that document
    text: str  # one row per line, "label: value | value"


def _line_key(line: str) -> str:
    # Page numbers sit at the start or end of a header line, so they are ignored there.
    return EDGE_NUMBERS_RE.sub("", line.strip().lower())


def strip_repeated_lines(
    text: str, min_repeats: int = REPEAT_MIN, max_len: int = REPEAT_MAX_LEN
) -> str:
    """Remove short lines that repeat on many pages, such as "Apple Inc. | 2025 Form 10-K | 21"."""
    lines = text.split("\n")
    counts = Counter(_line_key(line) for line in lines if line.strip())

    def repeated(line: str) -> bool:
        key = _line_key(line)
        return (
            bool(line.strip())
            and len(line.strip()) <= max_len
            and counts[key] >= min_repeats
            and any(ch.isalpha() for ch in key)
        )

    return "\n".join(line for line in lines if not repeated(line))


def _is_page_furniture(paragraph: str) -> bool:
    """A page number or a "Table of Contents" link left on its own between paragraphs."""
    return bool(PAGE_NUMBER_RE.fullmatch(paragraph) or TABLE_OF_CONTENTS_RE.fullmatch(paragraph))


def _ends_unfinished(paragraph: str) -> bool:
    """Whether a paragraph stops mid-sentence and is not a heading, label, footer or footnote.

    Headings ("Interest Rate Risk"), product labels ("iPhone"), page footers ("2023 Annual
    Report  13") and short footnotes ("(3) As of end of period") also lack a full stop, but
    the paragraph after them is not their continuation.
    """
    if SENTENCE_END_RE.search(paragraph):
        return False
    if "\n" in paragraph or SENTENCE_MARK_RE.search(paragraph) or len(paragraph) > SHORT_LINE:
        return True  # a long or punctuated paragraph: the end of a sentence's first half
    return not (
        paragraph[:1].isupper()  # a heading
        or len(paragraph.split()) <= LABEL_MAX_WORDS  # a product or table label
        or PAGE_FOOTER_RE.search(paragraph)
        or FOOTNOTE_START_RE.match(paragraph)
        or not LETTER_RE.search(paragraph)  # a rule line such as "________"
    )


def tidy_paragraphs(text: str) -> str:
    """Drop page numbers and "Table of Contents" lines, then rejoin sentences a page split.

    The furniture goes first, so the two halves of a sentence it separated can join. Two
    paragraphs join when the first stops mid-sentence and the second starts in lowercase.
    """
    paragraphs = [p for p in text.split("\n\n") if not _is_page_furniture(p.strip())]
    if paragraphs:
        first, _, rest = paragraphs[0].partition("\n")
        if TABLE_OF_CONTENTS_RE.fullmatch(first.strip()) and rest.strip():
            paragraphs[0] = rest  # a leading "Table of Contents" line above the heading
    joined: list[str] = []
    for paragraph in paragraphs:
        if joined and paragraph[:1].islower() and _ends_unfinished(joined[-1]):
            joined[-1] = f"{joined[-1]} {paragraph}"
        else:
            joined.append(paragraph)
    return "\n\n".join(joined)


def clean_item_text(text: str) -> str:
    """Clean an Item's text before it is saved and chunked.

    Plain spaces only; page headers, footers, page numbers, "Table of Contents" lines and
    blank runs removed; sentences split by a page break rejoined.
    """
    text = strip_repeated_lines(text.translate(SPACE_CHARS))
    text = "\n".join(line.rstrip() for line in text.split("\n"))
    text = BLANK_RUN_RE.sub("\n\n", text).strip()
    return tidy_paragraphs(text).strip()


def split_spans(text: str, size: int, overlap: int) -> list[tuple[int, int]]:
    """Cut text into windows of at most `size` characters that overlap by about `overlap`.

    Each window ends at a paragraph break if one falls in its second half, else at the end
    of a sentence, else between words.
    """
    spans: list[tuple[int, int]] = []
    start, length = 0, len(text)
    while start < length:
        end = min(start + size, length)
        if end < length:
            floor = start + size // 2
            cut = text.rfind("\n\n", floor, end)
            if cut == -1:
                period = max(text.rfind(". ", floor, end), text.rfind(".\n", floor, end))
                cut = period + 1 if period != -1 else -1
            if cut == -1:
                cut = text.rfind(" ", floor, end)
            if cut > start:
                end = cut
        spans.append((start, end))
        if end >= length:
            break
        resume = max(end - overlap, start + 1)
        space = text.find(" ", resume, end)  # start the overlap at a word boundary
        start = space + 1 if space != -1 and space + 1 < end else resume
    return spans


def junk_reason(text: str) -> str | None:
    """Why a chunk is noise ("short", "table" or "toc"), or None when it is worth keeping."""
    stripped = text.strip()
    if len(stripped) < MIN_CHUNK_CHARS:
        return "short"
    visible = [ch for ch in stripped if not ch.isspace()]
    symbols = sum(1 for ch in visible if not ch.isalpha())
    if symbols / len(visible) > MAX_SYMBOL_SHARE:
        return "table"
    if len(TOC_LINE_RE.findall(stripped)) >= TOC_MIN_LINES:
        return "toc"
    lines = [line.strip() for line in stripped.split("\n") if line.strip()]
    tiny = sum(1 for line in lines if len(line) <= 3)  # page numbers and section letters
    if len(lines) >= CONTENTS_MIN_LINES and tiny / len(lines) >= CONTENTS_SHORT_SHARE:
        return "toc"
    return None


def chunk_item(
    text: str,
    *,
    ticker: str,
    cik: str,
    fiscal_year: int,
    accession: str,
    item: str,
    shared: Sequence[SharedSpan] = (),
    boundary: Boundary = "exact",
) -> tuple[list[Chunk], Counter[str]]:
    """Chunk one Item's cleaned text; return the kept chunks and the count of dropped ones.

    `shared` marks passages of the text that also belong to other Items; a chunk overlapping
    one lists those Items in `also_in`.
    """
    chunks: list[Chunk] = []
    dropped: Counter[str] = Counter()
    for start, end in split_spans(text, CHUNK_SIZE, OVERLAP):
        while start < end and text[start].isspace():
            start += 1
        while end > start and text[end - 1].isspace():
            end -= 1
        piece = text[start:end]
        reason = junk_reason(piece)
        if reason:
            dropped[reason] += 1
            continue
        others = {other for s, e, items in shared if s < end and e > start for other in items}
        chunks.append(
            Chunk(
                ticker=ticker,
                cik=cik,
                fiscal_year=fiscal_year,
                accession=accession,
                item=item,
                chunk_index=len(chunks),
                char_start=start,
                char_end=end,
                text=piece,
                also_in=sorted(others - {item}, key=ITEM_ORDER.index),
                boundary=boundary,
            )
        )
    return chunks, dropped
