"""The hand-checked facts file is well formed; verified facts must carry a value."""

from datetime import date
from pathlib import Path
from typing import Any

import yaml

GOLDEN = Path(__file__).resolve().parent / "golden_facts.yaml"
FIELDS = {
    "id",
    "ticker",
    "fiscal_year",
    "period_end",
    "metric",
    "xbrl_tag",
    "where_to_look",
    "source_url",
    "expected_around",
    "value_as_printed",
    "printed_units",
    "value",
    "unit",
    "verified_by_hand",
}


def facts() -> list[dict[str, Any]]:
    data = yaml.safe_load(GOLDEN.read_text(encoding="utf-8"))
    rows: list[dict[str, Any]] = data["facts"]
    return rows


def test_every_fact_has_the_same_fields_and_a_unique_id() -> None:
    rows = facts()
    assert len(rows) == 3
    assert all(set(row) == FIELDS for row in rows)
    assert len({row["id"] for row in rows}) == len(rows)


def test_every_fact_points_to_an_sec_document_and_a_period() -> None:
    for row in facts():
        assert row["source_url"].startswith("https://www.sec.gov/Archives/edgar/data/")
        assert isinstance(row["period_end"], date)
        assert row["xbrl_tag"].startswith("us-gaap:")


def test_a_fact_marked_verified_has_its_value_filled_in() -> None:
    for row in facts():
        assert isinstance(row["verified_by_hand"], bool)
        if row["verified_by_hand"]:
            assert isinstance(row["value"], int), f"{row['id']}: value must be raw units"
            assert row["value_as_printed"] is not None and row["printed_units"], row["id"]
        else:
            assert row["value"] is None, f"{row['id']}: a value without verification"
