"""Command line for the ingest stages: `python -m filingcheck.ingest <stage>`."""

import argparse
import sys
from pathlib import Path

from filingcheck.paths import DATA_DIR

COMPANIES_FILE = DATA_DIR / "companies.yaml"


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


def main(argv: list[str] | None = None) -> int:
    """Run one ingest stage."""
    parser = argparse.ArgumentParser(prog="python -m filingcheck.ingest")
    stages = parser.add_subparsers(dest="stage", required=True)
    stages.add_parser("companies", help="resolve tickers to SEC CIKs in data/companies.yaml")
    args = parser.parse_args(argv)
    if args.stage == "companies":
        return run_companies(COMPANIES_FILE)
    return 1  # pragma: no cover  (argparse rejects unknown stages first)


if __name__ == "__main__":
    sys.exit(main())
