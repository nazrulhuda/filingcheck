"""The labeling rules (see the package docstring)."""

import re
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Any, Literal, Protocol

from pydantic import BaseModel, Field

from filingcheck.answer.citations import cited_numbers, normalize_text, parse_fact_citations
from filingcheck.eval.grade import GROUP_SPACE_RE, RIGHT_QUOTE, Figure, read_figures
from filingcheck.facts.lookup import TotalFact
from filingcheck.facts.metrics import ANNUAL_DAYS

Label = Literal["verified", "conflict", "unverified"]
Basis = Literal["fact", "fact_other_period", "calculation", "passage"]
Kind = Literal["money", "per_share", "shares"]

# A unit's kind, for the Conflict rule.
UNIT_KINDS: dict[str, Kind] = {"USD": "money", "USD/shares": "per_share", "shares": "shares"}
# The scales a calculation's inputs may have been written in ("713163" for $713,163 million).
INPUT_SCALES = (1, 10**3, 10**6, 10**9)
# An input that is a power of ten is a unit change or a percent factor, not a value to check.
POWERS_OF_TEN = {Decimal(10) ** k for k in range(13)}
INPUT_RE = re.compile(r"\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?|\.\d+")
PER_SHARE_AFTER_RE = re.compile(r"\s*(?:per|a)\s+(?:diluted\s+|basic\s+)?share\b", re.IGNORECASE)
SHARES_AFTER_RE = re.compile(r"\s*(?:\w+\s+)?shares?\b", re.IGNORECASE)
PER_SHARE_WORDS_RE = re.compile(
    r"\bEPS\b|\bper\s+(?:diluted\s+|basic\s+)?share\b|\bearnings per\b", re.IGNORECASE
)
DOLLARS_AFTER_RE = re.compile(r"\s*\(?(?:USD|dollars)\b", re.IGNORECASE)
PER_SHARE_MAX = Decimal(10000)  # a dollar figure this small, with no scale, can be per share


class SourceFact(BaseModel):
    """A fact the run's get_financial_fact returned; `number` is its n in [Fn]."""

    number: int
    concept: str
    value: Decimal
    unit: str
    period_start: date | None
    period_end: date | None
    instant: date | None
    accession: str


class SourcePassage(BaseModel):
    """A passage the run retrieved, with its number in the answer's [n] markers."""

    number: int
    text: str


class SourceCalculation(BaseModel):
    """A calculate call of the run: the expression it was given and its exact result."""

    expression: str
    value: Decimal


class FilingFacts(Protocol):
    """Read-only facts of a filing: the facts table, or the facts file."""

    def facts(self, accession: str, concepts: Sequence[str]) -> list[TotalFact]:
        """The filing's company totals (no dimensions) under any of `concepts`."""
        ...


@dataclass
class Sources:
    """What one run used: its facts, the passages it retrieved, its calculations."""

    facts: list[SourceFact] = field(default_factory=list)
    passages: list[SourcePassage] = field(default_factory=list)
    calculations: list[SourceCalculation] = field(default_factory=list)
    filing_facts: FilingFacts | None = None


class NumberLabel(BaseModel):
    """One figure's label and where it was found."""

    figure: str  # as written
    value: Decimal  # raw units; a percentage as shown (5.4 for "5.4%")
    percent: bool
    label: Label
    basis: Basis | None = None  # for Verified: which rule
    fact: int | None = None  # the n of [Fn]: the fact, the fact whose concept, or the cited fact
    concept: str | None = None
    period: str | None = None  # "2024-02-01 to 2025-01-31" or "as of 2025-06-30"
    fiscal_year: int | None = None  # the period's fiscal year: its end's calendar year
    passage: int | None = None
    calculation: str | None = None  # the expression
    cited_value: Decimal | None = None  # for a Conflict: what the cited fact says
    source: str | None = None  # the source in words
    inputs: list[str] = Field(default_factory=list)  # a calculation's sources: "F1", "passage 2"
    # Where the figure ends in the answer text, in UTF-16 code units (how the page counts),
    # so the page can put the label right after it; None if it could not be placed.
    end: int | None = None


@dataclass(frozen=True)
class _Period:
    start: date | None
    end: date | None
    instant: date | None

    @property
    def fiscal_year(self) -> int | None:
        last = self.instant or self.end
        return last.year if last else None

    def __str__(self) -> str:
        if self.instant:
            return f"as of {self.instant.isoformat()}"
        start = self.start.isoformat() if self.start else "?"
        end = self.end.isoformat() if self.end else "?"
        return f"{start} to {end}"


def _half_step(decimals: int, scale: int) -> Decimal:
    """Half the last place shown: $1.3 billion is shown to the nearest $0.1 billion."""
    return Decimal(1).scaleb(-decimals) * scale / 2


def _agrees(value: Decimal, decimals: int, scale: int, source: Decimal) -> bool:
    """Whether a value shown to this precision agrees with the source value, signs included."""
    half = _half_step(decimals, scale)
    if value == 0 or source == 0:
        return abs(source - value) < half
    if (value < 0) != (source < 0):
        return False
    return abs(value) - half <= abs(source) < abs(value) + half


def _matches(figure: Figure, source: Decimal) -> bool:
    return _agrees(figure.value, figure.decimals, figure.scale, source)


def _labelable(figure: Figure) -> bool:
    """Money, plain numbers of 100 or more, decimals, percentages and per-share amounts."""
    return figure.amount or abs(figure.value) >= 100


def _kind(figure: Figure) -> Kind | None:
    """What a figure counts: money, a per-share amount, shares, or unknown."""
    if figure.percent:
        return None
    if PER_SHARE_AFTER_RE.match(figure.after):
        return "per_share"
    if SHARES_AFTER_RE.match(figure.after):
        return "shares"
    if (
        figure.currency
        and figure.scale == 1
        and abs(figure.value) < PER_SHARE_MAX
        and PER_SHARE_WORDS_RE.search(figure.sentence)
    ):
        return "per_share"
    if figure.currency or figure.scale != 1 or DOLLARS_AFTER_RE.match(figure.after):
        return "money"
    return None


def _period(fact: SourceFact | TotalFact) -> _Period:
    return _Period(fact.period_start, fact.period_end, fact.instant)


def _fact_words(fact: SourceFact) -> str:
    period = _period(fact)
    return f"F{fact.number}, {fact.concept}, fiscal {period.fiscal_year} ({period})"


def _annual_or_year_end(fact: TotalFact) -> bool:
    if fact.dimensions:
        return False
    if fact.instant is not None:
        return True
    if fact.period_start is None or fact.period_end is None:
        return False
    return (fact.period_end - fact.period_start).days in ANNUAL_DAYS


def _other_periods(fact: SourceFact, filing_facts: FilingFacts) -> list[TotalFact]:
    """The fact's concept for its filing's other annual periods and year ends, latest first."""
    own = _period(fact)
    found: dict[_Period, TotalFact] = {}
    for other in filing_facts.facts(fact.accession, [fact.concept]):
        period = _period(other)
        if other.concept == fact.concept and period != own and _annual_or_year_end(other):
            found.setdefault(period, other)
    return sorted(found.values(), key=lambda f: f.instant or f.period_end or date.min, reverse=True)


def _calculation_inputs(expression: str, known: list[tuple[Decimal, str]]) -> list[str] | None:
    """The sources of the expression's inputs ("F1", "passage 2"), or None if one is unknown.

    Each input must be a returned fact or a cited passage's figure, written in units, thousands,
    millions or billions; a power of ten is a unit change or a percent factor, not an input.
    """
    names: list[str] = []
    for token in INPUT_RE.findall(expression):
        value = Decimal(token.replace(",", ""))
        if value in POWERS_OF_TEN:
            continue
        decimals = len(token.partition(".")[2])
        name = next(
            (
                source_name
                for source, source_name in known
                for scale in INPUT_SCALES
                if _agrees(value * scale, decimals, scale, abs(source))
            ),
            None,
        )
        if name is None:
            return None
        if name not in names:
            names.append(name)
    return names


def _results(value: Decimal, percent: bool) -> list[Decimal]:
    """A calculation's result in the units a figure may show it in."""
    if percent:
        return [value, value * 100]
    return [value * scale for scale in INPUT_SCALES]


def _new(figure: Figure, label: Label, **found: Any) -> NumberLabel:
    """A label for the figure, with what was found for it."""
    return NumberLabel(
        figure=figure.text, value=figure.value, percent=figure.percent, label=label, **found
    )


def _fact_found(fact: SourceFact) -> dict[str, Any]:
    period = _period(fact)
    return {
        "fact": fact.number,
        "concept": fact.concept,
        "period": str(period),
        "fiscal_year": period.fiscal_year,
        "source": _fact_words(fact),
    }


def label_numbers(answer_text: str, sources: Sources) -> list[NumberLabel]:
    """A label for every figure in the answer, in the order written."""
    facts = {f.number: f for f in sources.facts}
    passage_numbers = {p.number for p in sources.passages}
    highest = max(passage_numbers, default=0)
    cited_passages = [n for n in cited_numbers(answer_text, highest) if n in passage_numbers]
    cited_facts = [n for n in parse_fact_citations(answer_text, len(facts)) if n in facts]
    cites_something = bool(cited_passages or cited_facts)
    passage_figures = {
        p.number: read_figures(p.text) for p in sources.passages if p.number in cited_passages
    }
    known_inputs = [(f.value, f"F{f.number}") for f in sources.facts] + [
        (figure.value, f"passage {number}")
        for number, figures in passage_figures.items()
        for figure in figures
    ]
    labels: list[NumberLabel] = []
    for figure in read_figures(answer_text):
        if not _labelable(figure):
            continue
        if not cites_something:
            labels.append(_new(figure, "unverified"))
            continue
        labels.append(_label(figure, sources, facts, cited_passages, passage_figures, known_inputs))
    return _placed(answer_text, labels)


def _label(
    figure: Figure,
    sources: Sources,
    facts: dict[int, SourceFact],
    cited_passages: list[int],
    passage_figures: dict[int, list[Figure]],
    known_inputs: list[tuple[Decimal, str]],
) -> NumberLabel:
    if not figure.percent:
        for fact in sources.facts:  # 1. a returned fact
            if _matches(figure, fact.value):
                return _new(figure, "verified", basis="fact", **_fact_found(fact))
        if sources.filing_facts is not None:  # 2. the same concept, another period
            for fact in sources.facts:
                for other in _other_periods(fact, sources.filing_facts):
                    if _matches(figure, other.value):
                        period = _period(other)
                        return _new(
                            figure,
                            "verified",
                            basis="fact_other_period",
                            fact=fact.number,
                            concept=fact.concept,
                            period=str(period),
                            fiscal_year=period.fiscal_year,
                            source=(
                                f"F{fact.number}'s concept, {fact.concept}, "
                                f"fiscal {period.fiscal_year} ({period})"
                            ),
                        )
    for calculation in sources.calculations:  # 3. a calculation from known inputs
        if not any(
            _matches(figure, result) for result in _results(calculation.value, figure.percent)
        ):
            continue
        inputs = _calculation_inputs(calculation.expression, known_inputs)
        if inputs is not None:
            return _new(
                figure,
                "verified",
                basis="calculation",
                calculation=calculation.expression,
                inputs=inputs,
                source=f"calculation: {calculation.expression}",
            )
    # 4. a cited passage: the ones its sentence cites first, in the order cited
    order = [n for n in figure.passage_refs if n in passage_figures]
    order += [n for n in cited_passages if n not in order]
    for number in order:
        for found in passage_figures[number]:
            if found.percent == figure.percent and _matches(figure, found.value):
                return _new(
                    figure, "verified", basis="passage", passage=number, source=f"passage {number}"
                )
    kind = _kind(figure)  # 5. a figure of a cited fact's kind that matches nothing
    if kind is not None:
        for number in figure.fact_refs:
            cited = facts.get(number)
            if cited is not None and UNIT_KINDS.get(cited.unit) == kind:
                return _new(figure, "conflict", cited_value=cited.value, **_fact_found(cited))
    return _new(figure, "unverified")


NUMBER_CORE_RE = re.compile(r"\d[\d,]*(?:\.\d+)?")


def _prepared(text: str) -> str:
    """The text as the number reader sees it, one character for one character."""
    return normalize_text(GROUP_SPACE_RE.sub(",", text)).replace(RIGHT_QUOTE, "'")


def _placed(text: str, labels: list[NumberLabel]) -> list[NumberLabel]:
    """Each label with where its figure ends in the text, found in order, in UTF-16 units."""
    prepared = _prepared(text)
    position = 0
    placed: list[NumberLabel] = []
    for label in labels:
        match = re.compile(r"(?<![\d.,])" + re.escape(label.figure) + r"(?!\d)").search(
            prepared, position
        )
        if match is None:  # written across a line break: place it after its digits
            core = NUMBER_CORE_RE.search(label.figure)
            match = (
                re.compile(r"(?<![\d.,])" + re.escape(core.group(0)) + r"(?!\d)").search(
                    prepared, position
                )
                if core
                else None
            )
        if match is None:
            placed.append(label)
            continue
        position = match.end()
        end = len(text[:position].encode("utf-16-le")) // 2
        placed.append(label.model_copy(update={"end": end}))
    return placed
