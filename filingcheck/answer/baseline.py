"""The plain-RAG baseline: hybrid search, numbered passages, one model call, no checks.

This is the "hybrid RAG, no agent, no checks" row of the evaluation; the agent and the
skeptical checks are measured against it.
"""

import re
import time

from pydantic import BaseModel

from filingcheck.answer.citations import Citation, has_uncited_claims, parse_citations
from filingcheck.llm import ChatModel, Message
from filingcheck.retrieval import Hit, Retriever

ABSTAIN = "I can't find this in the filings I have."
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
QUOTES = str.maketrans({"\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"'})
EMPHASIS_RE = re.compile(r"[*_`]")


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


def _normalize(text: str) -> str:
    text = EMPHASIS_RE.sub("", text.translate(QUOTES))
    return " ".join(text.split()).lower().rstrip(".!?").strip()


def is_abstain(text: str) -> bool:
    """True if the answer is the abstain sentence and nothing else, whatever its formatting."""
    return _normalize(text) == _normalize(ABSTAIN)


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
        has_uncited_claims=not abstained and has_uncited_claims(completion.text),
        degraded=result.degraded,
    )
