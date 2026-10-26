"""10-Ks that map Items to pages through their own index, and repeated passages in a filing."""

import json
from pathlib import Path

from filingcheck.ingest.chunking import chunk_item
from filingcheck.ingest.filings import Manifest
from filingcheck.ingest.sections import (
    CLOSING_SECTIONS_RE,
    build_sections,
    dedupe_paragraphs,
    has_cross_reference_index,
    html_to_text,
    iter_chunks,
    relocate_financial_statements,
    section_boundary,
)
from tests.ingest.test_sections import FakeClient, filing, fixture, write_document

SHARED = "A long passage that the company's own index places in more than one Item of the 10-K."
SENTENCE = "Net revenue rose because the bank earned more net interest income on higher balances. "


# ---------------------------------------------------------------- detection and the Item 8 cut


def test_a_10k_with_its_own_item_index_is_detected() -> None:
    assert has_cross_reference_index("Cover\n\nFORM 10-K CROSS-REFERENCE INDEX\n\nItem Number")
    assert has_cross_reference_index("Shares outstanding\n\nForm 10-K Index\n\nPart I")
    assert not has_cross_reference_index("TABLE OF CONTENTS\n\nItem 1. Business 3")
    assert not has_cross_reference_index("The 10-K index fund rose in a sentence.")


def test_item_8_of_an_index_based_10k_stops_at_the_first_closing_section() -> None:
    text = html_to_text(fixture("tenk_xref_sample.html"))
    statements = relocate_financial_statements(text, CLOSING_SECTIONS_RE)
    assert statements is not None
    assert statements.startswith("REPORT OF INDEPENDENT REGISTERED PUBLIC ACCOUNTING FIRM")
    assert "XREF-NOTES-MARKER" in statements
    assert "XREF-AFTER-MARKER" not in statements  # the Financial Data Supplement is not Item 8


def test_boundaries_are_exact_unless_pages_were_mapped_through_an_index() -> None:
    assert section_boundary(index_based=False, method="edgartools") == "exact"
    assert section_boundary(index_based=True, method="edgartools") == "approximate"
    assert section_boundary(index_based=True, method="regex") == "approximate"
    assert section_boundary(index_based=True, method="relocated") == "exact"
    assert section_boundary(index_based=True, method="exhibit") == "exact"


def test_build_sections_cuts_item_8_of_an_index_based_10k(tmp_path: Path) -> None:
    path = write_document(tmp_path, fixture("tenk_xref_sample.html"))
    _, summary = build_sections(
        Manifest(filings=[filing(path)]), FakeClient({}), root=tmp_path, min_chars=100
    )
    row = summary[0]
    assert row.cross_reference_index is True
    assert (row.items["8"].method, row.items["8"].boundary) == ("relocated", "exact")


# ---------------------------------------------------------------- repeated passages


def test_a_passage_in_two_items_is_kept_once_with_both_items() -> None:
    texts = {
        "7": f"{SHARED}\n\nOnly in Item 7. {SENTENCE}",
        "7A": f"{SHARED}\n\nOnly in 7A. {SENTENCE}",
    }
    kept, shared, removed = dedupe_paragraphs(texts)
    assert kept["7"].startswith(SHARED)
    assert SHARED not in kept["7A"]
    assert shared["7"] == [(0, len(SHARED), ["7A"])]
    assert removed == 1


def test_a_passage_repeated_inside_one_item_is_kept_once() -> None:
    kept, shared, removed = dedupe_paragraphs({"1": f"{SHARED}\n\nMiddle. {SENTENCE}\n\n{SHARED}"})
    assert kept["1"].count(SHARED) == 1
    assert shared["1"] == []
    assert removed == 1


def test_short_repeated_lines_such_as_headings_are_left_alone() -> None:
    kept, _, removed = dedupe_paragraphs(
        {"1": f"Overview\n\n{SENTENCE}", "7": f"Overview\n\n{SENTENCE}x"}
    )
    assert kept["7"].startswith("Overview")
    assert removed == 0


def test_a_chunk_over_a_shared_passage_lists_the_other_items() -> None:
    text = f"{SHARED}\n\n" + SENTENCE * 20
    chunks, _ = chunk_item(
        text,
        ticker="C",
        cik="0000831001",
        fiscal_year=2025,
        accession="acc",
        item="7",
        shared=[(0, len(SHARED), ["7A"])],
        boundary="approximate",
    )
    assert chunks[0].also_in == ["7A"]
    assert chunks[0].boundary == "approximate"
    assert all(c.also_in == [] for c in chunks[2:])


def test_iter_chunks_drops_an_identical_chunk_and_records_its_item(tmp_path: Path) -> None:
    body = (SENTENCE.strip() + "\n") * 8  # short lines: not caught as a repeated paragraph
    f = filing("data/filings/EXMP/x.html")
    folder = tmp_path / "data/sections/EXMP/2025"
    folder.mkdir(parents=True)
    for item in ("7", "8"):
        (folder / f"item_{item}.txt").write_text(body, encoding="utf-8")
    summary = [
        {
            "ticker": "EXMP",
            "fiscal_year": 2025,
            "accession": f.accession,
            "items": {i: {"chars": len(body), "method": "edgartools"} for i in ("7", "8")},
            "short": [],
            "gaps": [],
        }
    ]
    (tmp_path / "data/sections/summary.json").write_text(json.dumps(summary), encoding="utf-8")
    batches = list(iter_chunks(Manifest(filings=[f]), tmp_path))
    chunks = [c for batch, _ in batches for c in batch]
    dropped = sum(d.get("repeat", 0) for _, d in batches)
    assert [c.item for c in chunks] == ["7"]
    assert chunks[0].also_in == ["8"]
    assert dropped == 1
