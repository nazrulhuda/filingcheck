"""`make verify-facts`, part 2: cross-check the filings' own facts against SEC companyfacts.

For every pinned filing and every candidate tag of the metric map, the company-total facts
(no dimensions) that end on the filing's period of report are compared with the
companyfacts rows of the same accession, tag and period. companyfacts is only a cross-check:
the numbers come from the filing. Writes `docs/facts_report.md`.
"""

import hashlib
import json
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any

from filingcheck.ingest.facts_coverage import METRICS
from filingcheck.paths import REPO_ROOT

STATUSES = ("agree", "disagree", "not in companyfacts", "not in the filing's XBRL")


@dataclass(frozen=True)
class CrossRow:
    """One tag and period of one filing, in the filing's XBRL, in companyfacts, or both."""

    ticker: str
    fiscal_year: int
    accession: str
    tag: str
    period: str
    status: str
    ours: str | None
    theirs: str | None


def _plain(number: Decimal) -> str:
    return "0" if number == 0 else format(number.normalize(), "f")


def _concept(tag: str) -> str:
    return tag if ":" in tag else f"us-gaap:{tag}"


def _period(start: str | None, end: str) -> str:
    return f"{start} to {end}" if start else end


def cross_check(
    filing: dict[str, Any],
    facts: list[dict[str, Any]],
    companyfacts: dict[str, Any],
    tags: list[str],
) -> list[CrossRow]:
    """Compare one filing's company totals ending on its period of report with companyfacts."""
    end = str(filing["period_of_report"])
    accession = filing["accession"]
    rows: list[CrossRow] = []
    for tag in tags:
        concept = _concept(tag)
        taxonomy, _, name = concept.partition(":")
        ours: dict[tuple[str | None, str], set[Decimal]] = defaultdict(set)
        for fact in facts:
            if fact["accession"] != accession or fact["concept"] != concept or fact["dimensions"]:
                continue
            key: tuple[str | None, str]
            if fact["instant"] == end:
                key = (None, end)
            elif fact["period_end"] == end:
                key = (fact["period_start"], end)
            else:
                continue
            ours[key].add(Decimal(fact["value"]))
        theirs: dict[tuple[str | None, str], set[Decimal]] = defaultdict(set)
        entry = companyfacts.get("facts", {}).get(taxonomy, {}).get(name, {})
        for unit_rows in entry.get("units", {}).values():
            for row in unit_rows:
                if row.get("accn") == accession and row.get("end") == end:
                    theirs[(row.get("start"), end)].add(Decimal(str(row["val"])))
        for key in sorted(set(ours) | set(theirs), key=lambda k: (k[0] or "", k[1])):
            mine, other = ours.get(key), theirs.get(key)
            if mine and other:
                status = "agree" if mine == other else "disagree"
            else:
                status = "not in companyfacts" if mine else "not in the filing's XBRL"
            rows.append(
                CrossRow(
                    ticker=filing["ticker"],
                    fiscal_year=filing["fiscal_year"],
                    accession=accession,
                    tag=tag,
                    period=_period(key[0], key[1]),
                    status=status,
                    ours=", ".join(_plain(v) for v in sorted(mine)) if mine else None,
                    theirs=", ".join(_plain(v) for v in sorted(other)) if other else None,
                )
            )
    return sorted(rows, key=lambda r: (r.tag, r.period))


def candidate_tags() -> list[str]:
    """Every candidate tag of the metric map, once, in map order."""
    return list(dict.fromkeys(tag for metric in METRICS for tag in metric.tags))


def facts_report(
    filings: list[dict[str, Any]],
    facts: list[dict[str, Any]],
    companyfacts: dict[str, dict[str, Any] | None],
    tags: list[str],
    pins: dict[str, tuple[str, bool]] | None = None,
) -> str:
    """docs/facts_report.md: facts per filing, the cross-check, and the conflicts."""
    by_accession: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for fact in facts:
        by_accession[fact["accession"]].append(fact)
    ordered = sorted(filings, key=lambda f: (f["ticker"], f["fiscal_year"]))
    rows: list[CrossRow] = []
    for filing in ordered:
        data = companyfacts.get(filing["ticker"]) or {}
        rows += cross_check(filing, by_accession[filing["accession"]], data, tags)
    status_count = Counter(r.status for r in rows)
    lines = [
        "# XBRL facts report",
        "",
        "The numeric facts of each pinned filing, read from the filing's own inline XBRL "
        "(`data/facts.jsonl`), and a cross-check against the SEC's companyfacts files. For "
        "every filing and every candidate tag of the metric map, the company totals (facts "
        "with no dimensions) that end on the filing's period of report are compared with the "
        "companyfacts rows of the same accession, tag and period. companyfacts is only a "
        "cross-check; the numbers come from the filings. Written by `make verify-facts`; do "
        "not edit by hand.",
        "",
        "## Facts per filing",
        "",
        "| Ticker | FY | Accession | Facts | Company totals |",
        "|---|---:|---|---:|---:|",
    ]
    for filing in ordered:
        mine = by_accession[filing["accession"]]
        totals = sum(1 for f in mine if not f["dimensions"])
        lines.append(
            f"| {filing['ticker']} | {filing['fiscal_year']} | {filing['accession']} | "
            f"{len(mine):,} | {totals:,} |"
        )
    lines.append(
        f"| **All** | | | **{len(facts):,}** | "
        f"**{sum(1 for f in facts if not f['dimensions']):,}** |"
    )
    lines += [
        "",
        "## Cross-check with companyfacts",
        "",
        f"Candidate tags compared: {len(tags)} ({', '.join(f'`{t}`' for t in tags)}).",
        "",
        f"- Agreements: {status_count['agree']:,}",
        f"- Disagreements: {status_count['disagree']:,}",
        f"- Not in companyfacts: {status_count['not in companyfacts']:,}",
        f"- Not in the filing's XBRL: {status_count[STATUSES[3]]:,}",
        "",
        "| Ticker | FY | Agree | Disagree | Not in companyfacts | Not in the filing's XBRL |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for filing in ordered:
        counted = Counter(r.status for r in rows if r.accession == filing["accession"])
        lines.append(
            f"| {filing['ticker']} | {filing['fiscal_year']} | "
            + " | ".join(str(counted[s]) for s in STATUSES)
            + " |"
        )
    others = [r for r in rows if r.status != "agree"]
    lines += ["", "Every row that is not an agreement:", ""]
    if others:
        lines += [
            "| Ticker | FY | Tag | Period | Status | Filing's XBRL | companyfacts |",
            "|---|---:|---|---|---|---:|---:|",
        ]
        lines += [
            f"| {r.ticker} | {r.fiscal_year} | `{r.tag}` | {r.period} | {r.status} | "
            f"{r.ours or '—'} | {r.theirs or '—'} |"
            for r in others
        ]
    else:
        lines.append("None.")
    conflicts: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for fact in facts:
        if fact["conflict"]:
            key = (
                fact["ticker"],
                fact["fiscal_year"],
                fact["concept"],
                fact["period_start"],
                fact["period_end"],
                fact["instant"],
                fact["unit"],
                json.dumps(fact["dimensions"], sort_keys=True),
            )
            conflicts[key].append(fact)
    lines += [
        "",
        "## Conflicts",
        "",
        "Facts with the same concept, period, unit and dimensions but different values in one "
        "filing. Both values are kept and marked `conflict: true`.",
        "",
        f"Conflicts: {sum(len(g) for g in conflicts.values())} facts in {len(conflicts)} groups",
        "",
    ]
    for key, group in sorted(conflicts.items(), key=lambda kv: str(kv[0])):
        ticker, year, concept, start, end, instant, unit, dims = key
        period = _period(start, end) if end else instant
        extra = f" {dims}" if dims != "{}" else ""
        values = ", ".join(sorted(f["value"] for f in group))
        lines.append(f"- {ticker} FY{year} `{concept}`{extra} {period} ({unit}): {values}")
    if pins is not None:
        lines += [
            "",
            "## companyfacts files used",
            "",
            "| Ticker | SHA-256 | Equals its pin in `data/companyfacts_pins.json` |",
            "|---|---|---|",
        ]
        lines += [
            f"| {t} | `{digest}` | {'yes' if same else 'NO'} |"
            for t, (digest, same) in sorted(pins.items())
        ]
    return "\n".join(lines).rstrip("\n") + "\n"


def main(root: Path = REPO_ROOT) -> int:
    """Write docs/facts_report.md and print the cross-check totals."""
    manifest = json.loads((root / "data" / "manifest.json").read_text(encoding="utf-8"))
    filings = manifest["filings"]
    with (root / "data" / "facts.jsonl").open(encoding="utf-8") as handle:
        facts = [json.loads(line) for line in handle if line.strip()]
    pinned_path = root / "data" / "companyfacts_pins.json"
    pinned = json.loads(pinned_path.read_text(encoding="utf-8")) if pinned_path.exists() else {}
    companyfacts: dict[str, dict[str, Any] | None] = {}
    used: dict[str, tuple[str, bool]] = {}
    for ticker in sorted({f["ticker"] for f in filings}):
        path = root / "data" / "companyfacts" / f"{ticker}.json"
        if not path.exists():
            companyfacts[ticker] = None
            continue
        body = path.read_bytes()
        companyfacts[ticker] = json.loads(body)
        digest = hashlib.sha256(body).hexdigest()
        used[ticker] = (digest, pinned.get(ticker, {}).get("sha256") == digest)
    page = facts_report(filings, facts, companyfacts, candidate_tags(), used)
    (root / "docs" / "facts_report.md").write_text(page, encoding="utf-8", newline="\n")
    for line in page.splitlines():
        if (
            line.startswith("- ")
            and ": " in line
            and line[2:].split(":")[0]
            in (
                "Agreements",
                "Disagreements",
                "Not in companyfacts",
                "Not in the filing's XBRL",
            )
        ):
            print(line[2:])
        if line.startswith("Conflicts: "):
            print(line)
    print("wrote docs/facts_report.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
