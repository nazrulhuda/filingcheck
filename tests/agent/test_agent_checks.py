"""The check layer inside the agent: rejects and repairs reach the model as tool results, the
override log reaches the answer, and `checks=False` is the Week 3 agent, shown on the Day 18
scripted scenarios run in both modes."""

import json
from typing import Any

import pytest

from filingcheck.agent import AgentAnswer, run_agent, run_agent_with_fallbacks
from filingcheck.answer.run import format_agent_answer
from filingcheck.ingest.companies import load_companies, load_not_covered
from filingcheck.ingest.filings import load_manifest
from filingcheck.llm import FakeChat, scripted_tool_calls
from filingcheck.paths import DATA_DIR
from filingcheck.tools import ToolDeps
from tests.agent.test_agent import YEAR, apple_deps, fact_call, tool_messages
from tests.facts.test_lookup import duration

COMPANIES = load_companies(DATA_DIR / "companies.yaml")
NOT_COVERED = load_not_covered(DATA_DIR / "companies.yaml")
MANIFEST = load_manifest(DATA_DIR / "manifest.json")
APPLE_Q = "What were Apple's total net sales in fiscal 2025?"


def checked_deps(facts: Any = None) -> ToolDeps:
    """The Apple fake facts plus the reference data the checks read."""
    plain = apple_deps(facts)
    return ToolDeps(
        retriever=plain.retriever,
        facts=plain.facts,
        companies=COMPANIES,
        not_covered=NOT_COVERED,
        manifest=MANIFEST,
    )


# ---------------------------------------------------------------- the three outcomes in the loop


def test_a_reject_is_the_tools_result_with_the_reason_and_the_options() -> None:
    chat = FakeChat(
        [
            fact_call(ticker="MS", fiscal_year=2025, metric="revenue"),
            "Do you mean JPMorgan Chase or Morgan Stanley?",
        ]
    )
    answer = run_agent(
        "How much net revenue did Morgan report last year?",
        model=chat,
        deps=checked_deps(),
        checks=True,
    )
    assert answer.checks is True
    result = json.loads(tool_messages(chat, 1)[0]["content"])
    assert set(result) == {"error", "options"}  # the shape of a validation error, plus options
    assert result["options"] == ["JPM", "MS"] and "ambiguous" in result["error"]
    [record] = answer.tool_calls
    assert record.status == "error" and record.result_summary.startswith("error: ")
    assert answer.facts_used == [] and answer.fact_citations == []
    [override] = [o for o in answer.overrides if o.check == "company"]
    assert (override.check, override.outcome, override.sent, override.used) == (
        "company",
        "reject",
        "MS",
        None,
    )


def test_a_repair_runs_the_tool_with_the_repaired_arguments_and_tells_the_model() -> None:
    chat = FakeChat(
        [
            fact_call(ticker="MSFT", fiscal_year=2025, metric="revenue"),
            "Apple's total net sales in fiscal 2025 were $416,161 million [F1].",
        ]
    )
    answer = run_agent(APPLE_Q, model=chat, deps=checked_deps(), checks=True)
    result = json.loads(tool_messages(chat, 1)[0]["content"])
    assert result["status"] == "found" and result["fact"]["ticker"] == "AAPL"
    [checked] = result["checked"]
    assert (checked["check"], checked["sent"], checked["used"]) == ("company", "MSFT", "AAPL")
    [record] = answer.tool_calls
    assert record.status == "ok" and record.arguments["ticker"] == "AAPL"  # as run
    assert record.sent_arguments == {"ticker": "MSFT", "fiscal_year": 2025, "metric": "revenue"}
    assert answer.facts_used[0].value == 416161000000
    [override] = [o for o in answer.overrides if o.check == "company"]
    assert override.outcome == "repair" and override.used == "AAPL"


def test_a_pass_leaves_the_tool_result_as_it_is_and_is_still_logged() -> None:
    chat = FakeChat(
        [
            fact_call(ticker="AAPL", fiscal_year=2025, metric="revenue"),
            "Apple's total net sales in fiscal 2025 were $416,161 million [F1].",
        ]
    )
    on = run_agent(APPLE_Q, model=chat, deps=checked_deps(), checks=True)
    result = json.loads(tool_messages(chat, 1)[0]["content"])
    assert "checked" not in result and "options" not in result
    [override] = [o for o in on.overrides if o.check == "company"]
    assert override.outcome == "pass" and override.sent == override.used == "AAPL"


def test_search_filings_goes_through_the_fiscal_year_check_and_calculate_does_not() -> None:
    """A text question with no year: the search is repaired to the latest pinned year."""
    chat = FakeChat(
        [
            scripted_tool_calls(
                (
                    "search_filings",
                    {"query": "risks in Mexico", "ticker": "WMT", "fiscal_year": 2023},
                )
            ),
            scripted_tool_calls(("calculate", {"expression": "1 + 1"})),
            "Risks [1].",
        ]
    )
    answer = run_agent(
        "What are Walmart's main risks in Mexico?", model=chat, deps=checked_deps(), checks=True
    )
    assert [(o.check, o.outcome, o.tool) for o in answer.overrides] == [
        ("fiscal_year", "repair", "search_filings")
    ]
    assert answer.tool_calls[0].arguments["fiscal_year"] == 2026  # Walmart's latest pinned year
    assert [r.status for r in answer.tool_calls] == ["ok", "ok"]
    # The model sees what changed, as for the fact tool.
    result = json.loads(tool_messages(chat, 1)[0]["content"])
    assert result["checked"][0]["used"] == 2026


def test_with_the_checks_off_search_filings_runs_as_sent() -> None:
    chat = FakeChat(
        [
            scripted_tool_calls(
                (
                    "search_filings",
                    {"query": "risks in Mexico", "ticker": "WMT", "fiscal_year": 2023},
                )
            ),
            "Risks [1].",
        ]
    )
    answer = run_agent(
        "What are Walmart's main risks in Mexico?", model=chat, deps=checked_deps(), checks=False
    )
    assert answer.overrides == [] and answer.tool_calls[0].arguments["fiscal_year"] == 2023


def test_a_validation_error_comes_before_the_checks_and_is_unchanged() -> None:
    chat = FakeChat(
        [
            fact_call(ticker="Apple", fiscal_year=2025, metric="revenue"),
            fact_call(ticker="AAPL", fiscal_year=2025, metric="revenue"),
            "Apple's total net sales in fiscal 2025 were $416,161 million [F1].",
        ]
    )
    answer = run_agent(APPLE_Q, model=chat, deps=checked_deps(), checks=True)
    error = json.loads(tool_messages(chat, 1)[0]["content"])
    assert set(error) == {"error"} and "ticker" in error["error"]
    assert [r.status for r in answer.tool_calls] == ["error", "ok"]
    # Only the valid call was checked: one record per check, all passes.
    assert [o.check for o in answer.overrides] == [
        "company",
        "fiscal_year",
        "metric",
        "units",
        "segment",
    ]
    assert {o.outcome for o in answer.overrides} == {"pass"}


def test_a_rejected_call_counts_as_a_tool_call_toward_the_limit() -> None:
    chat = FakeChat(
        [
            fact_call(ticker="MS", fiscal_year=2025, metric="revenue"),
            "Which Morgan do you mean?",
        ]
    )
    answer = run_agent("Morgan's revenue?", model=chat, deps=checked_deps(), checks=True)
    assert len(answer.tool_calls) == 1 and answer.tool_calls[0].status == "error"


def test_the_page_filter_reaches_the_check() -> None:
    chat = FakeChat([fact_call(ticker="AAPL", fiscal_year=2025, metric="revenue"), "Revenue [F1]."])
    answer = run_agent(
        "What was revenue in 2025?",
        model=chat,
        deps=checked_deps(),
        checks=True,
        ticker="WMT",
    )
    [override] = [o for o in answer.overrides if o.check == "company"]
    assert override.outcome == "repair" and override.used == "WMT"
    result = json.loads(tool_messages(chat, 1)[0]["content"])
    assert result["status"] == "unavailable"  # the fake facts hold Apple only: WMT has no filing


def test_checks_need_the_company_list() -> None:
    chat = FakeChat([fact_call(ticker="AAPL", fiscal_year=2025, metric="revenue"), "Sales [F1]."])
    with pytest.raises(ValueError, match="compan"):
        run_agent(APPLE_Q, model=chat, deps=apple_deps(), checks=True)


def test_the_switch_and_the_log_reach_the_fallback_runner() -> None:
    chat = FakeChat([fact_call(ticker="MSFT", fiscal_year=2025, metric="revenue"), "Sales [F1]."])
    answer = run_agent_with_fallbacks(APPLE_Q, models=[chat], deps=checked_deps(), checks=True)
    assert answer.checks is True
    assert [o.outcome for o in answer.overrides if o.check == "company"] == ["repair"]


def test_make_ask_output_lists_the_override_log() -> None:
    chat = FakeChat([fact_call(ticker="MSFT", fiscal_year=2025, metric="revenue"), "Sales [F1]."])
    answer = run_agent(APPLE_Q, model=chat, deps=checked_deps(), checks=True)
    text = format_agent_answer(answer)
    assert "checks: on" in text
    assert "company: repair" in text and "MSFT" in text and "AAPL" in text
    off = run_agent(
        APPLE_Q,
        model=FakeChat(
            [fact_call(ticker="AAPL", fiscal_year=2025, metric="revenue"), "Sales [F1]."]
        ),
        deps=apple_deps(),
    )
    assert "checks: off" in format_agent_answer(off)


# ---------------------------------------------------------------- checks=False is the Week 3 agent


def day18_scenarios() -> list[Any]:
    """The Day 18 scripted scenarios on which no check changes anything (passes only)."""
    both = [
        duration(
            "us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax", "416161000000", *YEAR
        ),
        duration("us-gaap:NetIncomeLoss", "112010000000", *YEAR),
    ]
    return [
        pytest.param(
            APPLE_Q,
            [
                fact_call(ticker="AAPL", fiscal_year=2025, metric="revenue"),
                "Apple's total net sales in fiscal 2025 (2024-09-29 to 2025-09-27) were "
                "$416,161 million [F1].",
            ],
            {},
            id="number question",
        ),
        pytest.param(
            # The searches name Walmart's latest pinned year: since 2026-11-12 the fiscal-year
            # check runs on search_filings too, and would repair a search with no year.
            "What are Walmart's main risks in Mexico?",
            [
                scripted_tool_calls(
                    (
                        "search_filings",
                        {"query": "risks in Mexico", "ticker": "WMT", "fiscal_year": 2026},
                    )
                ),
                scripted_tool_calls(
                    (
                        "search_filings",
                        {"query": "peso exposure", "ticker": "WMT", "k": 2, "fiscal_year": 2026},
                    )
                ),
                "Currency swings in Mexico are a risk [2], and so is the peso [1].",
            ],
            {},
            id="text question",
        ),
        pytest.param(
            "Apple's sales in fiscal 2025?",
            [
                fact_call(ticker="Apple", fiscal_year=2025, metric="revenue"),
                fact_call(ticker="AAPL", fiscal_year=2025, metric="revenue"),
                "Apple's total net sales in fiscal 2025 were $416,161 million [F1].",
            ],
            {},
            id="validation error then retry",
        ),
        pytest.param(
            "What were Apple's total liabilities in fiscal 2025?",
            [
                fact_call(ticker="AAPL", fiscal_year=2025, metric="total_liabilities"),
                "Apple's 10-K for fiscal 2025 does not report total liabilities, so I cannot "
                "give it.",
            ],
            {},
            id="unavailable metric",
        ),
        pytest.param(
            "What was Apple's net margin in fiscal 2025?",
            [
                scripted_tool_calls(
                    (
                        "get_financial_fact",
                        {"ticker": "AAPL", "fiscal_year": 2025, "metric": "revenue"},
                    ),
                    (
                        "get_financial_fact",
                        {"ticker": "AAPL", "fiscal_year": 2025, "metric": "net_income"},
                    ),
                ),
                scripted_tool_calls(
                    ("calculate", {"expression": "112010000000 / 416161000000 * 100"})
                ),
                "Apple's net margin in fiscal 2025 was 26.9% [F1] [F2].",
            ],
            {"facts": both},
            id="arithmetic",
        ),
        pytest.param(
            "Add things up forever.",
            [
                *[scripted_tool_calls(("calculate", {"expression": f"{n} + 1"})) for n in range(5)],
                "I could not finish the calculation.",
            ],
            {},
            id="model-call limit",
        ),
        pytest.param(
            "Many sums.",
            [
                scripted_tool_calls(*[("calculate", {"expression": "1 + 1"})] * 5),
                scripted_tool_calls(*[("calculate", {"expression": "1 + 1"})] * 5),
                "Done with what I have.",
            ],
            {},
            id="tool-call limit",
        ),
        pytest.param(
            "What was revenue?",
            [fact_call(metric="revenue"), "Revenue was $416,161 million in fiscal 2025 [F1]."],
            {"ticker": "AAPL", "fiscal_year": 2025},
            id="page filters as defaults",
        ),
    ]


def normalized(answer: AgentAnswer) -> dict[str, Any]:
    data = answer.model_dump(mode="json", exclude={"latency_ms", "checks", "overrides"})
    for record in data["tool_calls"]:
        record.pop("duration_ms")
    return data


@pytest.mark.parametrize(("question", "replies", "extra"), day18_scenarios())
def test_with_no_check_firing_the_two_modes_give_the_same_answer(
    question: str, replies: list[Any], extra: dict[str, Any]
) -> None:
    facts = extra.get("facts")
    filters = {k: v for k, v in extra.items() if k != "facts"}
    off_chat, on_chat = FakeChat(list(replies)), FakeChat(list(replies))
    off = run_agent(question, model=off_chat, deps=apple_deps(facts), **filters)
    on = run_agent(question, model=on_chat, deps=checked_deps(facts), checks=True, **filters)
    assert normalized(on) == normalized(off)
    assert on_chat.calls == off_chat.calls  # the model saw the same messages and tool results
    assert off.checks is False and off.overrides == []
    assert all(o.outcome == "pass" for o in on.overrides)
    assert on.checks is True


def test_the_sent_arguments_are_the_models_own_before_the_page_filter_fills_any_in() -> None:
    chat = FakeChat(
        [fact_call(metric="revenue"), "Revenue was $416,161 million in fiscal 2025 [F1]."]
    )
    answer = run_agent(
        "What was revenue?",
        model=chat,
        deps=checked_deps(),
        checks=False,
        ticker="AAPL",
        fiscal_year=2025,
    )
    [record] = answer.tool_calls
    assert record.sent_arguments == {"metric": "revenue"}
    assert record.arguments == {"metric": "revenue", "ticker": "AAPL", "fiscal_year": 2025}
    assert record.defaults_applied == ["ticker", "fiscal_year"]
