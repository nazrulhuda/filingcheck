"""Day 23 in the agent: retry once after a reject, the requested scale next to the value, and
the full chain's override log."""

import json

from filingcheck.agent import run_agent
from filingcheck.agent.graph import NO_FURTHER_ATTEMPTS
from filingcheck.llm import FakeChat
from tests.agent.test_agent import fact_call, tool_messages
from tests.agent.test_agent_checks import checked_deps

MORGAN_Q = "How much net revenue did Morgan report last year?"


def test_a_second_reject_of_the_same_class_ends_the_tools_use_and_says_so() -> None:
    chat = FakeChat(
        [
            fact_call(ticker="MS", fiscal_year=2025, metric="revenue"),
            fact_call(ticker="JPM", fiscal_year=2025, metric="revenue"),
            fact_call(ticker="JPM", fiscal_year=2026, metric="revenue"),
            "Which Morgan do you mean, JPMorgan Chase or Morgan Stanley?",
        ]
    )
    answer = run_agent(MORGAN_Q, model=chat, deps=checked_deps(), checks=True)
    first = json.loads(tool_messages(chat, 1)[0]["content"])
    assert "ambiguous" in first["error"] and NO_FURTHER_ATTEMPTS not in first["error"]
    second = json.loads(tool_messages(chat, 2)[1]["content"])
    assert "ambiguous" in second["error"] and NO_FURTHER_ATTEMPTS in second["error"]
    third = json.loads(tool_messages(chat, 3)[2]["content"])
    assert third == {"error": NO_FURTHER_ATTEMPTS}  # the tool no longer runs
    assert [r.status for r in answer.tool_calls] == ["error", "error", "error"]
    # Both rejects and the blocked call stay in the log.
    assert [(o.check, o.outcome) for o in answer.overrides] == [
        ("company", "reject"),
        ("company", "reject"),
        ("retry", "reject"),
    ]
    assert answer.facts_used == []


def test_rejects_of_different_classes_each_get_their_own_retry() -> None:
    chat = FakeChat(
        [
            fact_call(ticker="AAPL", fiscal_year=2023, metric="revenue"),  # year: not pinned
            fact_call(ticker="MS", fiscal_year=2025, metric="revenue"),  # company: not named
            fact_call(ticker="AAPL", fiscal_year=2025, metric="revenue"),
            "Apple's fiscal 2025 total net sales were $416,161 million [F1].",
        ]
    )
    answer = run_agent(
        "What were Apple's total net sales in fiscal 2023?",
        model=chat,
        deps=checked_deps(),
        checks=True,
    )
    rejects = [o.check for o in answer.overrides if o.outcome == "reject"]
    assert rejects == ["fiscal_year", "fiscal_year"]  # the 2023 question is rejected twice
    third = json.loads(tool_messages(chat, 3)[2]["content"])
    assert third == {"error": NO_FURTHER_ATTEMPTS}


def test_with_the_checks_off_there_is_no_retry_rule() -> None:
    from tests.agent.test_agent import apple_deps

    chat = FakeChat(
        [
            fact_call(ticker="Morgan", fiscal_year=2025, metric="revenue"),
            fact_call(ticker="Morgan", fiscal_year=2025, metric="revenue"),
            fact_call(ticker="Morgan", fiscal_year=2025, metric="revenue"),
            "I can't find this in the filings I have.",
        ]
    )
    answer = run_agent(MORGAN_Q, model=chat, deps=apple_deps())
    third = json.loads(tool_messages(chat, 3)[2]["content"])
    assert "ticker" in third["error"] and NO_FURTHER_ATTEMPTS not in third["error"]
    assert answer.overrides == []


def test_a_requested_scale_comes_back_next_to_the_raw_value() -> None:
    chat = FakeChat(
        [
            fact_call(ticker="AAPL", fiscal_year=2025, metric="revenue"),
            "Apple's fiscal 2025 total net sales were $416,161 million [F1].",
        ]
    )
    run_agent(
        "What were Apple's total net sales in fiscal 2025, in millions?",
        model=chat,
        deps=checked_deps(),
        checks=True,
    )
    result = json.loads(tool_messages(chat, 1)[0]["content"])
    assert result["fact"]["value"] == "416161000000"  # the stored value is unchanged
    assert result["requested_scale"] == {"scale": "millions", "value": "416,161 million"}
    assert "checked" not in result


def test_every_check_logs_a_record_for_each_checked_call() -> None:
    chat = FakeChat(
        [
            fact_call(ticker="AAPL", fiscal_year=2025, metric="revenue"),
            "Apple's fiscal 2025 total net sales were $416,161 million [F1].",
        ]
    )
    answer = run_agent(
        "What were Apple's total net sales in fiscal 2025?",
        model=chat,
        deps=checked_deps(),
        checks=True,
    )
    assert [(o.check, o.outcome) for o in answer.overrides] == [
        ("company", "pass"),
        ("fiscal_year", "pass"),
        ("metric", "pass"),
        ("units", "pass"),
        ("segment", "pass"),
    ]
