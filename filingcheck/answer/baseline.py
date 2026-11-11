"""The plain-RAG baseline: hybrid search, numbered passages, one model call, no checks.

This is the "hybrid RAG, no agent, no checks" row of the evaluation; the agent and the
skeptical checks are measured against it.
"""

import time
from collections.abc import Iterator

from pydantic import BaseModel, Field

from filingcheck.answer.abstain import ABSTAIN, is_abstain
from filingcheck.answer.citations import (
    Citation,
    has_uncited_claims,
    parse_citations,
)
from filingcheck.labels import NumberLabel, SourcePassage, Sources, label_numbers
from filingcheck.llm import ChatModel, Completion, Message
from filingcheck.retrieval import Hit, Retriever, SearchResult

__all__ = ["ABSTAIN", "Answer", "answer_question", "is_abstain", "stream_answer"]
K = 8
MAX_TOKENS = 700  # the same cap the live API uses
SYSTEM_PROMPT = (
    "You answer questions about public companies from passages of their SEC 10-K filings.\n"
    "- Answer only from the numbered passages the user gives you.\n"
    "- Cite every claim with the number of its passage in square brackets, like [n].\n"
    f'- If the passages do not contain the answer, say "{ABSTAIN}" and nothing else.\n'
    "- Never guess a number.\n"
    "- When you give a figure, state the fiscal year and the period it covers."
)


class Answer(BaseModel):
    """A baseline answer with what produced it; `degraded` when keyword search answered alone."""

    text: str
    citations: list[Citation]
    model_used: str
    retriever_name: str
    usage: dict[str, int | None]
    latency_ms: float
    cost_usd: float | None
    finish_reason: str
    abstained: bool
    has_uncited_claims: bool
    degraded: bool
    # Each figure's label against the sources this answer used, computed after the model
    # finished; the model never sees them.
    number_labels: list[NumberLabel] = Field(default_factory=list)


def passage_header(hit: Hit) -> str:
    """For example "WMT, fiscal year 2025 (ended 2025-01-31), Item 1A"."""
    ended = f" (ended {hit.period_end.isoformat()})" if hit.period_end else ""
    return f"{hit.ticker}, fiscal year {hit.fiscal_year}{ended}, Item {hit.item}"


def build_messages(question: str, hits: list[Hit]) -> list[Message]:
    """The system rules, then the numbered passages and the question."""
    passages = "\n\n".join(
        f"[{n}] {passage_header(hit)}\n{hit.text}" for n, hit in enumerate(hits, 1)
    )
    user = f"Passages:\n\n{passages or '(none found)'}\n\nQuestion: {question}"
    return [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": user}]


def answer_question(
    question: str,
    *,
    retriever: Retriever,
    model: ChatModel,
    ticker: str | None = None,
    fiscal_year: int | None = None,
    k: int = K,
    max_tokens: int = MAX_TOKENS,
) -> Answer:
    """Search, ask the model with the top k passages, and read the citations back."""
    start = time.perf_counter()
    result = retriever.search(question, ticker=ticker, fiscal_year=fiscal_year, k=k)
    completion = model.complete(build_messages(question, result.hits), max_tokens=max_tokens)
    return _answer(completion, result, start)


def stream_answer(
    question: str,
    *,
    retriever: Retriever,
    model: ChatModel,
    ticker: str | None = None,
    fiscal_year: int | None = None,
    k: int = K,
    max_tokens: int = MAX_TOKENS,
) -> Iterator[str | Answer]:
    """Like `answer_question`, but yields the text as it arrives and then the `Answer`."""
    start = time.perf_counter()
    result = retriever.search(question, ticker=ticker, fiscal_year=fiscal_year, k=k)
    for event in model.stream(build_messages(question, result.hits), max_tokens=max_tokens):
        if isinstance(event, Completion):
            yield _answer(event, result, start)
        else:
            yield event


def _answer(completion: Completion, result: SearchResult, start: float) -> Answer:
    abstained = is_abstain(completion.text)
    return Answer(
        text=completion.text,
        citations=[] if abstained else parse_citations(completion.text, result.hits),
        model_used=completion.model,
        retriever_name=result.retriever,
        usage={
            "prompt_tokens": completion.prompt_tokens,
            "completion_tokens": completion.completion_tokens,
        },
        latency_ms=(time.perf_counter() - start) * 1000,
        cost_usd=completion.cost_usd,
        finish_reason=completion.finish_reason,
        abstained=abstained,
        has_uncited_claims=not abstained
        and has_uncited_claims(completion.text, passages=len(result.hits)),
        degraded=result.degraded,
        number_labels=baseline_labels(completion.text, result.hits),
    )


def baseline_labels(text: str, hits: list[Hit]) -> list[NumberLabel]:
    """The labels of a baseline answer: no facts, and the passages it was given as [1]..[k]."""
    passages = [SourcePassage(number=n, text=hit.text) for n, hit in enumerate(hits, 1)]
    return label_numbers(text, Sources(passages=passages))
