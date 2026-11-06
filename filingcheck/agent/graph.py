"""The agent: a LangGraph state graph of plain Python nodes over our own chat client and tools.

model -> (tool calls) -> tools -> model ... -> (no tool calls) -> answer. At most 6 model
calls and 8 tool calls per question; when a limit is reached the next model call may not
use tools, so the model answers with what it has (or the agent abstains). No skeptical
checks: a wrong tool argument comes back to the model as the tool's error, nothing more.
"""

import json
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Any, Literal, TypedDict

from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field

from filingcheck.answer.baseline import ABSTAIN, MAX_TOKENS, Answer, is_abstain
from filingcheck.answer.citations import (
    QUOTE_CHARS,
    Citation,
    cited_numbers,
    has_uncited_claims,
    parse_fact_citations,
)
from filingcheck.checks import (
    CHECKED_TOOL,
    CHECKS,
    CheckContext,
    CheckedCall,
    Override,
    run_checks,
)
from filingcheck.facts.lookup import FactResult
from filingcheck.llm import (
    ChatModel,
    Completion,
    IncompleteAnswer,
    Message,
    ProviderError,
    ProviderUnavailable,
)
from filingcheck.tools import (
    ToolDeps,
    ToolInputError,
    run_tool,
    run_validated,
    tool_schemas,
    validate_call,
)

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


class FailedAttempt(BaseModel):
    """One model's run that failed before it answered; its model calls were still paid for."""

    model: str  # provider:model
    log_code: str
    model_calls: int
    usage: dict[str, int | None]
    cost_usd: float | None
    tool_calls: list[ToolCallRecord]


@dataclass
class RunLog:
    """What one run has done so far, filled in as it goes, so a failed run's cost is kept.

    `completions` includes a reply that was cut off (its tokens were paid for); a provider
    that did not answer at all adds nothing.
    """

    completions: list[Completion] = field(default_factory=list)
    tool_calls: list[ToolCallRecord] = field(default_factory=list)
    facts: list[FactResult] = field(default_factory=list)
    overrides: list[Override] = field(default_factory=list)


def total_usage(completions: Sequence[Completion]) -> tuple[dict[str, int | None], float | None]:
    """Prompt and completion tokens and cost summed over model calls (None if any is unknown)."""
    prompt = [c.prompt_tokens for c in completions]
    output = [c.completion_tokens for c in completions]
    costs = [c.cost_usd for c in completions]
    usage = {
        "prompt_tokens": None if None in prompt else sum(p for p in prompt if p is not None),
        "completion_tokens": None if None in output else sum(o for o in output if o is not None),
    }
    return usage, None if None in costs else sum(c for c in costs if c is not None)


def _add(
    a: tuple[dict[str, int | None], float | None], b: tuple[dict[str, int | None], float | None]
) -> tuple[dict[str, int | None], float | None]:
    def plus(x: float | int | None, y: float | int | None) -> Any:
        return None if x is None or y is None else x + y

    usage = {
        key: plus(a[0].get(key), b[0].get(key)) for key in ("prompt_tokens", "completion_tokens")
    }
    return usage, plus(a[1], b[1])


class AgentAnswer(Answer):
    """A baseline `Answer` plus what the agent did: its tool calls and the facts it used.

    After a restart, `usage`, `cost_usd` and `latency_ms` cover the whole question, failed
    attempts included; `model_calls`, `tool_calls` and the citations are the answering run's,
    and each failed run is in `failed_attempts`.
    """

    mode: Literal["agent"] = "agent"
    tool_calls: list[ToolCallRecord]
    facts_used: list[FactResult]
    fact_citations: list[FactCitation]
    model_calls: int
    stopped_by: Literal["model_calls", "tool_calls"] | None = None
    # Log codes of models that failed before this one answered; each restart began the
    # question again from an empty message list.
    restarts: list[str] = Field(default_factory=list)
    failed_attempts: list[FailedAttempt] = Field(default_factory=list)
    # The skeptical checks: whether they ran on this answer, and their override log (one
    # record per check per checked tool call: pass, repair or reject, with the reason).
    checks: bool = False
    overrides: list[Override] = Field(default_factory=list)


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
    overrides: list[Override]  # the checks' records, in order
    completions: list[Completion]
    stopped_by: str | None
    degraded: bool  # a search fell back to keywords
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


def _checked_call(
    name: str, arguments_json: str, deps: ToolDeps, context: CheckContext
) -> tuple[dict[str, Any], list[Override], dict[str, Any] | None]:
    """Validate, check, then run: the tool result, the checks' records, the arguments as run.

    A validation error comes back as today, before any check. A reject becomes the tool's
    result, `{"error": reason, "options": [...]}`, the shape of a validation error plus the
    options. A repair runs the tool with the repaired arguments and adds `"checked"` to the
    result so the model sees what changed. A pass leaves the result exactly as `run_tool`
    would give it.
    """
    try:
        tool, parsed = validate_call(name, arguments_json)
    except ToolInputError as exc:
        return json.loads(exc.result), [], None
    sent = parsed.model_dump()
    checked, overrides = run_checks(CheckedCall(name, sent), context, CHECKS)
    if checked is None:
        last = overrides[-1]
        return {"error": last.reason, "options": last.options}, overrides, None
    if checked.arguments != sent:
        parsed = tool.input_model.model_validate(checked.arguments)
    result: dict[str, Any] = json.loads(run_validated(tool, parsed, deps))
    repairs = [o.model_dump() for o in overrides if o.outcome == "repair"]
    if repairs and "error" not in result:
        result["checked"] = repairs
    return result, overrides, checked.arguments


def build_agent(
    model: ChatModel,
    deps: ToolDeps,
    *,
    max_tokens: int = MAX_TOKENS,
    on_tool_call: Callable[[ToolCallRecord], None] | None = None,
    run_log: RunLog | None = None,
    checks: bool = False,
) -> Any:
    """The compiled graph; `on_tool_call` sees each tool call as it finishes.

    `run_log`, when given, is filled in as the run goes (see RunLog). With `checks`,
    every get_financial_fact call goes through the skeptical checks before the tool.
    """
    log = run_log if run_log is not None else RunLog()
    if checks and deps.companies is None:
        raise ValueError("the checks need the company list: ToolDeps(companies=...)")
    tools = tool_schemas()

    def model_node(state: AgentState) -> dict[str, Any]:
        used = len(state["completions"])
        stopped = state["stopped_by"]
        if stopped is None and used == MAX_MODEL_CALLS - 1:
            stopped = "model_calls"
        try:
            completion = model.complete(
                state["messages"],
                max_tokens=max_tokens,
                tools=tools,
                tool_choice="none" if stopped else "auto",
            )
        except IncompleteAnswer as exc:
            log.completions.append(exc.completion)  # cut off, but paid for
            raise
        log.completions.append(completion)
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
        degraded = state["degraded"]
        overrides = list(state["overrides"])
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
                    if value is not None and arguments.get(key) is None:
                        arguments[key] = value
                        defaults.append(key)
            if ran >= MAX_TOOL_CALLS:
                limit = f"tool-call limit reached ({MAX_TOOL_CALLS}); answer with what you have"
                result: dict[str, Any] = {"error": limit}
                status: Literal["ok", "error", "skipped"] = "skipped"
                stopped = stopped or "tool_calls"
            else:
                text_arguments = json.dumps(arguments) if arguments is not None else call.arguments
                if checks and call.name == CHECKED_TOOL:
                    context = CheckContext(
                        question=state["question"],
                        ticker=state["ticker"],
                        fiscal_year=state["fiscal_year"],
                        companies=deps.companies or [],
                        not_covered=deps.not_covered,
                        manifest=deps.manifest,
                        facts=deps.facts,
                    )
                    result, call_overrides, as_run = _checked_call(
                        call.name, text_arguments, deps, context
                    )
                    overrides += call_overrides
                    if as_run is not None:
                        arguments = as_run
                else:
                    result = json.loads(run_tool(call.name, text_arguments, deps))
                status = "error" if "error" in result else "ok"
                if status == "ok" and call.name == "search_filings":
                    _number_passages(result, passages)
                    degraded = degraded or bool(result.get("degraded"))
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
            log.tool_calls.append(record)
            if on_tool_call is not None:
                on_tool_call(record)
            messages.append(
                {"role": "tool", "tool_call_id": call.id, "content": json.dumps(result)}
            )
        if stopped is None and sum(1 for r in records if r.status != "skipped") >= MAX_TOOL_CALLS:
            stopped = "tool_calls"
        log.facts[:] = facts
        log.overrides[:] = overrides
        return {
            "messages": messages,
            "tool_records": records,
            "passages": passages,
            "facts": facts,
            "stopped_by": stopped,
            "degraded": degraded,
            "overrides": overrides,
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
    run_log: RunLog | None = None,
    checks: bool = False,
) -> AgentAnswer:
    """Answer one question with the agent and return what it said and did.

    `run_log`, when given, keeps what the run spent even if a provider failure is raised.
    `checks` switches the skeptical checks on; off, this is the Week 3 agent.
    """
    start = time.perf_counter()
    agent = build_agent(
        model,
        deps,
        max_tokens=max_tokens,
        on_tool_call=on_tool_call,
        run_log=run_log,
        checks=checks,
    )
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
        "degraded": False,
        "overrides": [],
        "final": None,
    }
    final_state = agent.invoke(state, config={"recursion_limit": 4 * MAX_MODEL_CALLS + 4})
    return _answer(final_state, start, checks)


def run_agent_with_fallbacks(
    question: str,
    *,
    models: Sequence[ChatModel],
    deps: ToolDeps,
    ticker: str | None = None,
    fiscal_year: int | None = None,
    max_tokens: int = MAX_TOKENS,
    on_tool_call: Callable[[ToolCallRecord], None] | None = None,
    on_restart: Callable[[str], None] | None = None,
    failed: list[FailedAttempt] | None = None,
    checks: bool = False,
) -> AgentAnswer:
    """The agent with each model in turn: if one fails mid-run, the next starts again.

    A run is never continued by another model, whose tool calls would follow a
    conversation it did not have; the next model gets the question from the beginning.
    The last model's failure, or any failure another model would not fix, is raised. Each
    failed run is appended to `failed` as it happens, so a caller has them (and what they
    cost) even when the question fails; the last entry is the failure that was raised.
    """
    start = time.perf_counter()
    attempts: list[FailedAttempt] = failed if failed is not None else []
    for i, model in enumerate(models):
        run_log = RunLog()
        try:
            answer = run_agent(
                question,
                model=model,
                deps=deps,
                ticker=ticker,
                fiscal_year=fiscal_year,
                max_tokens=max_tokens,
                on_tool_call=on_tool_call,
                run_log=run_log,
                checks=checks,
            )
        except ProviderError as exc:
            # Every provider failure is recorded; only these two move on to the next model.
            usage, cost = total_usage(run_log.completions)
            attempts.append(
                FailedAttempt(
                    model=model.name,
                    log_code=exc.log_code,
                    model_calls=len(run_log.completions),
                    usage=usage,
                    cost_usd=cost,
                    tool_calls=run_log.tool_calls,
                )
            )
            restartable = isinstance(exc, ProviderUnavailable | IncompleteAnswer)
            if not restartable or i == len(models) - 1:
                raise
            if on_restart is not None:
                on_restart(exc.log_code)
            continue
        if not attempts:
            return answer
        usage, cost = (answer.usage, answer.cost_usd)
        for attempt in attempts:
            usage, cost = _add((usage, cost), (attempt.usage, attempt.cost_usd))
        return answer.model_copy(
            update={
                "restarts": [a.log_code for a in attempts],
                "failed_attempts": list(attempts),
                "usage": usage,
                "cost_usd": cost,
                "latency_ms": (time.perf_counter() - start) * 1000,
            }
        )
    raise ValueError("no models to run the agent with")


def _answer(state: AgentState, start: float, checks: bool = False) -> AgentAnswer:
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
    usage, cost = total_usage(completions)
    return AgentAnswer(
        text=text,
        citations=citations,
        model_used=final.model,
        retriever_name="hybrid",
        usage=usage,
        latency_ms=(time.perf_counter() - start) * 1000,
        cost_usd=cost,
        finish_reason=final.finish_reason,
        abstained=abstained,
        has_uncited_claims=not abstained
        and has_uncited_claims(text, passages=len(passages), facts=len(facts)),
        degraded=state["degraded"],
        tool_calls=state["tool_records"],
        facts_used=facts,
        fact_citations=fact_citations,
        model_calls=len(completions),
        stopped_by=state["stopped_by"],  # type: ignore[arg-type]
        checks=checks,
        overrides=state["overrides"],
    )
