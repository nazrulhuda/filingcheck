"""Download each company's XBRL "companyfacts" file: every number it has tagged in its filings.

Only cached and sanity-checked here; parsing the facts and mapping them to metrics comes
later.
"""

import json
from pathlib import Path

from filingcheck.ingest.companies import Company
from filingcheck.ingest.filings import SecFetcher, write_atomic

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


def fetch_companyfacts(company: Company, client: SecFetcher, root: Path) -> int:
    """Save the company's companyfacts file exactly as downloaded; return its us-gaap tag count."""
    if company.cik is None:
        raise ValueError(f"{company.ticker} has no CIK; run the companies stage first")
    body = client.get_bytes(companyfacts_url(company.cik))
    tags = count_us_gaap_tags(body)
    if tags == 0:
        raise CompanyFactsError(f"{company.ticker}: the companyfacts file has no us-gaap facts")
    write_atomic(root / companyfacts_path(company.ticker), body)
    return tags
