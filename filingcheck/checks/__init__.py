"""The skeptical checks: rules over a tool call's arguments, run before the tool.

`CHECKS` is the chain in order: company, fiscal year, metric and period, units, segment.
`reference_data` loads what the checks read from `data/`, in the shape `ToolDeps` takes.

The rules are frozen from the Day 23 merge on 2026-11-09, like the agent's prompt: the
Week 6 measurement compares the agent with the checks off and on, so a change to any check
means re-running both arms (docs/decisions.md, docs/week4_notes.md). One check was added
after the freeze, on 2026-11-12: the fiscal-year check on `search_filings` (`SEARCH_CHECKS`),
with the Day 33 dry run as its evidence; both arms were re-run.
"""

from pathlib import Path
from typing import Any

from filingcheck.checks.base import (
    Check,
    CheckContext,
    CheckedCall,
    CheckResult,
    Outcome,
    Override,
    run_checks,
)
from filingcheck.checks.company import CompanyCheck
from filingcheck.checks.fiscal_year import FiscalYearCheck, SearchYearCheck
from filingcheck.checks.metric import MetricCheck
from filingcheck.checks.segment import SegmentCheck
from filingcheck.checks.units import UnitsCheck
from filingcheck.ingest.companies import load_companies, load_not_covered
from filingcheck.ingest.filings import load_manifest
from filingcheck.paths import DATA_DIR

CHECKED_TOOL = "get_financial_fact"
CHECKS: tuple[Check, ...] = (
    CompanyCheck(),
    FiscalYearCheck(),
    MetricCheck(),
    UnitsCheck(),
    SegmentCheck(),
)
# The fiscal-year check on search_filings was added after the freeze, on 2026-11-12, with the
# Day 33 dry run as evidence (docs/decisions.md); it applies in the checks-on arm only.
SEARCH_CHECKS: tuple[Check, ...] = (SearchYearCheck(),)
CHECKS_BY_TOOL: dict[str, tuple[Check, ...]] = {
    CHECKED_TOOL: CHECKS,
    "search_filings": SEARCH_CHECKS,
}


def reference_data(root: Path = DATA_DIR) -> dict[str, Any]:
    """The company list, the not-covered list and the manifest, for `ToolDeps(**...)`."""
    companies_path = root / "companies.yaml"
    return {
        "companies": load_companies(companies_path),
        "not_covered": load_not_covered(companies_path),
        "manifest": load_manifest(root / "manifest.json"),
    }


__all__ = [
    "CHECKED_TOOL",
    "CHECKS",
    "CHECKS_BY_TOOL",
    "SEARCH_CHECKS",
    "Check",
    "CheckContext",
    "CheckResult",
    "CheckedCall",
    "CompanyCheck",
    "Outcome",
    "Override",
    "SearchYearCheck",
    "reference_data",
    "run_checks",
]
