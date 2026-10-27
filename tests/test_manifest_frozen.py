"""The pinned filings must not change without a deliberate update of the expected list.

All 75 filings in `tests/expected_manifest.json` were checked one by one on sec.gov. The one
planned change is re-pinning Apple for its FY2026 10-K; that PR updates the expected file too.
"""

import json
from pathlib import Path

from filingcheck.paths import REPO_ROOT

FIELDS = ("ticker", "fiscal_year", "accession", "period_of_report", "filing_date")
EXPECTED = Path(__file__).parent / "expected_manifest.json"


def pinned() -> list[dict[str, object]]:
    filings = json.loads((REPO_ROOT / "data" / "manifest.json").read_text(encoding="utf-8"))
    return [{field: f[field] for field in FIELDS} for f in filings["filings"]]


def test_the_manifest_pins_exactly_the_checked_filings() -> None:
    expected = json.loads(EXPECTED.read_text(encoding="utf-8"))
    assert len(expected) == 75
    key = lambda row: (row["ticker"], row["fiscal_year"])  # noqa: E731
    assert sorted(pinned(), key=key) == sorted(expected, key=key)
