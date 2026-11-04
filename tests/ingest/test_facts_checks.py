"""Checks around the facts file: its snapshot, the companyfacts pins and the cross-check."""

import hashlib
import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from filingcheck.ingest.companyfacts import count_pinned_us_gaap_tags, pin_entry
from filingcheck.ingest.facts_check import cross_check, facts_report
from filingcheck.ingest.verify import compare_facts, current_facts, pin_differences

ACC = "0000999999-26-000001"
OTHER = "0000999999-25-000001"


def fact(**over: Any) -> dict[str, Any]:
    row: dict[str, Any] = {
        "accession": ACC,
        "ticker": "EXMP",
        "fiscal_year": 2025,
        "concept": "us-gaap:Revenues",
        "value": "1234000000",
        "unit": "USD",
        "period_start": "2025-01-01",
        "period_end": "2025-12-31",
        "instant": None,
        "decimals": "-6",
        "scale": 6,
        "sign": None,
        "dimensions": {},
        "context_ref": "c-1",
        "conflict": False,
    }
    row.update(over)
    return row


def write_facts_file(root: Path, rows: list[dict[str, Any]]) -> Path:
    path = root / "data" / "facts.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8", newline="\n")
    return path


# ---------------------------------------------------------------- facts snapshot


def test_the_facts_snapshot_holds_counts_and_a_hash_per_filing(tmp_path: Path) -> None:
    rows = [
        fact(),
        fact(context_ref="c-3", value="500000000", dimensions={"a:Axis": "a:Member"}),
        fact(accession=OTHER, fiscal_year=2024, period_end="2024-12-31"),
    ]
    path = write_facts_file(tmp_path, rows)
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    current = current_facts(tmp_path)
    assert current == {
        "EXMP FY2025": {
            "facts": 2,
            "totals": 1,
            "sha256": hashlib.sha256("".join(lines[:2]).encode("utf-8")).hexdigest(),
        },
        "EXMP FY2024": {
            "facts": 1,
            "totals": 1,
            "sha256": hashlib.sha256(lines[2].encode("utf-8")).hexdigest(),
        },
    }


def test_every_difference_from_the_facts_snapshot_is_listed(tmp_path: Path) -> None:
    write_facts_file(tmp_path, [fact(), fact(accession=OTHER, fiscal_year=2024)])
    expected = current_facts(tmp_path)
    assert compare_facts(expected, expected) == []
    write_facts_file(tmp_path, [fact(value="1234000001"), fact(concept="us-gaap:Assets")])
    changed = current_facts(tmp_path)
    assert compare_facts(expected, changed) == [
        "EXMP FY2024: 1 facts in the snapshot, none now",
        "EXMP FY2025: facts changed (1 to 2 facts; 1 to 2 company totals)",
    ]
    write_facts_file(tmp_path, [fact(value="1234000001"), fact(accession=OTHER, fiscal_year=2024)])
    assert compare_facts(expected, current_facts(tmp_path)) == [
        "EXMP FY2025: facts changed (same counts, different values or fields)"
    ]


def test_a_missing_facts_file_is_reported_not_crashed_on(tmp_path: Path) -> None:
    assert current_facts(tmp_path) == {}


# ---------------------------------------------------------------- companyfacts pins


def test_pins_record_hash_size_and_the_download_time_of_the_cached_copy(tmp_path: Path) -> None:
    body = b'{"facts": {"us-gaap": {}}}'
    cached = tmp_path / "cache-file"
    cached.write_bytes(body)
    when = datetime(2026, 10, 25, 21, 28, 22, tzinfo=UTC).timestamp()
    os.utime(cached, (when, when))
    assert pin_entry(body, cached) == {
        "sha256": hashlib.sha256(body).hexdigest(),
        "bytes": len(body),
        "downloaded_utc": "2026-10-25T21:28:22Z",
    }


def test_companyfacts_files_that_differ_from_their_pins_are_listed(tmp_path: Path) -> None:
    folder = tmp_path / "data" / "companyfacts"
    folder.mkdir(parents=True)
    (folder / "AAA.json").write_bytes(b"one")
    (folder / "BBB.json").write_bytes(b"two")
    pins = {
        "AAA": {"sha256": hashlib.sha256(b"one").hexdigest(), "bytes": 3, "downloaded_utc": "x"},
        "BBB": {"sha256": hashlib.sha256(b"old").hexdigest(), "bytes": 3, "downloaded_utc": "x"},
        "CCC": {"sha256": "0" * 64, "bytes": 1, "downloaded_utc": "x"},
    }
    (tmp_path / "data" / "companyfacts_pins.json").write_text(json.dumps(pins), encoding="utf-8")
    assert pin_differences(tmp_path) == [
        "BBB: data/companyfacts/BBB.json differs from its pin (downloaded x)",
        "CCC: pinned, but data/companyfacts/CCC.json is missing",
    ]
    (folder / "DDD.json").write_bytes(b"new")
    assert pin_differences(tmp_path)[-1] == "DDD: data/companyfacts/DDD.json has no pin"


# ---------------------------------------------------------------- data report tag counts


def test_us_gaap_tags_are_counted_only_from_the_pinned_filings() -> None:
    body = json.dumps(
        {
            "facts": {
                "us-gaap": {
                    "Revenues": {"units": {"USD": [{"accn": ACC, "val": 1}]}},
                    "Assets": {"units": {"USD": [{"accn": "0000999999-26-000009", "val": 2}]}},
                    "Liabilities": {"units": {"USD": [{"accn": OTHER, "val": 3}]}},
                },
                "dei": {
                    "EntityCommonStockSharesOutstanding": {"units": {"shares": [{"accn": ACC}]}}
                },
            }
        }
    ).encode()
    assert count_pinned_us_gaap_tags(body, {ACC, OTHER}) == 2
    assert count_pinned_us_gaap_tags(body, set()) == 0


# ---------------------------------------------------------------- companyfacts cross-check


def companyfacts(rows: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    return {
        "facts": {
            "us-gaap": {tag: {"units": {"USD": units}} for tag, units in rows.items()},
        }
    }


FILING = {"ticker": "EXMP", "fiscal_year": 2025, "accession": ACC, "period_of_report": "2025-12-31"}


def test_the_cross_check_finds_agreements_disagreements_and_missing_facts() -> None:
    facts = [
        fact(),  # agrees
        fact(concept="us-gaap:NetIncomeLoss", value="-45000000"),  # disagrees
        fact(
            concept="us-gaap:Assets",
            period_start=None,
            period_end=None,
            instant="2025-12-31",
            value="9876000000",
        ),  # not in companyfacts
        fact(
            concept="us-gaap:Revenues", value="500000000", dimensions={"a:Axis": "a:M"}
        ),  # segment: ignored
        fact(concept="us-gaap:Revenues", period_start="2025-10-01", value="300000000"),  # a quarter
        fact(
            concept="us-gaap:Revenues",
            period_start="2024-01-01",
            period_end="2024-12-31",
            value="1100000000",
        ),  # an earlier year: not compared
    ]
    data = companyfacts(
        {
            "Revenues": [
                {"accn": ACC, "start": "2025-01-01", "end": "2025-12-31", "val": 1234000000},
                {"accn": ACC, "start": "2025-10-01", "end": "2025-12-31", "val": 300000000},
                {"accn": OTHER, "start": "2025-01-01", "end": "2025-12-31", "val": 999},
            ],
            "NetIncomeLoss": [
                {"accn": ACC, "start": "2025-01-01", "end": "2025-12-31", "val": -44000000}
            ],
            "OperatingIncomeLoss": [
                {"accn": ACC, "start": "2025-01-01", "end": "2025-12-31", "val": 7}
            ],
        }
    )
    rows = cross_check(
        FILING, facts, data, ["Revenues", "NetIncomeLoss", "Assets", "OperatingIncomeLoss"]
    )
    assert [(r.tag, r.period, r.status) for r in rows] == [
        ("Assets", "2025-12-31", "not in companyfacts"),
        ("NetIncomeLoss", "2025-01-01 to 2025-12-31", "disagree"),
        ("OperatingIncomeLoss", "2025-01-01 to 2025-12-31", "not in the filing's XBRL"),
        ("Revenues", "2025-01-01 to 2025-12-31", "agree"),
        ("Revenues", "2025-10-01 to 2025-12-31", "agree"),
    ]
    [disagree] = [r for r in rows if r.status == "disagree"]
    assert (disagree.ours, disagree.theirs) == ("-45000000", "-44000000")


def test_a_filing_with_no_facts_in_companyfacts_has_only_not_in_companyfacts_rows() -> None:
    rows = cross_check(FILING, [fact()], {"facts": {"us-gaap": {}}}, ["Revenues"])
    assert [r.status for r in rows] == ["not in companyfacts"]


def test_the_facts_report_lists_counts_the_cross_check_and_conflicts() -> None:
    facts = [
        fact(),
        fact(concept="us-gaap:OperatingIncomeLoss", value="1", conflict=True),
        fact(concept="us-gaap:OperatingIncomeLoss", value="2", conflict=True),
        fact(context_ref="c-3", dimensions={"a:Axis": "a:M"}, value="5"),
    ]
    data = companyfacts(
        {"Revenues": [{"accn": ACC, "start": "2025-01-01", "end": "2025-12-31", "val": 1234000000}]}
    )
    page = facts_report([FILING], facts, {"EXMP": data}, ["Revenues"])
    assert "| EXMP | 2025 | 0000999999-26-000001 | 4 | 3 |" in page
    assert "Agreements: 1" in page and "Disagreements: 0" in page
    assert "Conflicts: 2 facts in 1 groups" in page
    assert "us-gaap:OperatingIncomeLoss" in page.split("## Conflicts")[1]
