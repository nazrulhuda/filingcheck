from datetime import date
from pathlib import Path

import psycopg
import pytest

from filingcheck.db.load import load_all, read_chunks
from filingcheck.db.migrate import migrate
from filingcheck.ingest.chunking import Chunk
from filingcheck.ingest.companies import Company
from filingcheck.ingest.filings import Filing, Manifest

APPLE = Company(
    ticker="AAPL",
    name="Apple Inc.",
    cik="0000320193",
    sector="technology",
    fiscal_year_end=9,
    revenue_rule="standard",
    financebench=True,
    aliases=["Apple", "AAPL"],
)
FILING = Filing(
    ticker="AAPL",
    cik="0000320193",
    fiscal_year=2025,
    fiscal_year_source="dei",
    form="10-K",
    accession="0000320193-25-000079",
    filing_date=date(2025, 10, 31),
    period_of_report=date(2025, 9, 27),
    primary_document_url="https://www.sec.gov/Archives/edgar/data/320193/x/aapl-20250927.htm",
    document_path="data/filings/AAPL/2025_0000320193-25-000079.html",
)
TEXT = {
    "1A": "Risk factors: the company's results depend on demand for its products. " * 4,
    "7": "Net sales rose in fiscal 2025 because of higher iPhone and services sales. " * 4,
}


def chunks(count: int = 100) -> list[Chunk]:
    items = ["1A", "7"]
    return [
        Chunk(
            ticker="AAPL",
            cik="0000320193",
            fiscal_year=2025,
            accession=FILING.accession,
            item=items[i % 2],
            chunk_index=i // 2,
            char_start=i * 10,
            char_end=i * 10 + len(TEXT[items[i % 2]]),
            text=f"{TEXT[items[i % 2]]} (chunk {i})",
        )
        for i in range(count)
    ]


def write_jsonl(path: Path, rows: list[Chunk]) -> Path:
    path.write_text("".join(c.model_dump_json() + "\n" for c in rows), encoding="utf-8")
    return path


def test_read_chunks_parses_the_jsonl_file(tmp_path: Path) -> None:
    path = write_jsonl(tmp_path / "chunks.jsonl", chunks(3))
    assert list(read_chunks(path)) == chunks(3)


@pytest.mark.integration
def test_loading_100_chunks_round_trips(db: psycopg.Connection, tmp_path: Path) -> None:
    migrate(db)
    path = write_jsonl(tmp_path / "chunks.jsonl", chunks())
    counts = load_all(db, [APPLE], Manifest(filings=[FILING]), path)
    assert counts == {"companies": 1, "filings": 1, "chunks": 100}
    rows = db.execute(
        "SELECT c.item, c.chunk_index, c.char_start, c.char_end, c.text, f.accession "
        "FROM chunks c JOIN filings f ON f.id = c.filing_id ORDER BY c.id"
    ).fetchall()
    expected = [
        (c.item, c.chunk_index, c.char_start, c.char_end, c.text, c.accession) for c in chunks()
    ]
    assert rows == expected
    aliases = db.execute("SELECT aliases FROM companies WHERE ticker = 'AAPL'").fetchone()
    assert aliases == (["Apple", "AAPL"],)


@pytest.mark.integration
def test_loading_twice_replaces_instead_of_duplicating(
    db: psycopg.Connection, tmp_path: Path
) -> None:
    migrate(db)
    path = write_jsonl(tmp_path / "chunks.jsonl", chunks())
    load_all(db, [APPLE], Manifest(filings=[FILING]), path)
    load_all(db, [APPLE], Manifest(filings=[FILING]), path)
    assert db.execute("SELECT count(*) FROM chunks").fetchone() == (100,)


@pytest.mark.integration
def test_a_full_text_search_for_risk_factors_finds_item_1a(
    db: psycopg.Connection, tmp_path: Path
) -> None:
    migrate(db)
    load_all(db, [APPLE], Manifest(filings=[FILING]), write_jsonl(tmp_path / "c.jsonl", chunks()))
    items = db.execute(
        "SELECT DISTINCT item FROM chunks WHERE tsv @@ plainto_tsquery('english', 'risk factors')"
    ).fetchall()
    assert items == [("1A",)]


@pytest.mark.integration
def test_a_chunk_for_an_unknown_filing_fails_loudly(db: psycopg.Connection, tmp_path: Path) -> None:
    migrate(db)
    stray = chunks(1)[0].model_copy(update={"accession": "no-such-filing"})
    path = write_jsonl(tmp_path / "chunks.jsonl", [stray])
    with pytest.raises(KeyError, match="no-such-filing"):
        load_all(db, [APPLE], Manifest(filings=[FILING]), path)


@pytest.mark.integration
def test_the_load_stage_loads_the_files_and_checks_the_count(
    fresh_db_url: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from filingcheck.ingest import __main__ as cli
    from filingcheck.ingest.companies import save_companies
    from filingcheck.ingest.filings import write_manifest

    monkeypatch.setenv("DATABASE_URL", fresh_db_url)
    companies, manifest = tmp_path / "companies.yaml", tmp_path / "manifest.json"
    save_companies(companies, [APPLE])
    write_manifest(manifest, Manifest(filings=[FILING]))
    (tmp_path / "data").mkdir()
    write_jsonl(tmp_path / cli.CHUNKS_FILE, chunks())
    assert cli.run_load(companies, manifest, tmp_path) == 0
    out = capsys.readouterr().out
    assert "applied migrations: 0001_initial" in out
    assert "loaded 1 companies, 1 filings and 100 chunks (100 in data/chunks.jsonl)" in out
