"""Write `docs/data_report.md`: what the dataset contains, and every gap in it.

The report is built only from files the ingest stages wrote, has no timestamps, and so
changes only when the data changes.
"""

import calendar
from collections import defaultdict

from filingcheck.ingest.companies import Company
from filingcheck.ingest.filings import Manifest
from filingcheck.ingest.sections import (
    ALL_ITEMS,
    ITEMS,
    MERGED_ITEM,
    MERGED_LABEL,
    SHORT_ITEM_CHARS,
    ItemSummary,
    SectionSummary,
)

SOURCE_LABELS = {"exhibit": "EX-13", "relocated": "relocated"}


def _cell(found: ItemSummary | None) -> str:
    if found is None:
        return "—"
    labels = [SOURCE_LABELS[found.method]] if found.method in SOURCE_LABELS else []
    if found.boundary == "approximate":
        labels.append("approx.")
    return f"{found.chars:,} ({', '.join(labels)})" if labels else f"{found.chars:,}"


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
        f"| Number tables set aside (table_chunks) | {sum(s.tables_saved for s in summaries):,} |",
        "",
    ]

    lines += ["## Gaps", ""]
    missing = [
        f"- {s.ticker} FY{s.fiscal_year}: "
        f"{_listing([i for i in ITEMS if i not in s.items and i not in s.merged])} not found"
        for s in summaries
        if any(i not in s.items and i not in s.merged for i in ITEMS)
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

    lines += [
        "## Sections with approximate boundaries",
        "",
        "These 10-Ks map their Items to page ranges through their own index, so a section "
        "starts and ends where those pages do, not at a heading. Item 8 is cut instead from "
        "the auditor's report on the financial statements, so its start is exact. A section "
        "that does not start at its own heading is not given a label that may not fit it: "
        f'those are kept together as Items {MERGED_ITEM}, "{MERGED_LABEL}".',
        "",
    ]
    approximate = [
        f"- {s.ticker} FY{s.fiscal_year}: "
        + _listing([i for i in ALL_ITEMS if i in s.items and s.items[i].boundary == "approximate"])
        + (f" ({', '.join(s.merged)} kept together as {MERGED_ITEM})" if s.merged else "")
        for s in sorted(summaries, key=lambda s: (s.ticker, s.fiscal_year))
        if any(found.boundary == "approximate" for found in s.items.values())
    ]
    lines += approximate or ["None."]
    lines.append("")

    lines += [
        "## Repeated passages removed",
        "",
        "Passages that appear more than once in the same filing are kept once, under the "
        "first Item that has them, and their chunks list the other Items. Repeats across "
        "fiscal years are kept.",
        "",
    ]
    repeats = [
        f"- {s.ticker} FY{s.fiscal_year}: {s.repeats_removed:,}"
        for s in sorted(summaries, key=lambda s: (s.ticker, s.fiscal_year))
        if s.repeats_removed
    ]
    lines += repeats or ["None."]
    lines.append("")

    lines += [
        "## Number tables",
        "",
        "Tables with more than half their non-empty cells numeric (contents lists aside) are "
        "taken out of the prose before the sections are cut, and each is saved as one record "
        'in table_chunks: its rows as "label: values" text, the Item that held it, and its '
        "position in the source document. companyfacts has whole-company numbers only; "
        "segment numbers are only in these tables. They are not searched with the chunks.",
        "",
        f"- Saved: {sum(s.tables_saved for s in summaries):,}, of which "
        f"{sum(s.tables_outside_items for s in summaries):,} lie outside the Items above",
        "",
        "Where taking the tables out would move a section's start or end, that section is cut "
        "from the full document instead, and its tables are also left to the chunk filter:",
        "",
    ]
    kept = [
        f"- {s.ticker} FY{s.fiscal_year}: {_listing(s.tables_kept)}"
        for s in sorted(summaries, key=lambda s: (s.ticker, s.fiscal_year))
        if s.tables_kept
    ]
    lines += kept or ["None."]
    lines.append("")

    # Every company table has the same columns, so "Chunks" is always the last one.
    columns = list(ALL_ITEMS)
    for company in ordered:
        names = [
            f"Items {i} ({MERGED_LABEL})" if i == MERGED_ITEM else f"Item {i}" for i in columns
        ]
        header = "| FY | Accession | Period of report | " + " | ".join(names)
        month = calendar.month_name[company.fiscal_year_end]
        tags = tag_counts.get(company.ticker)
        tag_text = f" · {tags:,} us-gaap tags" if tags is not None else ""
        lines += [
            f"## {company.ticker}",
            "",
            f"{company.name} · CIK {company.cik} · fiscal year ends in {month}{tag_text}",
            "",
            header + " | Chunks |",
            "|---|---|---|" + "---:|" * (len(columns) + 1),
        ]
        for filing in filings_by_ticker.get(company.ticker, []):
            summary = by_accession.get(filing.accession)
            cells = [
                f"in {MERGED_ITEM}"
                if summary and i in summary.merged
                else _cell(summary.items.get(i) if summary else None)
                for i in columns
            ]
            chunks = sum(n for (acc, _), n in chunk_counts.items() if acc == filing.accession)
            lines.append(
                f"| {filing.fiscal_year} | {filing.accession} | {filing.period_of_report} | "
                + " | ".join(cells)
                + f" | {chunks:,} |"
            )
        lines.append("")
    return "\n".join(lines)
