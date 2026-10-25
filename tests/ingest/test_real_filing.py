"""Integration check on a real downloaded 10-K. Skipped unless `make ingest` has run."""

from pathlib import Path

import pytest

from filingcheck.ingest.sections import ITEMS, extract_items

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
