"""Load the companies, filings and chunks into Postgres, replacing what was there."""

from collections.abc import Iterator
from pathlib import Path

import psycopg
from psycopg.types.json import Jsonb

from filingcheck.ingest.chunking import Chunk
from filingcheck.ingest.companies import Company
from filingcheck.ingest.filings import Manifest

COPY_CHUNKS = "COPY chunks (filing_id, item, chunk_index, char_start, char_end, text) FROM STDIN"


def read_chunks(path: Path) -> Iterator[Chunk]:
    """Read the chunks written by the chunks stage, one JSON object per line."""
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield Chunk.model_validate_json(line)


def load_all(
    conn: psycopg.Connection, companies: list[Company], manifest: Manifest, chunks_path: Path
) -> dict[str, int]:
    """Replace the companies, filings and chunks in one transaction; return the row counts.

    Chunks are bulk-loaded with COPY. A chunk whose filing is not in the manifest stops the
    load, and nothing is changed.
    """
    with conn.transaction():
        conn.execute("TRUNCATE companies, filings, chunks RESTART IDENTITY CASCADE")
        with conn.cursor() as cur:
            cur.executemany(
                "INSERT INTO companies (ticker, cik, name, sector, fiscal_year_end, "
                "revenue_rule, aliases) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                [
                    (
                        c.ticker,
                        c.cik,
                        c.name,
                        c.sector,
                        c.fiscal_year_end,
                        c.revenue_rule,
                        Jsonb(c.aliases),
                    )
                    for c in companies
                ],
            )
        filing_ids: dict[str, int] = {}
        for f in manifest.filings:
            row = conn.execute(
                "INSERT INTO filings (ticker, cik, accession, form, filing_date, "
                "period_of_report, fiscal_year, primary_url) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id",
                (
                    f.ticker,
                    f.cik,
                    f.accession,
                    f.form,
                    f.filing_date,
                    f.period_of_report,
                    f.fiscal_year,
                    f.primary_document_url,
                ),
            ).fetchone()
            assert row is not None
            filing_ids[f.accession] = row[0]
        with conn.cursor() as cur, cur.copy(COPY_CHUNKS) as copy:
            for chunk in read_chunks(chunks_path):
                if chunk.accession not in filing_ids:
                    raise KeyError(f"chunk for a filing not in the manifest: {chunk.accession}")
                copy.write_row(
                    (
                        filing_ids[chunk.accession],
                        chunk.item,
                        chunk.chunk_index,
                        chunk.char_start,
                        chunk.char_end,
                        chunk.text,
                    )
                )
    counts = {}
    for table in ("companies", "filings", "chunks"):
        row = conn.execute(f"SELECT count(*) FROM {table}").fetchone()  # fixed table names
        counts[table] = int(row[0]) if row else 0
    conn.commit()
    return counts
