"""Embeddings for chunk search: the client interface, batching and the content hash.

The vectors are paid for once: every vector is cached by (model, content hash), so a chunk
whose text has not changed is never embedded twice.
"""

import hashlib
from typing import Protocol

MODEL = "text-embedding-3-small"
MAX_BATCH_TEXTS = 100
MAX_BATCH_TOKENS = 8_000
CHARS_PER_TOKEN = 3  # deliberately low: English text runs about 4, so estimates err high


class EmbeddingClient(Protocol):
    """Anything that turns texts into vectors of a fixed size."""

    model_name: str
    dimensions: int
    tokens_used: int  # input tokens billed so far

    def embed(self, texts: list[str]) -> list[list[float]]:
        """One vector per text, in the same order."""
        ...


def content_hash(text: str) -> str:
    """The SHA-256 hex digest of the UTF-8 text; the same value Postgres computes in 0004."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def estimate_tokens(text: str) -> int:
    """A safe upper estimate of a text's tokens, used for batching and the cost plan."""
    return max(1, len(text) // CHARS_PER_TOKEN)


def make_batches(
    texts: list[str], max_texts: int = MAX_BATCH_TEXTS, max_tokens: int = MAX_BATCH_TOKENS
) -> list[list[str]]:
    """Split texts, in order, into requests of at most `max_texts` texts and `max_tokens`.

    A single text over the token limit goes in a request of its own.
    """
    batches: list[list[str]] = []
    current: list[str] = []
    tokens = 0
    for text in texts:
        cost = estimate_tokens(text)
        if current and (len(current) == max_texts or tokens + cost > max_tokens):
            batches.append(current)
            current, tokens = [], 0
        current.append(text)
        tokens += cost
    if current:
        batches.append(current)
    return batches
