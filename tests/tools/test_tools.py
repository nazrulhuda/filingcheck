"""The three tools, their JSON schemas and the dispatcher (no network, no database)."""

import json
from datetime import date
from decimal import Decimal
from typing import Any, get_args

import pytest
import yaml

from filingcheck.paths import REPO_ROOT
from filingcheck.tools import TOOL_NAMES, ToolDeps, run_tool, tool_schemas
from filingcheck.tools.inputs import COMPANY_LIST, EXTRA_NAMES, TICKER_NAMES, Ticker
from tests.answer.test_baseline import FakeRetriever, hit
from tests.facts.test_lookup import FakeFacts, duration


def deps(facts: list[Any] | None = None) -> ToolDeps:
    return ToolDeps(retriever=FakeRetriever(), facts=FakeFacts(facts or []))


def call(name: str, arguments: Any, tool_deps: ToolDeps | None = None) -> dict[str, Any]:
    text = run_tool(
        name,
        arguments if isinstance(arguments, str) else json.dumps(arguments),
        tool_deps or deps(),
    )
    assert isinstance(text, str)
    result: dict[str, Any] = json.loads(text)  # always JSON text, errors included
    return result


# ---------------------------------------------------------------- schemas


def test_the_tickers_are_the_25_companies_in_the_data() -> None:
    data = yaml.safe_load((REPO_ROOT / "data" / "companies.yaml").read_text(encoding="utf-8"))
    assert set(get_args(Ticker)) == {c["ticker"] for c in data["companies"]}
    assert len(get_args(Ticker)) == 25


def test_the_official_names_are_the_ones_in_the_data() -> None:
    data = yaml.safe_load((REPO_ROOT / "data" / "companies.yaml").read_text(encoding="utf-8"))
    assert {c["ticker"]: c["name"] for c in data["companies"]} == TICKER_NAMES
    assert list(TICKER_NAMES) == sorted(get_args(Ticker))
    assert EXTRA_NAMES == {"GOOGL": "Google", "META": "Facebook"}


def test_the_company_list_names_every_ticker_with_its_official_name() -> None:
    entries = COMPANY_LIST.split("; ")
    assert len(entries) == 25
    assert "KO (The Coca-Cola Company)" in entries
    assert "AXP (American Express Company)" in entries
    assert "GOOGL (Alphabet Inc., Google)" in entries
    assert "META (Meta Platforms, Inc., Facebook)" in entries
    for ticker, name in TICKER_NAMES.items():
        assert any(e.startswith(f"{ticker} ({name}") for e in entries), ticker


def test_both_tools_ticker_descriptions_carry_the_company_list() -> None:
    schemas = {s["function"]["name"]: s["function"]["parameters"] for s in tool_schemas()}
    for tool in ("search_filings", "get_financial_fact"):
        description = schemas[tool]["properties"]["ticker"]["description"]
        assert COMPANY_LIST in description, tool
        assert len(schemas[tool]["properties"]["ticker"]["enum"]) == 25


def test_each_tool_has_a_schema_for_the_models_tools_list() -> None:
    schemas = tool_schemas()
    assert (
        [s["function"]["name"] for s in schemas]
        == list(TOOL_NAMES)
        == [
            "search_filings",
            "get_financial_fact",
            "calculate",
        ]
    )
    for schema in schemas:
        assert schema["type"] == "function"
        assert len(schema["function"]["description"]) > 40
        parameters = schema["function"]["parameters"]
        assert parameters["type"] == "object"
        text = json.dumps(parameters)
        assert "anyOf" not in text and '"null"' not in text and "$ref" not in text
        assert '"title"' not in text
    fact = schemas[1]["function"]["parameters"]
    assert fact["required"] == ["ticker", "fiscal_year", "metric"]
    assert len(fact["properties"]["ticker"]["enum"]) == 25
    assert "pretax_income" in fact["properties"]["metric"]["enum"]
    search = schemas[0]["function"]["parameters"]
    assert search["required"] == ["query"]
    assert search["properties"]["k"]["maximum"] == 10
    # No Items filter: the model narrowed searches to Items that did not hold the answer.
    assert set(search["properties"]) == {"query", "ticker", "fiscal_year", "k"}


# ---------------------------------------------------------------- the dispatcher


def test_an_unknown_tool_or_bad_json_is_an_error_result() -> None:
    assert "unknown tool" in call("delete_everything", {})["error"]
    assert "not valid JSON" in call("calculate", "{expression: 1}")["error"]
    assert "JSON object" in call("calculate", "[1, 2]")["error"]


def test_a_wrong_argument_is_returned_to_the_model_as_an_error_not_repaired() -> None:
    result = call(
        "get_financial_fact", {"ticker": "Morgan", "fiscal_year": 2025, "metric": "revenue"}
    )
    assert "ticker" in result["error"]
    result = call(
        "get_financial_fact", {"ticker": "WMT", "fiscal_year": "last year", "metric": "revenue"}
    )
    assert "fiscal_year" in result["error"]
    result = call(
        "get_financial_fact",
        {"ticker": "WMT", "fiscal_year": 2025, "metric": "revenue in millions"},
    )
    assert "metric" in result["error"]
    result = call("search_filings", {"query": "risks", "k": 50})
    assert "k" in result["error"]
    result = call(
        "get_financial_fact", {"ticker": "WMT", "fiscal_year": 2025, "metric": "revenue", "x": 1}
    )
    assert "x" in result["error"]


# ---------------------------------------------------------------- search_filings


def test_search_filings_passes_its_filters_and_returns_passages_with_sources() -> None:
    tool_deps = deps()
    result = call(
        "search_filings",
        {"query": "Mexico risks", "ticker": "WMT", "fiscal_year": 2025},
        tool_deps,
    )
    assert tool_deps.retriever.calls == [  # type: ignore[attr-defined]
        {"query": "Mexico risks", "ticker": "WMT", "fiscal_year": 2025, "k": 8}
    ]
    first = result["passages"][0]
    expected = hit(1)
    assert first["chunk_id"] == expected.chunk_id
    assert first["header"].startswith(f"{expected.ticker}, fiscal year {expected.fiscal_year}")
    assert first["text"] == expected.text
    assert first["source_url"] == expected.source_url
    assert len(result["passages"]) == 4


class ItemsRecorder:
    """A retriever that records the Items filter it was given."""

    def __init__(self) -> None:
        self.items: list[Any] = []

    def search(self, query: str, **filters: Any) -> Any:
        from filingcheck.retrieval.models import SearchResult

        self.items.append(filters.get("items"))
        return SearchResult(hits=[], retriever="recorder")


def test_search_filings_searches_every_item_of_the_filing() -> None:
    recorder = ItemsRecorder()
    tool_deps = ToolDeps(retriever=recorder, facts=FakeFacts([]))
    call(
        "search_filings",
        {"query": "currency swaps", "ticker": "WMT", "fiscal_year": 2024},
        tool_deps,
    )
    assert recorder.items == [None]


def test_a_search_that_still_sends_items_is_an_error_for_the_model() -> None:
    result = call("search_filings", {"query": "currency swaps", "items": ["8"]})
    assert "items" in result["error"]


def test_search_filings_k_defaults_to_8_and_accepts_1_to_10() -> None:
    tool_deps = deps()
    call("search_filings", {"query": "Mexico risks", "k": 2}, tool_deps)
    assert tool_deps.retriever.calls[-1]["k"] == 2  # type: ignore[attr-defined]
    assert "error" in call("search_filings", {"query": "Mexico risks", "k": 0})


# ---------------------------------------------------------------- get_financial_fact


def test_a_company_outside_the_25_is_refused_before_any_lookup() -> None:
    result = call(
        "get_financial_fact",
        {"ticker": "EXMP", "fiscal_year": 2025, "metric": "revenue"},
        deps([duration("us-gaap:Revenues", "416161000000")]),
    )
    assert "ticker" in result["error"]


def test_get_financial_fact_returns_the_fact_with_its_exact_value_as_text() -> None:
    source = FakeFacts([duration("us-gaap:Revenues", "416161000000")])
    source._filing = source._filing.__class__(
        ticker="AAPL",
        fiscal_year=2025,
        accession="0000320193-25-000079",
        period_of_report=date(2025, 12, 31),
        source_url="https://www.sec.gov/aapl.htm",
        revenue_rule="standard",
    )
    result = call(
        "get_financial_fact",
        {"ticker": "AAPL", "fiscal_year": 2025, "metric": "revenue"},
        ToolDeps(retriever=FakeRetriever(), facts=source),
    )
    assert result["status"] == "found"
    fact = result["fact"]
    assert fact["value"] == "416161000000" and Decimal(fact["value"]) == 416161000000
    assert (fact["unit"], fact["period_end"], fact["concept"]) == (
        "USD",
        "2025-12-31",
        "us-gaap:Revenues",
    )
    assert fact["line_label"] == "Revenues"
    assert fact["source_url"] == "https://www.sec.gov/aapl.htm"


def test_get_financial_fact_says_why_a_fact_is_unavailable() -> None:
    source = FakeFacts([])
    source._filing = source._filing.__class__(
        ticker="AAPL",
        fiscal_year=2025,
        accession="a",
        period_of_report=date(2025, 12, 31),
        source_url="u",
        revenue_rule="standard",
    )
    tool_deps = ToolDeps(retriever=FakeRetriever(), facts=source)
    no_year = call(
        "get_financial_fact",
        {"ticker": "AAPL", "fiscal_year": 2019, "metric": "revenue"},
        tool_deps,
    )
    assert no_year["status"] == "unavailable" and no_year["reason"] == "no_filing"
    assert "2019" in no_year["message"]
    missing = call(
        "get_financial_fact",
        {"ticker": "AAPL", "fiscal_year": 2025, "metric": "total_liabilities"},
        tool_deps,
    )
    assert missing["status"] == "unavailable" and missing["reason"] == "not_reported"


# ---------------------------------------------------------------- calculate


def test_calculate_returns_the_exact_result_or_an_error() -> None:
    assert call("calculate", {"expression": "(713163 - 680985) / 680985 * 100"})[
        "value"
    ].startswith("4.7252")
    assert "division by zero" in call("calculate", {"expression": "1 / 0"})["error"]
    assert "error" in call("calculate", {"expression": "import os"})


# ---------------------------------------------------------------- argument types


def test_a_whole_number_written_as_text_is_the_same_argument() -> None:
    from tests.agent.test_agent import apple_deps

    fact = {"ticker": "AAPL", "metric": "revenue"}
    as_text = call("get_financial_fact", {**fact, "fiscal_year": "2025"}, apple_deps())
    as_number = call("get_financial_fact", {**fact, "fiscal_year": 2025}, apple_deps())
    assert as_text == as_number and as_text["status"] == "found"
    tool_deps = deps()
    call("search_filings", {"query": "risks", "fiscal_year": "2025", "k": "3"}, tool_deps)
    retriever = tool_deps.retriever
    assert isinstance(retriever, FakeRetriever)
    assert (retriever.calls[0]["fiscal_year"], retriever.calls[0]["k"]) == (2025, 3)


def test_every_other_non_integer_number_is_still_rejected() -> None:
    full_width = "".join(chr(0xFF10 + int(d)) for d in "2025")  # 2025 in full-width digits
    for year in (2025.0, True, "2025.0", "FY2025", " 2025", full_width):
        result = call(
            "get_financial_fact", {"ticker": "WMT", "fiscal_year": year, "metric": "revenue"}
        )
        assert "fiscal_year" in result["error"], year
    for k in (5.0, True, "5.0"):
        assert "k" in call("search_filings", {"query": "risks", "k": k})["error"], k


def test_the_schemas_still_say_integer() -> None:
    schemas = {s["function"]["name"]: s["function"]["parameters"] for s in tool_schemas()}
    assert schemas["get_financial_fact"]["properties"]["fiscal_year"]["type"] == "integer"
    assert schemas["search_filings"]["properties"]["fiscal_year"]["type"] == "integer"
    assert schemas["search_filings"]["properties"]["k"]["type"] == "integer"


# ---------------------------------------------------------------- failures inside a tool


class BrokenRetriever(FakeRetriever):
    def search(self, query: str, **kwargs: Any) -> Any:
        raise RuntimeError("server closed the connection unexpectedly")


def test_a_failure_inside_a_tool_is_an_error_result_not_an_exception() -> None:
    broken = ToolDeps(retriever=BrokenRetriever(), facts=FakeFacts([]))
    result = call("search_filings", {"query": "risks"}, broken)
    assert "search_filings failed" in result["error"]
    # The exception's own text (it may name a host or a table) is not passed to the model.
    assert "server closed" not in result["error"]


def test_two_values_for_one_fact_are_unavailable_with_the_reason() -> None:
    from tests.agent.test_agent import APPLE, YEAR

    tag = "us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax"
    two = [duration(tag, "1", *YEAR), duration(tag, "2", *YEAR)]
    result = call(
        "get_financial_fact",
        {"ticker": "AAPL", "fiscal_year": 2025, "metric": "revenue"},
        ToolDeps(retriever=FakeRetriever(), facts=FakeFacts(two, filing=APPLE)),
    )
    assert (result["status"], result["reason"]) == ("unavailable", "conflicting_values")
    assert "1" in result["message"] and "2" in result["message"]


# ---------------------------------------------------------------- validate, then run


def test_validating_then_running_gives_exactly_what_run_tool_gives() -> None:
    from filingcheck.tools import run_validated, validate_call
    from tests.agent.test_agent import apple_deps

    tool_deps = apple_deps()
    for name, arguments in (
        ("get_financial_fact", {"ticker": "AAPL", "fiscal_year": 2025, "metric": "revenue"}),
        (
            "get_financial_fact",
            {"ticker": "AAPL", "fiscal_year": 2025, "metric": "operating_income"},
        ),
        ("search_filings", {"query": "risks in Mexico", "k": 2}),
        ("calculate", {"expression": "(2 - 1) / 4 * 100"}),
        ("calculate", {"expression": "1 / 0"}),
    ):
        text = json.dumps(arguments)
        tool, parsed = validate_call(name, text)
        assert tool.name == name
        assert run_validated(tool, parsed, tool_deps) == run_tool(name, text, tool_deps)


def test_an_invalid_call_raises_the_same_error_text_run_tool_returns() -> None:
    from filingcheck.tools import ToolInputError, validate_call

    morgan = json.dumps({"ticker": "Morgan", "fiscal_year": 2025, "metric": "revenue"})
    for name, text in (
        ("delete_everything", "{}"),
        ("calculate", "{expression: 1}"),
        ("calculate", "[1, 2]"),
        ("get_financial_fact", morgan),
    ):
        with pytest.raises(ToolInputError) as caught:
            validate_call(name, text)
        assert caught.value.result == run_tool(name, text, deps())
        assert "error" in json.loads(caught.value.result)
