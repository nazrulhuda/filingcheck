"""Integration check on a real downloaded 10-K. Skipped unless `make ingest` has run."""

from pathlib import Path

import pytest

from filingcheck.ingest.sec_client import decode_document
from filingcheck.ingest.sections import (
    ITEMS,
    extract_items,
    html_to_text,
    relocate_financial_statements,
)

REPO = Path(__file__).resolve().parents[2]
APPLE = sorted((REPO / "data" / "filings" / "AAPL").glob("2025_*.html"))


@pytest.mark.slow
@pytest.mark.skipif(not APPLE, reason="no cached Apple 10-K; run `make ingest` first")
def test_a_real_apple_10k_splits_into_all_five_items() -> None:
    items = extract_items(APPLE[0].read_text(encoding="utf-8"))
    assert set(items) == set(ITEMS)
    assert len(items["7"].text) > 10_000
    assert len(items["8"].text) > 30_000
    assert items["7"].text.lstrip().startswith("Item 7")


RELOCATED = sorted(
    p for ticker in ("NFLX", "NVDA") for p in (REPO / "data" / "filings" / ticker).glob("*.html")
)


@pytest.mark.slow
@pytest.mark.skipif(not RELOCATED, reason="no cached Netflix or Nvidia 10-K; run `make ingest`")
@pytest.mark.parametrize("path", RELOCATED, ids=lambda p: p.name)
def test_netflix_and_nvidia_statements_are_found_in_the_10k(path: Path) -> None:
    statements = relocate_financial_statements(html_to_text(decode_document(path.read_bytes())))
    assert statements is not None
    assert statements.startswith("Report of Independent Registered Public Accounting Firm")
    assert "Internal Control Over Financial Reporting" not in statements[:400].title() or (
        "Financial Statements" in statements[:400]
    )
    assert "Consolidated Balance Sheet" in statements
    assert len(statements) > 50_000
    assert "exhibit index" not in statements.lower()[-2000:]
