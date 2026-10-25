"""Write `docs/data_report.md`: what the dataset contains, and every gap in it.

The report is built only from files the ingest stages wrote, has no timestamps, and so
changes only when the data changes.
"""

import calendar
from collections import defaultdict

from filingcheck.ingest.companies import Company
from filingcheck.ingest.filings import Manifest
from filingcheck.ingest.sections import ITEMS, SHORT_ITEM_CHARS, ItemSummary, SectionSummary

SOURCE_LABELS = {"exhibit": "EX-13", "relocated": "relocated"}


def _cell(found: ItemSummary | None) -> str:
    if found is None:
        return "—"
    label = SOURCE_LABELS.get(found.method)
    return f"{found.chars:,} ({label})" if label else f"{found.chars:,}"


def _listing(items: list[str]) -> str:
    return ("Item " if len(items) == 1 else "Items ") + ", ".join(items)


def build_report(
    companies: list[Company],
    manifest: Manifest,
    summaries: list[SectionSummary],
    chunk_counts: dict[tuple[str, str], int],
    tag_counts: dict[str, int],
) -> str:
    """The data report as Markdown.

    `chunk_counts` maps (accession, Item) to the number of chunks kept; `tag_counts` maps a
    ticker to the number of us-gaap tags in its companyfacts file.
    """
    by_accession = {s.accession: s for s in summaries}
    filings_by_ticker = defaultdict(list)
    for filing in sorted(manifest.filings, key=lambda f: (f.ticker, f.fiscal_year)):
        filings_by_ticker[filing.ticker].append(filing)
    ordered = sorted(companies, key=lambda c: c.ticker)

    lines = [
        "# Data report",
        "",
        "Written by `make ingest` from `data/manifest.json` and the files the ingest stages "
        "produce. Do not edit by hand.",
        "",
        "## Totals",
        "",
        "| | Count |",
        "|---|---:|",
        f"| Companies | {len(ordered)} |",
        f"| Filings | {len(manifest.filings)} |",
        f"| Items saved | {sum(len(s.items) for s in summaries):,} |",
        f"| Chunks | {sum(chunk_counts.values()):,} |",
        f"| us-gaap tags (all companies) | {sum(tag_counts.values()):,} |",
        "",
    ]

    lines += ["## Gaps", ""]
    missing = [
        f"- {s.ticker} FY{s.fiscal_year}: {_listing([i for i in ITEMS if i not in s.items])} "
        "not found"
        for s in summaries
        if any(i not in s.items for i in ITEMS)
    ]
    lines += missing or ["No filing is missing an Item."]
    lines += [f"- {s.ticker} FY{s.fiscal_year}: {gap}" for s in summaries for gap in s.gaps]
    short = [
        f"- {s.ticker} FY{s.fiscal_year}: Item {item} has {s.items[item].chars:,} characters"
        for s in sorted(summaries, key=lambda s: (s.ticker, s.fiscal_year))
        for item in s.short
        if item in s.items
    ]
    lines += ["", f"Items under {SHORT_ITEM_CHARS:,} characters:", ""]
    lines += short or ["None."]
    if short:
        lines += [
            "",
            "A short Item 7A is usually a one-line pointer to the market-risk discussion "
            "inside Item 7.",
        ]
    lines.append("")

    lines += ["## Sections taken from elsewhere", ""]
    moved = []
    for s in sorted(summaries, key=lambda s: (s.ticker, s.fiscal_year)):
        exhibit = [i for i, found in s.items.items() if found.method == "exhibit"]
        relocated = [i for i, found in s.items.items() if found.method == "relocated"]
        if exhibit:
            moved.append(f"- {s.ticker} FY{s.fiscal_year}: {_listing(exhibit)} from Exhibit 13")
        if relocated:
            moved.append(
                f"- {s.ticker} FY{s.fiscal_year}: {_listing(relocated)} from later in the same 10-K"
            )
    lines += moved or ["None."]
    lines.append("")

    header = "| FY | Accession | Period of report | " + " | ".join(f"Item {i}" for i in ITEMS)
    for company in ordered:
        month = calendar.month_name[company.fiscal_year_end]
        tags = tag_counts.get(company.ticker)
        tag_text = f" · {tags:,} us-gaap tags" if tags is not None else ""
        lines += [
            f"## {company.ticker}",
            "",
            f"{company.name} · CIK {company.cik} · fiscal year ends in {month}{tag_text}",
            "",
            header + " | Chunks |",
            "|---|---|---|" + "---:|" * (len(ITEMS) + 1),
        ]
        for filing in filings_by_ticker.get(company.ticker, []):
            summary = by_accession.get(filing.accession)
            cells = [_cell(summary.items.get(i) if summary else None) for i in ITEMS]
            chunks = sum(n for (acc, _), n in chunk_counts.items() if acc == filing.accession)
            lines.append(
                f"| {filing.fiscal_year} | {filing.accession} | {filing.period_of_report} | "
                + " | ".join(cells)
                + f" | {chunks:,} |"
            )
        lines.append("")
    return "\n".join(lines)
