from datetime import date
from pathlib import Path

import psycopg
import pytest

from filingcheck.db.load import load_all, read_chunks, read_table_chunks
from filingcheck.db.migrate import migrate
from filingcheck.ingest.chunking import Chunk, TableChunk
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
            also_in=["7A"] if i == 0 else [],
            boundary="approximate" if i == 1 else "exact",
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
    assert counts == {"companies": 1, "filings": 1, "chunks": 100, "table_chunks": 0}
    rows = db.execute(
        "SELECT c.item, c.chunk_index, c.char_start, c.char_end, c.text, f.accession "
        "FROM chunks c JOIN filings f ON f.id = c.filing_id ORDER BY c.id"
    ).fetchall()
    expected = [
        (c.item, c.chunk_index, c.char_start, c.char_end, c.text, c.accession) for c in chunks()
    ]
    assert rows == expected
    extra = db.execute("SELECT also_in, boundary FROM chunks ORDER BY id LIMIT 2").fetchall()
    assert extra == [(["7A"], "exact"), ([], "approximate")]
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


SEGMENTS = TableChunk(
    ticker="AAPL",
    fiscal_year=2025,
    accession=FILING.accession,
    item="8",
    table_index=41,
    source_url=FILING.primary_document_url,
    position=912_345,
    text="iPhone: $209,586 | $201,183\nServices: $109,158 | $96,169",
)


def write_tables(path: Path, rows: list[TableChunk]) -> Path:
    path.write_text("".join(t.model_dump_json() + "\n" for t in rows), encoding="utf-8")
    return path


def test_read_table_chunks_parses_the_jsonl_file(tmp_path: Path) -> None:
    path = write_tables(tmp_path / "t.jsonl", [SEGMENTS])
    assert list(read_table_chunks(path)) == [SEGMENTS]


@pytest.mark.integration
def test_number_tables_load_into_their_own_table_not_chunks(
    db: psycopg.Connection, tmp_path: Path
) -> None:
    migrate(db)
    outside = SEGMENTS.model_copy(update={"item": None, "table_index": 42})
    counts = load_all(
        db,
        [APPLE],
        Manifest(filings=[FILING]),
        write_jsonl(tmp_path / "c.jsonl", chunks(2)),
        write_tables(tmp_path / "t.jsonl", [SEGMENTS, outside]),
    )
    assert counts == {"companies": 1, "filings": 1, "chunks": 2, "table_chunks": 2}
    rows = db.execute(
        "SELECT f.ticker, f.fiscal_year, t.item, t.table_index, t.source_url, t.position, t.text "
        "FROM table_chunks t JOIN filings f ON f.id = t.filing_id ORDER BY t.table_index"
    ).fetchall()
    assert rows[0] == ("AAPL", 2025, "8", 41, SEGMENTS.source_url, 912_345, SEGMENTS.text)
    assert rows[1][2] is None
    found = db.execute("SELECT count(*) FROM chunks WHERE text LIKE '%209,586%'").fetchone()
    assert found == (0,)


@pytest.mark.integration
def test_a_table_for_an_unknown_filing_fails_loudly(db: psycopg.Connection, tmp_path: Path) -> None:
    migrate(db)
    stray = SEGMENTS.model_copy(update={"accession": "no-such-filing"})
    with pytest.raises(KeyError, match="no-such-filing"):
        load_all(
            db,
            [APPLE],
            Manifest(filings=[FILING]),
            write_jsonl(tmp_path / "c.jsonl", chunks(1)),
            write_tables(tmp_path / "t.jsonl", [stray]),
        )
