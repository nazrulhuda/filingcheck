"""Numeric XBRL facts from each pinned filing's own inline XBRL, written to `data/facts.jsonl`.

The facts are read offline from the saved documents with edgartools' inline-XBRL reader,
which applies each fact's scale and sign and resolves its period, unit and dimensions.
Values are kept as exact decimal strings in the unit as filed (dollars, shares, ...); nothing
is rescaled. A fact printed more than once is kept once; different values for the same
fact are both kept and marked as a conflict.
"""

import json
import re
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict

from filingcheck.ingest.filings import Filing, Manifest
from filingcheck.ingest.sec_client import decode_document

FACTS_FILE = "data/facts.jsonl"

_HEADER = re.compile(r"<ix:header\b.*?</ix:header\s*>", re.IGNORECASE | re.DOTALL)
_BODY_END = re.compile(r"</body\s*>", re.IGNORECASE)


class FactsError(ValueError):
    """A document's facts cannot be read completely (no period, unit or value)."""


class Fact(BaseModel):
    """One numeric fact of a pinned filing, as filed (one line of `data/facts.jsonl`)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    accession: str
    ticker: str
    fiscal_year: int
    concept: str  # "taxonomy:Name", e.g. "us-gaap:Revenues"
    value: str  # an exact decimal, scale and sign applied, in the unit as filed
    unit: str  # USD, shares, USD/shares, pure, ...
    period_start: date | None
    period_end: date | None
    instant: date | None
    decimals: str | None  # as the attribute says: "-6", "2", "INF"
    scale: int | None
    sign: str | None  # "-" when the attribute flips the printed number
    dimensions: dict[str, str]  # empty for company totals
    context_ref: str
    conflict: bool = False


@dataclass
class ParsedDocument:
    """The numeric facts of one document, before de-duplication."""

    facts: list[dict[str, Any]]
    nil: int  # facts with xsi:nil (a line with no amount), left out


@dataclass
class Deduplicated:
    """Facts kept once each, and how many copies and conflicting groups were found."""

    facts: list[dict[str, Any]]
    duplicates_removed: int
    conflict_groups: int


@dataclass
class FilingFacts:
    """One filing's facts and what happened on the way."""

    filing: Filing
    facts: list[Fact]
    documents: int
    parsed: int
    nil: int
    duplicates_removed: int
    conflict_groups: int
    conflicts: list[list[Fact]] = field(default_factory=list)


def canonical_value(text: str) -> str:
    """An exact decimal string without exponent or trailing zeros ("0.0500" -> "0.05")."""
    try:
        number = Decimal(text)
    except InvalidOperation as exc:
        raise FactsError(f"not a number: {text!r}") from exc
    if number == 0:
        return "0"
    return format(number.normalize(), "f")


def _date(text: str | None) -> date | None:
    return date.fromisoformat(text) if text else None


def numeric_facts(html: str) -> ParsedDocument:
    """Every numeric fact (`ix:nonFraction`) of one inline-XBRL document.

    Text facts have no unit and are left out, and so are nil facts. A numeric fact without
    a period or unit means the document's contexts are defined elsewhere (an exhibit read
    without its filing's header), which is refused rather than guessed.
    """
    from edgar.documents import parse_html  # the ingest dependency group only

    rows: list[dict[str, Any]] = []
    nil = 0
    for fact in parse_html(html).xbrl_facts:
        if not fact.unit_ref:
            continue  # ix:nonNumeric: text
        if fact.value is None or not str(fact.value).strip():
            nil += 1
            continue
        context = fact.context or {}
        instant = _date(context.get("instant"))
        start, end = _date(context.get("start_date")), _date(context.get("end_date"))
        if instant is None and end is None:
            raise FactsError(f"{fact.concept} ({fact.context_ref}): no period")
        if not fact.unit:
            raise FactsError(f"{fact.concept} ({fact.context_ref}): no unit")
        dimensions = context.get("dimensions") or {}
        rows.append(
            {
                "concept": fact.concept,
                "value": canonical_value(str(fact.value)),
                "unit": fact.unit,
                "period_start": start,
                "period_end": end,
                "instant": instant,
                "decimals": fact.decimals,
                "scale": int(fact.scale) if fact.scale not in (None, "") else None,
                "sign": fact.sign,
                "dimensions": {str(k): str(dimensions[k]) for k in sorted(dimensions)},
                "context_ref": fact.context_ref or "",
            }
        )
    return ParsedDocument(facts=rows, nil=nil)


def _fact_key(row: dict[str, Any]) -> tuple[Any, ...]:
    """What makes two facts the same fact, apart from the value."""
    return (
        row["concept"],
        row["period_start"],
        row["period_end"],
        row["instant"],
        row["unit"],
        tuple(row["dimensions"].items()),
    )


def deduplicate(rows: list[dict[str, Any]]) -> Deduplicated:
    """Keep each fact once (the first printed); mark different values for one fact.

    Two facts are the same when concept, period, unit, dimensions and value are equal.
    """
    kept: dict[tuple[Any, ...], dict[str, Any]] = {}
    values: dict[tuple[Any, ...], set[str]] = defaultdict(set)
    for row in rows:
        key = _fact_key(row)
        full = (*key, row["value"])
        if full not in kept:
            kept[full] = row
            values[key].add(row["value"])
    conflicting = {key for key, seen in values.items() if len(seen) > 1}
    facts = [{**row, "conflict": _fact_key(row) in conflicting} for row in kept.values()]
    return Deduplicated(
        facts=facts, duplicates_removed=len(rows) - len(kept), conflict_groups=len(conflicting)
    )


def splice_header(primary_html: str, exhibit_html: str) -> str:
    """The exhibit with the primary document's `<ix:header>` block inserted before `</body>`.

    An exhibit's facts refer to contexts and units that only the primary document defines;
    edgartools resolves them when the header is in the same text.
    """
    headers: list[str] = _HEADER.findall(primary_html)
    if len(headers) != 1:
        raise FactsError(f"the primary document has {len(headers)} ix:header blocks, not 1")
    ends = list(_BODY_END.finditer(exhibit_html))
    at = ends[-1].start() if ends else len(exhibit_html)
    return exhibit_html[:at] + headers[0] + exhibit_html[at:]


def sort_key(fact: Fact) -> tuple[Any, ...]:
    """Accession, concept, period, dimensions; then unit, value and context for a full order."""
    return (
        fact.accession,
        fact.concept,
        (fact.period_start or date.min).isoformat(),
        (fact.period_end or date.min).isoformat(),
        (fact.instant or date.min).isoformat(),
        json.dumps(fact.dimensions, sort_keys=True),
        fact.unit,
        fact.value,
        fact.context_ref,
    )


def filing_facts(filing: Filing, root: Path) -> FilingFacts:
    """All numeric facts of one filing: its primary document and every extra document."""
    primary = decode_document((root / filing.document_path).read_bytes())
    parsed = [numeric_facts(primary)]
    for extra in filing.extra_documents:
        exhibit = decode_document((root / extra.document_path).read_bytes())
        parsed.append(numeric_facts(splice_header(primary, exhibit)))
    rows = [row for doc in parsed for row in doc.facts]
    result = deduplicate(rows)
    facts = sorted(
        (
            Fact(
                accession=filing.accession,
                ticker=filing.ticker,
                fiscal_year=filing.fiscal_year,
                **row,
            )
            for row in result.facts
        ),
        key=sort_key,
    )
    groups: dict[tuple[Any, ...], list[Fact]] = defaultdict(list)
    for fact in facts:
        if fact.conflict:
            key = (fact.concept, fact.period_start, fact.period_end, fact.instant, fact.unit)
            groups[(*key, json.dumps(fact.dimensions, sort_keys=True))].append(fact)
    return FilingFacts(
        filing=filing,
        facts=facts,
        documents=len(parsed),
        parsed=len(rows),
        nil=sum(doc.nil for doc in parsed),
        duplicates_removed=result.duplicates_removed,
        conflict_groups=result.conflict_groups,
        conflicts=list(groups.values()),
    )


def write_facts(manifest: Manifest, root: Path, out: Path) -> list[FilingFacts]:
    """Write every pinned filing's facts to `out`, sorted, one JSON object per line."""
    results = [filing_facts(f, root) for f in sorted(manifest.filings, key=lambda f: f.accession)]
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_name(out.name + ".tmp")
    with tmp.open("w", encoding="utf-8", newline="\n") as handle:
        for result in results:
            for fact in result.facts:
                handle.write(fact.model_dump_json() + "\n")
    tmp.replace(out)
    return results
