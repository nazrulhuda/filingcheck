"""The hand-checked facts file is well formed; verified facts must carry a value."""

import json
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest
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
    assert len(rows) == 4
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


SCALE = {"units": 1, "thousands": 1_000, "millions": 1_000_000, "billions": 1_000_000_000}


def test_a_verified_value_is_the_printed_number_in_its_printed_units() -> None:
    for row in facts():
        if not row["verified_by_hand"]:
            continue
        assert row["printed_units"] in SCALE, f"{row['id']}: unknown units {row['printed_units']}"
        printed = int(str(row["value_as_printed"]).replace(",", ""))
        assert row["value"] == printed * SCALE[row["printed_units"]], row["id"]


FACTS_FILE = Path(__file__).resolve().parents[1] / "data" / "facts.jsonl"
ANNUAL_DAYS = range(350, 381)


@pytest.mark.slow
@pytest.mark.skipif(not FACTS_FILE.exists(), reason="no data/facts.jsonl; run `make ingest` first")
def test_every_verified_golden_fact_is_reproduced_from_the_filings_own_xbrl() -> None:
    wanted = {(r["ticker"], r["fiscal_year"]): r for r in facts() if r["verified_by_hand"]}
    found: dict[str, set[int]] = {r["id"]: set() for r in wanted.values()}
    with FACTS_FILE.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            golden = wanted.get((row["ticker"], row["fiscal_year"]))
            if golden is None or row["concept"] != golden["xbrl_tag"] or row["dimensions"]:
                continue
            if row["period_end"] != golden["period_end"].isoformat() or not row["period_start"]:
                continue
            days = (
                date.fromisoformat(row["period_end"]) - date.fromisoformat(row["period_start"])
            ).days
            if days in ANNUAL_DAYS:  # the year, not a quarter ending on the same day
                found[golden["id"]].add(int(Decimal(row["value"])))
    assert {r["id"]: {r["value"]} for r in wanted.values()} == found
