"""The lookup on the real facts: from the files (golden facts) and from Postgres."""

import json
from decimal import Decimal
from pathlib import Path

import pytest
import yaml

from filingcheck.facts.lookup import JsonlFacts, lookup

REPO = Path(__file__).resolve().parents[2]
FACTS_FILE = REPO / "data" / "facts.jsonl"
GOLDEN = REPO / "tests" / "golden_facts.yaml"


@pytest.mark.slow
@pytest.mark.skipif(not FACTS_FILE.exists(), reason="no data/facts.jsonl; run `make ingest` first")
def test_every_golden_fact_is_reproduced_through_the_lookup() -> None:
    source = JsonlFacts(
        REPO / "data" / "manifest.json", REPO / "data" / "companies.yaml", FACTS_FILE
    )
    golden = [
        r
        for r in yaml.safe_load(GOLDEN.read_text(encoding="utf-8"))["facts"]
        if r["verified_by_hand"]
    ]
    assert len(golden) == 4
    for fact in golden:
        result = lookup(source, fact["ticker"], fact["fiscal_year"], fact["metric"])
        assert result is not None, fact["id"]
        assert result.concept == fact["xbrl_tag"], fact["id"]
        assert result.value == Decimal(fact["value"]), fact["id"]
        assert result.period_end == fact["period_end"], fact["id"]
        assert result.unit == fact["unit"], fact["id"]


def test_the_file_source_matches_what_the_facts_stage_writes(tmp_path: Path) -> None:
    manifest = {
        "filings": [
            {
                "ticker": "EXMP",
                "cik": "0000999999",
                "fiscal_year": 2025,
                "fiscal_year_source": "dei",
                "form": "10-K",
                "accession": "0000999999-26-000001",
                "filing_date": "2026-02-20",
                "period_of_report": "2025-12-31",
                "primary_document_url": "https://www.sec.gov/x.htm",
                "document_path": "data/filings/EXMP/x.html",
                "extra_documents": [],
            }
        ]
    }
    (tmp_path / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    (tmp_path / "companies.yaml").write_text(
        "companies:\n- ticker: EXMP\n  name: Example\n  cik: '0000999999'\n  sector: banking\n"
        "  fiscal_year_end: 12\n  revenue_rule: bank\n  financebench: false\n"
        "  aliases: [Example]\n",
        encoding="utf-8",
    )
    row = {
        "accession": "0000999999-26-000001",
        "ticker": "EXMP",
        "fiscal_year": 2025,
        "concept": "us-gaap:RevenuesNetOfInterestExpense",
        "value": "1234000000",
        "unit": "USD",
        "period_start": "2025-01-01",
        "period_end": "2025-12-31",
        "instant": None,
        "decimals": "-6",
        "scale": 6,
        "sign": None,
        "dimensions": {},
        "context_ref": "c-1",
        "conflict": False,
    }
    (tmp_path / "facts.jsonl").write_text(json.dumps(row) + "\n", encoding="utf-8")
    source = JsonlFacts(
        tmp_path / "manifest.json", tmp_path / "companies.yaml", tmp_path / "facts.jsonl"
    )
    filing = source.filing("EXMP", 2025)
    assert filing is not None and filing.revenue_rule == "bank"
    result = lookup(source, "EXMP", 2025, "revenue")
    assert result is not None and result.value == 1234000000
