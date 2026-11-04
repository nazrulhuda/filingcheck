"""The three tools, their JSON schemas and the dispatcher (no network, no database)."""

import json
from datetime import date
from decimal import Decimal
from typing import Any, get_args

import yaml

from filingcheck.paths import REPO_ROOT
from filingcheck.tools import TOOL_NAMES, ToolDeps, run_tool, tool_schemas
from filingcheck.tools.inputs import ITEMS, Ticker
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
    assert set(search["properties"]["items"]["items"]["enum"]) == set(ITEMS)


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
        {"query": "Mexico risks", "ticker": "WMT", "fiscal_year": 2025, "items": ["1A"]},
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
