"""The number labeler against the hand-written cases in tests/fixtures/label_cases.json."""

import json
from collections.abc import Sequence
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

import filingcheck.labels
from filingcheck.facts.lookup import TotalFact
from filingcheck.labels import (
    SourceCalculation,
    SourceFact,
    SourcePassage,
    Sources,
    label_numbers,
)

CASES = json.loads(
    (Path(__file__).resolve().parents[1] / "fixtures" / "label_cases.json").read_text(
        encoding="utf-8"
    )
)["cases"]


def _date(text: str | None) -> date | None:
    return date.fromisoformat(text) if text else None


class FilingFacts:
    """The filings' facts in memory, by accession: what a read-only facts source returns."""

    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self.rows = rows

    def facts(self, accession: str, concepts: Sequence[str]) -> list[TotalFact]:
        return [
            TotalFact(
                concept=r["concept"],
                value=Decimal(r["value"]),
                unit=r["unit"],
                period_start=_date(r["period_start"]),
                period_end=_date(r["period_end"]),
                instant=_date(r["instant"]),
                decimals=None,
            )
            for r in self.rows
            if r["accession"] == accession and r["concept"] in concepts
        ]


def sources(case: dict[str, Any]) -> Sources:
    facts = [
        SourceFact(
            number=f["number"],
            concept=f["concept"],
            value=Decimal(f["value"]),
            unit=f["unit"],
            period_start=_date(f["period_start"]),
            period_end=_date(f["period_end"]),
            instant=_date(f["instant"]),
            accession=f["accession"],
        )
        for f in case["facts"]
    ]
    # A returned fact is also among its filing's facts, as in the facts table.
    filing_rows = case["filing_facts"] + case["facts"]
    return Sources(
        facts=facts,
        passages=[SourcePassage(number=p["number"], text=p["text"]) for p in case["passages"]],
        calculations=[
            SourceCalculation(expression=c["expression"], value=Decimal(c["value"]))
            for c in case["calculations"]
        ],
        filing_facts=FilingFacts(filing_rows),
    )


def test_the_fixture_holds_at_least_60_cases() -> None:
    assert len(CASES) >= 60


@pytest.mark.parametrize("case", CASES, ids=[c["name"] for c in CASES])
def test_each_case_gets_the_labels_written_for_it(case: dict[str, Any]) -> None:
    labels = label_numbers(case["answer"], sources(case))
    got = [label.model_dump() for label in labels]
    assert len(got) == len(case["expected"]), [(g["figure"], g["label"]) for g in got]
    for found, expected in zip(got, case["expected"], strict=True):
        for key, want in expected.items():
            have = found[key]
            if key in ("value", "cited_value") and want is not None:
                assert have is not None and Decimal(str(have)) == Decimal(want), (key, found)
            else:
                assert have == want, (key, found)


def test_every_label_names_its_source_in_words() -> None:
    case = next(c for c in CASES if c["name"].startswith("another period: the prior year"))
    first, second = label_numbers(case["answer"], sources(case))
    assert first.source == "F1, us-gaap:Revenues, fiscal 2025 (2024-02-01 to 2025-01-31)"
    assert second.source == "F1's concept, us-gaap:Revenues, fiscal 2024 (2023-02-01 to 2024-01-31)"


def test_the_module_says_what_a_verified_label_does_not_prove() -> None:
    doc = filingcheck.labels.__doc__ or ""
    assert "does not prove" in doc and "grader" in doc
