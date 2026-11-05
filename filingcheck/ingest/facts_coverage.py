"""`make verify-facts`, part 1: what the lookup finds for every pinned filing and metric.

Runs the lookup itself on the `facts` table (the filings' own XBRL, by accession), so the
page shows exactly what an answer will get: the tag used, or "unavailable". Writes
`docs/facts_coverage.md`.
"""

import sys
from collections import Counter
from pathlib import Path

from filingcheck.facts.lookup import FactsSource, lookup
from filingcheck.facts.metrics import BANK_REVENUE_TAGS, METRICS
from filingcheck.ingest.companies import Company, load_companies
from filingcheck.ingest.filings import Filing, load_manifest
from filingcheck.paths import REPO_ROOT


def _short(concept: str) -> str:
    return concept.removeprefix("us-gaap:")


def build_coverage(companies: list[Company], filings: list[Filing], source: FactsSource) -> str:
    """docs/facts_coverage.md: per company, metric and fiscal year, the lookup's result."""
    by_ticker: dict[str, list[Filing]] = {}
    for filing in sorted(filings, key=lambda f: (f.ticker, f.fiscal_year)):
        by_ticker.setdefault(filing.ticker, []).append(filing)
    found: Counter[str] = Counter()
    used: dict[str, Counter[str]] = {name: Counter() for name in METRICS}
    unavailable: dict[str, list[str]] = {name: [] for name in METRICS}
    sections: list[str] = []
    for company in sorted(companies, key=lambda c: c.ticker):
        years = by_ticker.get(company.ticker, [])
        sections += [
            f"## {company.ticker}",
            "",
            "| Metric | " + " | ".join(f"FY{f.fiscal_year}" for f in years) + " |",
            "|---|" + "---|" * len(years),
        ]
        for name in METRICS:
            cells = []
            for filing in years:
                result = lookup(source, filing.ticker, filing.fiscal_year, name)
                if result is None:
                    unavailable[name].append(f"{filing.ticker} FY{filing.fiscal_year}")
                    cells.append("unavailable")
                    continue
                found[name] += 1
                used[name][result.concept] += 1
                cell = f"found: `{_short(result.concept)}`"
                if result.note:
                    cell += f" (cover page, {result.instant})"
                cells.append(cell)
            sections.append(f"| {name} | " + " | ".join(cells) + " |")
        sections.append("")
    total = sum(len(v) for v in by_ticker.values())
    lines = [
        "# XBRL facts coverage",
        "",
        "For each company and pinned fiscal year, what the lookup returns for each metric from "
        'the filing\'s own XBRL facts: the tag it used, or "unavailable" when the filing '
        "reports the metric under none of the candidate tags. Only company totals (facts with "
        "no dimensions) count; amounts over a period must end on the filing's period of report "
        "and cover a whole fiscal year (350 to 380 days), and balances must fall on that date. "
        "The cover-page share count is the one exception: it is dated a few weeks after the "
        "year ends and is used only when the filing has no year-end count for the company as "
        "a whole (counts by class of stock are not added up). Nothing is derived. Written by "
        "`make verify-facts`; do not edit by hand.",
        "",
        "## Totals",
        "",
        "| Metric | Found | Tags used |",
        "|---|---:|---|",
    ]
    for name in METRICS:
        tags = ", ".join(f"`{_short(t)}` {n}" for t, n in used[name].most_common())
        lines.append(f"| {name} | {found[name]} of {total} | {tags or '—'} |")
    lines += ["", "Candidate tags, in the order they are tried:", ""]
    for name, spec in METRICS.items():
        lines.append(f"- {name}: " + ", ".join(f"`{_short(t)}`" for t in spec.tags))
    lines.append(
        "- revenue, for companies with `revenue_rule: bank`: "
        + ", ".join(f"`{_short(t)}`" for t in BANK_REVENUE_TAGS)
    )
    lines += ["", "## Unavailable", ""]
    for name in METRICS:
        if unavailable[name]:
            lines.append(f"- {name} ({len(unavailable[name])}): " + ", ".join(unavailable[name]))
    lines += ["", *sections]
    return "\n".join(lines).rstrip("\n") + "\n"


def main(root: Path = REPO_ROOT) -> int:
    """Write docs/facts_coverage.md from the facts table and print the totals."""
    from filingcheck.db import connect
    from filingcheck.facts.lookup import PostgresFacts

    companies = load_companies(root / "data" / "companies.yaml")
    filings = load_manifest(root / "data" / "manifest.json").filings
    with connect() as conn:
        page = build_coverage(companies, filings, PostgresFacts(conn))
    (root / "docs" / "facts_coverage.md").write_text(page, encoding="utf-8", newline="\n")
    for line in page.splitlines():
        if line.startswith("| ") and " of " in line:
            print(line)
    print("wrote docs/facts_coverage.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
