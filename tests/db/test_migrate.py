import psycopg
import pytest

from filingcheck.db import EMBEDDING_DIMENSIONS
from filingcheck.db.migrate import migrate, migration_files, render

# ---------------------------------------------------------------- unit tests


def test_migrations_are_numbered_sql_files_in_order() -> None:
    names = [path.name for path in migration_files()]
    assert names == sorted(names)
    assert names[0].startswith("0001_") and names[0].endswith(".sql")


def test_the_embedding_dimension_comes_from_one_constant() -> None:
    sql = render("embedding halfvec({{EMBEDDING_DIMENSIONS}}) NULL")
    assert sql == f"embedding halfvec({EMBEDDING_DIMENSIONS}) NULL"
    assert EMBEDDING_DIMENSIONS == 1536


def test_an_unknown_placeholder_is_an_error() -> None:
    with pytest.raises(ValueError, match="NO_SUCH_THING"):
        render("select {{NO_SUCH_THING}}")


# ---------------------------------------------------------------- against Postgres

TABLES = {
    "companies",
    "filings",
    "chunks",
    "table_chunks",
    "facts",
    "embeddings_meta",
    "eval_questions",
    "eval_runs",
    "eval_answers",
    "schema_migrations",
}


def tables(conn: psycopg.Connection) -> set[str]:
    rows = conn.execute(
        "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
    ).fetchall()
    return {row[0] for row in rows}


@pytest.mark.integration
def test_migrations_apply_on_a_fresh_database(db: psycopg.Connection) -> None:
    applied = migrate(db)
    assert applied == [path.stem for path in migration_files()]
    assert tables(db) >= TABLES
    column = db.execute(
        "SELECT format_type(a.atttypid, a.atttypmod) FROM pg_attribute a "
        "WHERE a.attrelid = 'chunks'::regclass AND a.attname = 'embedding'"
    ).fetchone()
    assert column == (f"halfvec({EMBEDDING_DIMENSIONS})",)
    indexes = {row[0] for row in db.execute("SELECT indexname FROM pg_indexes").fetchall()}
    assert {"chunks_tsv_idx", "chunks_filing_item_idx"} <= indexes


@pytest.mark.integration
def test_running_the_migrations_again_changes_nothing(db: psycopg.Connection) -> None:
    migrate(db)
    assert migrate(db) == []


@pytest.mark.integration
def test_facts_reject_a_duplicate_instant_fact(db: psycopg.Connection) -> None:
    # Balance-sheet facts have no start date; NULLs must still count as equal.
    migrate(db)
    row = ("0000320193", "us-gaap", "Assets", "USD", 1, None, "2025-09-27", "acc-1")
    insert = (
        "INSERT INTO facts (cik, taxonomy, tag, unit, value, start_date, end_date, accession) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
    )
    db.execute(insert, row)
    with pytest.raises(psycopg.errors.UniqueViolation):
        db.execute(insert, row)


@pytest.mark.integration
def test_chunks_carry_their_boundary_and_other_items(db: psycopg.Connection) -> None:
    migrate(db)
    columns: dict[str, str] = dict(
        db.execute(
            "SELECT column_name, data_type FROM information_schema.columns "
            "WHERE table_name = 'chunks' AND column_name IN ('boundary', 'also_in')"
        ).fetchall()
    )
    assert columns == {"boundary": "text", "also_in": "ARRAY"}
