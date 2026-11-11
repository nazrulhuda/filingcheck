"""The API's request log, example answers, companies and deep health in Postgres (integration)."""

from datetime import UTC, datetime, timedelta

import psycopg
import pytest

from filingcheck.app.store import ExampleAnswer, PostgresStore
from filingcheck.db.migrate import migrate
from tests.app.test_api import row

pytestmark = pytest.mark.integration


@pytest.fixture
def store(db: psycopg.Connection, fresh_db_url: str) -> PostgresStore:
    migrate(db)
    db.execute(
        "INSERT INTO companies (ticker, cik, name, sector, fiscal_year_end, revenue_rule) VALUES "
        "('WMT', '0000104169', 'Walmart Inc.', 'Consumer Staples', 1, 'standard'), "
        "('AAPL', '0000320193', 'Apple Inc.', 'Technology', 9, 'standard')"
    )
    for ticker, cik, year in [("WMT", "0000104169", 2026), ("WMT", "0000104169", 2025)]:
        db.execute(
            "INSERT INTO filings (ticker, cik, accession, form, filing_date, period_of_report, "
            "fiscal_year, primary_url) VALUES (%s, %s, %s, '10-K', '2026-03-01', '2026-01-31', "
            "%s, 'https://www.sec.gov/x.htm')",
            (ticker, cik, f"acc-{year}", year),
        )
    db.commit()
    return PostgresStore(fresh_db_url)


def test_a_logged_request_reads_back_unchanged(store: PostgresStore) -> None:
    logged = row(1, error="groq 429 rate_limit_exceeded", ticker="WMT", fiscal_year=2025)
    store.log_request(logged)
    (back,) = store.requests_since(datetime.now(UTC) - timedelta(hours=1))
    assert back == logged


def test_counts_include_model_requests_only_within_the_window_and_address(
    store: PostgresStore,
) -> None:
    now = datetime.now(UTC)
    store.log_request(row(1))
    store.log_request(row(2, error="groq 429 rate_limit_exceeded"))
    store.log_request(row(3, error="refused:daily_cap", model_used=None))
    store.log_request(row(4, created_at=now - timedelta(hours=2)))
    store.log_request(row(5, client_ip_hash="someone-else"))
    since = now - timedelta(hours=1)
    assert store.count_model_requests(since) == 3
    assert store.count_model_requests(since, client_ip_hash=row(0).client_ip_hash) == 2


def test_companies_list_their_fiscal_years_in_order(store: PostgresStore) -> None:
    companies = store.companies()
    assert [(c.ticker, c.fiscal_years) for c in companies] == [("WMT", [2025, 2026])]
    assert companies[0].name == "Walmart Inc."


def test_examples_are_replaced_as_a_whole(store: PostgresStore) -> None:
    store.replace_examples([ExampleAnswer(question="Old?", answer={"text": "old"})])
    new = [
        ExampleAnswer(
            question="First?", ticker="WMT", fiscal_year=2026, answer={"text": "1", "citations": []}
        ),
        ExampleAnswer(question="Second?", answer={"text": "two", "citations": []}),
    ]
    store.replace_examples(new)
    assert store.examples() == new


def test_deep_health_needs_embeddings_meta(store: PostgresStore, db: psycopg.Connection) -> None:
    assert store.deep_health() == {"database": True, "embeddings": False}
    db.execute("INSERT INTO embeddings_meta (model, dimensions) VALUES ('m', 1536)")
    db.commit()
    assert store.deep_health() == {"database": True, "embeddings": True}


def test_deep_health_reports_an_unreachable_database() -> None:
    down = PostgresStore("postgresql://nobody:x@127.0.0.1:1/none?connect_timeout=1")
    assert down.deep_health() == {"database": False, "embeddings": False}


def test_the_number_labels_read_back_unchanged(store: PostgresStore) -> None:
    labels = [{"figure": "$5 billion", "value": "5000000000", "label": "unverified"}]
    logged = row(2, mode="agent", number_labels=labels)
    store.log_request(logged)
    (back,) = store.requests_since(datetime.now(UTC) - timedelta(hours=1))
    assert back.number_labels == labels
