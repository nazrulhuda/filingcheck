"""Command line for the database: `python -m filingcheck.db migrate`."""

import argparse
import sys

from filingcheck.db import connect, database_url
from filingcheck.db.migrate import migrate


def main(argv: list[str] | None = None) -> int:
    """Run one database command."""
    parser = argparse.ArgumentParser(prog="python -m filingcheck.db")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("migrate", help="apply any migrations not applied yet")
    parser.parse_args(argv)
    with connect() as conn:
        applied = migrate(conn)
    where = database_url().rsplit("@", 1)[-1]  # host and database only, never the password
    print(f"applied {len(applied)} migrations to {where}: {', '.join(applied) or 'none new'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
