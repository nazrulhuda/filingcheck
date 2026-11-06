"""The skeptical checks: rules over a tool call's arguments, run before the tool.

`CHECKS` is the chain in order (company first; the fiscal-year, metric-and-period, units
and segment checks join it on Day 23). `reference_data` loads what the checks read from
`data/`, in the shape `ToolDeps` takes.
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
from filingcheck.ingest.companies import load_companies, load_not_covered
from filingcheck.ingest.filings import load_manifest
from filingcheck.paths import DATA_DIR

CHECKED_TOOL = "get_financial_fact"
CHECKS: tuple[Check, ...] = (CompanyCheck(),)


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
    "Check",
    "CheckContext",
    "CheckResult",
    "CheckedCall",
    "CompanyCheck",
    "Outcome",
    "Override",
    "reference_data",
    "run_checks",
]
