"""Item 8 must hold the auditor's opinion and the notes; every report table has the same columns."""

from filingcheck.ingest.report import build_report
from filingcheck.ingest.sections import (
    ItemText,
    complete_item_8,
    item_8_is_complete,
    relocate_financial_statements,
)
from tests.ingest.test_report import CHUNKS, COMPANIES, MANIFEST, SUMMARIES

REPORT = (
    "Report of Independent Registered Public Accounting Firm\n\n"
    "To the Shareholders and Board of Directors of Example Corp\n\n"
    "Opinion on the Financial Statements\n\n"
    "We have audited the accompanying consolidated balance sheets of Example Corp.\n\n"
)
STATEMENTS = "Consolidated Statements of Income\n\nConsolidated Balance Sheets\n\n"
NOTES = (
    "Notes to Consolidated Financial Statements\n\n"
    "Note 1. Summary of Significant Accounting Policies\n\n"
    "The consolidated financial statements include the accounts of Example Corp.\n\n"
)
ITEM_9 = "Item 9. Changes in and Disagreements With Accountants\n\nNone.\n\n"
CONTENTS = "Item 8. Financial Statements\n\nNotes to Consolidated Financial Statements 59\n\n"


def test_an_item_8_needs_the_opinion_and_the_first_note() -> None:
    assert item_8_is_complete(REPORT + STATEMENTS + NOTES)
    assert item_8_is_complete(STATEMENTS + NOTES + REPORT)  # Apple: the report comes last
    assert not item_8_is_complete(REPORT + STATEMENTS)  # Walmart FY2024: no notes
    assert not item_8_is_complete(STATEMENTS + NOTES)  # no auditor's opinion


def test_a_note_on_basis_of_presentation_or_numbered_policies_counts_as_the_first_note() -> None:
    assert item_8_is_complete(REPORT + "Note 1 - Basis of presentation\n\nText.")
    assert item_8_is_complete(REPORT + "1. Accounting Policies\n\nNature of operations.")
    assert item_8_is_complete(REPORT + "NOTE 1: ORGANIZATION AND SIGNIFICANT ACCOUNTING POLICIES")


def test_relocated_statements_stop_at_the_next_item_9_heading() -> None:
    text = CONTENTS + REPORT + STATEMENTS + NOTES + ITEM_9 + "Item 15. Exhibits\n\nSignatures\n"
    moved = relocate_financial_statements(text)
    assert moved is not None
    assert moved.startswith("Report of Independent") and moved.endswith("Example Corp.")


def test_an_item_8_without_its_notes_is_cut_again_from_the_auditors_report() -> None:
    # Walmart FY2024: the parser's Item 8 stops after the list of statements.
    document = CONTENTS + REPORT + STATEMENTS + NOTES + ITEM_9
    truncated = ItemText(text=CONTENTS + REPORT + STATEMENTS, method="edgartools")
    fixed, gap = complete_item_8(truncated, document)
    assert gap is None
    assert fixed.method == "relocated" and "Note 1." in fixed.text and "Item 9" not in fixed.text


def test_a_complete_item_8_is_kept_as_it_is() -> None:
    found = ItemText(text=REPORT + STATEMENTS + NOTES, method="edgartools")
    assert complete_item_8(found, "unused") == (found, None)


def test_an_item_8_that_cannot_be_completed_is_kept_and_reported() -> None:
    truncated = ItemText(text=REPORT + STATEMENTS, method="edgartools")
    fixed, gap = complete_item_8(truncated, CONTENTS + REPORT + STATEMENTS + ITEM_9)
    assert fixed == truncated
    assert gap == "Item 8 lacks the auditor's opinion on the financial statements or the notes"


def test_every_company_table_has_the_merged_column_so_chunks_is_always_last() -> None:
    text = build_report(COMPANIES, MANIFEST, SUMMARIES, CHUNKS, {})
    tables = [line for line in text.splitlines() if line.startswith("| FY |")]
    assert tables
    for header in tables:
        cells = [cell.strip() for cell in header.strip("|").split("|")]
        assert cells[-2].startswith("Items 1-7A") and cells[-1] == "Chunks"
    rows = [line for line in text.splitlines() if line.startswith("| 20")]
    assert rows and all(row.count("|") == tables[0].count("|") for row in rows)
