"""`python -m filingcheck.embeddings [--dry-run] [--yes]`: plan, confirm, then embed."""

import argparse
import sys

from dotenv import load_dotenv

from filingcheck.db import connect
from filingcheck.db.migrate import migrate
from filingcheck.embeddings.openai_client import OpenAIEmbeddings
from filingcheck.embeddings.runner import describe, mirror_path, plan, run
from filingcheck.llm.pricing import cost_usd
from filingcheck.paths import REPO_ROOT


def main(argv: list[str] | None = None) -> int:
    """Print the plan; with --dry-run stop there, otherwise confirm and run it."""
    parser = argparse.ArgumentParser(prog="python -m filingcheck.embeddings")
    parser.add_argument("--dry-run", action="store_true", help="print the plan and stop")
    parser.add_argument("--yes", action="store_true", help="skip the confirmation prompt")
    args = parser.parse_args(argv)
    load_dotenv(REPO_ROOT / ".env")
    client = OpenAIEmbeddings()
    mirror = mirror_path(REPO_ROOT, client.model_name)
    with connect() as conn:
        applied = migrate(conn)
        if applied:
            print(f"applied migrations: {', '.join(applied)}")
        p = plan(conn, client, mirror)
        print(describe(p))
        if args.dry_run:
            print("dry run: no API call made; no vector, cache row or meta row written")
            return 0
        if p.texts_to_embed and not args.yes:
            answer = input(
                f"Embed {p.texts_to_embed:,} texts for about ${p.estimated_cost_usd:.4f}? [y/N] "
            )
            if answer.strip().lower() not in ("y", "yes"):
                print("stopped; nothing embedded")
                return 1
        try:
            result = run(conn, client, mirror)
        except Exception:
            # Everything that came back is saved; say what this run was billed before stopping.
            print(
                f"stopped with an error after {client.tokens_used:,} tokens billed "
                f"(${cost_usd(client.model_name, client.tokens_used):.4f}); "
                "run again to resume"
            )
            raise
    print(
        f"restored {result.restored:,} chunks from the cache; embedded {result.embedded:,} "
        f"texts; {result.tokens:,} tokens billed; cost ${result.cost_usd:.4f}"
    )
    print("HNSW index created" if result.index_created else "HNSW index already present")
    return 0


if __name__ == "__main__":
    sys.exit(main())
