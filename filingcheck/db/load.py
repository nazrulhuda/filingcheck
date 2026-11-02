"""Load the companies, filings, chunks and number tables into Postgres, replacing what was there."""

from collections.abc import Iterator
from pathlib import Path

import psycopg
from psycopg.types.json import Jsonb

from filingcheck.embeddings import content_hash
from filingcheck.ingest.chunking import Chunk, TableChunk
from filingcheck.ingest.companies import Company
from filingcheck.ingest.filings import Manifest
from filingcheck.ingest.sections import load_summary

COPY_CHUNKS = (
    "COPY chunks (filing_id, item, chunk_index, char_start, char_end, text, boundary, also_in, "
    "content_hash) FROM STDIN"
)
COPY_TYPES = ["bigint", "text", "integer", "integer", "integer", "text", "text", "text[]", "text"]
COPY_TABLES = (
    "COPY table_chunks (filing_id, item, table_index, source_url, position, text) FROM STDIN"
)
COPY_TABLE_TYPES = ["bigint", "text", "integer", "text", "integer", "text"]


def read_chunks(path: Path) -> Iterator[Chunk]:
    """Read the chunks written by the chunks stage, one JSON object per line."""
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield Chunk.model_validate_json(line)


def read_table_chunks(path: Path) -> Iterator[TableChunk]:
    """Read the number tables written by the chunks stage, one JSON object per line."""
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield TableChunk.model_validate_json(line)


def load_all(
    conn: psycopg.Connection,
    companies: list[Company],
    manifest: Manifest,
    chunks_path: Path,
    table_chunks_path: Path | None = None,
    summary_path: Path | None = None,
) -> dict[str, int]:
    """Replace the companies, filings, chunks and number tables in one transaction.

    Returns the row counts and how many chunk embeddings were restored from the cache.
    Chunks and tables are bulk-loaded with COPY. A row whose filing is not in the manifest
    stops the load, and nothing is changed. Embeddings already paid for are put back by
    content hash, so reloading never loses them.
    """
    with conn.transaction():
        conn.execute(
            "TRUNCATE companies, filings, chunks, table_chunks, section_sources "
            "RESTART IDENTITY CASCADE"
        )
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
            copy.set_types(COPY_TYPES)
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
                        chunk.boundary,
                        chunk.also_in,
                        content_hash(chunk.text),
                    )
                )
        if table_chunks_path is not None:
            with conn.cursor() as cur, cur.copy(COPY_TABLES) as copy:
                copy.set_types(COPY_TABLE_TYPES)
                for table in read_table_chunks(table_chunks_path):
                    if table.accession not in filing_ids:
                        raise KeyError(f"table for a filing not in the manifest: {table.accession}")
                    copy.write_row(
                        (
                            filing_ids[table.accession],
                            table.item,
                            table.table_index,
                            table.source_url,
                            table.position,
                            table.text,
                        )
                    )
        if summary_path is not None:
            _load_section_sources(conn, manifest, summary_path, filing_ids)
        model = current_model(conn)
        restored = restore_embeddings(conn, model) if model else 0
    counts = {}
    for table_name in ("companies", "filings", "chunks", "table_chunks", "section_sources"):
        row = conn.execute(f"SELECT count(*) FROM {table_name}").fetchone()  # fixed names
        counts[table_name] = int(row[0]) if row else 0
    counts["embeddings_restored"] = restored
    conn.commit()
    return counts


def _load_section_sources(
    conn: psycopg.Connection, manifest: Manifest, summary_path: Path, filing_ids: dict[str, int]
) -> None:
    """Record each saved section's source document: the Exhibit 13 for exhibit sections."""
    filings = {f.accession: f for f in manifest.filings}
    rows = []
    for summary in load_summary(summary_path):
        filing = filings.get(summary.accession)
        if filing is None:
            raise KeyError(f"section summary for a filing not in the manifest: {summary.accession}")
        exhibits = [doc.url for doc in filing.extra_documents if doc.type == "EX-13"]
        for item, found in summary.items.items():
            url = (
                exhibits[0]
                if found.method == "exhibit" and exhibits
                else filing.primary_document_url
            )
            rows.append((filing_ids[summary.accession], item, found.method, url))
    with conn.cursor() as cur:
        cur.executemany(
            "INSERT INTO section_sources (filing_id, item, method, source_url) "
            "VALUES (%s, %s, %s, %s)",
            rows,
        )


def current_model(conn: psycopg.Connection) -> str | None:
    """The embedding model recorded in embeddings_meta, or None before the first embed."""
    row = conn.execute("SELECT model FROM embeddings_meta ORDER BY id DESC LIMIT 1").fetchone()
    return str(row[0]) if row else None


def restore_embeddings(conn: psycopg.Connection, model: str) -> int:
    """Copy cached vectors into chunks that have none, matched by content hash."""
    cursor = conn.execute(
        "UPDATE chunks c SET embedding = e.embedding FROM embedding_cache e "
        "WHERE e.model = %s AND e.content_hash = c.content_hash AND c.embedding IS NULL",
        (model,),
    )
    return cursor.rowcount
