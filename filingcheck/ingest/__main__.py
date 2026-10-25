"""Command line for the ingest stages: `python -m filingcheck.ingest <stage>`."""

import argparse
import sys
from collections import defaultdict
from pathlib import Path

from filingcheck.paths import DATA_DIR, REPO_ROOT

COMPANIES_FILE = DATA_DIR / "companies.yaml"
MANIFEST_FILE = DATA_DIR / "manifest.json"


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


def main(argv: list[str] | None = None) -> int:
    """Run one ingest stage."""
    parser = argparse.ArgumentParser(prog="python -m filingcheck.ingest")
    stages = parser.add_subparsers(dest="stage", required=True)
    stages.add_parser("companies", help="resolve tickers to SEC CIKs in data/companies.yaml")
    filings = stages.add_parser("filings", help="pin and download the latest three 10-Ks")
    filings.add_argument(
        "--reselect", action="store_true", help="choose the filings again instead of reusing"
    )
    args = parser.parse_args(argv)
    if args.stage == "companies":
        return run_companies(COMPANIES_FILE)
    if args.stage == "filings":
        return run_filings(COMPANIES_FILE, MANIFEST_FILE, REPO_ROOT, reselect=args.reselect)
    return 1  # pragma: no cover  (argparse rejects unknown stages first)


if __name__ == "__main__":
    sys.exit(main())
