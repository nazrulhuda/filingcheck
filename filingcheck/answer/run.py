"""What `make ask` and the examples run share: the retriever, the settings line, the printout."""

import json
from typing import TYPE_CHECKING

import psycopg

from filingcheck.answer.baseline import MAX_TOKENS, Answer, K
from filingcheck.embeddings.openai_client import OpenAIEmbeddings
from filingcheck.llm import Completion, IncompleteAnswer, describe_settings
from filingcheck.retrieval import HybridRetriever, KeywordRetriever, VectorRetriever
from filingcheck.retrieval.query import QueryEmbedder

if TYPE_CHECKING:
    from filingcheck.agent import AgentAnswer, ToolCallRecord


def hybrid_retriever(conn: psycopg.Connection) -> HybridRetriever:
    """Hybrid search over the loaded chunks, embedding questions with the OpenAI model."""
    vector = VectorRetriever(conn, QueryEmbedder(OpenAIEmbeddings()))
    return HybridRetriever(vector, KeywordRetriever(conn))


def settings_line(model: str, *, filters: str, max_tokens: int = MAX_TOKENS) -> str:
    """The model and retrieval settings to write next to a saved result."""
    return f"{describe_settings(model, max_tokens)}; retriever hybrid, k {K}, {filters}"


def format_cost(cost: float | None) -> str:
    """Dollars to six places, or "unknown" when the provider sent no usage."""
    return "unknown" if cost is None else f"${cost:.6f}"


def format_incomplete(error: IncompleteAnswer) -> str:
    """An empty or cut-off reply, with the numbers needed to see why."""
    c = error.completion
    return "\n".join(
        [
            f"error: {error}",
            f"model: {c.model}",
            f"finish_reason: {c.finish_reason}",
            f"text so far: {c.text!r}",
            f"tokens: prompt {c.prompt_tokens}, completion {c.completion_tokens}",
            f"cost: {format_cost(c.cost_usd)}; usage as sent: {c.usage}",
        ]
    )


BASIS_WORDS = {
    "fact": "fact",
    "fact_other_period": "another period",
    "calculation": "calculation",
    "passage": "passage",
}


def format_labels(answer: Answer) -> list[str]:
    """One line per figure: its label and where it was found."""
    lines = ["Number labels:"]
    for label in answer.number_labels:
        if label.label == "verified" and label.basis is not None:
            words = f"Verified, {BASIS_WORDS[label.basis]} ({label.source})"
        elif label.label == "conflict":
            words = f"Conflict ({label.source}; the source says {label.cited_value})"
        else:
            words = "Unverified"
        lines.append(f"  {label.figure}: {words}")
    return lines if answer.number_labels else [*lines, "  (none)"]


def format_answer(answer: Answer, completion: Completion | None) -> str:
    """The answer, its citations and what it cost, for the terminal."""
    lines = [answer.text, "", "Citations:"]
    lines += [
        f"  {c.ticker} FY{c.fiscal_year} Item {c.item} (chunk {c.chunk_id}): {c.source_url}"
        for c in answer.citations
    ] or ["  (none)"]
    lines += format_labels(answer)
    lines += [
        "",
        f"model used: {answer.model_used}",
        f"tokens: prompt {answer.usage['prompt_tokens']}, "
        f"completion {answer.usage['completion_tokens']}",
        f"finish_reason: {answer.finish_reason}",
        f"cost: {format_cost(answer.cost_usd)}",
        f"degraded: {str(answer.degraded).lower()}",
        f"abstained: {str(answer.abstained).lower()}, "
        f"uncited figures: {str(answer.has_uncited_claims).lower()}",
        f"latency: {answer.latency_ms:.0f} ms",
    ]
    if completion is not None:
        lines.append(f"answer characters: {len(completion.text)}")
        lines.append(f"usage as sent: {completion.usage}")
        for name, value in sorted(completion.rate_limits.items()):
            lines.append(f"{name}: {value}")
    return "\n".join(lines)


def format_tool_call(record: "ToolCallRecord") -> str:
    """One tool call as the agent makes it, for the terminal."""
    filled = (
        f" (from the selection: {', '.join(record.defaults_applied)})"
        if record.defaults_applied
        else ""
    )
    return (
        f"-> {record.name}({json.dumps(record.arguments)}){filled} "
        f"[{record.status}, {record.duration_ms:.0f} ms]\n   {record.result_summary}"
    )


def format_agent_answer(answer: "AgentAnswer") -> str:
    """The agent's answer, its passage and fact citations, its calls and what it cost."""
    lines = [answer.text, "", "Passage citations:"]
    lines += [
        f"  [{c.number}] {c.ticker} FY{c.fiscal_year} Item {c.item} (chunk {c.chunk_id}): "
        f"{c.source_url}"
        for c in answer.citations
    ] or ["  (none)"]
    lines.append("Fact citations:")
    lines += [
        f"  [F{c.number}] {c.concept} = {c.value} {c.unit}, "
        f"{c.instant or f'{c.period_start} to {c.period_end}'}: {c.source_url}"
        for c in answer.fact_citations
    ] or ["  (none)"]
    lines += format_labels(answer)
    lines.append(f"checks: {'on' if answer.checks else 'off'}")
    for record in answer.overrides:
        options = f"; options: {', '.join(record.options)}" if record.options else ""
        lines.append(f"  {record.check}: {record.outcome}; {record.reason}{options}")
    lines += [
        "",
        f"model used: {answer.model_used}",
        f"model calls: {answer.model_calls}; tool calls: {len(answer.tool_calls)}"
        + (f"; stopped by the {answer.stopped_by} limit" if answer.stopped_by else ""),
        f"tokens: prompt {answer.usage['prompt_tokens']}, "
        f"completion {answer.usage['completion_tokens']}",
        f"finish_reason: {answer.finish_reason}",
        f"cost: {format_cost(answer.cost_usd)}",
        f"abstained: {str(answer.abstained).lower()}, "
        f"uncited figures: {str(answer.has_uncited_claims).lower()}",
        f"time: {answer.latency_ms / 1000:.1f} s",
    ]
    return "\n".join(lines)
