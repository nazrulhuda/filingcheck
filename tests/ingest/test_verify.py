import json
from pathlib import Path
from typing import Any

from filingcheck.ingest.verify import (
    check_chunk_counts,
    check_duplicates,
    check_heading,
    parse_report_chunk_counts,
    spot_check,
)

RIGHT_QUOTE = chr(0x2019)


# ---------------------------------------------------------------- headings


def test_a_section_starting_with_its_item_label_passes() -> None:
    assert check_heading("7", "edgartools", "Item 7. Management's Discussion and Analysis") is None
    assert check_heading("1A", "regex", "ITEM 1A.  RISK FACTORS\n\nOur business...") is None
    assert check_heading("1", "edgartools", "Items 1 and 2. Business and Properties") is None


def test_a_section_starting_with_its_item_title_passes() -> None:
    title = f"Table of Contents\n\nManagement{RIGHT_QUOTE}s Discussion and Analysis of Financial"
    assert check_heading("7", "edgartools", title) is None
    assert check_heading("1", "edgartools", "Table of Contents\n\nBusiness\n\nOverview") is None
    assert check_heading("8", "edgartools", "Financial Statements and Supplementary Data") is None


def test_a_section_starting_with_something_else_fails() -> None:
    problem = check_heading("7A", "edgartools", "Third Line of Defense: Internal Audit\n\nInternal")
    assert problem is not None and "Third Line of Defense" in problem


def test_item_1_does_not_accept_item_1a() -> None:
    assert check_heading("1", "edgartools", "Item 1A. Risk Factors") is not None


def test_exhibit_and_relocated_sections_need_their_own_headings() -> None:
    report = "Report of Independent Registered Public Accounting Firm\n\nTo the Board"
    assert check_heading("8", "exhibit", report) is None
    assert check_heading("8", "relocated", report) is None
    assert check_heading("8", "relocated", "Item 8. Financial Statements") is not None
    assert check_heading("7", "exhibit", "Management Discussion\n\nOVERVIEW") is None


def test_a_heading_after_the_first_500_characters_does_not_count() -> None:
    assert check_heading("7", "edgartools", "x" * 500 + "Item 7.") is not None


# ---------------------------------------------------------------- duplicates


def chunk(ticker: str, year: int, item: str, text: str) -> dict[str, Any]:
    return {"ticker": ticker, "fiscal_year": year, "item": item, "text": text}


def test_the_same_text_twice_in_one_filing_fails() -> None:
    rows = [chunk("C", 2025, "7", "shared text"), chunk("C", 2025, "7A", "shared text")]
    result = check_duplicates(rows)
    assert result.failures == ["C FY2025: 1 chunk texts appear more than once (Items 7, 7A)"]


def test_the_same_text_in_different_years_is_reported_but_allowed() -> None:
    rows = [chunk("AAPL", 2024, "1A", "same risk"), chunk("AAPL", 2025, "1A", "same risk")]
    result = check_duplicates(rows)
    assert result.failures == []
    assert result.across_filings == 1


# ---------------------------------------------------------------- the data report


REPORT = """\
## AAPL

| FY | Accession | Period of report | Item 1 | Item 1A | Item 7 | Item 7A | Item 8 | Chunks |
|---|---|---|---:|---:|---:|---:|---:|---:|
| 2024 | acc-24 | 2024-09-28 | 1 | 2 | 3 | 4 | 5 | 1,204 |
| 2025 | acc-25 | 2025-09-27 | 1 | 2 | 3 | 4 | 5 | 80 |
"""


def test_chunk_counts_are_read_from_the_report() -> None:
    assert parse_report_chunk_counts(REPORT) == {"acc-24": 1204, "acc-25": 80}


def test_a_count_that_differs_from_the_report_fails() -> None:
    counted = {"acc-24": 1204, "acc-25": 79, "acc-26": 3}
    assert check_chunk_counts(counted, {"acc-24": 1204, "acc-25": 80}) == [
        "acc-25: 79 chunks in data/chunks.jsonl, 80 in the data report",
        "acc-26: 3 chunks in data/chunks.jsonl, missing from the data report",
    ]


# ---------------------------------------------------------------- spot check


def write_inputs(root: Path) -> None:
    (root / "data/sections/AAPL/2025").mkdir(parents=True)
    for item in ("1", "1A", "7", "7A", "8"):
        (root / f"data/sections/AAPL/2025/item_{item}.txt").write_text(
            f"Item {item}. Heading\n\n" + "text " * 200, encoding="utf-8"
        )
    manifest = {
        "filings": [
            {
                "ticker": "AAPL",
                "fiscal_year": 2025,
                "accession": "acc-25",
                "primary_document_url": "https://www.sec.gov/primary.htm",
                "extra_documents": [],
            }
        ]
    }
    (root / "data/manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    summary = [
        {
            "ticker": "AAPL",
            "fiscal_year": 2025,
            "accession": "acc-25",
            "items": {
                i: {"chars": 1000, "method": "edgartools"} for i in ("1", "1A", "7", "7A", "8")
            },
        }
    ]
    (root / "data/sections/summary.json").write_text(json.dumps(summary), encoding="utf-8")
    rows = [
        {
            "ticker": "AAPL",
            "fiscal_year": 2025,
            "accession": "acc-25",
            "item": "7",
            "chunk_index": i,
            "text": f"chunk number {i} " + "word " * 80,
        }
        for i in range(40)
    ]
    with (root / "data/chunks.jsonl").open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")


def test_the_spot_check_has_15_chunks_and_5_section_starts_with_links(tmp_path: Path) -> None:
    write_inputs(tmp_path)
    text = spot_check(tmp_path)
    assert text.count("### Chunk ") == 15
    assert text.count("### Section ") == 5
    assert text.count("https://www.sec.gov/primary.htm") == 20


def test_the_spot_check_is_the_same_every_time(tmp_path: Path) -> None:
    write_inputs(tmp_path)
    assert spot_check(tmp_path) == spot_check(tmp_path)
