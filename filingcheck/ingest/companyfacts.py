"""Download each company's XBRL "companyfacts" file: every number it has tagged in its filings.

The numbers themselves come from each filing's own inline XBRL (`facts.py`); companyfacts
is only a cross-check, and each file in use is pinned by its SHA-256 and download time.
"""

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

from filingcheck.ingest.companies import Company
from filingcheck.ingest.filings import SecFetcher, write_atomic
from filingcheck.ingest.sec_client import cache_file

COMPANYFACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"


class CompanyFactsError(ValueError):
    """A companyfacts file is missing the us-gaap facts every US filer should have."""


def companyfacts_url(cik: str) -> str:
    """The SEC's companyfacts URL for a 10-digit CIK."""
    return COMPANYFACTS_URL.format(cik=cik)


def companyfacts_path(ticker: str) -> str:
    """Where a company's companyfacts file is saved, relative to the repository root."""
    return f"data/companyfacts/{ticker}.json"


def count_us_gaap_tags(body: bytes) -> int:
    """How many distinct us-gaap tags a companyfacts file holds (0 if none)."""
    facts = json.loads(body).get("facts", {})
    return len(facts.get("us-gaap", {}))


def fetch_companyfacts(
    company: Company, client: SecFetcher, root: Path, refresh: bool = False
) -> int:
    """Save the company's companyfacts file exactly as downloaded; return its us-gaap tag count.

    The file grows with every new filing, so `refresh=True` downloads it again (the re-pin).
    """
    if company.cik is None:
        raise ValueError(f"{company.ticker} has no CIK; run the companies stage first")
    body = client.get_bytes(companyfacts_url(company.cik), refresh=refresh)
    tags = count_us_gaap_tags(body)
    if tags == 0:
        raise CompanyFactsError(f"{company.ticker}: the companyfacts file has no us-gaap facts")
    write_atomic(root / companyfacts_path(company.ticker), body)
    return tags


PINS_FILE = "data/companyfacts_pins.json"


def count_pinned_us_gaap_tags(body: bytes, accessions: set[str]) -> int:
    """How many us-gaap tags have a fact from one of the pinned filings (`accessions`).

    Counting only the pinned filings' facts keeps the number the same when the SEC's file
    grows with later filings, so a fresh clone reproduces the data report.
    """
    tags = json.loads(body).get("facts", {}).get("us-gaap", {})
    return sum(
        1
        for entry in tags.values()
        if any(
            row.get("accn") in accessions
            for rows in entry.get("units", {}).values()
            for row in rows
        )
    )


def pin_entry(body: bytes, cached: Path) -> dict[str, object]:
    """A companyfacts file's pin: its SHA-256, its size and when its cached copy was saved."""
    saved = datetime.fromtimestamp(cached.stat().st_mtime, UTC)
    return {
        "sha256": hashlib.sha256(body).hexdigest(),
        "bytes": len(body),
        "downloaded_utc": saved.strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def write_pins(companies: list[Company], root: Path) -> None:
    """Record a pin for every company's companyfacts file in `data/companyfacts_pins.json`.

    The download time is the time the SEC client saved its cached copy, which must be
    byte-identical to the file in `data/companyfacts/`.
    """
    pins: dict[str, dict[str, object]] = {}
    for company in sorted(companies, key=lambda c: c.ticker):
        if company.cik is None:
            raise ValueError(f"{company.ticker} has no CIK; run the companies stage first")
        body = (root / companyfacts_path(company.ticker)).read_bytes()
        cached = cache_file(companyfacts_url(company.cik), root / "data" / "cache")
        if not cached.exists() or cached.read_bytes() != body:
            raise CompanyFactsError(
                f"{company.ticker}: no cached copy equal to its companyfacts file, so its "
                "download time is unknown"
            )
        pins[company.ticker] = pin_entry(body, cached)
    lines = ",\n".join(f"  {json.dumps(t)}: {json.dumps(pins[t])}" for t in pins)
    (root / PINS_FILE).write_text("{\n" + lines + "\n}\n", encoding="utf-8", newline="\n")
