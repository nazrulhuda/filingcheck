"""Where the API keeps its request log and cached example answers: Postgres, or memory in tests."""

from datetime import datetime
from typing import Any, Protocol

import psycopg
from psycopg.types.json import Jsonb
from pydantic import BaseModel

from filingcheck.db import database_url

REFUSED = "refused:"  # error codes of requests the API turned away without calling a model
COLUMNS = (
    "id, created_at, question_hash, question, ticker, fiscal_year, model_used, retriever, "
    "degraded, latency_ms, prompt_tokens, completion_tokens, cost_usd, abstained, error, "
    "client_ip_hash, mode, tool_calls, checks, overrides"
)


class RequestRow(BaseModel):
    """One /ask or /ask/stream call. `error` holds only a short code, never a raw message."""

    id: str
    created_at: datetime
    question_hash: str
    question: str
    ticker: str | None = None
    fiscal_year: int | None = None
    model_used: str | None = None
    retriever: str | None = None
    degraded: bool = False
    latency_ms: float | None = None
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    cost_usd: float | None = None
    abstained: bool | None = None
    error: str | None = None
    client_ip_hash: str
    mode: str = "baseline"  # "baseline" or "agent"
    # The agent's tool calls, restarts and failed runs:
    # {"calls": [...], "restarts": [log codes], "failed_attempts": [...]}.
    tool_calls: dict[str, Any] | None = None
    # The agent's skeptical checks: whether they ran (NULL for the baseline) and their
    # override log, one record per check per checked tool call.
    checks: bool | None = None
    overrides: list[dict[str, Any]] | None = None


class CompanyInfo(BaseModel):
    """A company and the fiscal years it has filings for."""

    ticker: str
    name: str
    fiscal_years: list[int]


class ExampleAnswer(BaseModel):
    """A cached answer to one example question, as the `Answer` JSON, with its search filters."""

    question: str
    ticker: str | None = None
    fiscal_year: int | None = None
    answer: dict[str, Any]


def reached_a_model(row: RequestRow) -> bool:
    """True unless the API refused the request before calling a model."""
    return row.error is None or not row.error.startswith(REFUSED)


class Store(Protocol):
    """What the API reads and writes; every method opens its own connection."""

    def log_request(self, row: RequestRow) -> None:
        """Append one row to the request log."""
        ...

    def requests_since(self, since: datetime) -> list[RequestRow]:
        """Every logged request at or after `since`, oldest first."""
        ...

    def count_model_requests(self, since: datetime, client_ip_hash: str | None = None) -> int:
        """Requests since `since` that reached a model, for one address or all."""
        ...

    def companies(self) -> list[CompanyInfo]:
        """Companies with at least one filing, by ticker."""
        ...

    def examples(self) -> list[ExampleAnswer]:
        """The cached example answers, in the order they were saved."""
        ...

    def replace_examples(self, examples: list[ExampleAnswer]) -> None:
        """Replace every cached example answer at once."""
        ...

    def deep_health(self) -> dict[str, bool]:
        """Whether the database answers and embeddings_meta has a row."""
        ...


class MemoryStore:
    """The store in memory, for tests. `calls` records which methods were used."""

    def __init__(
        self,
        *,
        companies: list[CompanyInfo] | None = None,
        examples: list[ExampleAnswer] | None = None,
        embeddings_meta: bool = True,
    ) -> None:
        self.rows: list[RequestRow] = []
        self._companies = list(companies or [])
        self._examples = list(examples or [])
        self._embeddings_meta = embeddings_meta
        self.calls: list[str] = []

    def log_request(self, row: RequestRow) -> None:
        """Append one row."""
        self.calls.append("log_request")
        self.rows.append(row)

    def requests_since(self, since: datetime) -> list[RequestRow]:
        """Rows at or after `since`."""
        self.calls.append("requests_since")
        return sorted((r for r in self.rows if r.created_at >= since), key=lambda r: r.created_at)

    def count_model_requests(self, since: datetime, client_ip_hash: str | None = None) -> int:
        """Rows since `since` that reached a model."""
        self.calls.append("count_model_requests")
        return sum(
            1
            for r in self.rows
            if r.created_at >= since
            and reached_a_model(r)
            and (client_ip_hash is None or r.client_ip_hash == client_ip_hash)
        )

    def companies(self) -> list[CompanyInfo]:
        """The companies given at construction."""
        self.calls.append("companies")
        return list(self._companies)

    def examples(self) -> list[ExampleAnswer]:
        """The current example answers."""
        self.calls.append("examples")
        return list(self._examples)

    def replace_examples(self, examples: list[ExampleAnswer]) -> None:
        """Replace the example answers."""
        self.calls.append("replace_examples")
        self._examples = list(examples)

    def deep_health(self) -> dict[str, bool]:
        """Always reachable; embeddings as given at construction."""
        self.calls.append("deep_health")
        return {"database": True, "embeddings": self._embeddings_meta}


class PostgresStore:
    """The store in Postgres (tables `requests` and `example_answers`, migration 0006)."""

    def __init__(self, url: str | None = None) -> None:
        self.url = url or database_url()

    def _connect(self) -> psycopg.Connection:
        return psycopg.connect(self.url, connect_timeout=5)

    def log_request(self, row: RequestRow) -> None:
        """Insert one row."""
        values = row.model_dump()
        for name in ("tool_calls", "overrides"):
            if values[name] is not None:
                values[name] = Jsonb(values[name])
        with self._connect() as conn:
            conn.execute(
                f"INSERT INTO requests ({COLUMNS}) VALUES ("
                + ", ".join(f"%({name})s" for name in values)
                + ")",
                values,
            )

    def requests_since(self, since: datetime) -> list[RequestRow]:
        """Rows at or after `since`, oldest first."""
        with self._connect() as conn:
            cursor = conn.execute(
                f"SELECT {COLUMNS.replace('id, ', 'id::text, ', 1)} FROM requests "
                "WHERE created_at >= %s ORDER BY created_at",
                (since,),
            )
            names = [d.name for d in cursor.description or []]
            names[0] = "id"
            return [RequestRow(**dict(zip(names, r, strict=True))) for r in cursor.fetchall()]

    def count_model_requests(self, since: datetime, client_ip_hash: str | None = None) -> int:
        """Rows since `since` that reached a model, for one address or all."""
        sql = (
            "SELECT count(*) FROM requests WHERE created_at >= %(since)s "
            "AND (error IS NULL OR error NOT LIKE %(refused)s)"
        )
        params: dict[str, Any] = {"since": since, "refused": REFUSED + "%"}
        if client_ip_hash is not None:
            sql += " AND client_ip_hash = %(ip)s"
            params["ip"] = client_ip_hash
        with self._connect() as conn:
            row = conn.execute(sql, params).fetchone()
        return int(row[0]) if row else 0

    def companies(self) -> list[CompanyInfo]:
        """Companies with filings and their fiscal years, by ticker."""
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT c.ticker, c.name, array_agg(DISTINCT f.fiscal_year ORDER BY f.fiscal_year) "
                "FROM companies c JOIN filings f ON f.ticker = c.ticker "
                "GROUP BY c.ticker, c.name ORDER BY c.ticker"
            ).fetchall()
        return [CompanyInfo(ticker=t, name=n, fiscal_years=list(years)) for t, n, years in rows]

    def examples(self) -> list[ExampleAnswer]:
        """The cached example answers in saved order."""
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT question, ticker, fiscal_year, answer_json FROM example_answers ORDER BY id"
            ).fetchall()
        return [ExampleAnswer(question=q, ticker=t, fiscal_year=y, answer=a) for q, t, y, a in rows]

    def replace_examples(self, examples: list[ExampleAnswer]) -> None:
        """Delete every example answer and insert these, in one transaction."""
        with self._connect() as conn, conn.transaction():
            conn.execute("DELETE FROM example_answers")
            for example in examples:
                conn.execute(
                    "INSERT INTO example_answers (question, ticker, fiscal_year, answer_json) "
                    "VALUES (%s, %s, %s, %s)",
                    (example.question, example.ticker, example.fiscal_year, Jsonb(example.answer)),
                )

    def deep_health(self) -> dict[str, bool]:
        """Whether the database answers and embeddings_meta has a row."""
        try:
            with self._connect() as conn:
                row = conn.execute("SELECT EXISTS (SELECT 1 FROM embeddings_meta)").fetchone()
        except psycopg.Error:
            return {"database": False, "embeddings": False}
        return {"database": True, "embeddings": bool(row and row[0])}
