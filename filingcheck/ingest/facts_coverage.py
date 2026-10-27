"""`make verify-facts`: which candidate XBRL tags have a 10-K fact for each pinned fiscal year.

Coverage only: it says whether a usable fact exists, not which one an answer should use.
A fact counts when it comes from a 10-K, ends on the filing's period of report and, for
amounts over a period, covers a whole fiscal year. Writes `docs/facts_coverage.md`.
"""

import json
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Literal

from filingcheck.ingest.companies import Company, load_companies
from filingcheck.ingest.companyfacts import companyfacts_path
from filingcheck.ingest.filings import Filing, load_manifest
from filingcheck.paths import REPO_ROOT

# A fiscal year in days: 365 or 366, or 364 and 371 for 52- and 53-week years. 10-Ks also
# carry quarters that end on the same day, which must not count.
ANNUAL_DAYS = range(350, 381)


@dataclass(frozen=True)
class Metric:
    """A metric and the tags that may hold it, in the order they are tried."""

    name: str
    tags: tuple[str, ...]  # "Tag" for us-gaap, "taxonomy:Tag" otherwise
    period: Literal["duration", "instant"]


METRICS = (
    Metric(
        "revenue",
        (
            "Revenues",
            "RevenueFromContractWithCustomerExcludingAssessedTax",
            "RevenuesNetOfInterestExpense",
            "SalesRevenueNet",
        ),
        "duration",
    ),
    Metric("net income", ("NetIncomeLoss", "ProfitLoss"), "duration"),
    Metric("diluted EPS", ("EarningsPerShareDiluted",), "duration"),
    Metric("operating income", ("OperatingIncomeLoss",), "duration"),
    Metric("total assets", ("Assets",), "instant"),
    Metric("total liabilities", ("Liabilities",), "instant"),
    Metric(
        "equity",
        (
            "StockholdersEquity",
            "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest",
        ),
        "instant",
    ),
    Metric("operating cash flow", ("NetCashProvidedByUsedInOperatingActivities",), "duration"),
    Metric("capex", ("PaymentsToAcquirePropertyPlantAndEquipment",), "duration"),
    Metric(
        "cash",
        (
            "CashAndCashEquivalentsAtCarryingValue",
            "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents",
        ),
        "instant",
    ),
    Metric("long-term debt", ("LongTermDebtNoncurrent", "LongTermDebt"), "instant"),
    Metric(
        "shares outstanding",
        ("dei:EntityCommonStockSharesOutstanding", "CommonStockSharesOutstanding"),
        "instant",
    ),
)


def _rows(facts: dict[str, Any], tag: str) -> list[dict[str, Any]]:
    taxonomy, _, name = tag.rpartition(":")
    entry = facts.get("facts", {}).get(taxonomy or "us-gaap", {}).get(name, {})
    return [row for unit_rows in entry.get("units", {}).values() for row in unit_rows]


def _days(row: dict[str, Any]) -> int:
    return (date.fromisoformat(row["end"]) - date.fromisoformat(row["start"])).days


def _fits(row: dict[str, Any], period: str) -> bool:
    if period == "instant":
        return "start" not in row
    return "start" in row and _days(row) in ANNUAL_DAYS


def find_fact(facts: dict[str, Any], metric: Metric, period_end: str) -> str | None:
    """The first candidate tag with a 10-K fact for the period ending `period_end`, or None."""
    for tag in metric.tags:
        for row in _rows(facts, tag):
            if row.get("form") == "10-K" and row["end"] == period_end and _fits(row, metric.period):
                return tag
    return None


def near_miss(facts: dict[str, Any], metric: Metric, accession: str) -> str | None:
    """A candidate tag that the filing itself reports with another date, if there is one.

    The cover-page share count, for example, is dated weeks after the period ends.
    """
    for tag in metric.tags:
        for row in _rows(facts, tag):
            if row.get("accn") == accession and row.get("form") == "10-K":
                return f"{tag} dated {row['end']} in this 10-K"
    return None


def build_coverage(
    companies: list[Company], filings: list[Filing], facts: dict[str, dict[str, Any]]
) -> str:
    """docs/facts_coverage.md: a found/missing grid per company, metric and fiscal year."""
    by_ticker: dict[str, list[Filing]] = {}
    for filing in sorted(filings, key=lambda f: (f.ticker, f.fiscal_year)):
        by_ticker.setdefault(filing.ticker, []).append(filing)
    found_count: Counter[str] = Counter()
    tags_used: dict[str, Counter[str]] = {m.name: Counter() for m in METRICS}
    sections: list[str] = []
    for company in sorted(companies, key=lambda c: c.ticker):
        years = by_ticker.get(company.ticker, [])
        data = facts.get(company.ticker)
        sections += [
            f"## {company.ticker}",
            "",
            "| Metric | " + " | ".join(f"FY{f.fiscal_year}" for f in years) + " |",
            "|---|" + "---|" * len(years),
        ]
        for metric in METRICS:
            cells = []
            for filing in years:
                tag = find_fact(data, metric, filing.period_of_report.isoformat()) if data else None
                if tag:
                    found_count[metric.name] += 1
                    tags_used[metric.name][tag] += 1
                    cells.append(f"found: `{tag}`")
                elif data is None:
                    cells.append("no companyfacts file")
                else:
                    other = near_miss(data, metric, filing.accession)
                    cells.append(f"missing ({other})" if other else "missing")
            sections.append(f"| {metric.name} | " + " | ".join(cells) + " |")
        sections.append("")
    total = sum(len(v) for v in by_ticker.values())
    lines = [
        "# XBRL facts coverage",
        "",
        "For each company and pinned fiscal year: does its companyfacts file hold a fact from "
        "a 10-K that ends on the filing's period of report, under one of the candidate tags? "
        "Amounts over a period must cover a whole fiscal year (350 to 380 days), because 10-Ks "
        "also report quarters ending on the same day. The first candidate that matches is "
        "shown. Where none matches, a candidate that the filing reports with another date is "
        "named in brackets. Coverage only: this does not choose the tag an answer will use. "
        "Written by `make verify-facts`; do not edit by hand.",
        "",
        "## Totals",
        "",
        "| Metric | Found | Tags that matched |",
        "|---|---:|---|",
    ]
    for metric in METRICS:
        used = ", ".join(f"`{tag}` {n}" for tag, n in tags_used[metric.name].most_common())
        lines.append(f"| {metric.name} | {found_count[metric.name]} of {total} | {used or '—'} |")
    lines += ["", "Candidate tags, in the order they are tried:", ""]
    lines += [f"- {m.name}: " + ", ".join(f"`{t}`" for t in m.tags) for m in METRICS]
    lines += ["", *sections]
    return "\n".join(lines).rstrip("\n") + "\n"


def main(root: Path = REPO_ROOT) -> int:
    """Write docs/facts_coverage.md and print the totals."""
    companies = load_companies(root / "data" / "companies.yaml")
    filings = load_manifest(root / "data" / "manifest.json").filings
    facts = {}
    for company in companies:
        path = root / companyfacts_path(company.ticker)
        if path.exists():
            facts[company.ticker] = json.loads(path.read_text(encoding="utf-8"))
    page = build_coverage(companies, filings, facts)
    (root / "docs" / "facts_coverage.md").write_text(page, encoding="utf-8", newline="\n")
    for line in page.splitlines():
        if line.startswith("| ") and " of " in line:
            print(line)
    print("wrote docs/facts_coverage.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
