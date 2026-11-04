"""The facts stage: numeric facts from each filing's own inline XBRL, de-duplicated."""

import json
import shutil
from datetime import date
from pathlib import Path

import pytest

from filingcheck.ingest.facts import (
    Fact,
    FactsError,
    canonical_value,
    deduplicate,
    filing_facts,
    numeric_facts,
    splice_header,
    write_facts,
)
from filingcheck.ingest.filings import ExtraDocument, Filing, Manifest

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
PRIMARY = "data/filings/EXMP/2025_0000999999-26-000001.html"
EXHIBIT = "data/filings/EXMP/2025_0000999999-26-000001_exmp-20251231_d2.htm"


def fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def make_filing(
    root: Path, accession: str = "0000999999-26-000001", exhibit: bool = False
) -> Filing:
    primary = PRIMARY.replace("0000999999-26-000001", accession)
    (root / primary).parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(FIXTURES / "ixbrl_sample.html", root / primary)
    extra = []
    if exhibit:
        path = EXHIBIT.replace("0000999999-26-000001", accession)
        shutil.copy(FIXTURES / "ixbrl_exhibit_sample.html", root / path)
        extra = [
            ExtraDocument(type="EX-13", url="https://www.sec.gov/x_d2.htm", document_path=path)
        ]
    return Filing(
        ticker="EXMP",
        cik="0000999999",
        fiscal_year=2025,
        fiscal_year_source="dei",
        form="10-K",
        accession=accession,
        filing_date=date(2026, 2, 20),
        period_of_report=date(2025, 12, 31),
        primary_document_url="https://www.sec.gov/Archives/edgar/data/999999/x/exmp-20251231.htm",
        document_path=primary,
        extra_documents=extra,
    )


def by(facts: list[Fact], concept: str, **where: object) -> list[Fact]:
    return [
        f
        for f in facts
        if f.concept == concept and all(getattr(f, k) == v for k, v in where.items())
    ]


# ---------------------------------------------------------------- one document


def test_numeric_facts_keep_value_unit_period_and_dimensions_as_filed() -> None:
    parsed = numeric_facts(fixture("ixbrl_sample.html"))
    rows = parsed.facts
    sales = [r for r in rows if r["concept"] == "us-gaap:Revenues" and r["context_ref"] == "c-1"]
    assert sales[0]["value"] == "1234000000"  # "1,234" with scale 6, in dollars
    assert sales[0]["unit"] == "USD"
    assert (sales[0]["period_start"], sales[0]["period_end"]) == (
        date(2025, 1, 1),
        date(2025, 12, 31),
    )
    assert sales[0]["instant"] is None
    assert (sales[0]["decimals"], sales[0]["scale"], sales[0]["sign"]) == ("-6", 6, None)
    assert sales[0]["dimensions"] == {}
    [loss] = [r for r in rows if r["concept"] == "us-gaap:NetIncomeLoss"]
    assert (loss["value"], loss["sign"]) == ("-45000000", "-")
    [eps] = [r for r in rows if r["concept"] == "us-gaap:EarningsPerShareDiluted"]
    assert (eps["value"], eps["unit"], eps["decimals"]) == ("-1.23", "USD/shares", "2")
    [assets] = [r for r in rows if r["concept"] == "us-gaap:Assets"]
    assert (assets["instant"], assets["period_start"], assets["period_end"]) == (
        date(2025, 12, 31),
        None,
        None,
    )
    [segment] = [r for r in rows if r["context_ref"] == "c-3"]
    assert segment["dimensions"] == {
        "us-gaap:StatementBusinessSegmentsAxis": "exmp:WidgetsSegmentMember"
    }
    [cover] = [r for r in rows if r["concept"] == "dei:EntityCommonStockSharesOutstanding"]
    assert (cover["value"], cover["unit"], cover["instant"]) == (
        "7500000",
        "shares",
        date(2026, 2, 10),
    )


def test_text_facts_and_nil_facts_are_left_out() -> None:
    parsed = numeric_facts(fixture("ixbrl_sample.html"))
    concepts = {r["concept"] for r in parsed.facts}
    assert "dei:DocumentType" not in concepts and "dei:EntityFilerCategory" not in concepts
    assert "us-gaap:CommitmentsAndContingencies" not in concepts  # xsi:nil, no amount
    assert parsed.nil == 1
    assert len(parsed.facts) == 10


def test_a_document_whose_facts_have_no_period_is_refused() -> None:
    # The exhibit's contexts and units are defined only in the primary document's header.
    with pytest.raises(FactsError, match="no period"):
        numeric_facts(fixture("ixbrl_exhibit_sample.html"))


def test_values_are_kept_as_exact_decimal_strings() -> None:
    assert canonical_value("416161000000") == "416161000000"
    assert canonical_value("0.0500") == "0.05"
    assert canonical_value("-0") == "0"
    assert canonical_value("1.2300E+3") == "1230"


# ---------------------------------------------------------------- de-duplication


def test_the_same_fact_printed_twice_is_kept_once() -> None:
    result = deduplicate(numeric_facts(fixture("ixbrl_sample.html")).facts)
    totals = [
        f for f in result.facts if f["concept"] == "us-gaap:Revenues" and f["context_ref"] == "c-1"
    ]
    assert len(totals) == 1  # "1,234" in millions and "1.234" in billions: the same fact
    assert totals[0]["decimals"] == "-6"  # the first one printed is kept
    assert result.duplicates_removed == 1


def test_different_values_for_one_fact_are_both_kept_and_marked_as_a_conflict() -> None:
    result = deduplicate(numeric_facts(fixture("ixbrl_sample.html")).facts)
    operating = [f for f in result.facts if f["concept"] == "us-gaap:OperatingIncomeLoss"]
    assert sorted(f["value"] for f in operating) == ["100000000", "101000000"]
    assert all(f["conflict"] for f in operating)
    assert not any(
        f["conflict"] for f in result.facts if f["concept"] != "us-gaap:OperatingIncomeLoss"
    )
    assert result.conflict_groups == 1


def test_a_segment_fact_is_neither_a_duplicate_nor_a_conflict_of_the_total() -> None:
    result = deduplicate(numeric_facts(fixture("ixbrl_sample.html")).facts)
    year = [
        f
        for f in result.facts
        if f["concept"] == "us-gaap:Revenues" and f["period_end"] == date(2025, 12, 31)
    ]
    assert sorted((f["value"], bool(f["dimensions"])) for f in year) == [
        ("1234000000", False),
        ("500000000", True),
    ]
    assert not any(f["conflict"] for f in year)


# ---------------------------------------------------------------- filings with an exhibit


def test_the_header_is_spliced_into_the_exhibit_before_its_body_ends() -> None:
    spliced = splice_header(fixture("ixbrl_sample.html"), fixture("ixbrl_exhibit_sample.html"))
    assert spliced.count("<ix:header>") == 1
    assert spliced.index("</ix:header>") < spliced.lower().rindex("</body>")
    assert "x-1" in spliced  # the exhibit's own facts are still there
    with pytest.raises(FactsError, match="ix:header"):
        splice_header(fixture("ixbrl_exhibit_sample.html"), fixture("ixbrl_exhibit_sample.html"))


def test_an_exhibit_is_read_with_the_primary_documents_contexts(tmp_path: Path) -> None:
    result = filing_facts(make_filing(tmp_path, exhibit=True), tmp_path)
    cash = by(result.facts, "us-gaap:NetCashProvidedByUsedInOperatingActivities")
    assert sorted((f.period_end, f.value) for f in cash) == [
        (date(2024, 12, 31), "300000000"),
        (date(2025, 12, 31), "321000000"),
    ]
    assert all(f.unit == "USD" and f.dimensions == {} for f in cash)
    # The exhibit prints the year's revenue again: still one fact.
    assert (
        len(by(result.facts, "us-gaap:Revenues", period_end=date(2025, 12, 31), dimensions={})) == 1
    )
    assert result.documents == 2


def test_filing_facts_carry_the_filing_and_count_what_was_dropped(tmp_path: Path) -> None:
    result = filing_facts(make_filing(tmp_path), tmp_path)
    assert {(f.accession, f.ticker, f.fiscal_year) for f in result.facts} == {
        ("0000999999-26-000001", "EXMP", 2025)
    }
    assert (len(result.facts), result.parsed, result.duplicates_removed, result.nil) == (
        9,
        10,
        1,
        1,
    )
    assert result.conflict_groups == 1


# ---------------------------------------------------------------- the facts file


def test_the_facts_file_has_one_sorted_fact_per_line(tmp_path: Path) -> None:
    manifest = Manifest(
        filings=[
            make_filing(tmp_path, "0000999999-26-000002"),
            make_filing(tmp_path, "0000999999-26-000001", exhibit=True),
        ]
    )
    out = tmp_path / "data" / "facts.jsonl"
    results = write_facts(manifest, tmp_path, out)
    lines = out.read_text(encoding="utf-8").splitlines()
    facts = [Fact.model_validate_json(line) for line in lines]
    assert len(facts) == sum(len(r.facts) for r in results) == 9 + 11
    keys = [
        (f.accession, f.concept, f.period_start or date.min, f.period_end or date.min)
        for f in facts
    ]
    assert keys == sorted(keys)
    assert facts[0].accession == "0000999999-26-000001"
    assert json.loads(lines[0])["value"] == facts[0].value  # a string, never a float
    assert isinstance(json.loads(lines[0])["value"], str)
    write_facts(manifest, tmp_path, out)
    assert out.read_text(encoding="utf-8").splitlines() == lines  # the same every run


def test_the_facts_stage_writes_the_file_and_prints_the_totals(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    from filingcheck.ingest import __main__ as cli
    from filingcheck.ingest.filings import write_manifest

    manifest = tmp_path / "manifest.json"
    write_manifest(manifest, Manifest(filings=[make_filing(tmp_path, exhibit=True)]))
    assert cli.run_facts(manifest, tmp_path) == 0
    out = capsys.readouterr().out
    assert (tmp_path / "data" / "facts.jsonl").exists()
    assert "11 facts from 1 filings (2 documents)" in out
    assert (
        "14 numeric facts parsed, 3 duplicates removed, 0 rounded copies removed, "
        "1 nil facts skipped" in out
    )
    assert "conflicts: 2 facts in 1 groups" in out
    assert (
        "EXMP FY2025 us-gaap:OperatingIncomeLoss 2025-01-01 to 2025-12-31: 100000000, 101000000"
        in out
    )


# ---------------------------------------------------------------- rounded copies


def row(value: str, decimals: str | None, **over: object) -> dict[str, object]:
    base: dict[str, object] = {
        "concept": "us-gaap:Assets",
        "value": value,
        "unit": "USD",
        "period_start": None,
        "period_end": None,
        "instant": date(2025, 12, 31),
        "decimals": decimals,
        "scale": 6,
        "sign": None,
        "dimensions": {},
        "context_ref": f"c-{value}",
    }
    base.update(over)
    return base


def test_a_rounded_copy_in_the_text_is_removed_and_the_table_value_kept() -> None:
    # 261,108 million in the balance sheet, "$261 billion" in the text.
    result = deduplicate([row("261000000000", "-9"), row("261108000000", "-6")])
    assert [(f["value"], f["conflict"]) for f in result.facts] == [("261108000000", False)]
    assert (result.rounded_copies_removed, result.conflict_groups) == (1, 0)


def test_in_a_three_way_group_only_the_most_precise_fact_is_kept() -> None:
    result = deduplicate(
        [row("1235000000", "-6"), row("1234567000", "-3"), row("1200000000", "-8")]
    )
    assert [f["value"] for f in result.facts] == ["1234567000"]
    assert (result.rounded_copies_removed, result.conflict_groups) == (2, 0)


def test_rounding_is_half_up_as_the_filings_round() -> None:
    # Goldman prints 1,245 million as 1.25 billion (decimals -7); half-even would give 1.24.
    for exact, rounded in (("1245000000", "1250000000"), ("27985000000", "27990000000")):
        result = deduplicate([row(exact, "-6"), row(rounded, "-7")])
        assert [f["value"] for f in result.facts] == [exact]
        assert result.rounded_copies_removed == 1
    negative = deduplicate([row("-1245000000", "-6"), row("-1250000000", "-7")])
    assert [f["value"] for f in negative.facts] == ["-1245000000"]


def test_a_value_that_is_not_a_rounding_of_the_precise_one_is_a_real_conflict() -> None:
    result = deduplicate([row("261108000000", "-6"), row("262000000000", "-9")])
    assert sorted((f["value"], f["conflict"]) for f in result.facts) == [
        ("261108000000", True),
        ("262000000000", True),
    ]
    assert (result.rounded_copies_removed, result.conflict_groups) == (0, 1)


def test_different_values_with_the_same_decimals_are_a_real_conflict() -> None:
    result = deduplicate([row("100000000", "-6"), row("101000000", "-6")])
    assert sorted((f["value"], f["conflict"]) for f in result.facts) == [
        ("100000000", True),
        ("101000000", True),
    ]
    assert (result.rounded_copies_removed, result.conflict_groups) == (0, 1)


def test_an_exact_fact_counts_as_the_most_precise() -> None:
    result = deduplicate([row("1626828437", "INF"), row("1627000000", "-6")])
    assert [f["value"] for f in result.facts] == ["1626828437"]
    assert result.rounded_copies_removed == 1
