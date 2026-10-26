"""An independent check of the ingest outputs: `make verify-data`.

It reads the saved files directly and shares no logic with the code that wrote them, so a
mistake in that code cannot hide itself. It checks that each section starts with its Item
heading, that no chunk text appears twice in one filing, and that the chunk counts match
`docs/data_report.md`. It also writes `docs/spot_check.md`, a fixed random sample to read
against the SEC documents by eye.
"""

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
SEED = 2027
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


def main(root: Path = REPO_ROOT) -> int:
    """Run every check, print the failures, and write docs/spot_check.md."""
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
    counted = Counter(row["accession"] for row in rows)
    report = (root / "docs" / "data_report.md").read_text(encoding="utf-8")
    failures["Chunk counts that differ from docs/data_report.md"] = check_chunk_counts(
        dict(counted), parse_report_chunk_counts(report)
    )

    (root / "docs" / "spot_check.md").write_text(spot_check(root), encoding="utf-8", newline="\n")
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
    print("wrote docs/spot_check.md")
    print("PASSED" if total == 0 else f"FAILED: {total} problems")
    return 0 if total == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
