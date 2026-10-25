import json
from pathlib import Path
from typing import Any

import pytest

from filingcheck.ingest.companies import Company
from filingcheck.ingest.companyfacts import (
    CompanyFactsError,
    companyfacts_path,
    companyfacts_url,
    fetch_companyfacts,
)

APPLE = Company(
    ticker="AAPL",
    name="Apple Inc.",
    cik="0000320193",
    sector="technology",
    fiscal_year_end=9,
    revenue_rule="standard",
    financebench=True,
    aliases=["Apple"],
)
FACTS: dict[str, Any] = {
    "cik": 320193,
    "entityName": "Apple Inc.",
    "facts": {
        "dei": {"EntityCommonStockSharesOutstanding": {}},
        "us-gaap": {"Assets": {}, "Revenues": {}, "NetIncomeLoss": {}},
    },
}


class FakeClient:
    def __init__(self, body: bytes) -> None:
        self.body = body
        self.urls: list[str] = []

    def get_json(self, url: str) -> Any:
        raise AssertionError("use get_bytes, so the file is saved exactly as downloaded")

    def get_bytes(self, url: str) -> bytes:
        self.urls.append(url)
        return self.body


def test_the_url_uses_the_10_digit_cik() -> None:
    assert companyfacts_url("0000320193") == (
        "https://data.sec.gov/api/xbrl/companyfacts/CIK0000320193.json"
    )


def test_fetch_saves_the_file_and_counts_the_us_gaap_tags(tmp_path: Path) -> None:
    client = FakeClient(json.dumps(FACTS).encode())
    assert fetch_companyfacts(APPLE, client, root=tmp_path) == 3
    assert client.urls == [companyfacts_url("0000320193")]
    saved = tmp_path / companyfacts_path("AAPL")
    assert saved == tmp_path / "data/companyfacts/AAPL.json"
    assert json.loads(saved.read_bytes()) == FACTS


def test_a_file_without_us_gaap_facts_fails_and_names_the_company(tmp_path: Path) -> None:
    body = json.dumps({"cik": 320193, "facts": {"dei": {}}}).encode()
    with pytest.raises(CompanyFactsError, match="AAPL"):
        fetch_companyfacts(APPLE, FakeClient(body), root=tmp_path)


def test_a_company_without_a_cik_fails(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="AAPL"):
        fetch_companyfacts(APPLE.model_copy(update={"cik": None}), FakeClient(b"{}"), tmp_path)
