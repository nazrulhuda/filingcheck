"""Apply the numbered SQL files in `migrations/` once each, in order.

Each file runs in its own transaction and is recorded in `schema_migrations`, so running
the migrations again applies only new files.
"""

import re
from pathlib import Path

import psycopg

from filingcheck.db import EMBEDDING_DIMENSIONS

MIGRATIONS_DIR = Path(__file__).resolve().parent / "migrations"
PLACEHOLDER_RE = re.compile(r"\{\{([A-Z_]+)\}\}")
PLACEHOLDERS = {"EMBEDDING_DIMENSIONS": str(EMBEDDING_DIMENSIONS)}

SCHEMA_TABLE = """
CREATE TABLE IF NOT EXISTS schema_migrations (
    version    text PRIMARY KEY,
    applied_at timestamptz NOT NULL DEFAULT now()
)
"""


def migration_files() -> list[Path]:
    """The migration files, in the order they apply."""
    return sorted(MIGRATIONS_DIR.glob("[0-9][0-9][0-9][0-9]_*.sql"))


def render(sql: str) -> str:
    """Fill in `{{NAME}}` placeholders, such as the embedding size, from Python constants."""

    def value(match: re.Match[str]) -> str:
        name = match.group(1)
        if name not in PLACEHOLDERS:
            raise ValueError(f"unknown placeholder in a migration: {name}")
        return PLACEHOLDERS[name]

    return PLACEHOLDER_RE.sub(value, sql)


def migrate(conn: psycopg.Connection) -> list[str]:
    """Apply every migration not applied yet; return the names of the ones applied now."""
    conn.execute(SCHEMA_TABLE)
    done = {row[0] for row in conn.execute("SELECT version FROM schema_migrations").fetchall()}
    conn.commit()
    applied: list[str] = []
    for path in migration_files():
        if path.stem in done:
            continue
        with conn.transaction():
            conn.execute(render(path.read_text(encoding="utf-8")).encode())
            conn.execute("INSERT INTO schema_migrations (version) VALUES (%s)", (path.stem,))
        applied.append(path.stem)
    return applied
