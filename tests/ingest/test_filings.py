import json
from datetime import date
from pathlib import Path
from typing import Any

import pytest

from filingcheck.ingest.companies import Company
from filingcheck.ingest.filings import (
    Filing,
    FiscalYearEndMismatchError,
    Manifest,
    NotEnoughFilingsError,
    build_manifest,
    check_fiscal_year_end,
    derive_fiscal_year,
    document_path,
    ensure_documents,
    load_manifest,
    primary_document_url,
    read_dei_fiscal_year,
    select_annual_filings,
    submission_rows,
    write_manifest,
)
from filingcheck.ingest.sec_client import CacheMissError


def company(ticker: str = "AAPL", fiscal_year_end: int = 9, cik: str = "0000320193") -> Company:
    return Company(
        ticker=ticker,
        name=f"{ticker} Inc.",
        cik=cik,
        sector="technology",
        fiscal_year_end=fiscal_year_end,
        revenue_rule="standard",
        financebench=False,
        aliases=[ticker],
    )


def columns(rows: list[tuple[str, str, str, str, str]]) -> dict[str, list[str]]:
    """Rows of (form, accession, filing date, report date, primary document) in SEC column form."""
    keys = ["form", "accessionNumber", "filingDate", "reportDate", "primaryDocument"]
    return {key: [row[i] for row in rows] for i, key in enumerate(keys)}


def ixbrl(fiscal_year: int) -> bytes:
    return (
        '<html><body><ix:nonNumeric contextRef="c-1" name="dei:DocumentFiscalYearFocus" '
        f'id="f-1"><span>{fiscal_year}</span></ix:nonNumeric><p>Annual report</p></body></html>'
    ).encode()


class FakeClient:
    """Serves canned SEC responses by URL and records which URLs were asked for."""

    def __init__(self, responses: dict[str, Any]) -> None:
        self.responses = responses
        self.urls: list[str] = []

    def get_json(self, url: str) -> Any:
        self.urls.append(url)
        return self.responses[url]

    def get_bytes(self, url: str) -> bytes:
        self.urls.append(url)
        if url not in self.responses:
            raise CacheMissError(url)
        body = self.responses[url]
        assert isinstance(body, bytes)
        return body


# ---------------------------------------------------------------- fiscal years


@pytest.mark.parametrize(
    ("period", "fiscal_year_end", "expected"),
    [
        (date(2025, 12, 31), 12, 2025),  # a December company
        (date(2022, 1, 1), 12, 2021),  # a 52/53-week year that ends a day into January
        (date(2025, 6, 30), 6, 2025),  # Microsoft: June
        (date(2025, 1, 31), 1, 2025),  # Walmart: FY2025 ended Jan 31, 2025
        (date(2025, 1, 26), 1, 2025),  # Nvidia: FY2025 ended Jan 26, 2025
        (date(2024, 9, 1), 8, 2024),  # Costco: FY2024 ended Sept 1, 2024
        (date(2025, 9, 27), 9, 2025),  # Apple: last Saturday of September
    ],
)
def test_fiscal_year_is_derived_from_the_period_end(
    period: date, fiscal_year_end: int, expected: int
) -> None:
    assert derive_fiscal_year(period, fiscal_year_end) == expected


def test_a_period_within_a_month_of_the_fiscal_year_end_passes() -> None:
    check_fiscal_year_end(company("AAPL", 9), date(2025, 9, 27))
    check_fiscal_year_end(company("COST", 8), date(2024, 9, 1))
    check_fiscal_year_end(company("KO", 12), date(2022, 1, 1))


def test_a_fiscal_year_end_mismatch_fails_and_names_the_company() -> None:
    with pytest.raises(FiscalYearEndMismatchError, match="MSFT"):
        check_fiscal_year_end(company("MSFT", 6), date(2025, 12, 31))


def test_the_dei_fiscal_year_is_read_from_inline_xbrl() -> None:
    assert read_dei_fiscal_year(ixbrl(2025).decode()) == 2025
    assert read_dei_fiscal_year("<html><body>no tags here</body></html>") is None


# ---------------------------------------------------------------- choosing filings


SUBMISSIONS = "https://data.sec.gov/submissions/CIK0000320193.json"
PAGE = "https://data.sec.gov/submissions/CIK0000320193-submissions-001.json"


def submissions() -> dict[str, Any]:
    recent = columns(
        [
            ("10-Q", "0000320193-26-000010", "2026-05-01", "2026-03-28", "q.htm"),
            ("10-K", "0000320193-25-000079", "2025-10-31", "2025-09-27", "k25.htm"),
            ("10-K/A", "0000320193-25-000002", "2025-01-15", "2024-09-28", "k24a.htm"),
            ("10-K", "0000320193-24-000123", "2024-11-01", "2024-09-28", "k24.htm"),
        ]
    )
    page = columns(
        [
            ("10-K", "0000320193-23-000106", "2023-11-03", "2023-09-30", "k23.htm"),
            ("10-K", "0000320193-22-000108", "2022-10-28", "2022-09-24", "k22.htm"),
        ]
    )
    return {
        SUBMISSIONS: {"filings": {"recent": recent, "files": [{"name": PAGE.rsplit("/", 1)[1]}]}},
        PAGE: page,
    }


def test_rows_come_from_the_recent_list_and_then_the_extra_pages() -> None:
    client = FakeClient(submissions())
    rows = list(submission_rows(client, "0000320193"))
    assert [r.accession for r in rows][-2:] == ["0000320193-23-000106", "0000320193-22-000108"]
    assert client.urls == [SUBMISSIONS, PAGE]


def test_extra_pages_are_not_fetched_once_three_years_are_found() -> None:
    data = submissions()
    data[SUBMISSIONS]["filings"]["recent"] = columns(
        [
            ("10-K", "a-25", "2025-10-31", "2025-09-27", "k25.htm"),
            ("10-K", "a-24", "2024-11-01", "2024-09-28", "k24.htm"),
            ("10-K", "a-23", "2023-11-03", "2023-09-30", "k23.htm"),
        ]
    )
    client = FakeClient(data)
    chosen = select_annual_filings(company(), submission_rows(client, "0000320193"))
    assert [fy for _, fy in chosen] == [2025, 2024, 2023]
    assert client.urls == [SUBMISSIONS]


def test_the_latest_three_fiscal_years_are_chosen_and_originals_beat_amendments() -> None:
    chosen = select_annual_filings(company(), submission_rows(FakeClient(submissions()), "x"))
    assert [(row.accession, fy) for row, fy in chosen] == [
        ("0000320193-25-000079", 2025),
        ("0000320193-24-000123", 2024),  # the original, not the 10-K/A
        ("0000320193-23-000106", 2023),
    ]


def test_an_amendment_is_used_when_the_original_is_missing() -> None:
    data = submissions()
    recent = data[SUBMISSIONS]["filings"]["recent"]
    original = recent["accessionNumber"].index("0000320193-24-000123")
    for values in recent.values():
        del values[original]
    chosen = select_annual_filings(company(), submission_rows(FakeClient(data), "x"))
    assert [row.form for row, _ in chosen] == ["10-K", "10-K/A", "10-K"]


def test_fewer_than_three_years_fails_loudly() -> None:
    data = submissions()
    data[SUBMISSIONS]["filings"]["files"] = []
    data[SUBMISSIONS]["filings"]["recent"] = columns(
        [("10-K", "a-25", "2025-10-31", "2025-09-27", "k25.htm")]
    )
    with pytest.raises(NotEnoughFilingsError, match="AAPL"):
        select_annual_filings(company(), submission_rows(FakeClient(data), "x"))


def test_the_primary_document_url_uses_the_archive_layout() -> None:
    assert primary_document_url("0000320193", "0000320193-25-000079", "aapl-20250927.htm") == (
        "https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/aapl-20250927.htm"
    )


# ---------------------------------------------------------------- manifest and downloads


def documents(data: dict[str, Any], years: dict[str, int]) -> dict[str, Any]:
    for doc, fiscal_year in years.items():
        accession = {
            "k25.htm": "0000320193-25-000079",
            "k24.htm": "0000320193-24-000123",
            "k23.htm": "0000320193-23-000106",
        }[doc]
        data[primary_document_url("0000320193", accession, doc)] = ixbrl(fiscal_year)
    return data


def test_build_manifest_downloads_documents_and_reads_the_dei_fiscal_year(tmp_path: Path) -> None:
    data = documents(submissions(), {"k25.htm": 2025, "k24.htm": 2024, "k23.htm": 2023})
    manifest = build_manifest([company()], FakeClient(data), root=tmp_path)
    assert [(f.fiscal_year, f.fiscal_year_source) for f in manifest.filings] == [
        (2023, "dei"),
        (2024, "dei"),
        (2025, "dei"),
    ]
    first = manifest.filings[0]
    assert first.document_path == "data/filings/AAPL/2023_0000320193-23-000106.html"
    assert (tmp_path / first.document_path).read_bytes() == ixbrl(2023)


def test_without_dei_tags_the_derived_fiscal_year_is_used(tmp_path: Path) -> None:
    data = documents(submissions(), {"k25.htm": 2025, "k24.htm": 2024, "k23.htm": 2023})
    data[primary_document_url("0000320193", "0000320193-23-000106", "k23.htm")] = b"<p>old</p>"
    manifest = build_manifest([company()], FakeClient(data), root=tmp_path)
    assert (manifest.filings[0].fiscal_year, manifest.filings[0].fiscal_year_source) == (
        2023,
        "derived",
    )


def test_a_dei_year_that_disagrees_with_the_period_is_reported(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    data = documents(submissions(), {"k25.htm": 2026, "k24.htm": 2024, "k23.htm": 2023})
    manifest = build_manifest([company()], FakeClient(data), root=tmp_path)
    assert manifest.filings[-1].fiscal_year == 2026
    assert "AAPL" in capsys.readouterr().out


def test_the_manifest_is_sorted_by_ticker_then_fiscal_year_and_round_trips(
    tmp_path: Path,
) -> None:
    def filing(ticker: str, fiscal_year: int) -> Filing:
        return Filing(
            ticker=ticker,
            cik="0000000001",
            fiscal_year=fiscal_year,
            fiscal_year_source="dei",
            form="10-K",
            accession=f"{ticker}-{fiscal_year}",
            filing_date=date(fiscal_year, 2, 1),
            period_of_report=date(fiscal_year - 1, 12, 31),
            primary_document_url="https://www.sec.gov/x.htm",
            document_path=document_path(ticker, fiscal_year, f"{ticker}-{fiscal_year}"),
        )

    path = tmp_path / "manifest.json"
    write_manifest(
        path, Manifest(filings=[filing("MSFT", 2024), filing("AAPL", 2025), filing("AAPL", 2023)])
    )
    raw = json.loads(path.read_text(encoding="utf-8"))
    assert [(f["ticker"], f["fiscal_year"]) for f in raw["filings"]] == [
        ("AAPL", 2023),
        ("AAPL", 2025),
        ("MSFT", 2024),
    ]
    assert raw["filings"][0]["filing_date"] == "2023-02-01"
    assert load_manifest(path) == Manifest.model_validate(raw)


def test_ensure_documents_only_downloads_what_is_missing(tmp_path: Path) -> None:
    data = documents(submissions(), {"k25.htm": 2025, "k24.htm": 2024, "k23.htm": 2023})
    manifest = build_manifest([company()], FakeClient(data), root=tmp_path)
    (tmp_path / manifest.filings[0].document_path).unlink()
    client = FakeClient(data)
    assert ensure_documents(manifest, client, root=tmp_path) == 1
    assert ensure_documents(manifest, client, root=tmp_path) == 0
    assert len(client.urls) == 1
