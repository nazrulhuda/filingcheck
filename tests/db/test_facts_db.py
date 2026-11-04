"""The facts table: migration 0007, the full load, and `load --only facts`."""

from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any

import psycopg
import pytest

from filingcheck.db.load import load_all, load_facts
from filingcheck.db.migrate import migrate
from filingcheck.ingest.facts import Fact
from filingcheck.ingest.filings import Manifest
from tests.db.test_load import APPLE, FILING, chunks, write_jsonl


def apple_facts(revenue: str = "416161000000") -> list[Fact]:
    common: dict[str, Any] = {
        "accession": FILING.accession,
        "ticker": "AAPL",
        "fiscal_year": 2025,
        "decimals": "-6",
        "scale": 6,
        "sign": None,
        "context_ref": "c-1",
    }
    return [
        Fact(
            concept="us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax",
            value=revenue,
            unit="USD",
            period_start=date(2024, 9, 29),
            period_end=date(2025, 9, 27),
            instant=None,
            dimensions={},
            conflict=False,
            **common,
        ),
        Fact(
            concept="us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax",
            value="109158000000",
            unit="USD",
            period_start=date(2024, 9, 29),
            period_end=date(2025, 9, 27),
            instant=None,
            dimensions={"srt:ProductOrServiceAxis": "us-gaap:ServiceMember"},
            conflict=False,
            **common,
        ),
        Fact(
            concept="us-gaap:Assets",
            value="359241000000",
            unit="USD",
            period_start=None,
            period_end=None,
            instant=date(2025, 9, 27),
            dimensions={},
            conflict=False,
            **common,
        ),
        Fact(
            concept="us-gaap:EarningsPerShareDiluted",
            value="7.46",
            unit="USD/shares",
            period_start=date(2024, 9, 29),
            period_end=date(2025, 9, 27),
            instant=None,
            dimensions={},
            conflict=False,
            **{**common, "decimals": "2", "scale": 0},
        ),
    ]


def write_facts(path: Path, rows: list[Fact]) -> Path:
    path.write_text("".join(f.model_dump_json() + "\n" for f in rows), encoding="utf-8")
    return path


@pytest.mark.integration
def test_the_facts_table_has_the_columns_of_the_facts_file(db: psycopg.Connection) -> None:
    migrate(db)
    columns: dict[str, str] = dict(
        db.execute(
            "SELECT column_name, data_type FROM information_schema.columns "
            "WHERE table_name = 'facts'"
        ).fetchall()
    )
    assert columns == {
        "id": "bigint",
        "filing_id": "bigint",
        "concept": "text",
        "value": "numeric",
        "unit": "text",
        "period_start": "date",
        "period_end": "date",
        "instant": "date",
        "decimals": "text",
        "scale": "integer",
        "sign": "text",
        "dimensions": "jsonb",
        "context_ref": "text",
        "conflict": "boolean",
    }
    indexes = {
        r[0] for r in db.execute("SELECT indexname FROM pg_indexes WHERE tablename = 'facts'")
    }
    assert {"facts_filing_concept_idx", "facts_filing_concept_totals_idx"} <= indexes


@pytest.mark.integration
def test_a_full_load_loads_the_facts_with_exact_values(
    db: psycopg.Connection, tmp_path: Path
) -> None:
    migrate(db)
    chunks_path = write_jsonl(tmp_path / "chunks.jsonl", chunks(4))
    facts_path = write_facts(tmp_path / "facts.jsonl", apple_facts())
    counts = load_all(db, [APPLE], Manifest(filings=[FILING]), chunks_path, facts_path=facts_path)
    assert counts["facts"] == 4
    row = db.execute(
        "SELECT value, unit, period_start, period_end, dimensions FROM facts "
        "WHERE concept LIKE '%RevenueFromContract%' AND dimensions = '{}'"
    ).fetchone()
    assert row == (Decimal("416161000000"), "USD", date(2024, 9, 29), date(2025, 9, 27), {})
    eps = db.execute(
        "SELECT value FROM facts WHERE concept = 'us-gaap:EarningsPerShareDiluted'"
    ).fetchone()
    assert eps == (Decimal("7.46"),)


@pytest.mark.integration
def test_loading_only_the_facts_leaves_passages_and_vectors_alone(
    db: psycopg.Connection, tmp_path: Path
) -> None:
    migrate(db)
    chunks_path = write_jsonl(tmp_path / "chunks.jsonl", chunks(4))
    load_all(
        db,
        [APPLE],
        Manifest(filings=[FILING]),
        chunks_path,
        facts_path=write_facts(tmp_path / "facts.jsonl", apple_facts()),
    )
    vector = "[" + ",".join(["0.01"] * 1536) + "]"
    db.execute("UPDATE chunks SET embedding = %s::halfvec", (vector,))
    db.commit()
    chunk_ids = [r[0] for r in db.execute("SELECT id FROM chunks ORDER BY id")]

    loaded = load_facts(db, write_facts(tmp_path / "facts2.jsonl", apple_facts("416161000001")[:2]))
    assert loaded == 2
    assert db.execute("SELECT count(*) FROM facts").fetchone() == (2,)
    assert db.execute("SELECT max(value) FROM facts WHERE dimensions = '{}'").fetchone() == (
        Decimal("416161000001"),
    )
    assert [r[0] for r in db.execute("SELECT id FROM chunks ORDER BY id")] == chunk_ids
    assert db.execute("SELECT count(*) FROM chunks WHERE embedding IS NULL").fetchone() == (0,)


@pytest.mark.integration
def test_facts_for_a_filing_not_in_the_database_stop_the_load(
    db: psycopg.Connection, tmp_path: Path
) -> None:
    migrate(db)
    load_all(
        db,
        [APPLE],
        Manifest(filings=[FILING]),
        write_jsonl(tmp_path / "c.jsonl", chunks(2)),
        facts_path=write_facts(tmp_path / "facts.jsonl", apple_facts()),
    )
    stranger = apple_facts()[0].model_copy(update={"accession": "0000000000-00-000000"})
    with pytest.raises(KeyError, match="0000000000-00-000000"):
        load_facts(db, write_facts(tmp_path / "bad.jsonl", [stranger]))
    db.rollback()
    assert db.execute("SELECT count(*) FROM facts").fetchone() == (4,)  # unchanged
