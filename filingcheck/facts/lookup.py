"""`lookup(source, ticker, fiscal_year, metric)`: one company total from one pinned filing.

Rules: only the pinned filing for (ticker, fiscal_year) is read; only company totals (no
dimensions) count; amounts over a period must end on the filing's period of report and
cover a whole fiscal year, and balances must fall on that date; the candidate tags are tried
in order and the first with a fact wins. The cover-page share count is the one exception on
dates: it is returned with its own date and a note. Nothing is derived and no unit is
changed; a metric the filing does not report is unavailable (None).
"""

import json
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any, Protocol

import psycopg
import yaml
from pydantic import BaseModel, ConfigDict

from filingcheck.facts.metrics import ANNUAL_DAYS, COVER_PAGE_SHARES, METRICS, candidate_tags


@dataclass(frozen=True)
class FilingRef:
    """The pinned filing for one company and fiscal year."""

    ticker: str
    fiscal_year: int
    accession: str
    period_of_report: date
    source_url: str  # the filing's primary document
    revenue_rule: str


@dataclass(frozen=True)
class TotalFact:
    """One fact as the lookup reads it."""

    concept: str
    value: Decimal
    unit: str
    period_start: date | None
    period_end: date | None
    instant: date | None
    decimals: str | None
    dimensions: dict[str, str] = field(default_factory=dict)


class FactsSource(Protocol):
    """Where the lookup reads filings and facts from (the facts table, or the files)."""

    def filing(self, ticker: str, fiscal_year: int) -> FilingRef | None:
        """The pinned filing for (ticker, fiscal_year), or None."""
        ...

    def facts(self, accession: str, concepts: Sequence[str]) -> list[TotalFact]:
        """The filing's company totals (no dimensions) under any of `concepts`."""
        ...


class FactResult(BaseModel):
    """A metric's value as one filing reports it, with where it came from."""

    model_config = ConfigDict(frozen=True)

    ticker: str
    fiscal_year: int
    metric: str
    value: Decimal  # in the unit as filed: dollars stay dollars
    unit: str
    period_start: date | None
    period_end: date | None
    instant: date | None
    concept: str
    accession: str
    source_url: str
    decimals: str | None
    note: str | None = None


def _fits(fact: TotalFact, period: str, period_of_report: date) -> bool:
    if fact.dimensions:
        return False
    if period == "instant":
        return fact.instant == period_of_report
    if fact.period_end != period_of_report or fact.period_start is None:
        return False
    return (fact.period_end - fact.period_start).days in ANNUAL_DAYS


def _cover_page(fact: TotalFact, period_of_report: date) -> bool:
    return not fact.dimensions and fact.instant is not None and fact.instant >= period_of_report


def lookup(source: FactsSource, ticker: str, fiscal_year: int, metric: str) -> FactResult | None:
    """The metric from the pinned filing for (ticker, fiscal_year), or None if unavailable."""
    filing = source.filing(ticker, fiscal_year)
    if filing is None:
        return None
    spec = METRICS[metric]
    tags = candidate_tags(metric, filing.revenue_rule)
    facts = source.facts(filing.accession, tags)
    for tag in tags:
        cover = tag == COVER_PAGE_SHARES
        matches = [
            f
            for f in facts
            if f.concept == tag
            and (
                _cover_page(f, filing.period_of_report)
                if cover
                else _fits(f, spec.period, filing.period_of_report)
            )
        ]
        if not matches:
            continue
        if cover:
            latest = max(f.instant for f in matches if f.instant is not None)
            matches = [f for f in matches if f.instant == latest]
        if len({(f.value, f.unit) for f in matches}) > 1:
            values = ", ".join(sorted(str(f.value) for f in matches))
            raise LookupError(f"{ticker} FY{fiscal_year} {tag}: more than one value ({values})")
        fact = matches[0]
        note = None
        if cover:
            note = (
                f"cover-page share count dated {fact.instant}, after the fiscal year ended "
                f"{filing.period_of_report}; the filing reports no count dated at year end"
            )
        return FactResult(
            ticker=filing.ticker,
            fiscal_year=filing.fiscal_year,
            metric=metric,
            value=fact.value,
            unit=fact.unit,
            period_start=fact.period_start,
            period_end=fact.period_end,
            instant=fact.instant,
            concept=fact.concept,
            accession=filing.accession,
            source_url=filing.source_url,
            decimals=fact.decimals,
            note=note,
        )
    return None


# ---------------------------------------------------------------- sources


def _optional_date(text: Any) -> date | None:
    if text is None or isinstance(text, date):
        return text
    return date.fromisoformat(str(text))


class PostgresFacts:
    """The `filings`, `companies` and `facts` tables (the live app and the tools)."""

    def __init__(self, conn: psycopg.Connection) -> None:
        self._conn = conn

    def filing(self, ticker: str, fiscal_year: int) -> FilingRef | None:
        """The pinned filing for (ticker, fiscal_year), or None."""
        row = self._conn.execute(
            "SELECT f.ticker, f.fiscal_year, f.accession, f.period_of_report, f.primary_url, "
            "c.revenue_rule FROM filings f JOIN companies c ON c.ticker = f.ticker "
            "WHERE f.ticker = %s AND f.fiscal_year = %s",
            (ticker, fiscal_year),
        ).fetchone()
        if row is None:
            return None
        return FilingRef(
            ticker=row[0],
            fiscal_year=row[1],
            accession=row[2],
            period_of_report=row[3],
            source_url=row[4],
            revenue_rule=row[5],
        )

    def facts(self, accession: str, concepts: Sequence[str]) -> list[TotalFact]:
        """The filing's company totals (no dimensions) under any of `concepts`."""
        rows = self._conn.execute(
            "SELECT x.concept, x.value, x.unit, x.period_start, x.period_end, x.instant, "
            "x.decimals FROM facts x JOIN filings f ON f.id = x.filing_id "
            "WHERE f.accession = %s AND x.concept = ANY(%s) AND x.dimensions = '{}'::jsonb",
            (accession, list(concepts)),
        ).fetchall()
        return [
            TotalFact(
                concept=r[0],
                value=r[1],
                unit=r[2],
                period_start=r[3],
                period_end=r[4],
                instant=r[5],
                decimals=r[6],
            )
            for r in rows
        ]


class JsonlFacts:
    """`data/manifest.json`, `data/companies.yaml` and `data/facts.jsonl` (checks and tests)."""

    def __init__(self, manifest: Path, companies: Path, facts: Path) -> None:
        rules = {
            c["ticker"]: c["revenue_rule"]
            for c in yaml.safe_load(companies.read_text(encoding="utf-8"))["companies"]
        }
        self._filings = {
            (f["ticker"], f["fiscal_year"]): FilingRef(
                ticker=f["ticker"],
                fiscal_year=f["fiscal_year"],
                accession=f["accession"],
                period_of_report=date.fromisoformat(f["period_of_report"]),
                source_url=f["primary_document_url"],
                revenue_rule=rules[f["ticker"]],
            )
            for f in json.loads(manifest.read_text(encoding="utf-8"))["filings"]
        }
        self._facts: dict[str, list[TotalFact]] = {}
        with facts.open(encoding="utf-8") as handle:
            for line in handle:
                row = json.loads(line)
                if row["dimensions"]:
                    continue
                self._facts.setdefault(row["accession"], []).append(
                    TotalFact(
                        concept=row["concept"],
                        value=Decimal(row["value"]),
                        unit=row["unit"],
                        period_start=_optional_date(row["period_start"]),
                        period_end=_optional_date(row["period_end"]),
                        instant=_optional_date(row["instant"]),
                        decimals=row["decimals"],
                    )
                )

    def filing(self, ticker: str, fiscal_year: int) -> FilingRef | None:
        """The pinned filing for (ticker, fiscal_year), or None."""
        return self._filings.get((ticker, fiscal_year))

    def facts(self, accession: str, concepts: Sequence[str]) -> list[TotalFact]:
        """The filing's company totals (no dimensions) under any of `concepts`."""
        wanted = set(concepts)
        return [f for f in self._facts.get(accession, []) if f.concept in wanted]
