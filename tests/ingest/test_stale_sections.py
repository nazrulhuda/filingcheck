"""Item files left by an earlier run must not survive, be chunked, or pass the data check."""

import json
from pathlib import Path

from filingcheck.ingest.filings import Manifest
from filingcheck.ingest.sections import (
    MERGED_ITEM,
    build_sections,
    iter_chunks,
    section_path,
    write_summary,
)
from tests.ingest.test_sections import FakeClient, filing, fixture, write_document

WORDS = "The company sells widgets in North America, Europe and Asia through its own stores. "


def sectioned(tmp_path: Path) -> Manifest:
    path = write_document(tmp_path, fixture("tenk_sample.html"))
    manifest = Manifest(filings=[filing(path)])
    _, summaries = build_sections(manifest, FakeClient({}), root=tmp_path, min_chars=100)
    write_summary(tmp_path / "data/sections/summary.json", summaries)
    return manifest


def test_an_item_file_left_from_an_earlier_run_is_removed(tmp_path: Path) -> None:
    path = write_document(tmp_path, fixture("tenk_sample.html"))
    manifest = Manifest(filings=[filing(path)])
    stale = tmp_path / section_path(manifest.filings[0], MERGED_ITEM)
    stale.parent.mkdir(parents=True, exist_ok=True)
    stale.write_text(WORDS * 20, encoding="utf-8")
    sidecar = stale.with_name(stale.stem + ".shared.json")
    sidecar.write_text("[]\n", encoding="utf-8")
    _, summaries = build_sections(manifest, FakeClient({}), root=tmp_path, min_chars=100)
    assert MERGED_ITEM not in summaries[0].items
    assert not stale.exists() and not sidecar.exists()
    assert (tmp_path / section_path(manifest.filings[0], "7")).exists()  # real items stay


def test_the_chunks_stage_reads_only_the_items_in_the_summary(tmp_path: Path) -> None:
    manifest = sectioned(tmp_path)
    stray = tmp_path / section_path(manifest.filings[0], MERGED_ITEM)
    stray.write_text(("STRAY-MARKER " + WORDS) * 20, encoding="utf-8")
    chunks = [c for filing_chunks, _ in iter_chunks(manifest, tmp_path) for c in filing_chunks]
    assert chunks
    assert {c.item for c in chunks} <= {"1", "1A", "7", "7A", "8"}
    assert not any("STRAY-MARKER" in c.text for c in chunks)


def test_verify_data_reports_item_files_that_are_not_in_the_summary(tmp_path: Path) -> None:
    from filingcheck.ingest.verify import stray_section_files

    manifest = sectioned(tmp_path)
    assert stray_section_files(tmp_path) == []
    stray = tmp_path / section_path(manifest.filings[0], MERGED_ITEM)
    stray.write_text(WORDS, encoding="utf-8")
    assert stray_section_files(tmp_path) == ["EXMP FY2025: data/sections/EXMP/2025/item_1-7A.txt"]


def test_verify_data_reports_chunks_whose_item_is_not_in_the_summary(tmp_path: Path) -> None:
    from filingcheck.ingest.verify import chunks_outside_summary

    sectioned(tmp_path)
    summary = json.loads((tmp_path / "data/sections/summary.json").read_text(encoding="utf-8"))
    row = {"ticker": "EXMP", "fiscal_year": 2025}
    rows = [dict(row, item="7"), dict(row, item="7"), dict(row, item="1-7A")]
    assert chunks_outside_summary(rows, summary) == ["EXMP FY2025: 1 chunks under Item 1-7A"]
    assert chunks_outside_summary(rows[:2], summary) == []
