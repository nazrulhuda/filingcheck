"""Page furniture removed and sentences split by a page break joined, in clean_item_text."""

from filingcheck.ingest.chunking import clean_item_text

FIRST = "Deferred income taxes reflect the effect of"
SECOND = "temporary differences between the book and tax bases of assets and liabilities."
SENTENCE = f"{FIRST} {SECOND}"


# ---------------------------------------------------------------- the spec's positive cases


def test_a_lone_page_number_line_goes() -> None:
    assert clean_item_text("Revenue rose.\n\n302\n\nCosts fell.") == "Revenue rose.\n\nCosts fell."


def test_a_leading_table_of_contents_line_goes_and_the_heading_stays() -> None:
    text = (
        "Table of Contents\n\nITEM 7A. QUANTITATIVE AND QUALITATIVE DISCLOSURES\n\nRefer to MD&A."
    )
    assert (
        clean_item_text(text)
        == "ITEM 7A. QUANTITATIVE AND QUALITATIVE DISCLOSURES\n\nRefer to MD&A."
    )


def test_a_leading_table_of_contents_line_inside_the_first_paragraph_goes() -> None:
    text = "Table of Contents\nItem 8. Financial Statements\n\nThe statements follow."
    assert clean_item_text(text) == "Item 8. Financial Statements\n\nThe statements follow."


def test_a_sentence_split_by_a_page_break_is_joined() -> None:
    assert clean_item_text(f"{FIRST}\n\n{SECOND}") == SENTENCE


def test_a_page_number_between_the_halves_goes_before_the_join() -> None:
    assert clean_item_text(f"{FIRST}\n\n65\n\n{SECOND}") == SENTENCE


def test_a_sentence_split_over_three_paragraphs_is_joined_once() -> None:
    text = (
        "Revenue in the year rose because the\n\ncompany sold more widgets in\n\nEurope and Asia."
    )
    assert clean_item_text(text) == (
        "Revenue in the year rose because the company sold more widgets in Europe and Asia."
    )


# ---------------------------------------------------------------- the spec's negative cases


def test_a_year_inside_a_sentence_stays() -> None:
    text = "Net sales rose in fiscal\n2023 compared with 2022.\n\nCosts fell."
    assert clean_item_text(text) == text


def test_a_percent_line_stays() -> None:
    assert clean_item_text("Margin was\n\n65%\n\nlast year.") == "Margin was\n\n65%\n\nlast year."


def test_a_numbered_list_item_stays() -> None:
    text = "The steps are:\n\n3.\n\nreview the results."
    assert clean_item_text(text) == text


def test_a_heading_followed_by_a_lowercase_line_stays() -> None:
    text = "Interest Rate Risk\n\nour exposure comes from floating-rate debt."
    assert clean_item_text(text) == text


def test_a_bullet_list_stays() -> None:
    text = "Risks include\n\n• changes in interest rates\n\n• changes in exchange rates"
    assert clean_item_text(text) == text


def test_a_paragraph_ending_a_sentence_is_not_joined() -> None:
    for end in (".", "?", "!", ":", ";", ".)", ".”", ";]"):
        text = f"The company sold widgets{end}\n\nthe next paragraph starts in lowercase."
        assert clean_item_text(text) == text, end


def test_a_paragraph_followed_by_an_uppercase_start_is_not_joined() -> None:
    text = f"{FIRST}\n\nTemporary differences arise between book and tax bases."
    assert clean_item_text(text) == text


# ---------------------------------------------------------------- the three guards


def test_a_short_product_heading_is_not_joined_to_its_text() -> None:
    text = (
        "iPhone\n\niPhone® is the Company's line of smartphones based on its iOS operating system."
    )
    assert clean_item_text(text) == text


def test_a_wrapped_lowercase_line_of_four_or_more_words_is_joined() -> None:
    text = "consumer mortgages and unsecured\n\nlending products, such as small business loans."
    assert clean_item_text(text) == (
        "consumer mortgages and unsecured lending products, such as small business loans."
    )


def test_a_page_footer_is_not_joined_to_the_next_page() -> None:
    text = "2023 Annual Report  13\n\ncountries experiencing high inflation rates."
    assert clean_item_text(text) == text


def test_a_line_ending_in_a_dollar_amount_is_still_joined() -> None:
    text = (
        "2025 and remitted the total proceeds of approximately $262\n\nmillion from its operations."
    )
    assert clean_item_text(text) == (
        "2025 and remitted the total proceeds of approximately $262 million from its operations."
    )


def test_a_short_footnote_is_not_joined_to_the_next_one() -> None:
    assert clean_item_text("(3) As of end of period\n\nnm - not meaningful") == (
        "(3) As of end of period\n\nnm - not meaningful"
    )
    assert clean_item_text("________\n\nnm = not meaningful") == "________\n\nnm = not meaningful"


def test_a_long_footnote_split_by_a_page_break_is_still_joined() -> None:
    text = (
        "(1) Reflects the divestitures of its Asia Consumer businesses and (ii) the\n\n"
        "planned divestiture of Mexico consumer banking."
    )
    assert clean_item_text(text) == text.replace("\n\n", " ")


# ---------------------------------------------------------------- "Table of Contents" anywhere


def test_a_table_of_contents_paragraph_inside_a_section_goes_and_the_sentence_joins() -> None:
    text = f"Earlier text.\n\n{FIRST}\n\n42\n\nTable of Contents\n\n{SECOND}\n\nLater text."
    assert clean_item_text(text) == f"Earlier text.\n\n{SENTENCE}\n\nLater text."


def test_table_of_contents_with_a_colon_or_period_and_any_case_goes() -> None:
    for line in ("TABLE OF CONTENTS", "Table of contents:", "table of contents."):
        assert clean_item_text(f"Revenue rose.\n\n{line}\n\nCosts fell.") == (
            "Revenue rose.\n\nCosts fell."
        ), line


def test_a_sentence_mentioning_the_table_of_contents_stays() -> None:
    text = "See the Table of Contents for page numbers.\n\nCosts fell."
    assert clean_item_text(text) == text
