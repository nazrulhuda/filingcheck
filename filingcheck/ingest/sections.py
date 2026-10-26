"""Split each 10-K into the five Items we search: 1, 1A, 7, 7A and 8.

edgartools finds the Items first; a heading-based splitter is the fallback. Both run on the
downloaded HTML only and never reach the network. When a filing's Item 7 or 8 is missing
or very short, it usually says the content is "incorporated by reference" from the annual
report filed as Exhibit 13; then the exhibit is downloaded and the two Items come from it.
"""

import json
import re
from collections import Counter, defaultdict
from collections.abc import Iterator
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict

from filingcheck.ingest.chunking import (
    CHUNK_SIZE,
    Boundary,
    Chunk,
    SharedSpan,
    TableChunk,
    chunk_item,
    clean_item_text,
    junk_reason,
)
from filingcheck.ingest.filings import (
    ExtraDocument,
    Filing,
    Manifest,
    SecFetcher,
    write_atomic,
)
from filingcheck.ingest.sec_client import decode_document

ITEMS = ("1", "1A", "7", "7A", "8")
# In a page-indexed 10-K, sections that do not start at their own heading are kept together
# under one honest label instead of a label that may not fit the text.
MERGED_ITEM = "1-7A"
MERGED_LABEL = "10-K text, sections not separable"
ALL_ITEMS = (*ITEMS, MERGED_ITEM)
MERGEABLE_ITEMS = ("1", "1A", "7", "7A")
HEADING_WINDOW = 300
SHORT_ITEM_CHARS = 2000
EXHIBIT_ITEMS = ("7", "8")  # the Items an Exhibit 13 annual report can supply

EDGARTOOLS_KEYS = {
    "1": "part_i_item_1",
    "1A": "part_i_item_1a",
    "7": "part_ii_item_7",
    "7A": "part_ii_item_7a",
    "8": "part_ii_item_8",
}
INDEX_URL = "https://www.sec.gov/Archives/edgar/data/{cik}/{folder}/{accession}-index.htm"

HEADING_RE = re.compile(r"^[ \t]*item[ \t]+(\d{1,2}[a-c]?)\b", re.IGNORECASE | re.MULTILINE)
TRAILING_PART_RE = re.compile(r"(?:\n[ \t]*PART[ \t]+[IVX]+\b[^\n]*)+\s*$", re.IGNORECASE)
ROW_RE = re.compile(r"<tr[^>]*>(.*?)</tr>", re.IGNORECASE | re.DOTALL)
CELL_RE = re.compile(r"<td[^>]*>(.*?)</td>", re.IGNORECASE | re.DOTALL)
HREF_RE = re.compile(r'href="([^"]+)"', re.IGNORECASE)
TAG_RE = re.compile(r"<[^>]+>")
EXHIBIT_13_RE = re.compile(r"EX-13(?:\.\d+)?", re.IGNORECASE)
AUDITOR_RE = re.compile(r"Report of Independent Registered Public Accounting Firm", re.IGNORECASE)
ADDRESSEE_RE = re.compile(r"\bTo the (?:Board|Stockholders|Shareholders|Shareowners)", re.I)
OPINION_RE = re.compile(r"Opinions? on the (?:Consolidated )?Financial Statements", re.I)
RELOCATED_END_RE = re.compile(
    r"^[ \t]*(?:(?:exhibit index|signatures?)[ \t]*$|item[ \t]+16\b)", re.I | re.MULTILINE
)
# A 10-K that maps Items to pages through its own index ("Form 10-K Cross-Reference Index"
# at Citigroup, "Form 10-K Index" at JPMorgan) is laid out like an annual report.
CROSS_REFERENCE_RE = re.compile(
    r"^[ \t]*(?:form[ \t]+)?10-K[ \t]+(?:cross[- ]reference[ \t]+)?index[ \t]*$"
    r"|^[ \t]*cross[- ]reference[ \t]+index[ \t]*$",
    re.IGNORECASE | re.MULTILINE,
)
INDEX_SEARCH_CHARS = 80_000  # the index sits near the front, after the cover page
# In such a 10-K the notes to the financial statements are followed by sections like these.
CLOSING_SECTIONS_RE = re.compile(
    r"^[ \t]*(?:(?:financial data supplement|glossary of terms|supervision and regulation|"
    r"corporate information|exhibit index|signatures?)\b[^\n]{0,60}$|item[ \t]+16\b)",
    re.IGNORECASE | re.MULTILINE,
)
MIN_SHARED_CHARS = 80  # shorter repeated lines (headings such as "Overview") are left alone
SHARED_SUFFIX = ".shared.json"
RIGHT_QUOTE = chr(0x2019)  # the curly apostrophe in "Management's"
MDNA_RE = re.compile("Management(?:'s|" + RIGHT_QUOTE + "s)?" + r"\s+Discussion", re.IGNORECASE)
OWN_HEADINGS = {
    "1": r"items?[ \t]+1(?![0-9a-z])|business\b",
    "1A": r"item[ \t]+1a\b|risk factors\b",
    "7": r"item[ \t]+7(?![0-9a-z])|management(?:'s|" + RIGHT_QUOTE + r"s)?\s+discussion",
    "7A": r"item[ \t]+7a\b|quantitative and qualitative disclosures? about (?:market )?risk",
}
TABLE_RE = re.compile(r"<table\b.*?</table\s*>", re.IGNORECASE | re.DOTALL)
CELL_TEXT_RE = re.compile(r"<t[dh]\b[^>]*>(.*?)</t[dh]\s*>", re.IGNORECASE | re.DOTALL)
CONTENTS_LINES = 12
PAGE_NUMBER_LINE_RE = re.compile(r"^\d{1,3}\b|\b\d{1,3}$")  # "6 Management Discussion", "Notes 48"
# A cell with no letters: a number, a currency sign, a percent, a dash or a footnote mark.
NUMERIC_CELL_RE = re.compile(r"[^A-Za-z]*")
ROW_RE = re.compile(r"<tr\b.*?</tr\s*>", re.IGNORECASE | re.DOTALL)
WHITESPACE_RE = re.compile(r"\s+")
LETTER_RE = re.compile(r"[A-Za-z]")
MARKER_RE = re.compile(r"\[\[#(\d+)#\]\]")  # where a number table was; see table_marker
DASHES = "-" + chr(0x2013) + chr(0x2014)  # hyphen, en dash, em dash
PAGE_RANGE = r"\d{1,3}(?:\s*[" + DASHES + r"]\s*\d{1,3})?"
# A page reference: "81", "4-36, 121-127". A comma followed by a space separates pages;
# a comma inside a number ("1,234") has none.
PAGE_REF_RE = re.compile(PAGE_RANGE + r"(?:,\s+" + PAGE_RANGE + r")*")
OPENING_MARKS = frozenset({"$", "(", "($", "$("})  # cells that belong to the next number
CLOSING_MARKS = frozenset({")", "%", ")%", "%)"})  # cells that belong to the previous one
# Removing number tables must not move a section. Its first and last EDGE_LETTERS letters
# must sit within EDGE_SLACK letters of the edges of the section cut from the full document;
# the slack allows for a table at either edge.
EDGE_LETTERS = 200
EDGE_SLACK = 5_000
EDGE_MIN_LETTERS = 50  # a probe shorter than this is too common to place a section
NON_LETTER_RE = re.compile(r"[^a-z]+")
PARAGRAPH_BREAK_RE = re.compile(r"\n[ \t]*\n")
EXHIBIT_END_RE = re.compile(
    r"^[ \t]*(?:\d+[ \t]+)?(?:Performance Graphs?|Stockholder Information|"
    r"Shareholder Information|Shareowner Information)\b",
    re.IGNORECASE | re.MULTILINE,
)
SPACES_RE = re.compile(r"[ \t" + chr(0xA0) + "]+")  # spaces, tabs and no-break spaces
BLANK_RUN_RE = re.compile(r"\n{3,}")

Method = Literal["edgartools", "regex", "exhibit", "relocated"]


class ItemText(BaseModel):
    """The text of one Item and how it was found."""

    model_config = ConfigDict(frozen=True)

    text: str
    method: Method


class ItemSummary(BaseModel):
    """Size, source and boundary of one saved Item."""

    chars: int
    method: Method
    boundary: Boundary = "exact"


class SectionSummary(BaseModel):
    """What the section split found in one filing; the data report is built from these."""

    ticker: str
    fiscal_year: int
    accession: str
    items: dict[str, ItemSummary]
    short: list[str]
    gaps: list[str]
    cross_reference_index: bool = False
    repeats_removed: int = 0
    merged: list[str] = []  # Items kept together under MERGED_ITEM
    tables_saved: int = 0  # number tables set aside from the prose, see TableChunk
    tables_outside_items: int = 0  # of those, tables in no saved Item
    tables_kept: list[str] = []  # Items cut from the full document: removal moved them


# ---------------------------------------------------------------- HTML to text


class _TextExtractor(HTMLParser):
    PARAGRAPH = frozenset(
        {"p", "div", "table", "h1", "h2", "h3", "h4", "h5", "h6", "section", "ul", "ol"}
    )
    LINE = frozenset({"tr", "li", "br"})
    SKIP = frozenset({"script", "style", "head", "ix:header"})

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.skipping = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in self.SKIP:
            self.skipping += 1
        elif tag in self.PARAGRAPH:
            self.parts.append("\n\n")
        elif tag in self.LINE:
            self.parts.append("\n")
        elif tag in ("td", "th"):
            self.parts.append(" ")

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in self.LINE:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in self.SKIP:
            self.skipping = max(0, self.skipping - 1)
        elif tag in self.PARAGRAPH:
            self.parts.append("\n\n")

    def handle_data(self, data: str) -> None:
        if not self.skipping:
            self.parts.append(data)


class NumberTable(BaseModel):
    """A table set aside from the prose: its number in the filing, where it was, its rows."""

    index: int
    position: int  # character offset of the table in the decoded source document
    text: str  # one row per line, "label: value | value"


def table_marker(index: int) -> str:
    """The placeholder left in the prose where table `index` was; it has no letters."""
    return f"[[#{index}#]]"


def remove_markers(text: str) -> str:
    """The prose without its table placeholders."""
    return MARKER_RE.sub("", text)


def _cell_text(cell: str) -> str:
    return WHITESPACE_RE.sub(" ", unescape(TAG_RE.sub(" ", cell))).strip()


def _is_number_table(table: str) -> bool:
    filled = [cell for cell in map(_cell_text, CELL_TEXT_RE.findall(table)) if cell]
    numeric = [cell for cell in filled if NUMERIC_CELL_RE.fullmatch(cell)]
    if all(PAGE_REF_RE.fullmatch(cell) for cell in numeric):
        return False  # a contents list: its only numbers are page numbers
    return len(numeric) * 2 > len(filled)


def table_text(table: str) -> str:
    """A table as plain rows, "label: value | value", with "$" and "%" kept on their numbers."""
    lines = []
    for row in ROW_RE.findall(table):
        values: list[str] = []
        opening = ""
        for cell in filter(None, map(_cell_text, CELL_TEXT_RE.findall(row))):
            if cell in OPENING_MARKS:
                opening += cell
            elif cell in CLOSING_MARKS and values and not opening:
                values[-1] += cell
            else:
                values.append(opening + cell)
                opening = ""
        if opening:
            values.append(opening)
        if len(values) > 1 and LETTER_RE.search(values[0]):
            lines.append(f"{values[0].rstrip(':')}: {' | '.join(values[1:])}")
        elif values:
            lines.append(" | ".join(values))
    return "\n".join(lines)


def strip_number_tables(html: str, start: int = 0) -> tuple[str, list[NumberTable]]:
    """Set aside tables whose non-empty cells are more than half numbers.

    The prose index keeps narrative only; each table is returned, numbered from `start`,
    and a marker is left in its place so the section that held it can be found. Tables
    that are mostly words, and contents lists, stay.
    """
    removed: list[NumberTable] = []

    def replace(match: re.Match[str]) -> str:
        if not _is_number_table(match.group(0)):
            return match.group(0)
        index = start + len(removed)
        removed.append(
            NumberTable(index=index, position=match.start(), text=table_text(match.group(0)))
        )
        return f"<p>{table_marker(index)}</p>"

    return TABLE_RE.sub(replace, html), removed


def html_to_text(html: str) -> str:
    """Plain text with paragraph breaks; hidden inline-XBRL facts are left out."""
    parser = _TextExtractor()
    parser.feed(html)
    parser.close()
    lines = [SPACES_RE.sub(" ", line).strip() for line in "".join(parser.parts).split("\n")]
    return BLANK_RUN_RE.sub("\n\n", "\n".join(lines)).strip()


# ---------------------------------------------------------------- finding the Items


def split_items_by_heading(text: str) -> dict[str, str]:
    """Split text at "Item N." headings that start a line.

    An Item heading appears in the table of contents and again where the Item starts; the
    occurrence followed by the most text is the real one.
    """
    marks = [(m.start(), m.group(1).upper()) for m in HEADING_RE.finditer(text)]
    best: dict[str, tuple[int, int]] = {}
    for i, (start, item) in enumerate(marks):
        end = marks[i + 1][0] if i + 1 < len(marks) else len(text)
        if item not in best or end - start > best[item][1] - best[item][0]:
            best[item] = (start, end)
    # The heading of the next Part ("PART II") sits between two Items; it belongs to neither.
    return {
        item: TRAILING_PART_RE.sub("", text[start:end]).strip()
        for item, (start, end) in best.items()
    }


def _edgartools_items(html: str) -> dict[str, str]:
    # Imported here: edgartools is large, and only the ingest step needs it. Only its
    # offline HTML parser is used, never its download functions.
    import edgar.documents as edgar_documents

    doc = edgar_documents.parse_html(html, edgar_documents.ParserConfig(form="10-K"))
    found: dict[str, str] = {}
    for item, key in EDGARTOOLS_KEYS.items():
        try:
            found[item] = str(doc.extract_section_text(key) or "")
        except Exception:  # edgartools raises various errors for Items it cannot find
            found[item] = ""
    return found


def extract_items(html: str) -> dict[str, ItemText]:
    """Find Items 1, 1A, 7, 7A and 8 in a 10-K, recording which method found each one."""
    try:
        found = _edgartools_items(html)
    except Exception:  # a parser failure falls back to the heading splitter below
        found = {}
    fallback: dict[str, str] = {}
    if any(not found.get(item, "").strip() for item in ITEMS):
        fallback = split_items_by_heading(html_to_text(html))
    items: dict[str, ItemText] = {}
    for item in ITEMS:
        if found.get(item, "").strip():
            items[item] = ItemText(text=found[item], method="edgartools")
        elif fallback.get(item, "").strip():
            items[item] = ItemText(text=fallback[item], method="regex")
    return items


def short_items(items: dict[str, ItemText], min_chars: int = SHORT_ITEM_CHARS) -> list[str]:
    """The Items that are missing or shorter than `min_chars`, in Item order."""
    return [item for item in ITEMS if item not in items or len(items[item].text) < min_chars]


# ---------------------------------------------------------------- Exhibit 13


def filing_index_url(cik: str, accession: str) -> str:
    """The filing's index page, which lists every document with its exhibit type."""
    return INDEX_URL.format(cik=int(cik), folder=accession.replace("-", ""), accession=accession)


def exhibit_13_documents(index_html: str) -> list[str]:
    """File names of the EX-13 documents listed on a filing index page.

    The page's table gives each document's type; `index.json` lists only file names, and an
    Exhibit 13 file name need not say "ex13" (IBM's is `ibm-20251231_d2.htm`).
    """
    names: list[str] = []
    for row in ROW_RE.findall(index_html):
        cells = CELL_RE.findall(row)
        if len(cells) < 4:
            continue
        doc_type = unescape(TAG_RE.sub("", cells[3])).strip()
        link = HREF_RE.search(cells[2])
        if link and EXHIBIT_13_RE.fullmatch(doc_type):
            names.append(link.group(1).rsplit("/", 1)[-1])
    return names


def financial_statements_start(text: str) -> int | None:
    """Where the auditor's report on the financial statements begins, or None.

    A 10-K can hold several "Report of Independent Registered Public Accounting Firm"
    headings: a line in a contents list, a report on internal control only (often in Item
    9A), and the report that opens the financial statements. The last one is recognised by
    its "Opinion on the Financial Statements"; failing that, by its addressee ("To the
    Board ..."). Each heading is judged only by the text before the next heading, so a
    contents line cannot borrow the opinion of the report that follows it.
    """
    heads = list(AUDITOR_RE.finditer(text))
    for marker, window in ((OPINION_RE, 600), (ADDRESSEE_RE, 200)):
        for i, head in enumerate(heads):
            limit = head.end() + window
            if i + 1 < len(heads):
                limit = min(limit, heads[i + 1].start())
            if marker.search(text, head.end(), limit):
                return head.start()
    return None


def relocate_financial_statements(
    text: str, end_re: re.Pattern[str] = RELOCATED_END_RE
) -> str | None:
    """Cut the financial statements out of a 10-K whose Item 8 only points to them.

    They run from the auditor's report on the financial statements to the first heading that
    `end_re` matches: by default the exhibit index, the signatures or Item 16. Netflix places
    them after Part IV; Nvidia places them under Item 15.
    """
    start = financial_statements_start(text)
    if start is None:
        return None
    end = end_re.search(text, start + 1)
    return text[start : end.start() if end else len(text)].strip()


def has_cross_reference_index(text: str) -> bool:
    """Whether the 10-K maps its Items to pages through its own index, near its front."""
    return CROSS_REFERENCE_RE.search(text[:INDEX_SEARCH_CHARS]) is not None


def starts_at_own_heading(item: str, text: str) -> bool:
    """Whether a section begins with its own Item label or title, on one of its first lines."""
    pattern = r"^[ \t]*(?:" + OWN_HEADINGS[item] + ")"
    return re.search(pattern, text[:HEADING_WINDOW], re.IGNORECASE | re.MULTILINE) is not None


def merge_unseparable(texts: dict[str, str]) -> tuple[dict[str, str], list[str]]:
    """In a page-indexed 10-K, keep Items 1 to 7A apart only where each starts at its heading.

    The others are joined, in Item order, under MERGED_ITEM: a broad label that is true is
    better than a specific one that may not fit the text. Item 8 is never merged.
    """
    merged = [i for i in MERGEABLE_ITEMS if i in texts and not starts_at_own_heading(i, texts[i])]
    if not merged:
        return texts, []
    kept = {item: text for item, text in texts.items() if item not in merged}
    kept[MERGED_ITEM] = "\n\n".join(texts[item] for item in merged)
    return kept, merged


def _paragraph_letters(text: str) -> list[str]:
    """The letters of each paragraph; a table marker counts as a paragraph break."""
    paragraphs = PARAGRAPH_BREAK_RE.split(MARKER_RE.sub("\n\n", text))
    return [letters for p in paragraphs if (letters := NON_LETTER_RE.sub("", p.lower()))]


def _probe(paragraphs: list[str]) -> str:
    # Short paragraphs, such as a "Table of Contents" page header, are too common to place.
    return next((p for p in paragraphs if len(p) >= EDGE_MIN_LETTERS), paragraphs[0])


def same_edges(original: str, stripped: str) -> bool:
    """Whether a section cut without number tables starts and ends where the full one does.

    The probes are whole paragraphs, so they never join the text on both sides of a
    removed table, and a page header or footer at either edge does not count as a move.
    """
    full = NON_LETTER_RE.sub("", original.lower())
    paragraphs = _paragraph_letters(stripped)
    if not paragraphs:
        return False
    head = _probe(paragraphs)[:EDGE_LETTERS]
    tail = _probe(paragraphs[::-1])[-EDGE_LETTERS:]
    start, end = full.find(head), full.rfind(tail)
    return 0 <= start <= EDGE_SLACK and end >= 0 and len(full) - end - len(tail) <= EDGE_SLACK


def tables_in_span(document: str, section: str) -> list[int]:
    """The tables whose markers fall inside `section`, located in the marked `document`.

    For a section cut from the original document, which has its tables inline and so no
    markers: its first and last prose paragraphs are found in the marked document, and the
    markers strictly between them are its tables.
    """
    letters: list[str] = []
    length = 0
    at: dict[int, int] = {}
    for n, piece in enumerate(MARKER_RE.split(document)):
        if n % 2:
            at[int(piece)] = length
        else:
            letters.append(NON_LETTER_RE.sub("", piece.lower()))
            length += len(letters[-1])
    full = "".join(letters)
    prose = [p[:EDGE_LETTERS] for p in _paragraph_letters(section) if len(p) >= EDGE_MIN_LETTERS]
    start = next((s for s in (full.find(p) for p in prose) if s >= 0), -1)
    if start < 0:
        return []
    ends = (full.rfind(p, start) + len(p) for p in reversed(prose) if full.rfind(p, start) >= 0)
    end = next(ends, start)
    return sorted(index for index, position in at.items() if start < position < end)


def assign_tables(texts: dict[str, str], order: list[str]) -> dict[int, str]:
    """Which section holds each table: the first in `order` whose text has its marker."""
    owners: dict[int, str] = {}
    for item in order:
        for match in MARKER_RE.finditer(texts[item]):
            owners.setdefault(int(match.group(1)), item)
    return owners


def choose_sections(
    original: dict[str, ItemText], stripped: dict[str, ItemText]
) -> tuple[dict[str, ItemText], list[str]]:
    """Take each section from the parse without number tables where that did not move it.

    The mapping of Items comes from the full document. A section whose edges moved when
    the tables were removed is taken from the full document instead, and listed.
    """
    items: dict[str, ItemText] = {}
    kept: list[str] = []
    for item, found in original.items():
        lean = stripped.get(item)
        if lean is not None and same_edges(found.text, lean.text):
            items[item] = lean
        else:
            items[item] = found
            kept.append(item)
    return items, kept


def section_boundary(index_based: bool, method: str) -> Boundary:
    """'approximate' for Items found through a page index; Items cut at a heading are exact."""
    return "approximate" if index_based and method in ("edgartools", "regex") else "exact"


def _paragraph_key(paragraph: str) -> str:
    return " ".join(paragraph.split()).lower()


def dedupe_paragraphs(
    texts: dict[str, str],
    min_chars: int = MIN_SHARED_CHARS,
    order: list[str] | None = None,
) -> tuple[dict[str, str], dict[str, list[SharedSpan]], int]:
    """Keep each repeated passage of a filing once, under the first Item (in `order`) that has it.

    Returns the Item texts without the repeats, the passages each Item shares with other
    Items (as character spans, with those Items), and how many repeats were removed.
    Paragraphs shorter than `min_chars`, such as headings, are never treated as repeats.
    `order` defaults to the Item order; pass exact sections first so that a passage shared
    with an approximate section stays in the exact one.
    """
    owner: dict[str, str] = {}
    also: dict[str, set[str]] = defaultdict(set)
    kept: dict[str, list[str]] = {}
    removed = 0
    for item in [i for i in (order or list(ALL_ITEMS)) if i in texts]:
        paragraphs = []
        for paragraph in texts[item].split("\n\n"):
            key = _paragraph_key(paragraph)
            if len(key) >= min_chars and key in owner:
                if owner[key] != item:
                    also[key].add(item)
                removed += 1
                continue
            if len(key) >= min_chars:
                owner[key] = item
            paragraphs.append(paragraph)
        kept[item] = paragraphs
    result: dict[str, str] = {}
    spans: dict[str, list[SharedSpan]] = {}
    for item, paragraphs in kept.items():
        position, item_spans = 0, []
        for n, paragraph in enumerate(paragraphs):
            position += 2 if n else 0  # the "\n\n" between paragraphs
            key = _paragraph_key(paragraph)
            if key in also:
                others = sorted(also[key], key=ALL_ITEMS.index)
                item_spans.append((position, position + len(paragraph), others))
            position += len(paragraph)
        result[item] = "\n\n".join(paragraphs)
        spans[item] = item_spans
    return result, spans, removed


def _looks_like_contents(window: str) -> bool:
    """Whether text is a contents list: most of its first lines carry a page number."""
    lines = [line.strip() for line in window.split("\n") if line.strip()][:CONTENTS_LINES]
    numbered = sum(1 for line in lines if PAGE_NUMBER_LINE_RE.search(line))
    return junk_reason(window) == "toc" or numbered * 2 > len(lines) >= 4


def split_exhibit_13(text: str) -> dict[str, str] | None:
    """Cut an annual-report exhibit into Item 7 (MD&A) and Item 8 (financial statements).

    Item 8 starts at the auditor's report on the financial statements and ends before
    closing sections such as "Performance Graphs". Item 7 runs from the first MD&A heading
    up to Item 8.
    """
    start8 = financial_statements_start(text)
    if start8 is None:
        return None
    start7 = next(
        (
            text.rfind("\n", 0, m.start()) + 1  # the start of the heading's line
            for m in MDNA_RE.finditer(text, 0, start8)
            if not _looks_like_contents(text[m.start() : m.start() + CHUNK_SIZE])
        ),
        0,
    )
    end = EXHIBIT_END_RE.search(text, start8 + 1)
    end8 = end.start() if end else len(text)
    return {"7": text[start7:start8].strip(), "8": text[start8:end8].strip()}


def exhibit_path(filing: Filing, name: str) -> str:
    """Where an exhibit is saved: next to the filing's primary document."""
    return f"data/filings/{filing.ticker}/{filing.fiscal_year}_{filing.accession}_{name}"


def _exhibit_13(
    filing: Filing, client: SecFetcher, root: Path, first_table: int
) -> tuple[list[ExtraDocument], dict[str, str] | None, list[tuple[str, NumberTable]]]:
    index = decode_document(client.get_bytes(filing_index_url(filing.cik, filing.accession)))
    folder = filing.primary_document_url.rsplit("/", 1)[0]
    documents: list[ExtraDocument] = []
    texts: list[str] = []
    tables: list[tuple[str, NumberTable]] = []
    for name in exhibit_13_documents(index):
        url = f"{folder}/{name}"
        body = client.get_bytes(url)
        path = exhibit_path(filing, name)
        write_atomic(root / path, body)
        documents.append(ExtraDocument(type="EX-13", url=url, document_path=path))
        html, removed = strip_number_tables(decode_document(body), start=first_table + len(tables))
        tables += [(url, table) for table in removed]
        texts.append(html_to_text(html))
    if not documents:
        return [], None, []
    return documents, split_exhibit_13("\n\n".join(texts)), tables


# ---------------------------------------------------------------- the stage


def section_path(filing: Filing, item: str) -> str:
    """Where one Item's cleaned text is saved, relative to the repository root."""
    return f"data/sections/{filing.ticker}/{filing.fiscal_year}/item_{item}.txt"


def tables_path(filing: Filing) -> str:
    """Where one filing's number tables are saved, one JSON object per line."""
    return f"data/sections/{filing.ticker}/{filing.fiscal_year}/tables.jsonl"


def _write_tables(
    root: Path, filing: Filing, tables: list[tuple[str, NumberTable]], owners: dict[int, str]
) -> None:
    path = root / tables_path(filing)
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = [
        TableChunk(
            ticker=filing.ticker,
            fiscal_year=filing.fiscal_year,
            accession=filing.accession,
            item=owners.get(table.index),
            table_index=table.index,
            source_url=url,
            position=table.position,
            text=table.text,
        )
        for url, table in tables
    ]
    path.write_text(
        "".join(row.model_dump_json() + "\n" for row in rows), encoding="utf-8", newline="\n"
    )


def _section_filing(
    filing: Filing, client: SecFetcher, root: Path, min_chars: int
) -> tuple[Filing, SectionSummary]:
    original = decode_document((root / filing.document_path).read_bytes())
    # The page-range index is read from the original document. Number tables are set aside
    # before the sections are cut, and a section moved by that is cut from the original.
    index_based = has_cross_reference_index(html_to_text(original))
    html, removed = strip_number_tables(original)
    tables = [(filing.primary_document_url, table) for table in removed]
    text = html_to_text(html)
    full_items = extract_items(original)
    items, tables_kept = choose_sections(full_items, extract_items(html))
    gaps: list[str] = []
    extra = list(filing.extra_documents)
    if index_based:
        # Items come from page ranges, so their edges are approximate; Item 8 is cut instead
        # from the auditor's report to the first section that follows the notes.
        statements = relocate_financial_statements(text, CLOSING_SECTIONS_RE)
        if statements is not None and len(statements) >= min_chars:
            items["8"] = ItemText(text=statements, method="relocated")
        else:
            gaps.append("Item 8: the auditor's report on the financial statements was not found")
    weak = [item for item in EXHIBIT_ITEMS if item in short_items(items, min_chars)]
    if weak:
        # First choice: an Exhibit 13 annual report filed with the 10-K.
        documents, parts, exhibit_tables = _exhibit_13(filing, client, root, len(tables))
        tables += exhibit_tables
        known = {doc.url for doc in extra}
        extra += [doc for doc in documents if doc.url not in known]
        for item in weak:
            if parts is not None and len(parts[item]) >= min_chars:
                items[item] = ItemText(text=parts[item], method="exhibit")
        unresolved = [i for i in weak if i not in items or items[i].method != "exhibit"]
        # Second choice for Item 8: the statements elsewhere in the same 10-K.
        if "8" in unresolved:
            moved = relocate_financial_statements(text)
            if moved is not None and len(moved) >= min_chars:
                items["8"] = ItemText(text=moved, method="relocated")
                unresolved.remove("8")
        if unresolved and not documents:
            listed = " and ".join(unresolved)
            words = ("Item", "is") if len(unresolved) == 1 else ("Items", "are")
            gaps.append(f"{words[0]} {listed} {words[1]} short and the filing has no Exhibit 13")
        elif unresolved and parts is None:
            gaps.append("Exhibit 13 found, but its MD&A and financial statements were not")
        else:
            gaps += [
                f"Item {item} is short in both the 10-K and its Exhibit 13" for item in unresolved
            ]
    # Which tables each section held: its own markers, or, for a section cut from the
    # original document, the markers between its first and last paragraphs.
    tables_kept = [item for item in tables_kept if items.get(item) == full_items[item]]
    holders = {item: found.text for item, found in items.items()}
    for item in tables_kept:
        holders[item] = " ".join(map(table_marker, tables_in_span(text, items[item].text)))
    merged: list[str] = []
    if index_based:
        kept, merged = merge_unseparable({item: found.text for item, found in items.items()})
        if merged:
            method = items[merged[0]].method
            items = {item: found for item, found in items.items() if item not in merged}
            items[MERGED_ITEM] = ItemText(text=kept[MERGED_ITEM], method=method)
            holders[MERGED_ITEM] = " ".join(holders.pop(item) for item in merged)
    cleaned = {item: clean_item_text(remove_markers(found.text)) for item, found in items.items()}
    boundaries = {
        item: section_boundary(index_based, found.method) for item, found in items.items()
    }
    exact_first = sorted(cleaned, key=lambda i: (boundaries[i] != "exact", ALL_ITEMS.index(i)))
    owners = assign_tables(holders, order=exact_first)
    _write_tables(root, filing, tables, owners)
    deduped, shared, removed_paragraphs = dedupe_paragraphs(cleaned, order=exact_first)
    summaries: dict[str, ItemSummary] = {}
    for item in [i for i in ALL_ITEMS if i in deduped]:
        path = root / section_path(filing, item)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(deduped[item], encoding="utf-8", newline="\n")
        sidecar = path.with_name(path.stem + SHARED_SUFFIX)
        if shared[item]:
            sidecar.write_text(json.dumps(shared[item]) + "\n", encoding="utf-8", newline="\n")
        elif sidecar.exists():
            sidecar.unlink()  # left from an earlier run
        summaries[item] = ItemSummary(
            chars=len(deduped[item]), method=items[item].method, boundary=boundaries[item]
        )
    missing = [item for item in ITEMS if item not in items and item not in merged]
    if missing:
        gaps.append(f"not found: Item {', Item '.join(missing)}")
    short = [item for item, s in summaries.items() if s.chars < min_chars]
    summary = SectionSummary(
        ticker=filing.ticker,
        fiscal_year=filing.fiscal_year,
        accession=filing.accession,
        items=summaries,
        short=short,
        gaps=gaps,
        cross_reference_index=index_based,
        repeats_removed=removed_paragraphs,
        merged=merged,
        tables_saved=len(tables),
        tables_outside_items=len(tables) - len(owners),
        tables_kept=tables_kept,
    )
    return filing.model_copy(update={"extra_documents": extra}), summary


def build_sections(
    manifest: Manifest, client: SecFetcher, root: Path, min_chars: int = SHORT_ITEM_CHARS
) -> tuple[Manifest, list[SectionSummary]]:
    """Save every filing's Items as text files; return the updated manifest and a summary."""
    filings: list[Filing] = []
    summaries: list[SectionSummary] = []
    for filing in manifest.filings:
        updated, summary = _section_filing(filing, client, root, min_chars)
        filings.append(updated)
        summaries.append(summary)
    return Manifest(filings=filings), summaries


def write_summary(path: Path, summaries: list[SectionSummary]) -> None:
    """Save the section summary that the data report is built from."""
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = [s.model_dump() for s in summaries]
    path.write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8", newline="\n")


def load_summary(path: Path) -> list[SectionSummary]:
    """Read the section summary written by `write_summary`."""
    rows = json.loads(path.read_text(encoding="utf-8"))
    return [SectionSummary.model_validate(row) for row in rows]


def _read_shared(path: Path) -> list[SharedSpan]:
    sidecar = path.with_name(path.stem + SHARED_SUFFIX)
    if not sidecar.exists():
        return []
    return [(int(s), int(e), list(items)) for s, e, items in json.loads(sidecar.read_text())]


def iter_chunks(manifest: Manifest, root: Path) -> Iterator[tuple[list[Chunk], dict[str, int]]]:
    """Chunk every saved Item; yields each filing's chunks with the count of dropped ones.

    A chunk whose text already appeared in the same filing is dropped (counted as "repeat")
    and its Item is added to the first one's `also_in`; repeats across filings are kept.
    """
    summaries = {s.accession: s for s in load_summary(root / "data/sections/summary.json")}
    for filing in manifest.filings:
        summary = summaries.get(filing.accession)
        kept: list[Chunk] = []
        first_with_text: dict[str, int] = {}
        dropped: Counter[str] = Counter()
        for item in ALL_ITEMS:
            path = root / section_path(filing, item)
            if not path.exists():
                continue
            found = summary.items.get(item) if summary else None
            chunks, item_dropped = chunk_item(
                path.read_text(encoding="utf-8"),
                ticker=filing.ticker,
                cik=filing.cik,
                fiscal_year=filing.fiscal_year,
                accession=filing.accession,
                item=item,
                shared=_read_shared(path),
                boundary=found.boundary if found else "exact",
            )
            dropped.update(item_dropped)
            for chunk in chunks:
                if chunk.text in first_with_text:
                    index = first_with_text[chunk.text]
                    first = kept[index]
                    others = (set(first.also_in) | {chunk.item, *chunk.also_in}) - {first.item}
                    kept[index] = first.model_copy(
                        update={"also_in": sorted(others, key=ALL_ITEMS.index)}
                    )
                    dropped["repeat"] += 1
                    continue
                first_with_text[chunk.text] = len(kept)
                kept.append(chunk)
        yield kept, dict(dropped)


def iter_table_chunks(manifest: Manifest, root: Path) -> Iterator[TableChunk]:
    """Every number table the sections stage set aside, filing by filing."""
    for filing in manifest.filings:
        path = root / tables_path(filing)
        if path.exists():
            with path.open(encoding="utf-8") as handle:
                for line in handle:
                    if line.strip():
                        yield TableChunk.model_validate_json(line)
