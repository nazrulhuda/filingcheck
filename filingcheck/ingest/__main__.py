"""Command line for the ingest stages: `python -m filingcheck.ingest <stage>`."""

import argparse
import sys
from collections import defaultdict
from pathlib import Path

from filingcheck.paths import DATA_DIR, REPO_ROOT

COMPANIES_FILE = DATA_DIR / "companies.yaml"
MANIFEST_FILE = DATA_DIR / "manifest.json"
SECTIONS_SUMMARY = "data/sections/summary.json"
CHUNKS_FILE = "data/chunks.jsonl"
TABLE_CHUNKS_FILE = "data/table_chunks.jsonl"
DATA_REPORT = "docs/data_report.md"


def run_companies(path: Path) -> int:
    """Resolve every company's CIK and print the result for checking."""
    from filingcheck.ingest.companies import TICKERS_URL, update_companies_file
    from filingcheck.ingest.sec_client import SecClient

    with SecClient() as client:
        companies = update_companies_file(path, client)
        titles = {
            str(row["ticker"]).upper(): row["title"]
            for row in client.get_json(TICKERS_URL).values()
        }
    for c in companies:
        print(f"{c.ticker:<6} {c.cik}  {titles[c.ticker.upper()]}")
    print(f"{len(companies)} companies written to {path}")
    return 0


def run_filings(
    companies_path: Path, manifest_path: Path, root: Path, reselect: bool = False
) -> int:
    """Pin the latest three 10-Ks per company in the manifest and save their documents.

    An existing manifest is reused as is, so re-runs keep the same filings; pass
    `reselect=True` to choose again (for example, when a new fiscal year should be added).
    """
    from filingcheck.ingest.companies import load_companies
    from filingcheck.ingest.filings import (
        build_manifest,
        ensure_documents,
        load_manifest,
        write_manifest,
    )
    from filingcheck.ingest.sec_client import SecClient

    with SecClient() as client:
        if manifest_path.exists() and not reselect:
            manifest = load_manifest(manifest_path)
            saved = ensure_documents(manifest, client, root)
            print(f"using the filings pinned in {manifest_path.name}; {saved} documents saved")
        else:
            manifest = build_manifest(load_companies(companies_path), client, root)
            write_manifest(manifest_path, manifest)
            print(f"chose {len(manifest.filings)} filings and wrote {manifest_path.name}")
        downloads = client.downloads
    years: dict[str, list[int]] = defaultdict(list)
    for filing in manifest.filings:
        years[filing.ticker].append(filing.fiscal_year)
    for ticker, fiscal_years in years.items():
        print(f"{ticker:<6} {', '.join(str(y) for y in fiscal_years)}")
    print(f"{len(manifest.filings)} filings; {downloads} downloaded from sec.gov in this run")
    return 0


def run_sections(manifest_path: Path, root: Path) -> int:
    """Split every pinned filing into its Items, fetching Exhibit 13 where it is needed."""
    from filingcheck.ingest.filings import load_manifest, write_manifest
    from filingcheck.ingest.sec_client import SecClient
    from filingcheck.ingest.sections import build_sections, write_summary

    with SecClient() as client:
        manifest, summaries = build_sections(load_manifest(manifest_path), client, root)
        downloads = client.downloads
    write_manifest(manifest_path, manifest)
    write_summary(root / SECTIONS_SUMMARY, summaries)
    for s in summaries:
        notes = [f"short: {', '.join(s.short)}"] if s.short else []
        exhibit = [item for item, found in s.items.items() if found.method == "exhibit"]
        notes += [f"from Exhibit 13: {', '.join(exhibit)}"] if exhibit else []
        notes += [f"GAP: {gap}" for gap in s.gaps]
        if notes:
            print(f"{s.ticker:<6} {s.fiscal_year}  " + "; ".join(notes))
    items = sum(len(s.items) for s in summaries)
    gaps = sum(1 for s in summaries if s.gaps)
    print(
        f"{items} Items saved from {len(summaries)} filings; {gaps} filings with gaps; "
        f"{downloads} downloaded from sec.gov in this run"
    )
    return 0


def run_chunks(manifest_path: Path, root: Path) -> int:
    """Chunk every saved Item into `data/chunks.jsonl`; gather the number tables too."""
    from collections import Counter

    from filingcheck.ingest.filings import load_manifest
    from filingcheck.ingest.sections import iter_chunks, iter_table_chunks

    kept: Counter[str] = Counter()
    dropped: Counter[str] = Counter()
    out = root / CHUNKS_FILE
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_name(out.name + ".tmp")
    with tmp.open("w", encoding="utf-8", newline="\n") as handle:
        for chunks, item_dropped in iter_chunks(load_manifest(manifest_path), root):
            for chunk in chunks:
                handle.write(chunk.model_dump_json() + "\n")
                kept[chunk.item] += 1
            dropped.update(item_dropped)
    tmp.replace(out)
    tables = root / TABLE_CHUNKS_FILE
    tmp = tables.with_name(tables.name + ".tmp")
    in_items: Counter[str] = Counter()
    with tmp.open("w", encoding="utf-8", newline="\n") as handle:
        for table in iter_table_chunks(load_manifest(manifest_path), root):
            handle.write(table.model_dump_json() + "\n")
            in_items[table.item or "none"] += 1
    tmp.replace(tables)
    print("chunks per Item: " + ", ".join(f"{item} {n:,}" for item, n in sorted(kept.items())))
    print("dropped as noise: " + ", ".join(f"{why} {n:,}" for why, n in sorted(dropped.items())))
    print(f"{sum(kept.values()):,} chunks written to {CHUNKS_FILE}")
    print("number tables per Item: " + ", ".join(f"{i} {n:,}" for i, n in sorted(in_items.items())))
    print(f"{sum(in_items.values()):,} number tables written to {TABLE_CHUNKS_FILE}")
    return 0


def run_load(companies_path: Path, manifest_path: Path, root: Path) -> int:
    """Apply the migrations, then replace the companies, filings and chunks in the database."""
    from filingcheck.db import connect
    from filingcheck.db.load import load_all
    from filingcheck.db.migrate import migrate
    from filingcheck.ingest.companies import load_companies
    from filingcheck.ingest.filings import load_manifest

    chunks_path = root / CHUNKS_FILE
    tables_path = root / TABLE_CHUNKS_FILE
    with connect() as conn:
        applied = migrate(conn)
        counts = load_all(
            conn,
            load_companies(companies_path),
            load_manifest(manifest_path),
            chunks_path,
            tables_path if tables_path.exists() else None,
        )
    with chunks_path.open(encoding="utf-8") as handle:
        in_file = sum(1 for line in handle if line.strip())
    tables_in_file = 0
    if tables_path.exists():
        with tables_path.open(encoding="utf-8") as handle:
            tables_in_file = sum(1 for line in handle if line.strip())
    if applied:
        print(f"applied migrations: {', '.join(applied)}")
    print(
        f"loaded {counts['companies']} companies, {counts['filings']} filings and "
        f"{counts['chunks']:,} chunks ({in_file:,} in {CHUNKS_FILE})"
    )
    print(
        f"loaded {counts['table_chunks']:,} number tables "
        f"({tables_in_file:,} in {TABLE_CHUNKS_FILE})"
    )
    if counts["chunks"] != in_file or counts["table_chunks"] != tables_in_file:
        print("ERROR: the database and the chunk files disagree")
        return 1
    return 0


def run_companyfacts(companies_path: Path, root: Path) -> int:
    """Download and check every company's XBRL companyfacts file."""
    from filingcheck.ingest.companies import load_companies
    from filingcheck.ingest.companyfacts import fetch_companyfacts
    from filingcheck.ingest.sec_client import SecClient

    with SecClient() as client:
        tags = {
            c.ticker: fetch_companyfacts(c, client, root) for c in load_companies(companies_path)
        }
        downloads = client.downloads
    for ticker, count in tags.items():
        print(f"{ticker:<6} {count:>5,} us-gaap tags")
    print(f"{len(tags)} companyfacts files; {downloads} downloaded from sec.gov in this run")
    return 0


def run_report(companies_path: Path, manifest_path: Path, root: Path) -> int:
    """Write docs/data_report.md from the files the other stages produced."""
    from collections import Counter

    from filingcheck.db.load import read_chunks
    from filingcheck.ingest.companies import load_companies
    from filingcheck.ingest.companyfacts import companyfacts_path, count_us_gaap_tags
    from filingcheck.ingest.filings import load_manifest
    from filingcheck.ingest.report import build_report
    from filingcheck.ingest.sections import load_summary

    companies = load_companies(companies_path)
    chunk_counts = Counter((c.accession, c.item) for c in read_chunks(root / CHUNKS_FILE))
    tags = {}
    for company in companies:
        path = root / companyfacts_path(company.ticker)
        if path.exists():
            tags[company.ticker] = count_us_gaap_tags(path.read_bytes())
    text = build_report(
        companies,
        load_manifest(manifest_path),
        load_summary(root / SECTIONS_SUMMARY),
        dict(chunk_counts),
        tags,
    )
    out = root / DATA_REPORT
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text.rstrip("\n") + "\n", encoding="utf-8", newline="\n")  # one final newline
    print(f"wrote {DATA_REPORT}")
    return 0


def main(argv: list[str] | None = None) -> int:
    """Run one ingest stage."""
    parser = argparse.ArgumentParser(prog="python -m filingcheck.ingest")
    stages = parser.add_subparsers(dest="stage", required=True)
    stages.add_parser("companies", help="resolve tickers to SEC CIKs in data/companies.yaml")
    filings = stages.add_parser("filings", help="pin and download the latest three 10-Ks")
    filings.add_argument(
        "--reselect", action="store_true", help="choose the filings again instead of reusing"
    )
    stages.add_parser("companyfacts", help="download each company's XBRL companyfacts file")
    stages.add_parser("sections", help="split each filing into Items 1, 1A, 7, 7A and 8")
    stages.add_parser("chunks", help="chunk the saved Items into data/chunks.jsonl")
    stages.add_parser("load", help="load companies, filings and chunks into Postgres")
    stages.add_parser("report", help="write docs/data_report.md")
    args = parser.parse_args(argv)
    if args.stage == "companies":
        return run_companies(COMPANIES_FILE)
    if args.stage == "filings":
        return run_filings(COMPANIES_FILE, MANIFEST_FILE, REPO_ROOT, reselect=args.reselect)
    if args.stage == "sections":
        return run_sections(MANIFEST_FILE, REPO_ROOT)
    if args.stage == "chunks":
        return run_chunks(MANIFEST_FILE, REPO_ROOT)
    if args.stage == "companyfacts":
        return run_companyfacts(COMPANIES_FILE, REPO_ROOT)
    if args.stage == "load":
        return run_load(COMPANIES_FILE, MANIFEST_FILE, REPO_ROOT)
    if args.stage == "report":
        return run_report(COMPANIES_FILE, MANIFEST_FILE, REPO_ROOT)
    return 1  # pragma: no cover  (argparse rejects unknown stages first)


if __name__ == "__main__":
    sys.exit(main())
