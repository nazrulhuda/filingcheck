from datetime import date
from pathlib import Path
from typing import Any

import httpx
import pytest

from filingcheck.ingest.filings import Filing, Manifest, primary_document_url
from filingcheck.ingest.sec_client import CacheMissError
from filingcheck.ingest.sections import (
    ITEMS,
    ItemText,
    build_sections,
    exhibit_13_documents,
    extract_items,
    filing_index_url,
    html_to_text,
    short_items,
    split_exhibit_13,
    split_items_by_heading,
)

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
MARKERS = {
    "1": "BUSINESS-MARKER",
    "1A": "RISK-MARKER",
    "7": "MDA-MARKER",
    "7A": "MARKET-RISK-MARKER",
    "8": "STATEMENTS-MARKER",
}


def fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


@pytest.fixture(autouse=True)
def no_network(monkeypatch: pytest.MonkeyPatch) -> None:
    """Any HTTP request from the parsers would fail the test."""

    def blocked(self: object, request: httpx.Request, *args: object, **kwargs: object) -> None:
        raise AssertionError(f"network call: {request.url}")

    monkeypatch.setattr(httpx.Client, "send", blocked)
    monkeypatch.setattr(httpx.AsyncClient, "send", blocked)


# ---------------------------------------------------------------- the heading splitter


def test_html_to_text_keeps_paragraphs_and_skips_hidden_xbrl() -> None:
    text = html_to_text(fixture("tenk_sample.html"))
    assert "DocumentFiscalYearFocus" not in text
    assert "2025\n" not in text.split("UNITED STATES")[0]  # the hidden XBRL value is dropped
    assert "\n\nBUSINESS-MARKER" in text


def test_the_heading_splitter_finds_all_five_items_and_skips_the_table_of_contents() -> None:
    items = split_items_by_heading(html_to_text(fixture("tenk_sample.html")))
    assert set(items) >= set(ITEMS)
    for item, marker in MARKERS.items():
        assert marker in items[item], item
        others = [m for i, m in MARKERS.items() if i != item]
        assert not any(m in items[item] for m in others), item
    assert items["1B"].strip().endswith("None.")


def test_extract_items_returns_every_item_with_the_method_used() -> None:
    items = extract_items(fixture("tenk_sample.html"))
    assert set(items) == set(ITEMS)
    for item, marker in MARKERS.items():
        assert marker in items[item].text, item
        assert items[item].method in ("edgartools", "regex")


def test_short_or_missing_items_are_listed() -> None:
    items = {
        "1": ItemText(text="x" * 3000, method="regex"),
        "7": ItemText(text="see the annual report", method="regex"),
    }
    assert short_items(items, min_chars=2000) == ["1A", "7", "7A", "8"]


# ---------------------------------------------------------------- Exhibit 13


def test_exhibit_13_documents_are_read_from_the_filing_index_page() -> None:
    assert exhibit_13_documents(fixture("filing_index_sample.html")) == ["ibm-20251231_d2.htm"]


def test_the_filing_index_url_uses_the_archive_layout() -> None:
    assert filing_index_url("0000051143", "0000051143-26-000010") == (
        "https://www.sec.gov/Archives/edgar/data/51143/000005114326000010/"
        "0000051143-26-000010-index.htm"
    )


def test_items_7_and_8_are_split_from_an_exhibit_13() -> None:
    parts = split_exhibit_13(html_to_text(fixture("ex13_sample.html")))
    assert parts is not None
    assert "EX13-MDA-MARKER" in parts["7"]
    assert "EX13-STATEMENTS-MARKER" not in parts["7"]
    assert parts["8"].startswith("Report of Independent Registered Public Accounting Firm")
    assert "EX13-STATEMENTS-MARKER" in parts["8"]
    assert "EX13-AFTER-MARKER" not in parts["8"]  # performance graphs are not financial statements


def test_an_exhibit_without_an_auditor_report_gives_nothing() -> None:
    assert split_exhibit_13("Letter to shareholders. We had a good year.") is None


# ---------------------------------------------------------------- the stage


IBM_CIK = "0000051143"
IBM_ACCESSION = "0000051143-26-000010"


def filing(document_path: str, ticker: str = "EXMP") -> Filing:
    return Filing(
        ticker=ticker,
        cik=IBM_CIK,
        fiscal_year=2025,
        fiscal_year_source="dei",
        form="10-K",
        accession=IBM_ACCESSION,
        filing_date=date(2026, 2, 24),
        period_of_report=date(2025, 12, 31),
        primary_document_url=primary_document_url(IBM_CIK, IBM_ACCESSION, "ibm-20251231.htm"),
        document_path=document_path,
    )


class FakeClient:
    def __init__(self, responses: dict[str, bytes]) -> None:
        self.responses = responses
        self.urls: list[str] = []

    def get_json(self, url: str) -> Any:
        raise AssertionError("not used")

    def get_bytes(self, url: str) -> bytes:
        self.urls.append(url)
        if url not in self.responses:
            raise CacheMissError(url)
        return self.responses[url]


def write_document(root: Path, html: str) -> str:
    path = "data/filings/EXMP/2025_0000051143-26-000010.html"
    (root / path).parent.mkdir(parents=True, exist_ok=True)
    (root / path).write_text(html, encoding="utf-8")
    return path


def test_build_sections_writes_item_files_and_a_summary(tmp_path: Path) -> None:
    path = write_document(tmp_path, fixture("tenk_sample.html"))
    client = FakeClient({})
    manifest, summary = build_sections(
        Manifest(filings=[filing(path)]), client, root=tmp_path, min_chars=100
    )
    assert client.urls == []  # nothing was short, so no exhibit lookup
    row = summary[0]
    assert set(row.items) == set(ITEMS)
    assert row.gaps == []
    item7 = tmp_path / "data/sections/EXMP/2025/item_7.txt"
    assert "MDA-MARKER" in item7.read_text(encoding="utf-8")
    assert row.items["7"].chars == len(item7.read_text(encoding="utf-8"))
    assert manifest.filings[0].extra_documents == []


def incorporated_by_reference() -> str:
    html = fixture("tenk_sample.html")
    start = html.index("<p>MDA-MARKER")
    end = html.index("<p>Item 9.")
    note = (
        "<p>Item 7. Management's Discussion and Analysis</p><p>Incorporated by reference to the"
        " Annual Report.</p><p>Item 7A. Quantitative and Qualitative Disclosures About Market"
        " Risk</p><p>Incorporated by reference to the Annual Report.</p><p>Item 8. Financial"
        " Statements and Supplementary Data</p><p>Incorporated by reference to the Annual"
        " Report.</p>"
    )
    return html[: html.index("<p>Item 7.")] + note + html[end:] if start < end else html


def test_short_items_7_and_8_are_taken_from_exhibit_13(tmp_path: Path) -> None:
    path = write_document(tmp_path, incorporated_by_reference())
    folder = primary_document_url(IBM_CIK, IBM_ACCESSION, "x").rsplit("/", 1)[0]
    client = FakeClient(
        {
            filing_index_url(IBM_CIK, IBM_ACCESSION): fixture("filing_index_sample.html").encode(),
            f"{folder}/ibm-20251231_d2.htm": fixture("ex13_sample.html").encode(),
        }
    )
    manifest, summary = build_sections(
        Manifest(filings=[filing(path)]), client, root=tmp_path, min_chars=100
    )
    row = summary[0]
    assert (row.items["7"].method, row.items["8"].method) == ("exhibit", "exhibit")
    assert "EX13-MDA-MARKER" in (tmp_path / "data/sections/EXMP/2025/item_7.txt").read_text(
        encoding="utf-8"
    )
    extra = manifest.filings[0].extra_documents
    assert [(e.type, e.url.rsplit("/", 1)[1]) for e in extra] == [("EX-13", "ibm-20251231_d2.htm")]
    assert (tmp_path / extra[0].document_path).exists()
    assert row.gaps == []


def test_a_missing_exhibit_is_listed_as_a_gap(tmp_path: Path) -> None:
    path = write_document(tmp_path, incorporated_by_reference())
    index_without_ex13 = fixture("filing_index_sample.html").replace("EX-13", "EX-99")
    client = FakeClient({filing_index_url(IBM_CIK, IBM_ACCESSION): index_without_ex13.encode()})
    _, summary = build_sections(
        Manifest(filings=[filing(path)]), client, root=tmp_path, min_chars=100
    )
    gaps = summary[0].gaps
    assert any("no Exhibit 13" in gap for gap in gaps)
    assert summary[0].items["8"].method in ("edgartools", "regex")  # kept, but flagged
