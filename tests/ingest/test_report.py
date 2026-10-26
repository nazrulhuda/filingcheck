from datetime import date

from filingcheck.ingest.companies import Company
from filingcheck.ingest.filings import Filing, Manifest
from filingcheck.ingest.report import build_report
from filingcheck.ingest.sections import ItemSummary, SectionSummary


def company(ticker: str, name: str, cik: str, fiscal_year_end: int = 12) -> Company:
    return Company(
        ticker=ticker,
        name=name,
        cik=cik,
        sector="technology",
        fiscal_year_end=fiscal_year_end,
        revenue_rule="standard",
        financebench=False,
        aliases=[ticker],
    )


COMPANIES = [
    company("IBM", "International Business Machines Corporation", "0000051143"),
    company("AAPL", "Apple Inc.", "0000320193", fiscal_year_end=9),
]


def filing(ticker: str, cik: str, year: int, accession: str) -> Filing:
    return Filing(
        ticker=ticker,
        cik=cik,
        fiscal_year=year,
        fiscal_year_source="dei",
        form="10-K",
        accession=accession,
        filing_date=date(year + 1, 2, 20),
        period_of_report=date(year, 12, 31),
        primary_document_url="https://www.sec.gov/x.htm",
        document_path=f"data/filings/{ticker}/{year}_{accession}.html",
    )


MANIFEST = Manifest(
    filings=[
        filing("AAPL", "0000320193", 2025, "0000320193-25-000079"),
        filing("IBM", "0000051143", 2025, "0000051143-26-000010"),
    ]
)


def items(method_7: str = "edgartools", chars_7a: int = 3_000) -> dict[str, ItemSummary]:
    return {
        "1": ItemSummary(chars=16_054, method="edgartools"),
        "1A": ItemSummary(chars=68_163, method="edgartools"),
        "7": ItemSummary(chars=18_238, method=method_7),  # type: ignore[arg-type]
        "7A": ItemSummary(chars=chars_7a, method="edgartools"),
        "8": ItemSummary(chars=62_223, method=method_7),  # type: ignore[arg-type]
    }


SUMMARIES = [
    SectionSummary(
        ticker="AAPL",
        fiscal_year=2025,
        accession="0000320193-25-000079",
        items=items(),
        short=[],
        gaps=[],
    ),
    SectionSummary(
        ticker="IBM",
        fiscal_year=2025,
        accession="0000051143-26-000010",
        items=items(method_7="exhibit", chars_7a=210),
        short=["7A"],
        gaps=[],
    ),
]
CHUNKS = {("0000320193-25-000079", "7"): 20, ("0000320193-25-000079", "8"): 60}
TAGS = {"AAPL": 503, "IBM": 611}


def report() -> str:
    return build_report(COMPANIES, MANIFEST, SUMMARIES, CHUNKS, TAGS)


def test_there_is_a_section_per_company_in_ticker_order() -> None:
    text = report()
    assert text.index("## AAPL") < text.index("## IBM")
    assert "Apple Inc. · CIK 0000320193 · fiscal year ends in September · 503 us-gaap tags" in text


def test_each_filing_row_shows_items_chunks_and_where_sections_came_from() -> None:
    text = report()
    assert "| 2025 | 0000320193-25-000079 | 2025-12-31 | 16,054 | 68,163 | 18,238 |" in text
    assert "| 80 |" in text  # 20 + 60 chunks for the Apple filing
    assert "18,238 (EX-13)" in text  # IBM's Item 7 came from its Exhibit 13


def test_the_totals_cover_every_company() -> None:
    text = report()
    assert "| Companies | 2 |" in text
    assert "| Filings | 2 |" in text
    assert "| Chunks | 80 |" in text
    assert "| us-gaap tags (all companies) | 1,114 |" in text


def test_short_items_and_moved_sections_are_listed() -> None:
    text = report()
    gaps = text[text.index("## Gaps") :]
    assert "IBM FY2025: Item 7A has 210 characters" in gaps
    assert "No filing is missing an Item." in gaps
    moved = text[text.index("## Sections taken from elsewhere") :]
    assert "IBM FY2025: Items 7, 8 from Exhibit 13" in moved


def test_the_report_is_the_same_every_time() -> None:
    assert report() == report()


def test_approximate_boundaries_and_removed_repeats_are_shown() -> None:
    approx = {
        item: ItemSummary(chars=found.chars, method=found.method, boundary="approximate")
        for item, found in items().items()
    }
    citi = SectionSummary(
        ticker="AAPL",
        fiscal_year=2025,
        accession="0000320193-25-000079",
        items=approx,
        short=[],
        gaps=[],
        cross_reference_index=True,
        repeats_removed=12,
    )
    text = build_report(COMPANIES, MANIFEST, [citi, SUMMARIES[1]], CHUNKS, TAGS)
    assert "16,054 (approx.)" in text
    approx_part = text[text.index("## Sections with approximate boundaries") :]
    assert "AAPL FY2025: Items 1, 1A, 7, 7A, 8" in approx_part
    assert "- AAPL FY2025: 12" in text[text.index("## Repeated passages removed") :]
