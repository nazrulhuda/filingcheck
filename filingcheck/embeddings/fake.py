"""Deterministic embeddings for tests: no network, and texts that share words are close."""

import hashlib
import math
import re

from filingcheck.db import EMBEDDING_DIMENSIONS
from filingcheck.embeddings import estimate_tokens

WORD_RE = re.compile(r"[a-z0-9]+")


class FakeEmbeddings:
    """Hashes each word to one dimension, so texts with words in common point the same way.

    `fail_after_calls` makes every call after that many raise, to test resuming a crashed run.
    """

    def __init__(
        self,
        model_name: str = "fake-embeddings",
        dimensions: int = EMBEDDING_DIMENSIONS,
        fail_after_calls: int | None = None,
    ) -> None:
        self.model_name = model_name
        self.dimensions = dimensions
        self.fail_after_calls = fail_after_calls
        self.calls = 0
        self.tokens_used = 0
        self.texts_embedded: list[str] = []

    def embed(self, texts: list[str]) -> list[list[float]]:
        """One unit-length vector per text."""
        self.calls += 1
        if self.fail_after_calls is not None and self.calls > self.fail_after_calls:
            raise RuntimeError(f"fake failure on call {self.calls}")
        self.tokens_used += sum(estimate_tokens(t) for t in texts)
        self.texts_embedded += texts
        return [self.vector(text) for text in texts]

    def vector(self, text: str) -> list[float]:
        """The vector of one text: word counts hashed into the dimensions, then normalized."""
        values = [0.0] * self.dimensions
        for word in WORD_RE.findall(text.lower()) or [text]:
            digest = hashlib.sha256(word.encode("utf-8")).digest()
            values[int.from_bytes(digest[:4], "big") % self.dimensions] += 1.0
        norm = math.sqrt(sum(v * v for v in values)) or 1.0
        return [v / norm for v in values]
