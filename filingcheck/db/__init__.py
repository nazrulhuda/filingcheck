"""The project database: one Postgres with pgvector for text, vectors, facts and eval results."""

import os

import psycopg
from dotenv import load_dotenv

# The only place the embedding size is set. The schema, the embedding code and the
# embeddings_meta check all read it from here.
EMBEDDING_DIMENSIONS = 1536

DEFAULT_DATABASE_URL = "postgresql://filingcheck:filingcheck@localhost:5432/filingcheck"


def database_url() -> str:
    """`DATABASE_URL` from the environment or `.env`, else the local database from `make db-up`."""
    load_dotenv()
    return os.environ.get("DATABASE_URL", "").strip() or DEFAULT_DATABASE_URL


def connect(url: str | None = None) -> psycopg.Connection:
    """Open a connection; the caller commits or uses `with conn.transaction()`."""
    return psycopg.connect(url or database_url())
