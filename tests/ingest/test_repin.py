"""The November re-pin: `filings --reselect` must see a 10-K filed after the first run."""

import json
from functools import partial
from pathlib import Path

import httpx
import pytest

from filingcheck.ingest import __main__ as cli
from filingcheck.ingest import sec_client
from filingcheck.ingest.companies import save_companies
from filingcheck.ingest.filings import SUBMISSIONS_URL
from filingcheck.ingest.sec_client import CacheMissError, RateLimiter, SecClient
from tests.ingest.test_filings import columns, company

APPLE_CIK = "0000320193"
TEN_KS = [
    ("10-K", "0000320193-25-000079", "2025-10-31", "2025-09-27", "k25.htm"),
    ("10-K", "0000320193-24-000123", "2024-11-01", "2024-09-28", "k24.htm"),
    ("10-K", "0000320193-23-000106", "2023-11-03", "2023-09-30", "k23.htm"),
]
FY2026 = ("10-K", "0000320193-26-000101", "2026-10-30", "2026-09-26", "k26.htm")


class FakeSec:
    """A sec.gov whose filing list can change between runs; counts each URL it serves."""

    def __init__(self) -> None:
        self.rows = list(TEN_KS)
        self.served: dict[str, int] = {}

    def handle(self, request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        self.served[url] = self.served.get(url, 0) + 1
        if url == SUBMISSIONS_URL.format(cik=APPLE_CIK):
            body = {"filings": {"recent": columns(self.rows), "files": []}}
            return httpx.Response(200, content=json.dumps(body).encode())
        return httpx.Response(200, content=b"<html><body><p>Annual report</p></body></html>")


def test_reselect_downloads_the_filing_list_again_and_picks_a_new_10k(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    sec = FakeSec()
    client = partial(
        SecClient,
        cache_dir=tmp_path / "cache",
        contact_email="test@example.com",
        limiter=RateLimiter(1_000_000),
        transport=httpx.MockTransport(sec.handle),
    )
    monkeypatch.setattr(sec_client, "SecClient", client)
    companies, manifest = tmp_path / "companies.yaml", tmp_path / "manifest.json"
    save_companies(companies, [company()])
    submissions = SUBMISSIONS_URL.format(cik=APPLE_CIK)

    assert cli.run_filings(companies, manifest, tmp_path) == 0
    first = json.loads(manifest.read_text(encoding="utf-8"))["filings"]
    assert [f["fiscal_year"] for f in first] == [2023, 2024, 2025]
    assert sec.served[submissions] == 1

    sec.rows = [FY2026, *TEN_KS]  # Apple files its FY2026 10-K
    assert cli.run_filings(companies, manifest, tmp_path, reselect=True) == 0
    second = json.loads(manifest.read_text(encoding="utf-8"))["filings"]
    assert sec.served[submissions] == 2  # the list was downloaded again, not read from cache
    assert [f["fiscal_year"] for f in second] == [2024, 2025, 2026]
    assert second[-1]["accession"] == FY2026[1]
    old_document = next(url for url in sec.served if url.endswith("k25.htm"))
    assert sec.served[old_document] == 1  # filing documents are never downloaded again


def test_refresh_downloads_again_and_overwrites_the_cache(tmp_path: Path) -> None:
    bodies = iter([b"first", b"second"])
    transport = httpx.MockTransport(lambda request: httpx.Response(200, content=next(bodies)))
    with SecClient(
        cache_dir=tmp_path,
        contact_email="test@example.com",
        limiter=RateLimiter(1_000_000),
        transport=transport,
    ) as client:
        url = "https://data.sec.gov/submissions/CIK0000320193.json"
        assert client.get_bytes(url) == b"first"
        assert client.get_bytes(url) == b"first"  # from the cache
        assert client.get_bytes(url, refresh=True) == b"second"
        assert client.get_bytes(url) == b"second"  # the cache now holds the new body
        assert client.downloads == 2


def test_refresh_in_cache_only_mode_is_a_cache_miss(tmp_path: Path) -> None:
    client = SecClient(cache_dir=tmp_path, cache_only=True, contact_email="test@example.com")
    with client, pytest.raises(CacheMissError):
        client.get_json("https://data.sec.gov/submissions/CIK0000320193.json", refresh=True)


class RecordingClient:
    """Answers every URL with the same JSON and records whether each call asked to refresh."""

    def __init__(self, body: dict[str, object]) -> None:
        self.body = body
        self.refreshed: list[bool] = []

    def get_json(self, url: str, refresh: bool = False) -> object:
        self.refreshed.append(refresh)
        return self.body

    def get_bytes(self, url: str, refresh: bool = False) -> bytes:
        self.refreshed.append(refresh)
        return json.dumps(self.body).encode()


def test_companyfacts_refresh_downloads_the_file_again(tmp_path: Path) -> None:
    from filingcheck.ingest.companyfacts import fetch_companyfacts

    client = RecordingClient({"facts": {"us-gaap": {"Revenues": {}}}})
    fetch_companyfacts(company(), client, tmp_path)
    fetch_companyfacts(company(), client, tmp_path, refresh=True)
    assert client.refreshed == [False, True]


def test_companies_refresh_downloads_the_ticker_list_again(tmp_path: Path) -> None:
    from filingcheck.ingest.companies import update_companies_file

    path = tmp_path / "companies.yaml"
    save_companies(path, [company()])
    client = RecordingClient({"0": {"ticker": "AAPL", "cik_str": 320193, "title": "Apple"}})
    update_companies_file(path, client, refresh=True)
    assert client.refreshed == [True]


@pytest.mark.parametrize("stage", ["companies", "companyfacts"])
def test_the_refresh_flag_reaches_the_stage(stage: str, monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[bool] = []
    monkeypatch.setattr(
        cli, f"run_{stage}", lambda *args, refresh=False: calls.append(refresh) or 0
    )
    assert cli.main([stage, "--refresh"]) == 0
    assert cli.main([stage]) == 0
    assert calls == [True, False]
