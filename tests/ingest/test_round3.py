"""Number tables removed before parsing, honest labels for page-indexed 10-Ks, IBM's MD&A start."""

from filingcheck.ingest.sections import (
    MERGED_ITEM,
    merge_unseparable,
    split_exhibit_13,
    strip_number_tables,
)

WORDS = "Management believes the company is well positioned for growth in its main markets. "


def table(rows: list[list[str]]) -> str:
    body = "".join("<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>" for row in rows)
    return f"<table>{body}</table>"


# ---------------------------------------------------------------- number tables


def test_a_table_of_numbers_is_removed_and_counted() -> None:
    numbers = table(
        [["", "2025", "2024"], ["Revenue", "$", "416,161"], ["Net income", "(1,234)", "—"]]
    )
    html, dropped = strip_number_tables(f"<p>{WORDS}</p>{numbers}<p>After the table.</p>")
    assert dropped == 1
    assert "416,161" not in html
    assert WORDS.strip() in html and "After the table." in html


def test_a_table_that_is_mostly_words_stays() -> None:
    contents = table([["Item 1.", "Business", "3"], ["Item 1A.", "Risk Factors", "9"]])
    html, dropped = strip_number_tables(contents)
    assert dropped == 0
    assert "Risk Factors" in html


def test_a_table_exactly_half_numbers_stays() -> None:
    _html, dropped = strip_number_tables(table([["1. Business", "4-36, 121-127"]]))
    assert dropped == 0


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
