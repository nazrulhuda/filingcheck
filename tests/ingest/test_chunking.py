import itertools
from collections import Counter

from filingcheck.ingest.chunking import (
    CHUNK_SIZE,
    OVERLAP,
    Chunk,
    chunk_item,
    clean_item_text,
    junk_reason,
    split_spans,
    strip_repeated_lines,
)

SENTENCE = "Net sales rose because the company sold more widgets in Europe and raised prices. "


def paragraphs(count: int, sentences: int = 4) -> str:
    return "\n\n".join(f"Paragraph {i}. " + SENTENCE * sentences for i in range(count))


def chunks_of(text: str, item: str = "7") -> tuple[list[Chunk], Counter[str]]:
    return chunk_item(
        text, ticker="AAPL", cik="0000320193", fiscal_year=2025, accession="acc-1", item=item
    )


# ---------------------------------------------------------------- splitting


def test_chunks_are_at_most_the_chunk_size_and_cover_the_whole_text() -> None:
    text = paragraphs(20)
    spans = split_spans(text, CHUNK_SIZE, OVERLAP)
    assert all(end - start <= CHUNK_SIZE for start, end in spans)
    assert spans[0][0] == 0
    assert spans[-1][1] == len(text)


def test_consecutive_chunks_overlap_by_at_most_the_overlap() -> None:
    spans = split_spans(paragraphs(20), CHUNK_SIZE, OVERLAP)
    for (_, prev_end), (next_start, _) in itertools.pairwise(spans):
        assert 0 < prev_end - next_start <= OVERLAP


def test_chunks_prefer_to_end_at_a_paragraph_break() -> None:
    text = paragraphs(20)
    spans = split_spans(text, CHUNK_SIZE, OVERLAP)
    ends_at_break = [text[end : end + 2] == "\n\n" for _, end in spans[:-1]]
    assert sum(ends_at_break) >= len(ends_at_break) * 0.8


def test_a_paragraph_longer_than_a_chunk_is_split_between_words() -> None:
    text = SENTENCE * 40  # one long paragraph, no breaks
    for _start, end in split_spans(text, CHUNK_SIZE, OVERLAP)[:-1]:
        assert text[end - 1] in ". " or text[end] == " "


def test_a_chunk_never_spans_two_items() -> None:
    items = {"7": "MDA-ONLY " + paragraphs(6), "8": "STATEMENTS-ONLY " + paragraphs(6)}
    for item, text in items.items():
        chunks, _ = chunks_of(text, item=item)
        for chunk in chunks:
            assert chunk.text == text[chunk.char_start : chunk.char_end]
            assert chunk.item == item
        other = "STATEMENTS-ONLY" if item == "7" else "MDA-ONLY"
        assert not any(other in c.text for c in chunks)


def test_every_chunk_carries_complete_metadata() -> None:
    chunks, _ = chunks_of(paragraphs(10))
    assert [c.chunk_index for c in chunks] == list(range(len(chunks)))
    first = chunks[0].model_dump()
    assert set(first) == {
        "ticker",
        "cik",
        "fiscal_year",
        "accession",
        "item",
        "chunk_index",
        "char_start",
        "char_end",
        "text",
    }
    assert all(value not in (None, "") for value in first.values())


# ---------------------------------------------------------------- junk rules


def test_a_short_chunk_is_junk_and_a_normal_one_is_not() -> None:
    assert junk_reason("Too short to say anything.") == "short"
    assert junk_reason(SENTENCE * 4) is None


def test_table_soup_is_junk_and_prose_with_numbers_is_not() -> None:
    soup = "\n".join(f"$ {i},234 | ({i}.5)% | {i * 7},001 | -- |" for i in range(20))
    assert junk_reason(soup) == "table"
    prose = (
        "Revenue was $416.2 billion in fiscal 2025, up 6% from $391.0 billion, and gross margin "
        "was 46.9%. Services revenue reached $109.2 billion. "
    ) * 3
    assert junk_reason(prose) is None


def test_a_table_of_contents_is_junk_and_prose_that_mentions_items_is_not() -> None:
    toc = "\n".join(
        [
            "Item 1. Business 3",
            "Item 1A. Risk Factors 5",
            "Item 1B. Unresolved Staff Comments 12",
            "Item 2. Properties 13",
            "Item 7. Management's Discussion and Analysis 20",
            "Item 8. Financial Statements and Supplementary Data 35",
        ]
    )
    assert junk_reason(toc * 2) == "toc"
    prose = (
        "As described in Item 7, revenue grew. See Item 1A for the risks, and Item 8 for the "
        "full financial statements, which the auditors reviewed in detail this year. "
    ) * 3
    assert junk_reason(prose) is None


def test_repeated_page_headers_and_footers_are_removed_but_normal_lines_stay() -> None:
    pages = []
    for page in range(1, 8):
        pages.append(f"Apple Inc. | 2025 Form 10-K | {page}")
        pages.append(f"Body text of page {page} about the iPhone business and its sales.")
    text = "\n".join([*pages, "Total net sales rose.", "Total net sales rose."])
    cleaned = strip_repeated_lines(text)
    assert "Form 10-K |" not in cleaned
    assert "Body text of page 3" in cleaned
    assert cleaned.count("Total net sales rose.") == 2  # repeated only twice: kept


def test_clean_item_text_collapses_blank_runs() -> None:
    assert clean_item_text("A\n\n\n\n\nB  \n") == "A\n\nB"


def test_junk_chunks_are_dropped_and_counted() -> None:
    soup = "\n".join(f"$ {i},234 | ({i}.5)% | {i * 7},001 |" for i in range(40))
    text = paragraphs(4) + "\n\n" + soup + "\n\n" + paragraphs(4)
    chunks, dropped = chunks_of(text)
    assert dropped["table"] >= 1
    assert not any("$ 3,234 |" in c.text for c in chunks)
