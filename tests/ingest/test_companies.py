from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from filingcheck.ingest.companies import (
    TICKERS_URL,
    Company,
    CompanyResolutionError,
    load_companies,
    pad_cik,
    resolve_ciks,
    save_companies,
    update_companies_file,
)

YAML = """\
companies:
  - ticker: AAPL
    name: Apple Inc.
    sector: technology
    fiscal_year_end: 9
    revenue_rule: standard
    financebench: true
    aliases: [Apple, AAPL]
  - ticker: JPM
    name: JPMorgan Chase & Co.
    sector: banking
    fiscal_year_end: 12
    revenue_rule: bank
    financebench: true
    aliases: [JPMorgan, Chase]
"""

TICKERS: dict[str, Any] = {
    "0": {"cik_str": 320193, "ticker": "AAPL", "title": "Apple Inc."},
    "1": {"cik_str": 19617, "ticker": "JPM", "title": "JPMORGAN CHASE & CO"},
    "2": {"cik_str": 789019, "ticker": "MSFT", "title": "MICROSOFT CORP"},
}


def write(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "companies.yaml"
    path.write_text(text, encoding="utf-8")
    return path


def test_cik_is_zero_padded_to_10_digits() -> None:
    assert pad_cik(320193) == "0000320193"
    assert pad_cik("19617") == "0000019617"
    with pytest.raises(ValueError):
        pad_cik(12345678901)


def test_yaml_loads_into_the_model(tmp_path: Path) -> None:
    companies = load_companies(write(tmp_path, YAML))
    assert [c.ticker for c in companies] == ["AAPL", "JPM"]
    assert companies[0].fiscal_year_end == 9
    assert companies[1].revenue_rule == "bank"
    assert companies[0].cik is None


def test_an_unknown_revenue_rule_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(ValidationError):
        load_companies(write(tmp_path, YAML.replace("revenue_rule: bank", "revenue_rule: weird")))


def test_a_bad_fiscal_year_end_month_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(ValidationError):
        load_companies(write(tmp_path, YAML.replace("fiscal_year_end: 9", "fiscal_year_end: 13")))


def test_a_cik_that_is_not_10_digits_is_rejected() -> None:
    fields: dict[str, Any] = {
        "ticker": "AAPL",
        "name": "Apple Inc.",
        "sector": "technology",
        "fiscal_year_end": 9,
        "revenue_rule": "standard",
        "financebench": True,
        "aliases": ["Apple"],
    }
    assert Company(**fields, cik="0000320193").cik == "0000320193"
    with pytest.raises(ValidationError):
        Company(**fields, cik="320193")


def test_tickers_resolve_to_padded_ciks(tmp_path: Path) -> None:
    resolved = resolve_ciks(load_companies(write(tmp_path, YAML)), TICKERS)
    assert {c.ticker: c.cik for c in resolved} == {"AAPL": "0000320193", "JPM": "0000019617"}


def test_a_missing_ticker_fails_loudly_and_names_it(tmp_path: Path) -> None:
    companies = load_companies(write(tmp_path, YAML))
    tickers = {"0": TICKERS["0"]}
    with pytest.raises(CompanyResolutionError, match="JPM"):
        resolve_ciks(companies, tickers)


def test_save_then_load_round_trips(tmp_path: Path) -> None:
    path = write(tmp_path, YAML)
    resolved = resolve_ciks(load_companies(path), TICKERS)
    save_companies(path, resolved)
    assert load_companies(path) == resolved
    assert "'0000320193'" in path.read_text(encoding="utf-8")  # kept as text, leading zeros intact


class FakeClient:
    def __init__(self) -> None:
        self.urls: list[str] = []

    def get_json(self, url: str) -> Any:
        self.urls.append(url)
        return TICKERS


def test_update_companies_file_fetches_tickers_once_and_writes_ciks(tmp_path: Path) -> None:
    path = write(tmp_path, YAML)
    client = FakeClient()
    companies = update_companies_file(path, client)
    assert client.urls == [TICKERS_URL]
    assert all(c.cik for c in companies)
    assert [c.cik for c in load_companies(path)] == ["0000320193", "0000019617"]
