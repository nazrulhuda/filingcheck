"""The agent: a LangGraph state graph of plain Python nodes over our own chat client and tools.

model -> (tool calls) -> tools -> model ... -> (no tool calls) -> answer. At most 6 model
calls and 8 tool calls per question; when a limit is reached the next model call may not
use tools, so the model answers with what it has (or the agent abstains). No skeptical
checks: a wrong tool argument comes back to the model as the tool's error, nothing more.
"""

import json
import time
from collections.abc import Callable
from datetime import date
from decimal import Decimal
from typing import Any, Literal, TypedDict

from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel

from filingcheck.answer.baseline import ABSTAIN, MAX_TOKENS, Answer, is_abstain
from filingcheck.answer.citations import (
    QUOTE_CHARS,
    Citation,
    cited_numbers,
    has_uncited_claims,
    parse_fact_citations,
)
from filingcheck.facts.lookup import FactResult
from filingcheck.llm import ChatModel, Completion, Message
from filingcheck.tools import ToolDeps, run_tool, tool_schemas

MAX_MODEL_CALLS = 6
MAX_TOOL_CALLS = 8
SYSTEM_PROMPT = (
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
# The tools whose `ticker` and `fiscal_year` default to the user's selection.
FILTERED_TOOLS = ("search_filings", "get_financial_fact")


class ToolCallRecord(BaseModel):
    """One tool call the model made: what was run, how it went and how long it took."""

    name: str
    arguments: dict[str, Any]  # as run, after the user's selection filled in any left out
    defaults_applied: list[str]  # "ticker" or "fiscal_year", when filled from the selection
    status: Literal["ok", "error", "skipped"]  # skipped: past the tool-call limit
    result_summary: str
    duration_ms: float


class FactCitation(BaseModel):
    """A number from get_financial_fact, cited as [Fn]."""

    number: int
    concept: str
    value: Decimal
    unit: str
    period_start: date | None
    period_end: date | None
    instant: date | None
    accession: str
    source_url: str


class AgentAnswer(Answer):
    """A baseline `Answer` plus what the agent did: its tool calls and the facts it used."""

    mode: Literal["agent"] = "agent"
    tool_calls: list[ToolCallRecord]
    facts_used: list[FactResult]
    fact_citations: list[FactCitation]
    model_calls: int
    stopped_by: Literal["model_calls", "tool_calls"] | None = None


class _Passage(BaseModel):
    number: int
    chunk_id: int
    ticker: str
    fiscal_year: int
    item: str
    text: str
    source_url: str


class AgentState(TypedDict):
    """What the graph carries from node to node."""

    question: str
    ticker: str | None
    fiscal_year: int | None
    messages: list[Message]
    tool_records: list[ToolCallRecord]
    passages: list[_Passage]  # numbered across the whole run
    facts: list[FactResult]  # numbered across the whole run: [F1] is facts[0]
    completions: list[Completion]
    stopped_by: str | None
    final: Completion | None


def _user_message(question: str, ticker: str | None, fiscal_year: int | None) -> str:
    selection = []
    if ticker:
        selection.append(ticker)
    if fiscal_year is not None:
        selection.append(f"fiscal year {fiscal_year}")
    context = f"The user selected {' and '.join(selection)}.\n\n" if selection else ""
    return f"{context}Question: {question}"


def _summary(name: str, result: dict[str, Any]) -> str:
    if "error" in result:
        return f"error: {result['error']}"[:300]
    if name == "search_filings":
        heads = "; ".join(f"[{p['number']}] {p['header']}" for p in result["passages"][:10])
        return f"{len(result['passages'])} passages: {heads}"[:300]
    if name == "get_financial_fact":
        if result["status"] == "unavailable":
            return f"unavailable ({result['reason']}): {result['message']}"[:300]
        fact = result["fact"]
        period = fact["instant"] or f"{fact['period_start']} to {fact['period_end']}"
        return f"{result['citation']}: {fact['concept']} = {fact['value']} {fact['unit']}, {period}"
    return str(result.get("value"))


PASSAGE_FIELDS = ("chunk_id", "ticker", "fiscal_year", "item", "text", "source_url")


def _number_passages(result: dict[str, Any], passages: list[_Passage]) -> None:
    """Give each returned passage its number across the run; a passage seen before keeps it."""
    for passage in result["passages"]:
        known = next((p for p in passages if p.chunk_id == passage["chunk_id"]), None)
        if known is None:
            known = _Passage(number=len(passages) + 1, **{k: passage[k] for k in PASSAGE_FIELDS})
            passages.append(known)
        passage["number"] = known.number


def _cite_fact(result: dict[str, Any], facts: list[FactResult]) -> None:
    """Number a found fact [F1], [F2] ... across the run; the same fact keeps its number."""
    if result.get("status") != "found":
        return
    fact = FactResult.model_validate(result["fact"])

    def key(f: FactResult) -> tuple[Any, ...]:
        return (f.accession, f.concept, f.period_start, f.period_end, f.instant)

    index = next((i for i, f in enumerate(facts) if key(f) == key(fact)), None)
    if index is None:
        facts.append(fact)
        index = len(facts) - 1
    result["citation"] = f"F{index + 1}"


def build_agent(
    model: ChatModel,
    deps: ToolDeps,
    *,
    max_tokens: int = MAX_TOKENS,
    on_tool_call: Callable[[ToolCallRecord], None] | None = None,
) -> Any:
    """The compiled graph; `on_tool_call` sees each tool call as it finishes."""
    tools = tool_schemas()

    def model_node(state: AgentState) -> dict[str, Any]:
        used = len(state["completions"])
        stopped = state["stopped_by"]
        if stopped is None and used == MAX_MODEL_CALLS - 1:
            stopped = "model_calls"
        completion = model.complete(
            state["messages"],
            max_tokens=max_tokens,
            tools=tools,
            tool_choice="none" if stopped else "auto",
        )
        return {"completions": [*state["completions"], completion], "stopped_by": stopped}

    def route(state: AgentState) -> str:
        last = state["completions"][-1]
        if last.tool_calls and state["stopped_by"] is None:
            return "tools"
        return "answer"

    def tools_node(state: AgentState) -> dict[str, Any]:
        last = state["completions"][-1]
        messages = [*state["messages"], last.message]
        records = list(state["tool_records"])
        passages = list(state["passages"])
        facts = list(state["facts"])
        stopped = state["stopped_by"]
        for call in last.tool_calls:
            start = time.perf_counter()
            ran = sum(1 for r in records if r.status != "skipped")
            try:
                arguments = json.loads(call.arguments or "{}")
            except json.JSONDecodeError:
                arguments = None
            defaults: list[str] = []
            if isinstance(arguments, dict) and call.name in FILTERED_TOOLS:
                for key, value in (
                    ("ticker", state["ticker"]),
                    ("fiscal_year", state["fiscal_year"]),
                ):
                    if value is not None and key not in arguments:
                        arguments[key] = value
                        defaults.append(key)
            if ran >= MAX_TOOL_CALLS:
                limit = f"tool-call limit reached ({MAX_TOOL_CALLS}); answer with what you have"
                result: dict[str, Any] = {"error": limit}
                status: Literal["ok", "error", "skipped"] = "skipped"
                stopped = stopped or "tool_calls"
            else:
                text = run_tool(
                    call.name,
                    json.dumps(arguments) if arguments is not None else call.arguments,
                    deps,
                )
                result = json.loads(text)
                status = "error" if "error" in result else "ok"
                if status == "ok" and call.name == "search_filings":
                    _number_passages(result, passages)
                if status == "ok" and call.name == "get_financial_fact":
                    _cite_fact(result, facts)
            record = ToolCallRecord(
                name=call.name,
                arguments=arguments if isinstance(arguments, dict) else {"raw": call.arguments},
                defaults_applied=defaults,
                status=status,
                result_summary=_summary(call.name, result),
                duration_ms=(time.perf_counter() - start) * 1000,
            )
            records.append(record)
            if on_tool_call is not None:
                on_tool_call(record)
            messages.append(
                {"role": "tool", "tool_call_id": call.id, "content": json.dumps(result)}
            )
        if stopped is None and sum(1 for r in records if r.status != "skipped") >= MAX_TOOL_CALLS:
            stopped = "tool_calls"
        return {
            "messages": messages,
            "tool_records": records,
            "passages": passages,
            "facts": facts,
            "stopped_by": stopped,
        }

    def answer_node(state: AgentState) -> dict[str, Any]:
        return {"final": state["completions"][-1]}

    graph = StateGraph(AgentState)
    graph.add_node("model", model_node)
    graph.add_node("tools", tools_node)
    graph.add_node("answer", answer_node)
    graph.add_edge(START, "model")
    graph.add_conditional_edges("model", route, {"tools": "tools", "answer": "answer"})
    graph.add_edge("tools", "model")
    graph.add_edge("answer", END)
    return graph.compile()


def run_agent(
    question: str,
    *,
    model: ChatModel,
    deps: ToolDeps,
    ticker: str | None = None,
    fiscal_year: int | None = None,
    max_tokens: int = MAX_TOKENS,
    on_tool_call: Callable[[ToolCallRecord], None] | None = None,
) -> AgentAnswer:
    """Answer one question with the agent and return what it said and did."""
    start = time.perf_counter()
    agent = build_agent(model, deps, max_tokens=max_tokens, on_tool_call=on_tool_call)
    state: AgentState = {
        "question": question,
        "ticker": ticker,
        "fiscal_year": fiscal_year,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": _user_message(question, ticker, fiscal_year)},
        ],
        "tool_records": [],
        "passages": [],
        "facts": [],
        "completions": [],
        "stopped_by": None,
        "final": None,
    }
    final_state = agent.invoke(state, config={"recursion_limit": 4 * MAX_MODEL_CALLS + 4})
    return _answer(final_state, start)


def _answer(state: AgentState, start: float) -> AgentAnswer:
    final = state["final"]
    assert final is not None
    completions = state["completions"]
    text = final.text.strip()
    if final.tool_calls or not text:
        text = ABSTAIN  # still asking for tools at the last allowed call, or nothing said
    abstained = is_abstain(text)
    passages = state["passages"]
    facts = state["facts"]
    citations = (
        []
        if abstained
        else [
            Citation(
                number=n,
                chunk_id=passages[n - 1].chunk_id,
                ticker=passages[n - 1].ticker,
                fiscal_year=passages[n - 1].fiscal_year,
                item=passages[n - 1].item,
                source_url=passages[n - 1].source_url,
                quote=passages[n - 1].text[:QUOTE_CHARS],
            )
            for n in cited_numbers(text, len(passages))
        ]
    )
    fact_citations = (
        []
        if abstained
        else [
            FactCitation(
                number=n,
                concept=facts[n - 1].concept,
                value=facts[n - 1].value,
                unit=facts[n - 1].unit,
                period_start=facts[n - 1].period_start,
                period_end=facts[n - 1].period_end,
                instant=facts[n - 1].instant,
                accession=facts[n - 1].accession,
                source_url=facts[n - 1].source_url,
            )
            for n in parse_fact_citations(text, len(facts))
        ]
    )
    prompt = [c.prompt_tokens for c in completions]
    output = [c.completion_tokens for c in completions]
    costs = [c.cost_usd for c in completions]
    return AgentAnswer(
        text=text,
        citations=citations,
        model_used=final.model,
        retriever_name="hybrid",
        usage={
            "prompt_tokens": None if None in prompt else sum(p for p in prompt if p is not None),
            "completion_tokens": None
            if None in output
            else sum(o for o in output if o is not None),
        },
        latency_ms=(time.perf_counter() - start) * 1000,
        cost_usd=None if None in costs else sum(c for c in costs if c is not None),
        finish_reason=final.finish_reason,
        abstained=abstained,
        has_uncited_claims=not abstained and has_uncited_claims(text),
        degraded=False,
        tool_calls=state["tool_records"],
        facts_used=facts,
        fact_citations=fact_citations,
        model_calls=len(completions),
        stopped_by=state["stopped_by"],  # type: ignore[arg-type]
    )
