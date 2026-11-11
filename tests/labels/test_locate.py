"""Where each label's badge goes, and what a calculation was made from."""

from datetime import date
from decimal import Decimal

from filingcheck.labels import SourceCalculation, SourceFact, SourcePassage, Sources, label_numbers

NNBSP = chr(0x202F)  # narrow no-break space, as gpt-oss writes between digit groups
GROUPED = NNBSP.join(["713", "163", "000", "000"])
REVENUE = SourceFact(
    number=1,
    concept="us-gaap:Revenues",
    value=Decimal(713163000000),
    unit="USD",
    period_start=date(2025, 2, 1),
    period_end=date(2026, 1, 31),
    instant=None,
    accession="W26",
)
REVENUE_BEFORE = REVENUE.model_copy(
    update={
        "number": 2,
        "value": Decimal(680985000000),
        "period_start": date(2024, 2, 1),
        "period_end": date(2025, 1, 31),
        "accession": "W25",
    }
)


def ends(text: str, sources: Sources) -> list[str]:
    """The text up to each badge's place, read as the page reads it (UTF-16 offsets)."""
    units = text.encode("utf-16-le")
    out = []
    for label in label_numbers(text, sources):
        assert label.end is not None, label
        out.append(units[: 2 * label.end].decode("utf-16-le"))
    return out


def test_the_badge_goes_right_after_the_figure_before_its_marker() -> None:
    text = "Revenue was $713,163 million【F1】."
    assert ends(text, Sources(facts=[REVENUE])) == ["Revenue was $713,163 million"]


def test_digits_grouped_with_narrow_no_break_spaces_are_found_as_written() -> None:
    text = f"Revenue was {GROUPED} USD [F1]."
    assert ends(text, Sources(facts=[REVENUE])) == [f"Revenue was {GROUPED}"]


def test_bold_markers_stay_outside_the_figure() -> None:
    text = "Revenue was **$713,163 million** [F1]."
    assert ends(text, Sources(facts=[REVENUE])) == ["Revenue was **$713,163 million"]


def test_offsets_count_utf16_units_so_text_after_an_emoji_lines_up() -> None:
    text = "\U0001f4c8 Revenue was $713,163 million [F1]."
    assert ends(text, Sources(facts=[REVENUE])) == ["\U0001f4c8 Revenue was $713,163 million"]


def test_the_same_figure_twice_gets_two_places() -> None:
    text = "It was $713,163 million [F1], yes $713,163 million."
    assert ends(text, Sources(facts=[REVENUE])) == [
        "It was $713,163 million",
        "It was $713,163 million [F1], yes $713,163 million",
    ]


def test_a_year_that_looks_like_the_figure_is_not_taken_for_it() -> None:
    passage = SourcePassage(number=1, text="The company has 2025 stores.")
    text = "In fiscal 2025 it had 2,025 stores [1]."
    assert ends(text, Sources(passages=[passage])) == ["In fiscal 2025 it had 2,025"]


def test_a_calculation_names_the_sources_of_its_inputs() -> None:
    growth = Decimal(713163 - 680985) / Decimal(680985) * 100
    sources = Sources(
        facts=[REVENUE, REVENUE_BEFORE],
        calculations=[
            SourceCalculation(expression="(713163 - 680985) / 680985 * 100", value=growth)
        ],
    )
    (label,) = label_numbers("Revenue grew 4.7% [F1, F2].", sources)
    assert (label.basis, label.inputs) == ("calculation", ["F1", "F2"])


def test_a_calculation_from_a_passage_names_the_passage() -> None:
    passage = SourcePassage(
        number=1, text="The investment was $1.3 billion. The exposure was $0.9 billion."
    )
    sources = Sources(
        passages=[passage],
        calculations=[SourceCalculation(expression="1.3 - 0.9", value=Decimal("0.4"))],
    )
    (label,) = label_numbers("The rest is $0.4 billion [1].", sources)
    assert (label.basis, label.inputs) == ("calculation", ["passage 1"])
