"""What `make ask` and the examples run share: the retriever, the settings line, the printout."""

import psycopg

from filingcheck.answer.baseline import MAX_TOKENS, Answer, K
from filingcheck.embeddings.openai_client import OpenAIEmbeddings
from filingcheck.llm import Completion, describe_settings
from filingcheck.retrieval import HybridRetriever, KeywordRetriever, VectorRetriever
from filingcheck.retrieval.query import QueryEmbedder


def hybrid_retriever(conn: psycopg.Connection) -> HybridRetriever:
    """Hybrid search over the loaded chunks, embedding questions with the OpenAI model."""
    vector = VectorRetriever(conn, QueryEmbedder(OpenAIEmbeddings()))
    return HybridRetriever(vector, KeywordRetriever(conn))


def settings_line(model: str, *, filters: str) -> str:
    """The model and retrieval settings to write next to a saved result."""
    return f"{describe_settings(model, MAX_TOKENS)}; retriever hybrid, k {K}, {filters}"


def format_cost(cost: float | None) -> str:
    """Dollars to six places, or "unknown" when the provider sent no usage."""
    return "unknown" if cost is None else f"${cost:.6f}"


def format_answer(answer: Answer, completion: Completion | None) -> str:
    """The answer, its citations and what it cost, for the terminal."""
    lines = [answer.text, "", "Citations:"]
    lines += [
        f"  {c.ticker} FY{c.fiscal_year} Item {c.item} (chunk {c.chunk_id}): {c.source_url}"
        for c in answer.citations
    ] or ["  (none)"]
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
