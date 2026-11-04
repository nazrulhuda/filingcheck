"""The lookup reading the facts table through PostgresFacts."""

from datetime import date
from decimal import Decimal
from pathlib import Path

import psycopg
import pytest

from filingcheck.facts.lookup import PostgresFacts, lookup


@pytest.mark.integration
def test_the_postgres_source_reads_one_filing_and_its_company_totals(
    db: psycopg.Connection, tmp_path: Path
) -> None:
    from filingcheck.db.load import load_all
    from filingcheck.db.migrate import migrate
    from filingcheck.ingest.filings import Manifest
    from tests.db.test_facts_db import apple_facts, write_facts
    from tests.db.test_load import APPLE, FILING, chunks, write_jsonl

    migrate(db)
    load_all(
        db,
        [APPLE],
        Manifest(filings=[FILING]),
        write_jsonl(tmp_path / "c.jsonl", chunks(2)),
        facts_path=write_facts(tmp_path / "f.jsonl", apple_facts()),
    )
    source = PostgresFacts(db)
    filing = source.filing("AAPL", 2025)
    assert filing is not None
    assert (filing.accession, filing.period_of_report, filing.revenue_rule) == (
        FILING.accession,
        date(2025, 9, 27),
        "standard",
    )
    assert source.filing("AAPL", 2023) is None
    result = lookup(source, "AAPL", 2025, "revenue")
    assert result is not None
    assert (result.value, result.concept, result.source_url) == (
        Decimal("416161000000"),
        "us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax",
        FILING.primary_document_url,
    )
    totals = source.facts(
        FILING.accession, ["us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax"]
    )
    assert len(totals) == 1  # the segment fact (ServiceMember) is not a company total
