"""The agent graph with the fake chat: tools, citations, limits and filters (no network)."""

import json
from datetime import date
from decimal import Decimal
from typing import Any

import pytest

from filingcheck.agent import MAX_MODEL_CALLS, MAX_TOOL_CALLS, SYSTEM_PROMPT, AgentAnswer, run_agent
from filingcheck.answer.baseline import ABSTAIN, Answer
from filingcheck.answer.citations import has_uncited_claims, parse_fact_citations
from filingcheck.facts.lookup import FilingRef, TotalFact
from filingcheck.llm import FakeChat, scripted_tool_calls
from filingcheck.tools import ToolDeps
from tests.answer.test_baseline import HITS, FakeRetriever
from tests.facts.test_lookup import FakeFacts, duration, instant

APPLE = FilingRef(
    ticker="AAPL",
    fiscal_year=2025,
    accession="0000320193-25-000079",
    period_of_report=date(2025, 9, 27),
    source_url="https://www.sec.gov/Archives/edgar/data/320193/x/aapl-20250927.htm",
    revenue_rule="standard",
)
YEAR = (date(2024, 9, 29), date(2025, 9, 27))


def apple_deps(facts: list[TotalFact] | None = None) -> ToolDeps:
    if facts is None:
        facts = [
            duration(
                "us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax", "416161000000", *YEAR
            ),
            duration("us-gaap:NetIncomeLoss", "112010000000", *YEAR),
        ]
    return ToolDeps(retriever=FakeRetriever(), facts=FakeFacts(facts, filing=APPLE))


def fact_call(**arguments: Any) -> Any:
    return scripted_tool_calls(("get_financial_fact", arguments))


def tool_messages(chat: FakeChat, call: int) -> list[dict[str, Any]]:
    return [m for m in chat.calls[call]["messages"] if m["role"] == "tool"]


# ---------------------------------------------------------------- the prompt and the answer


def test_the_system_prompt_is_exactly_the_frozen_text() -> None:
    prompt = SYSTEM_PROMPT
    assert prompt == (
        "You answer questions about public companies from their SEC 10-K filings, using tools.\n"
        "- Answer only from tool results.\n"
        "- For any number, call get_financial_fact and quote its value, unit and period as "
        "returned; never use a number you remember. If the fact's line_label differs from "
        "the question's wording, name the line it comes from.\n"
        "- For what a filing says, call search_filings and cite passages by their number, like "
        "[n]. Cite a number from get_financial_fact by its citation, like [F1].\n"
        "- Use calculate for any arithmetic.\n"
        '- If a tool returns an error or "unavailable", say so and do not guess.\n'
        "- State the fiscal year and the period for every figure.\n"
        "- If the question is ambiguous about the company or the year, say what is ambiguous.\n"
        f'- If the tools do not give the answer, say "{ABSTAIN}" and nothing else.'
    )


def test_a_number_question_is_answered_from_get_financial_fact_and_cited_as_f1() -> None:
    chat = FakeChat(
        [
            fact_call(ticker="AAPL", fiscal_year=2025, metric="revenue"),
            "Apple's total net sales in fiscal 2025 (2024-09-29 to 2025-09-27) were "
            "$416,161 million [F1].",
        ]
    )
    answer = run_agent(
        "What were Apple's total net sales in fiscal 2025?", model=chat, deps=apple_deps()
    )
    assert isinstance(answer, AgentAnswer) and isinstance(answer, Answer)
    assert answer.mode == "agent"
    assert answer.model_calls == 2
    [record] = answer.tool_calls
    assert (record.name, record.arguments, record.status) == (
        "get_financial_fact",
        {"ticker": "AAPL", "fiscal_year": 2025, "metric": "revenue"},
        "ok",
    )
    assert "416161000000" in record.result_summary
    [fact] = answer.facts_used
    assert fact.value == Decimal("416161000000")
    [cite] = answer.fact_citations
    assert (cite.number, cite.concept, cite.period_end, cite.source_url) == (
        1,
        "us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax",
        date(2025, 9, 27),
        APPLE.source_url,
    )
    result = json.loads(tool_messages(chat, 1)[0]["content"])
    assert result["citation"] == "F1"  # the model is told how to cite the fact
    assert not answer.abstained and not answer.has_uncited_claims


def test_a_text_question_searches_then_cites_passages_numbered_across_the_run() -> None:
    chat = FakeChat(
        [
            scripted_tool_calls(("search_filings", {"query": "risks in Mexico", "ticker": "WMT"})),
            scripted_tool_calls(
                ("search_filings", {"query": "peso exposure", "ticker": "WMT", "k": 2})
            ),
            "Currency swings in Mexico are a risk [2], and so is the peso [1].",
        ]
    )
    answer = run_agent("What are Walmart's main risks in Mexico?", model=chat, deps=apple_deps())
    first = json.loads(tool_messages(chat, 1)[0]["content"])
    assert [p["number"] for p in first["passages"]] == [1, 2, 3, 4]
    second = json.loads(tool_messages(chat, 2)[1]["content"])
    assert [p["number"] for p in second["passages"]] == [
        1,
        2,
    ]  # the same passages keep their numbers
    assert [(c.number, c.chunk_id) for c in answer.citations] == [
        (2, HITS[1].chunk_id),
        (1, HITS[0].chunk_id),
    ]
    assert answer.retriever_name == "hybrid"


def test_a_validation_error_goes_back_to_the_model_which_tries_again() -> None:
    chat = FakeChat(
        [
            fact_call(ticker="Apple", fiscal_year=2025, metric="revenue"),
            fact_call(ticker="AAPL", fiscal_year=2025, metric="revenue"),
            "Apple's total net sales in fiscal 2025 were $416,161 million [F1].",
        ]
    )
    answer = run_agent("Apple's sales in fiscal 2025?", model=chat, deps=apple_deps())
    assert [r.status for r in answer.tool_calls] == ["error", "ok"]
    error = json.loads(tool_messages(chat, 1)[0]["content"])
    assert "ticker" in error["error"]  # the model sees the validation message; nothing repaired
    assert answer.tool_calls[0].arguments == {
        "ticker": "Apple",
        "fiscal_year": 2025,
        "metric": "revenue",
    }
    assert len(answer.facts_used) == 1


def test_an_unavailable_metric_is_reported_and_not_guessed() -> None:
    chat = FakeChat(
        [
            fact_call(ticker="AAPL", fiscal_year=2025, metric="total_liabilities"),
            "Apple's 10-K for fiscal 2025 does not report total liabilities, so I cannot give it.",
        ]
    )
    answer = run_agent(
        "What were Apple's total liabilities in fiscal 2025?", model=chat, deps=apple_deps()
    )
    [record] = answer.tool_calls
    assert record.status == "ok" and "unavailable" in record.result_summary
    assert answer.facts_used == []
    assert json.loads(tool_messages(chat, 1)[0]["content"])["status"] == "unavailable"


def test_arithmetic_goes_through_calculate() -> None:
    chat = FakeChat(
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
            scripted_tool_calls(("calculate", {"expression": "112010000000 / 416161000000 * 100"})),
            "Apple's net margin in fiscal 2025 was 26.9% [F1] [F2].",
        ]
    )
    answer = run_agent("What was Apple's net margin in fiscal 2025?", model=chat, deps=apple_deps())
    assert [r.name for r in answer.tool_calls] == [
        "get_financial_fact",
        "get_financial_fact",
        "calculate",
    ]
    assert answer.tool_calls[2].result_summary.startswith("26.91")
    assert [c.number for c in answer.fact_citations] == [1, 2]


# ---------------------------------------------------------------- limits


def test_after_five_model_calls_the_sixth_must_answer_without_tools() -> None:
    loops = [scripted_tool_calls(("calculate", {"expression": f"{n} + 1"})) for n in range(5)]
    chat = FakeChat([*loops, "I could not finish the calculation."])
    answer = run_agent("Add things up forever.", model=chat, deps=apple_deps())
    assert answer.model_calls == MAX_MODEL_CALLS == 6
    assert [c["tool_choice"] for c in chat.calls] == ["auto"] * 5 + ["none"]
    assert answer.stopped_by == "model_calls"
    assert answer.text == "I could not finish the calculation."


def test_a_model_that_still_asks_for_tools_at_the_last_call_abstains() -> None:
    loops = [scripted_tool_calls(("calculate", {"expression": "1 + 1"})) for _ in range(6)]
    answer = run_agent("Loop.", model=FakeChat(loops), deps=apple_deps())
    assert answer.model_calls == 6
    assert answer.abstained and answer.text == ABSTAIN


def test_no_more_than_eight_tool_calls_are_run() -> None:
    five = [("calculate", {"expression": "1 + 1"})] * 5
    chat = FakeChat(
        [scripted_tool_calls(*five), scripted_tool_calls(*five), "Done with what I have."]
    )
    answer = run_agent("Many sums.", model=chat, deps=apple_deps())
    assert MAX_TOOL_CALLS == 8
    assert [r.status for r in answer.tool_calls].count("ok") == 8
    skipped = [r for r in answer.tool_calls if r.status == "skipped"]
    assert len(skipped) == 2
    # Every call the model made gets a tool message, the skipped ones say why.
    results = [json.loads(m["content"]) for m in tool_messages(chat, 2)]
    assert len(results) == 10 and "limit" in results[-1]["error"]
    assert chat.calls[2]["tool_choice"] == "none"
    assert answer.stopped_by == "tool_calls"


# ---------------------------------------------------------------- filters


def test_the_selected_company_and_year_are_context_and_default_tool_arguments() -> None:
    chat = FakeChat(
        [fact_call(metric="revenue"), "Revenue was $416,161 million in fiscal 2025 [F1]."]
    )
    answer = run_agent(
        "What was revenue?", model=chat, deps=apple_deps(), ticker="AAPL", fiscal_year=2025
    )
    user = chat.calls[0]["messages"][1]["content"]
    assert "The user selected AAPL and fiscal year 2025." in user
    [record] = answer.tool_calls
    assert record.arguments == {"metric": "revenue", "ticker": "AAPL", "fiscal_year": 2025}
    assert record.defaults_applied == ["ticker", "fiscal_year"]
    assert record.status == "ok"


def test_the_model_may_pass_other_values_than_the_filters_and_the_log_shows_it() -> None:
    other = instant("us-gaap:Assets", "359241000000", on=date(2025, 9, 27))
    chat = FakeChat(
        [fact_call(ticker="AAPL", fiscal_year=2025, metric="total_assets"), "Total assets [F1]."]
    )
    answer = run_agent(
        "Assets?", model=chat, deps=apple_deps([other]), ticker="WMT", fiscal_year=2026
    )
    [record] = answer.tool_calls
    assert record.arguments["ticker"] == "AAPL" and record.defaults_applied == []


# ---------------------------------------------------------------- citations


def test_fact_citations_parse_the_fn_form_and_drop_unknown_numbers() -> None:
    assert parse_fact_citations("Revenue [F1], margin [F2, F1] and [F3].", facts=2) == [1, 2]
    assert parse_fact_citations("No citations here.", facts=2) == []
    assert not has_uncited_claims("Revenue was $416.2 billion [F1].")
    assert has_uncited_claims("Revenue was $416.2 billion.")


def test_cost_tokens_and_time_add_up_over_the_model_calls() -> None:
    chat = FakeChat(
        [
            fact_call(ticker="AAPL", fiscal_year=2025, metric="revenue"),
            "Sales were $416,161 million [F1].",
        ]
    )
    answer = run_agent("Sales?", model=chat, deps=apple_deps())
    assert answer.usage == {"prompt_tokens": 200, "completion_tokens": 40}
    assert answer.cost_usd == 0.0
    assert answer.latency_ms >= 0


def test_the_graph_sends_nothing_anywhere(monkeypatch: pytest.MonkeyPatch) -> None:
    import socket

    def blocked(*args: Any, **kwargs: Any) -> None:
        raise AssertionError(f"network call: {args[1:]}")

    monkeypatch.setattr(socket.socket, "connect", blocked)
    monkeypatch.setattr(socket, "create_connection", blocked)
    chat = FakeChat([fact_call(ticker="AAPL", fiscal_year=2025, metric="revenue"), "Sales [F1]."])
    answer = run_agent("Sales?", model=chat, deps=apple_deps())
    assert answer.model_calls == 2


def test_no_tracing_variable_is_set_in_the_public_config() -> None:
    from filingcheck.paths import REPO_ROOT

    for name in (".env.example", "render.yaml"):
        text = (REPO_ROOT / name).read_text(encoding="utf-8")
        assert "LANGSMITH" not in text and "LANGCHAIN" not in text, name


# ---------------------------------------------------------------- audit fixes


def test_passage_and_fact_numbers_in_one_bracket_are_each_read_as_written() -> None:
    from filingcheck.answer.citations import cited_numbers

    assert parse_fact_citations("Sales [F1, 2].", facts=3) == [1]
    assert cited_numbers("Sales [F1, 2].", passages=3) == [2]
    assert parse_fact_citations("Sales [1, F2].", facts=3) == [2]
    assert cited_numbers("Sales [1, F2].", passages=3) == [1]
    assert cited_numbers("Risks [1-3, F1].", passages=5) == [1, 2, 3]
    assert not has_uncited_claims("Sales were $416.2 billion [1, F2].")
    assert not has_uncited_claims("Sales were $416.2 billion [F1, 2].")


def test_an_explicit_null_is_filled_from_the_selection_like_a_left_out_argument() -> None:
    chat = FakeChat(
        [
            fact_call(ticker=None, fiscal_year=None, metric="revenue"),
            "Revenue was $416,161 million in fiscal 2025 [F1].",
        ]
    )
    answer = run_agent(
        "What was revenue?", model=chat, deps=apple_deps(), ticker="AAPL", fiscal_year=2025
    )
    [record] = answer.tool_calls
    assert record.arguments == {"ticker": "AAPL", "fiscal_year": 2025, "metric": "revenue"}
    assert record.defaults_applied == ["ticker", "fiscal_year"] and record.status == "ok"


def test_the_answer_is_degraded_when_a_search_fell_back_to_keywords() -> None:
    chat = FakeChat([scripted_tool_calls(("search_filings", {"query": "risks"})), "Risks [1]."])
    deps = ToolDeps(retriever=FakeRetriever(degraded=True), facts=FakeFacts([], filing=APPLE))
    assert run_agent("Risks?", model=chat, deps=deps).degraded
    chat = FakeChat([scripted_tool_calls(("search_filings", {"query": "risks"})), "Risks [1]."])
    assert not run_agent("Risks?", model=chat, deps=apple_deps()).degraded


def failing_model(*after: Any) -> FakeChat:
    from filingcheck.llm import ProviderUnavailable

    down = ProviderUnavailable("primary down", provider="fake", status=503, code="busy")
    return FakeChat(
        [fact_call(ticker="AAPL", fiscal_year=2025, metric="revenue"), *after, down],
        name="fake:primary",
    )


def test_a_restart_keeps_the_failed_attempts_cost_and_tool_calls() -> None:
    from filingcheck.agent import run_agent_with_fallbacks

    fallback = FakeChat(
        [fact_call(ticker="AAPL", fiscal_year=2025, metric="revenue"), "Sales [F1]."],
        name="fake:fallback",
    )
    answer = run_agent_with_fallbacks(
        "Sales?", models=[failing_model(), fallback], deps=apple_deps()
    )
    assert answer.restarts == ["fake 503 busy"]
    [attempt] = answer.failed_attempts
    assert (attempt.model, attempt.log_code, attempt.model_calls) == (
        "fake:primary",
        "fake 503 busy",
        1,
    )
    assert attempt.usage == {"prompt_tokens": 100, "completion_tokens": 20}
    assert [r.name for r in attempt.tool_calls] == ["get_financial_fact"]
    # The answer's own run: two calls and one tool call; its totals include the failed one.
    assert (answer.model_calls, len(answer.tool_calls)) == (2, 1)
    assert answer.usage == {"prompt_tokens": 300, "completion_tokens": 60}
    assert answer.cost_usd == 0.0


def cut_off(prompt_tokens: int = 7, completion_tokens: int = 3) -> Any:
    from filingcheck.llm import Completion, IncompleteAnswer

    return IncompleteAnswer(
        "fake: cut off",
        Completion(
            text="Sales were",
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            model="fake:primary",
            latency_ms=0.0,
            cost_usd=0.001,
            finish_reason="length",
        ),
        provider="fake",
        code="incomplete_length",
    )


def test_a_cut_off_reply_is_counted_in_the_failed_attempt() -> None:
    from filingcheck.agent import run_agent_with_fallbacks

    primary = FakeChat(
        [fact_call(ticker="AAPL", fiscal_year=2025, metric="revenue"), cut_off()],
        name="fake:primary",
    )
    fallback = FakeChat(["I can't find this in the filings I have."], name="fake:fallback")
    answer = run_agent_with_fallbacks("Sales?", models=[primary, fallback], deps=apple_deps())
    [attempt] = answer.failed_attempts
    assert attempt.model_calls == 2
    assert attempt.usage == {"prompt_tokens": 107, "completion_tokens": 23}
    assert attempt.cost_usd == pytest.approx(0.001)
    assert answer.usage == {"prompt_tokens": 207, "completion_tokens": 43}


def test_when_every_model_fails_the_caller_still_gets_every_attempt() -> None:
    from filingcheck.agent import FailedAttempt, run_agent_with_fallbacks
    from filingcheck.llm import ProviderUnavailable

    failed: list[FailedAttempt] = []
    with pytest.raises(ProviderUnavailable):
        run_agent_with_fallbacks(
            "Sales?", models=[failing_model(), failing_model()], deps=apple_deps(), failed=failed
        )
    assert [a.log_code for a in failed] == ["fake 503 busy", "fake 503 busy"]
    assert [len(a.tool_calls) for a in failed] == [1, 1]


def test_a_run_log_keeps_what_a_failed_run_spent() -> None:
    from filingcheck.agent import RunLog
    from filingcheck.llm import IncompleteAnswer

    log = RunLog()
    chat = FakeChat([fact_call(ticker="AAPL", fiscal_year=2025, metric="revenue"), cut_off()])
    with pytest.raises(IncompleteAnswer):
        run_agent("Sales?", model=chat, deps=apple_deps(), run_log=log)
    assert [c.prompt_tokens for c in log.completions] == [100, 7]
    assert [r.name for r in log.tool_calls] == ["get_financial_fact"]
    assert [f.value for f in log.facts] == [Decimal("416161000000")]
