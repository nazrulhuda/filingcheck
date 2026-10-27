"""An independent check of the ingest outputs: `make verify-data`.

It reads the saved files directly and shares no logic with the code that wrote them, so a
mistake in that code cannot hide itself. It checks that each section starts with its Item
heading, that no chunk text appears twice in one filing, and that the chunk counts match
`docs/data_report.md`. It also writes `docs/spot_check.md`, a fixed random sample to read
against the SEC documents by eye.
"""

import hashlib
import json
import random
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from html import unescape
from pathlib import Path
from typing import Any

from filingcheck.paths import REPO_ROOT

ITEM_ORDER = ["1", "1A", "7", "7A", "8", "1-7A"]  # "1-7A": Items not separable
HEAD_CHARS = 500
SEED = 2028
SAMPLE_CHUNKS = 15
SAMPLE_SECTIONS = 5
APOSTROPHE = "['" + chr(0x2019) + "]"  # straight or curly

# A section passes when one of its first lines is the Item's label ("Item 7.") or title.
LINE = r"^[ \t]*"
LABELS = {
    "1": LINE + r"items?\s+1(?![0-9a-z])",  # also "Items 1 and 2."
    "1A": LINE + r"item\s+1a\b",
    "7": LINE + r"item\s+7(?![0-9a-z])",
    "7A": LINE + r"item\s+7a\b",
    "8": LINE + r"item\s+8(?![0-9])",
}
AUDITOR = LINE + r"report of independent registered public accounting firm"
TITLES = {
    "1": LINE + r"business\b",
    "1A": LINE + r"risk factors\b",
    "7": LINE + rf"management(?:{APOSTROPHE}s)?\s+discussion",
    "7A": LINE + r"quantitative and qualitative disclosures? about (?:market )?risk",  # MS: "Risk"
    "8": LINE + r"financial statements and supplementary data|" + AUDITOR,
}
# Sections cut from an Exhibit 13 or from later in the 10-K start at a known heading.
MOVED_HEADINGS = {"7": TITLES["7"], "8": AUDITOR}
REPORT_ROW_RE = re.compile(r"^\|\s*\d{4}\s*\|\s*([^|]+?)\s*\|.*\|\s*([\d,]+)\s*\|\s*$", re.M)


# Item 8 must hold the auditor's opinion on the statements and the first note.
FS_OPINION_RE = re.compile(r"opinions? on the (?:consolidated )?financial statements", re.I)
FIRST_NOTE_RE = re.compile(
    r"^[ \t]*(?:note[ \t]+1\b|1[.:)]?[ \t]+[a-z][^\n]{0,80}"
    r"(?:policies|presentation|organization|basis)|[^\n]{0,60}significant accounting policies)",
    re.I | re.M,
)
# docs/section_bounds.md
BOUND_CHARS = 150
PROBE_LETTERS = 300  # most of a paragraph: short endings such as "in Item 8 of this Report" repeat
PROBE_MIN_LETTERS = 50
NEXT_HEADING_LINES = 200
HEADING_CHARS = 100
SIZE_CHANGE_FLAG = 0.35
ITEM_OR_PART_RE = re.compile(r"(?:item|part)\s+(?:\d{1,2}[a-c]?|[ivx]+)\b", re.I)
ITEM_LINE_RE = re.compile(r"items?\s+\d{1,2}[a-c]?\b", re.I)
# docs/table_sample.md
SAMPLE_TABLES = 10
TABLE_LINES = 40
# data/section_snapshot.json and data/chunk_snapshot.json
SNAPSHOT_ENDS = 200
HASH_CHARS = 16
SOURCE_WINDOW = 300  # how far before a section's start, in the source, its heading may sit
PROBE_CHARS = 60


def plain_text(html: str) -> str:
    """A flat text version of a filing: tags removed, entities decoded, whitespace collapsed.

    Deliberately simpler than the pipeline's own converter, so the two do not share mistakes.
    """
    html = re.sub(r"(?is)<(script|style|ix:header)\b.*?</\1\s*>", " ", html)
    return re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", " ", html))).strip().lower()


def heading_before_in_source(item: str, section: str, source: str) -> bool:
    """Whether the Item's label or title sits just before where the section starts in the source.

    Some parsers drop the heading line itself (Mastercard's "Item 1A. Risk factors"); the
    section is still right if that heading comes directly before its first words.
    """
    probe = re.sub(r"\s+", " ", section).strip().lower()[:PROBE_CHARS]
    if not probe:
        return False
    pattern = (LABELS[item] + "|" + TITLES[item]).replace(LINE, "")
    for match in re.finditer(re.escape(probe), source):
        before = source[max(0, match.start() - SOURCE_WINDOW) : match.start()]
        if re.search(pattern, before, re.IGNORECASE):
            return True
    return False


def heading_source(method: str) -> str | None:
    """Which document may confirm a heading just before the section: the 10-K, the exhibit.

    A relocated Item 8 starts at the auditor's report itself, so it is never excused.
    """
    return {"edgartools": "primary", "regex": "primary", "exhibit": "exhibit"}.get(method)


def check_heading(item: str, method: str, text: str) -> str | None:
    """None if the section starts with its expected heading, else a description of its start."""
    head = text[:HEAD_CHARS]
    if method in ("exhibit", "relocated"):
        pattern = MOVED_HEADINGS[item]
    else:
        pattern = LABELS[item] + "|" + TITLES[item]
    if re.search(pattern, head, re.IGNORECASE | re.MULTILINE):
        return None
    start = " / ".join(line.strip() for line in head.splitlines() if line.strip())[:90]
    return f"Item {item} ({method}) starts with: {start}"


@dataclass
class DuplicateResult:
    """Chunk texts that repeat: inside one filing (failures) and across filings (allowed)."""

    failures: list[str]
    across_filings: int


def check_duplicates(rows: list[dict[str, Any]]) -> DuplicateResult:
    """Find chunk texts that appear more than once in the same filing.

    The same text in different fiscal years is allowed and only counted: companies repeat
    paragraphs, such as risk factors, from one year's 10-K to the next.
    """
    items_by_text: dict[tuple[str, int, str], list[str]] = defaultdict(list)
    filings_by_text: dict[str, set[tuple[str, int]]] = defaultdict(set)
    for row in rows:
        key = (row["ticker"], row["fiscal_year"])
        items_by_text[(*key, row["text"])].append(row["item"])
        filings_by_text[row["text"]].add(key)
    repeats: dict[tuple[str, int], int] = Counter()
    items_involved: dict[tuple[str, int], set[str]] = defaultdict(set)
    for (ticker, year, _), items in items_by_text.items():
        if len(items) > 1:
            repeats[(ticker, year)] += 1
            items_involved[(ticker, year)].update(items)
    failures = [
        f"{ticker} FY{year}: {count} chunk texts appear more than once "
        f"(Items {', '.join(sorted(items_involved[(ticker, year)], key=ITEM_ORDER.index))})"
        for (ticker, year), count in sorted(repeats.items())
    ]
    across = sum(1 for filings in filings_by_text.values() if len(filings) > 1)
    return DuplicateResult(failures=failures, across_filings=across)


def parse_report_chunk_counts(report: str) -> dict[str, int]:
    """Read each filing's chunk count (the last column) from the data report's tables."""
    return {
        accession: int(count.replace(",", "")) for accession, count in REPORT_ROW_RE.findall(report)
    }


def check_chunk_counts(counted: dict[str, int], reported: dict[str, int]) -> list[str]:
    """Compare chunks counted in the chunk file with the data report, filing by filing."""
    problems = []
    for accession in sorted(set(counted) | set(reported)):
        mine = counted.get(accession, 0)
        if accession not in reported:
            problems.append(
                f"{accession}: {mine} chunks in data/chunks.jsonl, missing from the data report"
            )
        elif mine != reported[accession]:
            problems.append(
                f"{accession}: {mine} chunks in data/chunks.jsonl, "
                f"{reported[accession]} in the data report"
            )
    return problems


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_chunks(root: Path) -> list[dict[str, Any]]:
    with (root / "data" / "chunks.jsonl").open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def _source_urls(root: Path) -> tuple[dict[tuple[str, int], str], dict[tuple[str, int], str]]:
    primary: dict[tuple[str, int], str] = {}
    exhibit: dict[tuple[str, int], str] = {}
    for filing in _read_json(root / "data" / "manifest.json")["filings"]:
        key = (filing["ticker"], filing["fiscal_year"])
        primary[key] = filing["primary_document_url"]
        for doc in filing.get("extra_documents", []):
            exhibit.setdefault(key, doc["url"])
    return primary, exhibit


def _sections(root: Path) -> dict[tuple[str, int, str], dict[str, Any]]:
    rows = _read_json(root / "data" / "sections" / "summary.json")
    return {
        (row["ticker"], row["fiscal_year"], item): found
        for row in rows
        for item, found in row["items"].items()
    }


def _methods(root: Path) -> dict[tuple[str, int, str], str]:
    return {key: found["method"] for key, found in _sections(root).items()}


def _fence(text: str) -> list[str]:
    return ["```text", text.replace("```", "'''").rstrip(), "```", ""]


def spot_check(root: Path) -> str:
    """A fixed random sample of chunks and section starts, each with its SEC document link."""
    rng = random.Random(SEED)
    primary, exhibit = _source_urls(root)
    methods = _methods(root)

    def link(ticker: str, year: int, item: str) -> str:
        if methods.get((ticker, year, item)) == "exhibit":
            return exhibit[(ticker, year)]
        return primary[(ticker, year)]

    rows = _read_chunks(root)
    lines = [
        "# Spot check",
        "",
        f"A fixed random sample (seed {SEED}) of the chunks and section starts, to read "
        "against the SEC documents by eye. Written by `make verify-data`; do not edit by hand.",
        "",
        "## Chunks",
        "",
    ]
    for n, i in enumerate(sorted(rng.sample(range(len(rows)), min(SAMPLE_CHUNKS, len(rows)))), 1):
        row = rows[i]
        ticker, year, item = row["ticker"], row["fiscal_year"], row["item"]
        lines += [
            f"### Chunk {n}: {ticker} FY{year}, Item {item}, chunk {row['chunk_index']}",
            "",
            f"Source: {link(ticker, year, item)}",
            "",
            *_fence(row["text"][:300]),
        ]
    lines += ["## Section starts", ""]
    sections = sorted(methods, key=lambda k: (k[0], k[1], ITEM_ORDER.index(k[2])))
    picked = sorted(rng.sample(range(len(sections)), min(SAMPLE_SECTIONS, len(sections))))
    for n, i in enumerate(picked, 1):
        ticker, year, item = sections[i]
        path = root / "data" / "sections" / ticker / str(year) / f"item_{item}.txt"
        lines += [
            f"### Section {n}: {ticker} FY{year}, Item {item} ({methods[sections[i]]})",
            "",
            f"Source: {link(ticker, year, item)}",
            "",
            *_fence(path.read_text(encoding="utf-8")[:400]),
        ]
    return "\n".join(lines).rstrip("\n") + "\n"


# ---------------------------------------------------------------- Item 8 and the report


def check_item_8(text: str) -> str | None:
    """None if an Item 8 holds the auditor's opinion on the statements and the first note."""
    if not FS_OPINION_RE.search(text):
        return "no opinion on the financial statements"
    if not FIRST_NOTE_RE.search(text):
        return "no Note 1"
    return None


def check_report_tables(report: str) -> list[str]:
    """Rows of the data report's tables whose number of cells differs from their header's."""
    problems = []
    header = 0
    for line in report.splitlines():
        if not line.startswith("|"):
            header = 0
            continue
        cells = line.strip().count("|") - 1
        if not header:
            header = cells
        elif not line.startswith("|---") and cells != header:
            problems.append(f"{line}: {cells} cells, header has {header}")
    return problems


# ---------------------------------------------------------------- section bounds


def source_lines(html: str) -> str:
    """The source document as text, one block (paragraph, row, heading) per line."""
    html = re.sub(r"(?is)<(script|style|ix:header)\b.*?</\1\s*>", " ", html)
    html = re.sub(r"(?i)<br\s*/?>|</(?:p|div|tr|h[1-6]|li|table|title)\s*>", "\n", html)
    html = re.sub(r"(?i)</t[dh]\s*>", " ", html)
    text = unescape(re.sub(r"<[^>]+>", "", html))
    lines = (re.sub(r"\s+", " ", line).strip() for line in text.split("\n"))
    return "\n".join(line for line in lines if line)


def _letters(text: str) -> str:
    return re.sub(r"[^a-z]+", "", text.lower())


def _letters_pattern(letters: str) -> re.Pattern[str]:
    # The letters in order, with anything but letters allowed between them.
    return re.compile("[^a-z]*".join(letters), re.IGNORECASE)


def locate(section: str, source: str) -> tuple[int, int] | None:
    """Where a saved section starts and ends in the source text, found by letters only.

    The section has lost tables, page headers and spacing on the way, so it is found by the
    letters of its first and last long paragraphs.
    """
    paragraphs = [p for p in map(_letters, re.split(r"\n\s*\n", section)) if p]
    if not paragraphs:
        return None
    long = [p for p in paragraphs if len(p) >= PROBE_MIN_LETTERS] or paragraphs
    # A paragraph the parser laid out differently (a table's cells in another order) is not
    # in the source as written, so the first and last paragraphs that are found are used.
    # The end is found first: a section's heading line is also in the contents list at the
    # top, so its start is the last match before the end, not the first in the document. A
    # closing sentence can also occur elsewhere (Nike's Item 7 and Item 3 end alike), so every
    # match of the end is tried, and the span closest in length to the section wins.
    tail = next(
        (
            pattern
            for p in long[::-1]
            if (pattern := _letters_pattern(p[-PROBE_LETTERS:])).search(source)
        ),
        None,
    )
    if tail is None:
        return None
    spans = []
    for end in tail.finditer(source):
        for p in long:
            starts = list(_letters_pattern(p[:PROBE_LETTERS]).finditer(source, 0, end.end()))
            if starts:
                spans.append((starts[-1].start(), end.end()))
                break
    return min(spans, key=lambda s: abs(s[1] - s[0] - len(section)), default=None)


def next_heading(source: str, position: int) -> str | None:
    """The first heading-like line after `position`: an Item or Part line, or a short title.

    Page numbers, "Table of Contents", sentences and lines with numbers (table rows, page
    footers) are skipped.
    """
    for line in source[position:].split("\n")[1 : NEXT_HEADING_LINES + 1]:
        line = line.strip()
        if ITEM_OR_PART_RE.match(line):
            return line[:HEADING_CHARS]
        if (
            3 <= len(line) <= HEADING_CHARS
            and line[0].isupper()
            and not re.search(r"[\d$%]", line)
            and not line.endswith((".", ",", ";", ":"))
            and line.lower() != "table of contents"
        ):
            return line
    return None


def next_item_heading(source: str, position: int) -> str | None:
    """The first line after `position` that starts with an Item label, such as "Item 1A."."""
    for line in source[position:].split("\n")[1:]:
        line = line.strip()
        if ITEM_LINE_RE.match(line) and len(line) <= HEADING_CHARS:
            return line
    return None


def size_change(previous: int, current: int) -> float | None:
    """The change in size from the previous fiscal year, as a fraction (0.36 is +36%)."""
    if previous <= 0:
        return None
    return round((current - previous) / previous, 2)


def _one_line(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().replace("`", "'")


def section_bounds(root: Path) -> str:
    """docs/section_bounds.md: where each saved section starts and ends, and what follows it."""
    rows = _read_json(root / "data" / "sections" / "summary.json")
    manifest = {
        (f["ticker"], f["fiscal_year"]): f
        for f in _read_json(root / "data" / "manifest.json")["filings"]
    }
    sources: dict[tuple[str, int, str], str] = {}

    def source(ticker: str, year: int, method: str) -> str:
        kind = "exhibit" if method == "exhibit" else "primary"
        key = (ticker, year, kind)
        if key not in sources:
            filing = manifest[(ticker, year)]
            paths = (
                [d["document_path"] for d in filing.get("extra_documents", [])]
                if kind == "exhibit"
                else [filing["document_path"]]
            )
            sources[key] = "\n".join(
                source_lines((root / p).read_text(encoding="utf-8", errors="replace"))
                for p in paths
            )
        return sources[key]

    sizes = {
        (r["ticker"], r["fiscal_year"], item): f["chars"]
        for r in rows
        for item, f in r["items"].items()
    }
    entries: list[str] = []
    flagged: list[str] = []
    not_located: list[str] = []
    count = 0
    for row in sorted(rows, key=lambda r: (r["ticker"], r["fiscal_year"])):
        ticker, year = row["ticker"], row["fiscal_year"]
        for item in sorted(row["items"], key=ITEM_ORDER.index):
            found = row["items"][item]
            name = f"{ticker} FY{year}, Item {item}"
            text = (root / "data" / "sections" / ticker / str(year) / f"item_{item}.txt").read_text(
                encoding="utf-8"
            )
            earlier = [y for (t, y, i) in sizes if t == ticker and i == item and y < year]
            size = f"{found['chars']:,} characters"
            if earlier:
                before = max(earlier)
                previous = sizes[(ticker, before, item)]
                change = size_change(previous, found["chars"])
                if change is not None:
                    size += f"; {change:+.0%} from FY{before}"
                    if abs(change) > SIZE_CHANGE_FLAG:
                        flagged.append(
                            f"- {name}: {change:+.0%} from FY{before} "
                            f"({previous:,} to {found['chars']:,} characters)"
                        )
            src = source(ticker, year, found["method"])
            span = locate(text, src)
            if span is None:
                after = next_item = "the section was not found in the source"
                not_located.append(f"- {name}")
            else:
                heading = next_heading(src, span[1])
                after = (
                    f"`{_one_line(heading)}`"
                    if heading
                    else f"none in the next {NEXT_HEADING_LINES} lines"
                )
                item_heading = next_item_heading(src, span[1])
                next_item = f"`{_one_line(item_heading)}`" if item_heading else "none"
            count += 1
            entries += [
                f"### {name} ({found['method']}, {found.get('boundary', 'exact')}; {size})",
                "",
                f"- Starts: `{_one_line(text[:BOUND_CHARS])}`",
                f"- Ends: `{_one_line(text[-BOUND_CHARS:])}`",
                f"- Next heading in the source: {after}",
                f"- Next Item heading in the source: {next_item}",
                "",
            ]
    lines = [
        "# Section bounds",
        "",
        f"Every saved section ({count}): its first and last {BOUND_CHARS} characters "
        "the first heading-like line in the source document after the section ends (often a "
        "page header or a table's header row), and the next Item heading. Written by "
        "`make verify-data`; do not edit by hand.",
        "",
        f"## Size changes over {SIZE_CHANGE_FLAG:.0%} from the previous year",
        "",
        *(flagged or ["None."]),
        "",
        "## Sections not found in the source",
        "",
        *(not_located or ["None."]),
        "",
        "## Sections",
        "",
        *entries,
    ]
    return "\n".join(lines).rstrip("\n") + "\n"


# ---------------------------------------------------------------- number tables


def sample_tables(rows: list[dict[str, Any]], count: int, seed: int) -> list[dict[str, Any]]:
    """A fixed random sample of saved tables, in file order."""
    rng = random.Random(seed)
    return [rows[i] for i in sorted(rng.sample(range(len(rows)), min(count, len(rows))))]


def table_sample(root: Path) -> str:
    """docs/table_sample.md: saved number tables as parsed, each with its source link."""
    with (root / "data" / "table_chunks.jsonl").open(encoding="utf-8") as handle:
        rows = [json.loads(line) for line in handle if line.strip()]
    lines = [
        "# Number table sample",
        "",
        f"A fixed random sample (seed {SEED}) of the {len(rows):,} number tables set aside in "
        "`table_chunks`, as parsed, to read against the SEC documents by eye. Written by "
        "`make verify-data`; do not edit by hand.",
        "",
    ]
    for n, row in enumerate(sample_tables(rows, SAMPLE_TABLES, SEED), 1):
        item = f"Item {row['item']}" if row["item"] else "outside the saved Items"
        name = f"{row['ticker']} FY{row['fiscal_year']}, {item}, table {row['table_index']}"
        table_lines = row["text"].splitlines()
        shown = table_lines[:TABLE_LINES]
        if len(table_lines) > TABLE_LINES:
            shown.append(f"... ({len(table_lines) - TABLE_LINES} more rows)")
        lines += [
            f"### Table {n}: {name}",
            "",
            f"Source: {row['source_url']} (character {row['position']:,} of the document)",
            "",
            *_fence("\n".join(shown)),
        ]
    return "\n".join(lines).rstrip("\n") + "\n"


# ---------------------------------------------------------------- snapshots


def _short_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:HASH_CHARS]


def section_fingerprint(text: str) -> dict[str, Any]:
    """A section's size and hashes of its first and last SNAPSHOT_ENDS characters."""
    return {
        "chars": len(text),
        "head": _short_hash(text[:SNAPSHOT_ENDS]),
        "tail": _short_hash(text[-SNAPSHOT_ENDS:]),
    }


def current_sections(root: Path) -> dict[str, dict[str, Any]]:
    """The fingerprint of every saved section, keyed "TICKER FYyear Item n"."""
    current = {}
    for row in _read_json(root / "data" / "sections" / "summary.json"):
        ticker, year = row["ticker"], row["fiscal_year"]
        for item in row["items"]:
            path = root / "data" / "sections" / ticker / str(year) / f"item_{item}.txt"
            current[f"{ticker} FY{year} Item {item}"] = section_fingerprint(
                path.read_text(encoding="utf-8")
            )
    return current


def current_chunk_counts(root: Path) -> dict[str, int]:
    """The number of chunks per filing, keyed "TICKER FYyear"."""
    return dict(Counter(f"{r['ticker']} FY{r['fiscal_year']}" for r in _read_chunks(root)))


def compare_sections(
    expected: dict[str, dict[str, Any]], current: dict[str, dict[str, Any]]
) -> list[str]:
    """Every section that is new, gone or changed since the snapshot."""
    problems = []
    for name in sorted(set(expected) | set(current)):
        if name not in current:
            problems.append(f"{name}: in the snapshot, not saved now")
        elif name not in expected:
            problems.append(f"{name}: saved now, not in the snapshot")
        elif expected[name] != current[name]:
            was, now = expected[name], current[name]
            changes = []
            if was["chars"] != now["chars"]:
                changes.append(f"{was['chars']:,} to {now['chars']:,} characters")
            if was["head"] != now["head"]:
                changes.append(f"first {SNAPSHOT_ENDS} characters changed")
            if was["tail"] != now["tail"]:
                changes.append(f"last {SNAPSHOT_ENDS} characters changed")
            problems.append(f"{name}: " + "; ".join(changes))
    return problems


def compare_chunk_counts(expected: dict[str, int], current: dict[str, int]) -> list[str]:
    """Every filing whose chunk count differs from the snapshot."""
    problems = []
    for name in sorted(set(expected) | set(current)):
        if name not in current:
            problems.append(f"{name}: {expected[name]:,} chunks in the snapshot, none now")
        elif name not in expected:
            problems.append(f"{name}: {current[name]:,} chunks now, not in the snapshot")
        elif expected[name] != current[name]:
            problems.append(
                f"{name}: {expected[name]:,} chunks in the snapshot, {current[name]:,} now"
            )
    return problems


def write_snapshot(path: Path, entries: dict[str, Any]) -> None:
    """One entry per line, sorted, so a change shows as a one-line diff."""
    body = ",\n".join(f"  {json.dumps(k)}: {json.dumps(entries[k])}" for k in sorted(entries))
    path.write_text("{\n" + body + "\n}\n", encoding="utf-8", newline="\n")


def check_snapshot(path: Path, current: dict[str, Any], compare: Any) -> list[str]:
    """Differences from a committed snapshot, or a note that it is missing."""
    if not path.exists():
        return [f"{path.name} is missing; run `make snapshot` and commit it"]
    problems: list[str] = compare(_read_json(path), current)
    return problems


def main(root: Path = REPO_ROOT, write_snapshots: bool = False) -> int:
    """Run every check, print the failures, and write the review pages.

    With `write_snapshots`, the section and chunk snapshots are first rewritten from the
    current data: for an intended change, committed together with the change.
    """
    sections_file = root / "data" / "section_snapshot.json"
    chunks_file = root / "data" / "chunk_snapshot.json"
    if write_snapshots:
        write_snapshot(sections_file, current_sections(root))
        write_snapshot(chunks_file, current_chunk_counts(root))
        print(f"wrote {sections_file.name} and {chunks_file.name}")
    failures: dict[str, list[str]] = {}
    documents: dict[tuple[str, int, str], list[Path]] = {}
    for f in _read_json(root / "data" / "manifest.json")["filings"]:
        key = (f["ticker"], f["fiscal_year"])
        documents[(*key, "primary")] = [root / f["document_path"]]
        documents[(*key, "exhibit")] = [
            root / d["document_path"] for d in f.get("extra_documents", [])
        ]
    sources: dict[tuple[str, int, str], str] = {}

    def source(key: tuple[str, int, str]) -> str:
        if key not in sources:
            sources[key] = " ".join(
                plain_text(path.read_text(encoding="utf-8", errors="replace"))
                for path in documents[key]
            )
        return sources[key]

    heading_problems: list[str] = []
    approximate: list[str] = []
    for (ticker, year, item), found in sorted(_sections(root).items()):
        if found.get("boundary", "exact") == "approximate":
            approximate.append(f"{ticker} FY{year}: Item {item}")
            continue
        text = (root / "data" / "sections" / ticker / str(year) / f"item_{item}.txt").read_text(
            encoding="utf-8"
        )
        problem = check_heading(item, found["method"], text)
        document = heading_source(found["method"])
        if (
            problem
            and document
            and heading_before_in_source(item, text, source((ticker, year, document)))
        ):
            problem = None
        if problem:
            heading_problems.append(f"{ticker} FY{year}: {problem}")
    failures["Sections without their Item heading (in the section or just before it)"] = (
        heading_problems
    )
    rows = _read_chunks(root)
    duplicates = check_duplicates(rows)
    failures["Chunk texts repeated inside one filing"] = duplicates.failures
    item_8_problems = []
    for ticker, year, _ in sorted(k for k in documents if k[2] == "primary"):
        path = root / "data" / "sections" / ticker / str(year) / "item_8.txt"
        problem = check_item_8(path.read_text(encoding="utf-8")) if path.exists() else "no Item 8"
        if problem:
            item_8_problems.append(f"{ticker} FY{year}: {problem}")
    failures["Item 8 without the auditor's opinion or the notes"] = item_8_problems
    counted = Counter(row["accession"] for row in rows)
    report = (root / "docs" / "data_report.md").read_text(encoding="utf-8")
    failures["Chunk counts that differ from docs/data_report.md"] = check_chunk_counts(
        dict(counted), parse_report_chunk_counts(report)
    )
    failures["Data report rows whose cells do not match their header"] = check_report_tables(report)
    failures["Sections that differ from data/section_snapshot.json"] = check_snapshot(
        sections_file, current_sections(root), compare_sections
    )
    failures["Chunk counts that differ from data/chunk_snapshot.json"] = check_snapshot(
        chunks_file, current_chunk_counts(root), compare_chunk_counts
    )

    (root / "docs" / "spot_check.md").write_text(spot_check(root), encoding="utf-8", newline="\n")
    for name, page in (("section_bounds.md", section_bounds), ("table_sample.md", table_sample)):
        (root / "docs" / name).write_text(page(root), encoding="utf-8", newline="\n")
    total = 0
    for title, problems in failures.items():
        print(f"{title}: {len(problems)}")
        for problem in problems:
            print(f"  {problem}")
        total += len(problems)
    print(
        f"Sections with approximate boundaries (10-Ks that map Items to pages through their "
        f"own index; not checked for a heading, flagged in the data report): {len(approximate)}"
    )
    for entry in approximate:
        print(f"  {entry}")
    print(
        f"Chunk texts shared by different filings (allowed, e.g. risk factors repeated "
        f"year to year): {duplicates.across_filings:,}"
    )
    print("wrote docs/spot_check.md, docs/section_bounds.md and docs/table_sample.md")
    print("PASSED" if total == 0 else f"FAILED: {total} problems")
    return 0 if total == 0 else 1


if __name__ == "__main__":
    sys.exit(main(write_snapshots="--write-snapshots" in sys.argv[1:]))
