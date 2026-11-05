"""Gold values for number questions, from the filing's own XBRL facts through the lookup.

`python -m filingcheck.eval gold` fills `gold_value`, `gold_unit`, the period, the tag and
the filing of every number question (`expected_behavior: answer`) that names a company, a
fiscal year and a metric, using the same lookup the agent's `get_financial_fact` tool uses, and
records the same metric for the company's other pinned years (`gold_other_years`). A clarify
or refuse question gets no gold value. A value a person set (`gold_source: "hand"`), or any
value with no source, is never overwritten. The evaluation therefore measures whether
an answer picks the right filing, year and metric and reports the number correctly; the facts
themselves are checked separately (eval/README.md).
"""

import json
from decimal import Decimal
from pathlib import Path
from typing import Any

from filingcheck.facts.lookup import FactsSource, lookup

GOLD_FIELDS = (
    "gold_value",
    "gold_unit",
    "gold_source",
    "gold_concept",
    "gold_accession",
    "gold_period_start",
    "gold_period_end",
    "gold_instant",
    "gold_other_years",
)
# The pinned years are three in a row; this reaches every other one from any of them.
OTHER_YEAR_SPAN = 3


def _number(value: Decimal) -> int | float:
    """The JSON number for a fact's exact decimal: an integer when it is whole."""
    return int(value) if value == value.to_integral_value() else float(value)


def _other_years(facts: FactsSource, ticker: str, year: int, metric: str) -> dict[str, Any]:
    """The metric's value in each other pinned year of the company, keyed by year as text."""
    others: dict[str, Any] = {}
    for other in range(year - OTHER_YEAR_SPAN, year + OTHER_YEAR_SPAN + 1):
        if other == year or facts.filing(ticker, other) is None:
            continue
        result = lookup(facts, ticker, other, metric)
        if result is not None:
            others[str(other)] = _number(result.value)
    return others


def fill_gold(
    rows: list[dict[str, Any]], facts: FactsSource
) -> tuple[list[dict[str, Any]], list[tuple[str, str, str]]]:
    """The question rows with gold values filled in, and what was done to each (id, action, detail).

    Rows are dictionaries as read from the question file, so fields the filler does not know
    are kept as they are.
    """
    out: list[dict[str, Any]] = []
    report: list[tuple[str, str, str]] = []
    for row in rows:
        qid = row["id"]
        if row.get("gold_value") is not None and row.get("gold_source") != "facts":
            who = "set by hand" if row.get("gold_source") == "hand" else "no gold_source"
            report.append((qid, f"kept: {who}", str(row["gold_value"])))
            out.append(row)
            continue
        behavior = row.get("expected_behavior")
        if behavior in ("clarify", "refuse"):
            report.append((qid, f"skipped: a {behavior} question", ""))
            had_gold = row.get("gold_source") == "facts"
            out.append({**row, **dict.fromkeys(GOLD_FIELDS)} if had_gold else row)
            continue
        ticker, year, metric = row.get("company"), row.get("fiscal_year"), row.get("metric")
        if ticker is None or year is None or metric is None:
            report.append((qid, "skipped: no company, year or metric", ""))
            out.append(row)
            continue
        result = lookup(facts, ticker, year, metric)
        if result is None:
            report.append((qid, f"unavailable: the filing reports no {metric}", ""))
            out.append({**row, **dict.fromkeys(GOLD_FIELDS)} | {"gold_unit": row.get("gold_unit")})
            continue
        filled = {
            **row,
            "gold_value": _number(result.value),
            "gold_unit": result.unit,
            "gold_source": "facts",
            "gold_concept": result.concept,
            "gold_accession": result.accession,
            "gold_period_start": result.period_start.isoformat() if result.period_start else None,
            "gold_period_end": result.period_end.isoformat() if result.period_end else None,
            "gold_instant": result.instant.isoformat() if result.instant else None,
            "gold_other_years": _other_years(facts, ticker, year, metric),
        }
        period = (
            f"{result.period_start} to {result.period_end}"
            if result.period_start
            else str(result.instant)
        )
        report.append((qid, "filled", f"{result.value} {result.unit}, {period}"))
        out.append(filled)
    return out, report


def fill_gold_file(path: Path, facts: FactsSource) -> list[tuple[str, str, str]]:
    """Fill the gold values of one question file in place, keeping its order and other fields."""
    rows = [
        json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()
    ]
    filled, report = fill_gold(rows, facts)
    path.write_text("".join(json.dumps(r) + "\n" for r in filled), encoding="utf-8", newline="\n")
    return report
