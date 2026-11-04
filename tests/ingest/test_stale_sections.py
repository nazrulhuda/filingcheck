"""Item files left by an earlier run must not survive, be chunked, or pass the data check."""

import json
from pathlib import Path

import pytest

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


def _leftover_folders(root: Path) -> tuple[Path, Path, Path]:
    """A listed filing's folder with an extra file, a dropped year and a dropped company."""
    listed = root / "data/sections/EXMP/2025"
    listed.mkdir(parents=True, exist_ok=True)
    (listed / "notes.txt").write_text("kept\n", encoding="utf-8")
    dropped_year = root / "data/sections/EXMP/2023"
    dropped_year.mkdir(parents=True)
    for name in ("item_1.txt", "item_1.shared.json", "tables.jsonl"):
        (dropped_year / name).write_text(WORDS, encoding="utf-8")
    dropped_company = root / "data/sections/GONE/2024"
    dropped_company.mkdir(parents=True)
    (dropped_company / "tables.jsonl").write_text("{}\n", encoding="utf-8")
    return listed, dropped_year, dropped_company


def test_the_sections_stage_removes_folders_of_filings_not_in_the_manifest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    from filingcheck.ingest import __main__ as cli
    from filingcheck.ingest import sec_client
    from filingcheck.ingest.filings import write_manifest
    from tests.ingest.test_main import FakeSectionsClient

    path = write_document(tmp_path, fixture("tenk_sample.html"))
    manifest_path = tmp_path / "manifest.json"
    write_manifest(manifest_path, Manifest(filings=[filing(path)]))
    listed, dropped_year, dropped_company = _leftover_folders(tmp_path)
    monkeypatch.setattr(sec_client, "SecClient", FakeSectionsClient)

    assert cli.run_sections(manifest_path, tmp_path) == 0
    out = capsys.readouterr().out
    assert not dropped_year.exists()
    assert not dropped_company.parent.exists()  # the whole company folder
    assert "removed data/sections/EXMP/2023 (not in the manifest)" in out
    assert "removed data/sections/GONE (not in the manifest)" in out
    # The listed filing's folder is untouched apart from the files the run writes.
    assert (listed / "notes.txt").read_text(encoding="utf-8") == "kept\n"
    assert (listed / "item_7.txt").exists()
    assert (tmp_path / "data/sections/summary.json").exists()


def test_removing_unlisted_folders_keeps_every_listed_folder(tmp_path: Path) -> None:
    from filingcheck.ingest.sections import remove_unlisted_section_folders

    path = write_document(tmp_path, fixture("tenk_sample.html"))
    manifest = Manifest(filings=[filing(path)])
    listed, _, _ = _leftover_folders(tmp_path)
    removed = remove_unlisted_section_folders(manifest, tmp_path)
    assert removed == ["data/sections/EXMP/2023", "data/sections/GONE"]
    assert sorted(p.name for p in listed.iterdir()) == ["notes.txt"]
    assert remove_unlisted_section_folders(manifest, tmp_path) == []  # nothing left to remove


def test_verify_data_reports_section_folders_the_manifest_does_not_list(tmp_path: Path) -> None:
    from filingcheck.ingest.verify import stray_section_folders

    (tmp_path / "data").mkdir()
    rows = [{"ticker": "EXMP", "fiscal_year": 2025}]
    (tmp_path / "data/manifest.json").write_text(json.dumps({"filings": rows}), encoding="utf-8")
    listed = tmp_path / "data/sections/EXMP/2025"
    listed.mkdir(parents=True)
    (listed / "item_1.txt").write_text(WORDS, encoding="utf-8")
    (tmp_path / "data/sections/summary.json").write_text("[]\n", encoding="utf-8")
    assert stray_section_folders(tmp_path) == []

    _, dropped_year, _ = _leftover_folders(tmp_path)
    for name in ("item_1.txt", "item_1.shared.json"):
        (dropped_year / name).unlink()  # any file type counts, not only item_*.txt
    assert stray_section_folders(tmp_path) == [
        "EXMP FY2023: data/sections/EXMP/2023",
        "GONE: data/sections/GONE",
    ]
