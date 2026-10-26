"""Number tables set aside, honest labels for page-indexed 10-Ks, and IBM's MD&A start."""

from pathlib import Path

from filingcheck.ingest.filings import Manifest
from filingcheck.ingest.sections import (
    MERGED_ITEM,
    ItemText,
    assign_tables,
    build_sections,
    choose_sections,
    iter_table_chunks,
    merge_unseparable,
    remove_markers,
    same_edges,
    split_exhibit_13,
    strip_number_tables,
    table_marker,
    tables_in_span,
)
from tests.ingest.test_sections import FakeClient, filing, fixture, write_document

WORDS = "Management believes the company is well positioned for growth in its main markets. "


def table(rows: list[list[str]]) -> str:
    body = "".join("<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>" for row in rows)
    return f"<table>{body}</table>"


# ---------------------------------------------------------------- number tables


def test_a_table_of_numbers_is_set_aside_with_its_rows_and_position() -> None:
    numbers = table(
        [["", "2025", "2024"], ["Revenue", "$", "416,161"], ["Net income", "(1,234)", "—"]]
    )
    source = f"<p>{WORDS}</p>{numbers}<p>After the table.</p>"
    html, removed = strip_number_tables(source)
    assert len(removed) == 1
    assert removed[0].index == 0
    assert removed[0].position == source.index("<table")
    assert removed[0].text == "2025 | 2024\nRevenue: $416,161\nNet income: (1,234) | —"
    assert "416,161" not in html and table_marker(0) in html
    assert WORDS.strip() in html and "After the table." in html


def test_table_numbers_continue_from_a_given_start() -> None:
    html, removed = strip_number_tables(table([["Revenue", "416,161", "391,035"]]), start=7)
    assert [t.index for t in removed] == [7]
    assert table_marker(7) in html


def test_currency_signs_and_closing_marks_join_their_numbers() -> None:
    rows = table(
        [
            ["iPhone", "$", "209,586", "", "$", "201,183"],
            ["Gross margin", "46.2", "%", "45.6", "%"],
            ["Net loss", "(", "12", ")", "3"],
        ]
    )
    _html, removed = strip_number_tables(rows)
    assert removed[0].text == (
        "iPhone: $209,586 | $201,183\nGross margin: 46.2% | 45.6%\nNet loss: (12) | 3"
    )


def test_a_table_that_is_mostly_words_stays() -> None:
    contents = table([["Item 1.", "Business", "3"], ["Item 1A.", "Risk Factors", "9"]])
    html, removed = strip_number_tables(contents)
    assert removed == []
    assert "Risk Factors" in html


def test_a_table_exactly_half_numbers_stays() -> None:
    _html, removed = strip_number_tables(table([["1. Business", "4-36, 121-127"]]))
    assert removed == []


def test_a_contents_list_whose_numbers_are_page_numbers_stays() -> None:
    # S&P Global's index to its financial statements: note number, title, page.
    contents = table(
        [["1", "Accounting Policies", "81"], ["2", "Acquisitions", "89"], ["", "Page", ""]]
    )
    _html, removed = strip_number_tables(contents)
    assert removed == []


def test_each_table_belongs_to_the_first_section_in_the_given_order() -> None:
    texts = {
        "7": f"Results.\n{table_marker(0)}\nMore.\n{table_marker(1)}",
        "7A": f"Market risk.\n{table_marker(1)}",
        "8": f"Statements.\n{table_marker(2)}",
    }
    assert assign_tables(texts, order=["8", "7A", "7"]) == {0: "7", 1: "7A", 2: "8"}
    assert remove_markers(texts["7"]) == "Results.\n\nMore.\n"


# ---------------------------------------------------------------- the mapping stays put

TABLE_TEXT = "Revenue 416,161 391,035 Net income 99,803 93,736 Cost of sales 223,546 214,137\n"
OPENING = "Item 7. Management's Discussion and Analysis\n\n" + WORDS * 4
CLOSING = WORDS * 4 + "The outlook for next year is described above.\n"


def test_a_section_cut_the_same_way_without_its_tables_keeps_its_edges() -> None:
    original = OPENING + TABLE_TEXT * 5 + CLOSING
    assert same_edges(original, OPENING + CLOSING)


def test_the_edge_probe_does_not_run_across_a_removed_table() -> None:
    heading = "Item 8. Financial Statements\n"
    original = heading + TABLE_TEXT * 5 + CLOSING
    assert same_edges(original, heading + table_marker(0) + "\n" + CLOSING)


def test_a_table_removed_at_the_start_does_not_count_as_a_move() -> None:
    original = "THREE-YEAR SUMMARY\n" + TABLE_TEXT * 5 + OPENING + CLOSING
    assert same_edges(original, OPENING + CLOSING)


def test_a_section_that_starts_somewhere_else_without_its_tables_has_moved() -> None:
    # JPMorgan FY2023: without the tables, Item 7 became the one-paragraph pointer.
    pointer = "Item 7. Management's Discussion. It appears on pages 48-161. " + WORDS
    assert not same_edges(OPENING + WORDS * 200 + CLOSING, pointer)


def test_a_section_that_loses_its_opening_pages_has_moved() -> None:
    # S&P Global: without the tables, Item 8 lost its heading and auditor's report.
    report = "Report of Independent Registered Public Accounting Firm. " + WORDS * 120
    notes = "Notes to the Consolidated Financial Statements\n" + WORDS * 20
    assert not same_edges("Item 8. Financial Statements\n" + report + notes, notes)


def test_sections_come_from_the_tableless_parse_only_where_their_edges_hold() -> None:
    original = {
        "1": ItemText(text=OPENING + TABLE_TEXT * 5 + CLOSING, method="edgartools"),
        "7": ItemText(text=OPENING + WORDS * 200 + CLOSING, method="edgartools"),
        "8": ItemText(text=OPENING + CLOSING, method="regex"),
    }
    stripped = {
        "1": ItemText(text=OPENING + CLOSING, method="edgartools"),
        "7": ItemText(text="Item 7. See pages 48-161. " + WORDS, method="edgartools"),
        "7A": ItemText(text=OPENING + CLOSING, method="edgartools"),
    }
    items, kept = choose_sections(original, stripped)
    assert items["1"] == stripped["1"]
    assert items["7"] == original["7"] and items["8"] == original["8"]
    assert "7A" not in items  # the mapping comes from the full document
    assert kept == ["7", "8"]


# ---------------------------------------------------------------- labels


def test_sections_that_do_not_start_at_their_heading_merge_into_one() -> None:
    items = {
        "1": "OVERVIEW\n\nCitigroup's history dates back to 1812.",
        "1A": "RISK FACTORS\n\nThe following discussion presents the risks.",
        "7": "MANAGEMENT'S DISCUSSION AND ANALYSIS\n\nResults of operations.",
        "7A": "Third Line of Defense: Internal Audit\n\nInternal Audit is independent.",
        "8": "Report of Independent Registered Public Accounting Firm",
    }
    kept, merged = merge_unseparable(items)
    assert merged == ["1", "7A"]
    assert set(kept) == {"1A", "7", "8", MERGED_ITEM}
    assert kept[MERGED_ITEM].startswith("OVERVIEW") and "Third Line of Defense" in kept[MERGED_ITEM]


def test_sections_that_start_at_their_heading_keep_their_labels() -> None:
    items = {
        "1": "Item 1. Business.\n\nOverview",
        "1A": "Item 1A. Risk Factors.\n\nThe following",
        "7": "Financial\n\nTHREE-YEAR SUMMARY OF CONSOLIDATED FINANCIAL HIGHLIGHTS",
        "7A": "Item 7A. Quantitative and Qualitative Disclosures About Market Risk.",
    }
    kept, merged = merge_unseparable(items)
    assert merged == ["7"]
    assert set(kept) == {"1", "1A", "7A", MERGED_ITEM}


def test_nothing_merges_when_every_section_starts_at_its_heading() -> None:
    items = {"1": "Item 1. Business", "7": "Item 7. Management's Discussion"}
    assert merge_unseparable(items) == (items, [])


# ---------------------------------------------------------------- IBM's Exhibit 13


def test_item_7_from_an_exhibit_starts_after_its_contents_list() -> None:
    contents = [
        f"{page} Management Discussion" if page == 6 else f"{page} Note {page}"
        for page in range(4, 20)
    ]
    text = (
        "Table of Contents\n" + "\n".join(contents) + "\n\n"
        "6 Management Discussion\nExample Corp\n\nOVERVIEW\n\n" + WORDS * 6 + "\n\n"
        "Report of Independent Registered Public Accounting Firm\n\nTo the Board of Directors\n\n"
        "Opinion on the Financial Statements. " + WORDS * 3
    )
    parts = split_exhibit_13(text)
    assert parts is not None
    assert parts["7"].startswith("6 Management Discussion\nExample Corp")
    assert "Note 7" not in parts["7"]


def test_a_section_cut_from_the_original_holds_the_tables_between_its_paragraphs() -> None:
    # The section has its tables inline; the marked document has markers in their place.
    first = "Management's discussion begins with the results of operations for the year. "
    last = "The outlook for the coming year depends on interest rates and loan demand. "
    document = (
        f"Item 1. Business\n{table_marker(0)}\n{first}\n{table_marker(1)}\n"
        f"{WORDS}\n{table_marker(2)}\n{last}\n{table_marker(3)}\nItem 8."
    )
    section = f"{first}\n\n{TABLE_TEXT}\n\n{WORDS}\n\n{TABLE_TEXT}\n\n{last}"
    assert tables_in_span(document, section) == [1, 2]
    assert tables_in_span(document, "Text that is not in the document at all, anywhere.") == []


# ---------------------------------------------------------------- tables kept as records


def test_build_sections_saves_each_number_table_with_its_item(tmp_path: Path) -> None:
    segments = table(
        [["", "2025", "2024"], ["Widgets", "$", "3,100", "$", "2,900"], ["Parts", "1,100", "1,050"]]
    )
    html = fixture("tenk_sample.html")
    after = html.index("</p>", html.index("MDA-MARKER")) + len("</p>")
    html = html[:after] + segments + html[after:]
    path = write_document(tmp_path, html)
    manifest = Manifest(filings=[filing(path)])
    _, summary = build_sections(manifest, FakeClient({}), root=tmp_path, min_chars=100)
    item7 = (tmp_path / "data/sections/EXMP/2025/item_7.txt").read_text(encoding="utf-8")
    assert "MDA-MARKER" in item7
    assert "3,100" not in item7 and "[[#" not in item7
    saved = list(iter_table_chunks(manifest, tmp_path))
    assert summary[0].tables_saved == 1
    on_disk = (tmp_path / path).read_bytes().decode("utf-8")  # positions are in this text
    assert [(t.item, t.table_index, t.position) for t in saved] == [
        ("7", 0, on_disk.index(segments))
    ]
    assert saved[0].text == "2025 | 2024\nWidgets: $3,100 | $2,900\nParts: 1,100 | 1,050"
    assert saved[0].source_url == manifest.filings[0].primary_document_url
