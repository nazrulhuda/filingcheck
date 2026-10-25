"""Choose each company's last three 10-K filings, pin them in a manifest, and download them.

The filing lists come from the SEC's submissions JSON through `SecClient`, so every request
is rate-limited and cached. Once `data/manifest.json` exists, later runs use the filings it
pins instead of choosing again, so the evaluation always sees the same documents.
"""

import json
import re
from collections.abc import Iterable, Iterator
from datetime import date
from pathlib import Path
from typing import Any, Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field

from filingcheck.ingest.companies import Company
from filingcheck.ingest.sec_client import decode_document

SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"
SUBMISSIONS_PAGE_URL = "https://data.sec.gov/submissions/{name}"
ARCHIVE_URL = "https://www.sec.gov/Archives/edgar/data/{cik}/{folder}/{document}"
ORIGINAL_FORM = "10-K"
AMENDED_FORM = "10-K/A"
FISCAL_YEARS = 3

DEI_FISCAL_YEAR_RE = re.compile(
    r'<ix:nonNumeric\b[^>]*\bname="dei:DocumentFiscalYearFocus"[^>]*>(.*?)</ix:nonNumeric>',
    re.IGNORECASE | re.DOTALL,
)
TAG_RE = re.compile(r"<[^>]+>")


class FiscalYearEndMismatchError(ValueError):
    """A filing's period of report does not match the company's fiscal-year-end month."""


class NotEnoughFilingsError(LookupError):
    """A company has fewer annual filings than the dataset needs."""


class SecFetcher(Protocol):
    """The parts of `SecClient` this module uses."""

    def get_json(self, url: str) -> Any:
        """Return the body of `url` parsed as JSON."""
        ...

    def get_bytes(self, url: str) -> bytes:
        """Return the body of `url`."""
        ...


class FilingRow(BaseModel):
    """One row of a company's SEC filing list."""

    model_config = ConfigDict(frozen=True)

    form: str
    accession: str
    filing_date: date
    report_date: date | None
    primary_document: str


class ExtraDocument(BaseModel):
    """A document of the filing besides the primary one, such as an Exhibit 13 annual report."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    type: str
    url: str
    document_path: str


class Filing(BaseModel):
    """One pinned 10-K filing in the manifest."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    ticker: str
    cik: str
    fiscal_year: int
    fiscal_year_source: Literal["dei", "derived"]
    form: str
    accession: str
    filing_date: date
    period_of_report: date
    primary_document_url: str
    document_path: str
    extra_documents: list[ExtraDocument] = Field(default_factory=list)


class Manifest(BaseModel):
    """Every filing the dataset uses, pinned by accession number."""

    model_config = ConfigDict(extra="forbid")

    filings: list[Filing]


def derive_fiscal_year(period: date, fiscal_year_end: int) -> int:
    """Name a fiscal year by the calendar year it ends in.

    A 52/53-week year can end a few days into the following month (Costco's FY2024 ended
    Sept 1, 2024); those days count as the fiscal-year-end month.
    """
    year, month = period.year, period.month
    if period.day <= 7 and month == fiscal_year_end % 12 + 1:
        month -= 1
        if month == 0:
            year -= 1
    return year


def check_fiscal_year_end(company: Company, period: date) -> None:
    """Fail unless the period ends in the company's fiscal-year-end month, give or take one."""
    if (period.month - company.fiscal_year_end) % 12 not in (0, 1, 11):
        raise FiscalYearEndMismatchError(
            f"{company.ticker}: a 10-K period ends on {period}, but companies.yaml says the "
            f"fiscal year ends in month {company.fiscal_year_end}"
        )


def read_dei_fiscal_year(html: str) -> int | None:
    """Return the DocumentFiscalYearFocus tagged in a 10-K's inline XBRL, if there is one."""
    match = DEI_FISCAL_YEAR_RE.search(html)
    if not match:
        return None
    text = TAG_RE.sub("", match.group(1)).strip()
    return int(text) if re.fullmatch(r"\d{4}", text) else None


def _rows(columns: dict[str, list[Any]]) -> Iterator[FilingRow]:
    for i, form in enumerate(columns["form"]):
        report = columns["reportDate"][i]
        yield FilingRow(
            form=form,
            accession=columns["accessionNumber"][i],
            filing_date=date.fromisoformat(columns["filingDate"][i]),
            report_date=date.fromisoformat(report) if report else None,
            primary_document=columns["primaryDocument"][i],
        )


def submission_rows(client: SecFetcher, cik: str) -> Iterator[FilingRow]:
    """Yield a company's filings, newest first, fetching older pages only when needed."""
    data = client.get_json(SUBMISSIONS_URL.format(cik=cik))
    yield from _rows(data["filings"]["recent"])
    for page in data["filings"].get("files", []):
        yield from _rows(client.get_json(SUBMISSIONS_PAGE_URL.format(name=page["name"])))


def select_annual_filings(
    company: Company, rows: Iterable[FilingRow], years: int = FISCAL_YEARS
) -> list[tuple[FilingRow, int]]:
    """Choose the filing for each of the latest `years` fiscal years, newest first.

    The original 10-K wins; a 10-K/A is used only when the original is missing. Rows come
    newest first, so reading stops as soon as the latest years all have an original.
    """
    chosen: dict[int, FilingRow] = {}
    for row in rows:
        if row.form not in (ORIGINAL_FORM, AMENDED_FORM) or row.report_date is None:
            continue
        fiscal_year = derive_fiscal_year(row.report_date, company.fiscal_year_end)
        current = chosen.get(fiscal_year)
        if current is None or (current.form == AMENDED_FORM and row.form == ORIGINAL_FORM):
            chosen[fiscal_year] = row
        latest = sorted(chosen, reverse=True)[:years]
        if len(latest) == years and all(chosen[fy].form == ORIGINAL_FORM for fy in latest):
            break
    latest = sorted(chosen, reverse=True)[:years]
    if len(latest) < years:
        raise NotEnoughFilingsError(
            f"{company.ticker}: found 10-Ks for {len(latest)} fiscal years, need {years}"
        )
    return [(chosen[fy], fy) for fy in latest]


def primary_document_url(cik: str, accession: str, document: str) -> str:
    """The EDGAR archive URL of a filing's primary document."""
    return ARCHIVE_URL.format(cik=int(cik), folder=accession.replace("-", ""), document=document)


def document_path(ticker: str, fiscal_year: int, accession: str) -> str:
    """Where a filing's primary document is saved, relative to the repository root."""
    return f"data/filings/{ticker}/{fiscal_year}_{accession}.html"


def write_atomic(path: Path, body: bytes) -> None:
    """Write a file through a temporary name, so an interrupted run never leaves half of it."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_bytes(body)
    tmp.replace(path)


def build_manifest(companies: list[Company], client: SecFetcher, root: Path) -> Manifest:
    """Choose, check and download the latest three 10-Ks for every company."""
    filings: list[Filing] = []
    for company in companies:
        if company.cik is None:
            raise ValueError(f"{company.ticker} has no CIK; run the companies stage first")
        for row, derived in select_annual_filings(company, submission_rows(client, company.cik)):
            assert row.report_date is not None  # select_annual_filings skips rows without one
            check_fiscal_year_end(company, row.report_date)
            url = primary_document_url(company.cik, row.accession, row.primary_document)
            body = client.get_bytes(url)
            dei = read_dei_fiscal_year(decode_document(body))
            if dei is not None and dei != derived:
                print(
                    f"note: {company.ticker} {row.accession}: DocumentFiscalYearFocus is {dei}, "
                    f"but the period ending {row.report_date} gives {derived}; using {dei}"
                )
            fiscal_year = dei if dei is not None else derived
            path = document_path(company.ticker, fiscal_year, row.accession)
            write_atomic(root / path, body)
            filings.append(
                Filing(
                    ticker=company.ticker,
                    cik=company.cik,
                    fiscal_year=fiscal_year,
                    fiscal_year_source="dei" if dei is not None else "derived",
                    form=row.form,
                    accession=row.accession,
                    filing_date=row.filing_date,
                    period_of_report=row.report_date,
                    primary_document_url=url,
                    document_path=path,
                )
            )
    return Manifest(filings=sorted(filings, key=lambda f: (f.ticker, f.fiscal_year)))


def write_manifest(path: Path, manifest: Manifest) -> None:
    """Write the manifest as JSON, sorted by ticker and then fiscal year."""
    ordered = Manifest(filings=sorted(manifest.filings, key=lambda f: (f.ticker, f.fiscal_year)))
    text = json.dumps(ordered.model_dump(mode="json"), indent=2) + "\n"
    path.write_text(text, encoding="utf-8", newline="\n")


def load_manifest(path: Path) -> Manifest:
    """Read and validate the manifest."""
    return Manifest.model_validate_json(path.read_text(encoding="utf-8"))


def ensure_documents(manifest: Manifest, client: SecFetcher, root: Path) -> int:
    """Save any pinned document that is missing on disk; return how many were saved."""
    saved = 0
    for filing in manifest.filings:
        path = root / filing.document_path
        if path.exists():
            continue
        write_atomic(path, client.get_bytes(filing.primary_document_url))
        saved += 1
    return saved
