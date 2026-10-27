import json
from pathlib import Path
from typing import Any

from filingcheck.ingest.verify import (
    check_chunk_counts,
    check_duplicates,
    check_heading,
    parse_report_chunk_counts,
    spot_check,
)

RIGHT_QUOTE = chr(0x2019)


# ---------------------------------------------------------------- headings


def test_a_section_starting_with_its_item_label_passes() -> None:
    assert check_heading("7", "edgartools", "Item 7. Management's Discussion and Analysis") is None
    assert check_heading("1A", "regex", "ITEM 1A.  RISK FACTORS\n\nOur business...") is None
    assert check_heading("1", "edgartools", "Items 1 and 2. Business and Properties") is None


def test_a_section_starting_with_its_item_title_passes() -> None:
    title = f"Table of Contents\n\nManagement{RIGHT_QUOTE}s Discussion and Analysis of Financial"
    assert check_heading("7", "edgartools", title) is None
    assert check_heading("1", "edgartools", "Table of Contents\n\nBusiness\n\nOverview") is None
    assert check_heading("8", "edgartools", "Financial Statements and Supplementary Data") is None


def test_a_section_starting_with_something_else_fails() -> None:
    problem = check_heading("7A", "edgartools", "Third Line of Defense: Internal Audit\n\nInternal")
    assert problem is not None and "Third Line of Defense" in problem


def test_item_1_does_not_accept_item_1a() -> None:
    assert check_heading("1", "edgartools", "Item 1A. Risk Factors") is not None


def test_exhibit_and_relocated_sections_need_their_own_headings() -> None:
    report = "Report of Independent Registered Public Accounting Firm\n\nTo the Board"
    assert check_heading("8", "exhibit", report) is None
    assert check_heading("8", "relocated", report) is None
    assert check_heading("8", "relocated", "Item 8. Financial Statements") is not None
    assert check_heading("7", "exhibit", "Management Discussion\n\nOVERVIEW") is None


def test_a_heading_after_the_first_500_characters_does_not_count() -> None:
    assert check_heading("7", "edgartools", "x" * 500 + "Item 7.") is not None


# ---------------------------------------------------------------- duplicates


def chunk(ticker: str, year: int, item: str, text: str) -> dict[str, Any]:
    return {"ticker": ticker, "fiscal_year": year, "item": item, "text": text}


def test_the_same_text_twice_in_one_filing_fails() -> None:
    rows = [chunk("C", 2025, "7", "shared text"), chunk("C", 2025, "7A", "shared text")]
    result = check_duplicates(rows)
    assert result.failures == ["C FY2025: 1 chunk texts appear more than once (Items 7, 7A)"]


def test_the_same_text_in_different_years_is_reported_but_allowed() -> None:
    rows = [chunk("AAPL", 2024, "1A", "same risk"), chunk("AAPL", 2025, "1A", "same risk")]
    result = check_duplicates(rows)
    assert result.failures == []
    assert result.across_filings == 1


# ---------------------------------------------------------------- the data report


REPORT = """\
## AAPL

| FY | Accession | Period of report | Item 1 | Item 1A | Item 7 | Item 7A | Item 8 | Chunks |
|---|---|---|---:|---:|---:|---:|---:|---:|
| 2024 | acc-24 | 2024-09-28 | 1 | 2 | 3 | 4 | 5 | 1,204 |
| 2025 | acc-25 | 2025-09-27 | 1 | 2 | 3 | 4 | 5 | 80 |
"""


def test_chunk_counts_are_read_from_the_report() -> None:
    assert parse_report_chunk_counts(REPORT) == {"acc-24": 1204, "acc-25": 80}


def test_a_count_that_differs_from_the_report_fails() -> None:
    counted = {"acc-24": 1204, "acc-25": 79, "acc-26": 3}
    assert check_chunk_counts(counted, {"acc-24": 1204, "acc-25": 80}) == [
        "acc-25: 79 chunks in data/chunks.jsonl, 80 in the data report",
        "acc-26: 3 chunks in data/chunks.jsonl, missing from the data report",
    ]


# ---------------------------------------------------------------- spot check


def write_inputs(root: Path) -> None:
    (root / "data/sections/AAPL/2025").mkdir(parents=True)
    for item in ("1", "1A", "7", "7A", "8"):
        (root / f"data/sections/AAPL/2025/item_{item}.txt").write_text(
            f"Item {item}. Heading\n\n" + "text " * 200, encoding="utf-8"
        )
    manifest = {
        "filings": [
            {
                "ticker": "AAPL",
                "fiscal_year": 2025,
                "accession": "acc-25",
                "primary_document_url": "https://www.sec.gov/primary.htm",
                "extra_documents": [],
            }
        ]
    }
    (root / "data/manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    summary = [
        {
            "ticker": "AAPL",
            "fiscal_year": 2025,
            "accession": "acc-25",
            "items": {
                i: {"chars": 1000, "method": "edgartools"} for i in ("1", "1A", "7", "7A", "8")
            },
        }
    ]
    (root / "data/sections/summary.json").write_text(json.dumps(summary), encoding="utf-8")
    rows = [
        {
            "ticker": "AAPL",
            "fiscal_year": 2025,
            "accession": "acc-25",
            "item": "7",
            "chunk_index": i,
            "text": f"chunk number {i} " + "word " * 80,
        }
        for i in range(40)
    ]
    with (root / "data/chunks.jsonl").open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")


def test_the_spot_check_has_15_chunks_and_5_section_starts_with_links(tmp_path: Path) -> None:
    write_inputs(tmp_path)
    text = spot_check(tmp_path)
    assert text.count("### Chunk ") == 15
    assert text.count("### Section ") == 5
    assert text.count("https://www.sec.gov/primary.htm") == 20


def test_the_spot_check_is_the_same_every_time(tmp_path: Path) -> None:
    write_inputs(tmp_path)
    assert spot_check(tmp_path) == spot_check(tmp_path)


def test_morgan_stanleys_item_7a_title_passes() -> None:
    lines = ["Table of Contents", "", "Quantitative and Qualitative Disclosures about Risk", "Risk"]
    assert check_heading("7A", "edgartools", "\n".join(lines)) is None


# ---------------------------------------------------------------- the source document


def test_a_heading_just_before_the_section_in_the_source_counts() -> None:
    from filingcheck.ingest.verify import heading_before_in_source, plain_text

    source = plain_text(
        "<p>26 MASTERCARD 2025 FORM 10-K</p><p>ITEM 1A. RISK FACTORS</p>"
        "<p>RISK HIGHLIGHTS</p><p>Legal and Regulatory matters could hurt our business.</p>"
    )
    section = "RISK HIGHLIGHTS\n\nLegal and Regulatory matters could hurt our business."
    assert heading_before_in_source("1A", section, source)
    assert not heading_before_in_source("7", section, source)


def test_a_section_that_does_not_occur_in_the_source_is_not_confirmed() -> None:
    from filingcheck.ingest.verify import heading_before_in_source, plain_text

    assert not heading_before_in_source("1A", "Something else entirely", plain_text("<p>x</p>"))


def test_an_exhibit_section_is_confirmed_against_the_exhibit_document() -> None:
    from filingcheck.ingest.verify import heading_before_in_source, heading_source, plain_text

    # IBM: the cut starts at "Management Discussion", which the cleaner then removes as a
    # running page header; the heading is still right before the section in the exhibit.
    exhibit = plain_text(
        "<p>Management Discussion</p><p>International Business Machines Corporation</p>"
        "<p>OVERVIEW</p><p>The financial section of the annual report includes the MD&amp;A.</p>"
    )
    section = "OVERVIEW\n\nThe financial section of the annual report includes the MD&A."
    assert heading_source("exhibit") == "exhibit"
    assert heading_source("edgartools") == heading_source("regex") == "primary"
    assert heading_source("relocated") is None
    assert heading_before_in_source("7", section, exhibit)


# ---------------------------------------------------------------- final data round


def test_item_8_must_hold_the_opinion_and_the_first_note() -> None:
    from filingcheck.ingest.verify import check_item_8

    opinion = (
        "Report of Independent Registered Public Accounting Firm\n"
        "Opinion on the Financial Statements\n"
    )
    note = "Note 1 - Summary of Significant Accounting Policies\n"
    assert check_item_8(opinion + "Statements\n" + note) is None
    assert check_item_8(note + opinion) is None
    assert check_item_8(opinion + "Consolidated Statements of Cash Flows") == "no Note 1"
    assert check_item_8(note) == "no opinion on the financial statements"


def test_report_rows_must_have_as_many_cells_as_their_header() -> None:
    from filingcheck.ingest.verify import check_report_tables

    good = "| FY | Item 8 | Chunks |\n|---|---:|---:|\n| 2025 | 1,000 | 12 |\n"
    bad = "| FY | Item 8 | Chunks |\n|---|---:|---:|\n| 2025 | 1,000 | in 1-7A | 12 |\n"
    assert check_report_tables(good) == []
    assert check_report_tables(bad) == ["| 2025 | 1,000 | in 1-7A | 12 |: 4 cells, header has 3"]


def test_source_lines_keep_one_block_per_line() -> None:
    from filingcheck.ingest.verify import source_lines

    html = (
        "<p>Item 7A.&nbsp;Market Risk</p><div>We are <b>exposed</b>.</div>"
        "<table><tr><td>A</td><td>1</td></tr></table>"
    )
    assert source_lines(html).splitlines() == ["Item 7A. Market Risk", "We are exposed.", "A 1"]


def test_a_section_is_located_in_the_source_by_its_first_and_last_paragraphs() -> None:
    from filingcheck.ingest.verify import locate

    first = "Our business depends on the demand for widgets in our largest markets."
    last = "We expect demand to grow in the coming year as factories reopen."
    source = (
        f"Contents\nItem 1. Business\n{first}\nRevenue 1,234 5,678\n{last}\nItem 1A. Risk Factors\n"
    )
    section = f"{first}\n\n{last}"  # the table was set aside, so it is not in the section
    span = locate(section, source)
    assert span is not None
    assert source[span[0] :].startswith("Our business") and source[: span[1]].endswith("reopen")
    assert locate("A paragraph that the source does not contain anywhere at all.", source) is None


def test_the_next_heading_skips_page_numbers_running_headers_and_table_rows() -> None:
    from filingcheck.ingest.verify import next_heading

    source = (
        "the last words.\n27\nTable of Contents\nTotal revenue 1,234 5,678\n"
        "Item 1A. Risk Factors\nText."
    )
    assert next_heading(source, source.index("\n")) == "Item 1A. Risk Factors"
    assert next_heading("the end.\nOnly a sentence that ends with a period.", 8) is None


def test_size_changes_over_35_percent_are_flagged() -> None:
    from filingcheck.ingest.verify import size_change

    assert size_change(100_000, 64_000) == -0.36
    grown = size_change(10_488, 90_000)
    assert grown is not None and grown > 0.35
    assert size_change(0, 5) is None


def test_the_table_sample_is_fixed_by_the_seed() -> None:
    from filingcheck.ingest.verify import sample_tables

    rows = [{"table_index": i} for i in range(100)]
    first = sample_tables(rows, count=10, seed=2028)
    assert len(first) == 10 and first == sample_tables(rows, count=10, seed=2028)
    assert first != sample_tables(rows, count=10, seed=2027)


def test_a_paragraph_rendered_differently_from_the_source_is_skipped_when_locating() -> None:
    from filingcheck.ingest.verify import locate

    # Mastercard: the parser lays out the index table's cells in another order.
    table = "Page Index to consolidated financial statements as of December and for the years"
    first = "Management is responsible for establishing and maintaining internal control."
    last = "The following table reflects the location of the company's property and equipment."
    index = "Index to consolidated financial statements Page as of December and for the years"
    source = f"{index}\n{first}\n{last}\nItem 9."
    span = locate(f"{table}\n\n{first}\n\n{last}", source)
    assert span is not None and source[span[0] :].startswith("Management is")


def test_the_next_item_heading_skips_running_headers_and_cross_references() -> None:
    from filingcheck.ingest.verify import next_item_heading

    source = (
        "the last words.\nTHE EXAMPLE GROUP, INC. AND SUBSIDIARIES\n"
        "See Item 7 for more.\nItem 1A. Risk Factors\nText."
    )
    assert next_item_heading(source, source.index("\n")) == "Item 1A. Risk Factors"
    assert next_item_heading("the end.\nNo heading here.", 8) is None


def test_a_heading_that_is_also_in_the_contents_list_is_located_in_the_body() -> None:
    from filingcheck.ingest.verify import locate

    heading = "Item 7. Management's Discussion and Analysis of Financial Condition"
    body = "Revenue rose because the company sold more widgets in Europe and in Asia."
    source = f"Contents\n{heading} 25\nItem 8. Financial Statements 40\n{heading}\n{body}\nItem 7A."
    span = locate(f"{heading}\n\n{body}", source)
    assert span is not None and span[0] == source.index(f"{heading}\n{body}")


def test_a_closing_sentence_repeated_earlier_does_not_shorten_the_match() -> None:
    from filingcheck.ingest.verify import locate

    # Nike: the last sentence of Item 7 also ends Item 3.
    heading = "Item 7. Management's Discussion and Analysis of Financial Condition"
    body = "Revenue rose because the company sold more shoes in Europe and in Asia. " * 5
    closing = "Refer to Note 16 in the accompanying Notes to the Financial Statements."
    source = (
        f"{heading} 25\nItem 3. Legal Proceedings\n{closing}\nItem 4.\n"
        f"{heading}\n{body}\n{closing}\nItem 7A."
    )
    span = locate(f"{heading}\n\n{body}\n\n{closing}", source)
    assert span is not None and source[span[1] :].startswith(".\nItem 7A.")  # ends at a letter


# ---------------------------------------------------------------- snapshots


def test_a_section_fingerprint_is_its_size_and_the_hashes_of_its_two_ends() -> None:
    from filingcheck.ingest.verify import section_fingerprint

    text = "A" * 300 + "middle" + "Z" * 300
    print_ = section_fingerprint(text)
    assert print_["chars"] == 606
    assert print_ == section_fingerprint("A" * 300 + "other middle!"[:6] + "Z" * 300)
    assert print_["head"] != section_fingerprint("B" + text[1:])["head"]
    assert print_["tail"] != section_fingerprint(text[:-1] + "Y")["tail"]


def test_every_difference_from_the_section_snapshot_is_listed() -> None:
    from filingcheck.ingest.verify import compare_sections

    same = {"chars": 10, "head": "aa", "tail": "bb"}
    expected = {"AAPL FY2025 Item 7": same, "AAPL FY2025 Item 8": same, "WMT FY2024 Item 8": same}
    current = {
        "AAPL FY2025 Item 7": same,
        "WMT FY2024 Item 8": {"chars": 90, "head": "aa", "tail": "cc"},
        "C FY2025 Item 1-7A": same,
    }
    assert compare_sections(expected, current) == [
        "AAPL FY2025 Item 8: in the snapshot, not saved now",
        "C FY2025 Item 1-7A: saved now, not in the snapshot",
        "WMT FY2024 Item 8: 10 to 90 characters; last 200 characters changed",
    ]


def test_every_difference_from_the_chunk_snapshot_is_listed() -> None:
    from filingcheck.ingest.verify import compare_chunk_counts

    expected = {"AAPL FY2025": 600, "WMT FY2024": 287}
    current = {"AAPL FY2025": 600, "WMT FY2024": 397, "MCO FY2025": 300}
    assert compare_chunk_counts(expected, current) == [
        "MCO FY2025: 300 chunks now, not in the snapshot",
        "WMT FY2024: 287 chunks in the snapshot, 397 now",
    ]
