"""A fresh, empty database per integration test, dropped afterwards.

Uses the Postgres from `make db-up` (or the CI service container). Without one, the tests
are skipped locally; in CI, where `REQUIRE_DB=1`, they fail instead of being skipped.
"""

import os
import uuid
from collections.abc import Iterator

import psycopg
import pytest
from psycopg.conninfo import make_conninfo

DEFAULT_URL = "postgresql://filingcheck:filingcheck@localhost:5432/filingcheck"


@pytest.fixture
def fresh_db_url() -> Iterator[str]:
    url = os.environ.get("DATABASE_URL", DEFAULT_URL)
    try:
        admin = psycopg.connect(url, autocommit=True, connect_timeout=3)
    except psycopg.OperationalError as exc:
        if os.environ.get("REQUIRE_DB") == "1":
            raise
        pytest.skip(f"no Postgres at DATABASE_URL ({exc.__class__.__name__}); run `make db-up`")
    name = f"filingcheck_test_{uuid.uuid4().hex[:10]}"
    admin.execute(f'CREATE DATABASE "{name}"')
    try:
        yield make_conninfo(url, dbname=name)
    finally:
        admin.execute(f'DROP DATABASE "{name}" WITH (FORCE)')
        admin.close()


@pytest.fixture
def db(fresh_db_url: str) -> Iterator[psycopg.Connection]:
    with psycopg.connect(fresh_db_url) as conn:
        yield conn
