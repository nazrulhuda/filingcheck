"""Labeling the stored answers: each stored row's sources, rebuilt from what the row recorded."""

from datetime import date
from decimal import Decimal
from typing import Any

from filingcheck.facts.lookup import FactResult
from filingcheck.labels.stored import is_agent_answer, page_example_rows, sources_for_row

FACT = {
    "ticker": "WMT",
    "fiscal_year": 2025,
    "metric": "revenue",
    "value": "680985000000",
    "unit": "USD",
    "period_start": "2024-02-01",
    "period_end": "2025-01-31",
    "instant": None,
    "concept": "us-gaap:Revenues",
    "accession": "0000104169-25-000021",
    "source_url": "u",
    "decimals": "-6",
    "line_label": "Total revenues",
    "note": None,
}
TEXTS = {101: "Passage one has $0.7 billion.", 102: "Passage two."}


def texts(ids: list[int]) -> dict[int, str]:
    return {i: TEXTS[i] for i in ids}


def no_lookup(ticker: str, fiscal_year: int, metric: str) -> FactResult | None:
    raise AssertionError("the row's recorded facts should be used")


def test_recorded_facts_and_citations_become_the_sources() -> None:
    row = {
        "mode": "agent",
        "answer": "Revenue was $680,985 million [F1], swaps $0.7 billion [2].",
        "facts_used": [FACT],
        "citations": [{"number": 2, "chunk_id": 101}],
        "tool_calls": [],
    }
    sources, facts_from, notes = sources_for_row(
        row, passage_text=texts, lookup_fact=no_lookup, filing_facts=None
    )
    assert facts_from == "recorded" and notes == []
    (fact,) = sources.facts
    assert (fact.number, fact.value, fact.period_end) == (
        1,
        Decimal(680985000000),
        date(2025, 1, 31),
    )
    assert [(p.number, p.text) for p in sources.passages] == [(2, TEXTS[101])]


def test_citations_without_numbers_take_them_from_the_markers_in_order() -> None:
    row = {
        "mode": "agent",
        "answer": "A [3] and B [1].",
        "facts_used": [],
        "citations": [{"chunk_id": 101}, {"chunk_id": 102}],
        "tool_calls": [],
    }
    sources, _, _ = sources_for_row(
        row, passage_text=texts, lookup_fact=no_lookup, filing_facts=None
    )
    assert [(p.number, p.text) for p in sources.passages] == [(3, TEXTS[101]), (1, TEXTS[102])]


def test_facts_not_recorded_are_looked_up_again_from_the_recorded_arguments() -> None:
    calls: list[tuple[str, int, str]] = []

    def lookup(ticker: str, fiscal_year: int, metric: str) -> FactResult | None:
        calls.append((ticker, fiscal_year, metric))
        return FactResult.model_validate(FACT) if metric == "revenue" else None

    row = {
        "mode": "agent",
        "answer": "Revenue was $680,985 million [F1].",
        "facts_used": None,
        "tool_calls": [
            {
                "name": "get_financial_fact",
                "arguments": {"ticker": "WMT", "fiscal_year": 2025, "metric": "revenue"},
                "status": "ok",
            },
            {
                "name": "get_financial_fact",
                "arguments": {"ticker": "WMT", "fiscal_year": 2025, "metric": "ebitda"},
                "status": "error",
            },
            {
                "name": "get_financial_fact",
                "arguments": {"ticker": "WMT", "fiscal_year": 2025, "metric": "net_income"},
                "status": "ok",
            },
            # The same fact again keeps its number, as in the run.
            {
                "name": "get_financial_fact",
                "arguments": {"ticker": "WMT", "fiscal_year": 2025, "metric": "revenue"},
                "status": "ok",
            },
        ],
    }
    sources, facts_from, _ = sources_for_row(
        row, passage_text=texts, lookup_fact=lookup, filing_facts=None
    )
    assert facts_from == "looked up again"
    assert calls == [
        ("WMT", 2025, "revenue"),
        ("WMT", 2025, "net_income"),
        ("WMT", 2025, "revenue"),
    ]
    assert [(f.number, f.concept) for f in sources.facts] == [(1, "us-gaap:Revenues")]


def test_probe_rows_number_their_cited_chunks_from_the_markers() -> None:
    row: dict[str, Any] = {
        "mode": "agent",
        "answer": "X [2]. Y [1].",
        "cited_chunks": [101, 102],
        "tool_calls": [],
    }
    sources, facts_from, notes = sources_for_row(
        row, passage_text=texts, lookup_fact=no_lookup, filing_facts=None
    )
    assert facts_from == "none" and notes == []
    assert [(p.number, p.text) for p in sources.passages] == [(2, TEXTS[101]), (1, TEXTS[102])]


def test_a_marker_whose_passage_was_not_recorded_is_noted_and_has_no_source() -> None:
    row = {"mode": "agent", "answer": "X [1].", "cited_chunks": [], "tool_calls": []}
    sources, _, notes = sources_for_row(
        row, passage_text=texts, lookup_fact=no_lookup, filing_facts=None
    )
    assert sources.passages == [] and notes == ["the cited passages were not recorded"]


def test_a_calculation_is_recomputed_with_the_calculate_tool() -> None:
    row = {
        "mode": "agent",
        "answer": "It is 619,003 [F1].",
        "facts_used": [],
        "tool_calls": [
            {
                "name": "calculate",
                "arguments": {"expression": "619003000000/1000000"},
                "status": "ok",
            }
        ],
    }
    sources, _, _ = sources_for_row(
        row, passage_text=texts, lookup_fact=no_lookup, filing_facts=None
    )
    (calculation,) = sources.calculations
    assert (calculation.expression, calculation.value) == ("619003000000/1000000", Decimal(619003))


def test_only_agent_rows_with_an_answer_are_labeled() -> None:
    assert is_agent_answer({"mode": "agent", "answer": "Yes [1]."})
    assert not is_agent_answer({"mode": "baseline", "answer": "Yes [1]."})
    assert not is_agent_answer({"mode": "agent", "answer": None})
    assert not is_agent_answer({"mode": "first model call only, reasoning returned", "answer": ""})


def test_the_page_examples_become_rows_with_their_stored_answers() -> None:
    examples = [
        {
            "question": "Q?",
            "ticker": "NKE",
            "fiscal_year": None,
            "company_name": "NIKE, Inc.",
            "answer": {
                "mode": "agent",
                "text": "T [F1].",
                "facts_used": [FACT],
                "citations": [],
                "tool_calls": [],
            },
        }
    ]
    (row,) = page_example_rows(examples)
    assert (row["id"], row["repeat"], row["answer"], row["facts_used"]) == (
        "page-1",
        1,
        "T [F1].",
        [FACT],
    )
    assert is_agent_answer(row)
