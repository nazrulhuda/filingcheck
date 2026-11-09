"""The real reference data the checks read, and a helper to run one check on one call."""

from typing import Any

from filingcheck.checks import CheckContext, CheckedCall, CheckResult
from filingcheck.ingest.companies import load_companies, load_not_covered
from filingcheck.ingest.filings import load_manifest
from filingcheck.paths import DATA_DIR

COMPANIES = load_companies(DATA_DIR / "companies.yaml")
NOT_COVERED = load_not_covered(DATA_DIR / "companies.yaml")
MANIFEST = load_manifest(DATA_DIR / "manifest.json")


def run_check(
    check: Any,
    question: str,
    *,
    ticker: str = "AAPL",
    fiscal_year: int = 2025,
    metric: str = "revenue",
    page_ticker: str | None = None,
    page_year: int | None = None,
    facts: Any = None,
) -> CheckResult:
    """Run `check` on a get_financial_fact call with these arguments and this question."""
    call = CheckedCall(
        "get_financial_fact", {"ticker": ticker, "fiscal_year": fiscal_year, "metric": metric}
    )
    context = CheckContext(
        question=question,
        ticker=page_ticker,
        fiscal_year=page_year,
        companies=COMPANIES,
        not_covered=NOT_COVERED,
        manifest=MANIFEST,
        facts=facts,
    )
    result: CheckResult = check.run(call, context)
    return result
