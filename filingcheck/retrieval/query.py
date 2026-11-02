"""Question embeddings, with a small in-memory cache: the same question twice costs nothing."""

from collections import OrderedDict

from filingcheck.embeddings import EmbeddingClient

CACHE_SIZE = 256


class QueryEmbedder:
    """Embeds one question at a time and remembers the most recent ones."""

    def __init__(self, client: EmbeddingClient, maxsize: int = CACHE_SIZE) -> None:
        self.client = client
        self.maxsize = maxsize
        self._cache: OrderedDict[str, list[float]] = OrderedDict()

    @property
    def model_name(self) -> str:
        """The embedding model; it must match the one that embedded the chunks."""
        return self.client.model_name

    @property
    def tokens_used(self) -> int:
        """Tokens billed for questions so far."""
        return self.client.tokens_used

    def prime(self, text: str, vector: list[float]) -> None:
        """Put a known vector in the cache (saved query vectors), so it is never re-embedded."""
        self._cache[text] = vector
        if len(self._cache) > self.maxsize:
            self._cache.popitem(last=False)

    def embed(self, text: str) -> list[float]:
        """The question's vector, from the cache when it was asked recently."""
        if text in self._cache:
            self._cache.move_to_end(text)
            return self._cache[text]
        vector = self.client.embed([text])[0]
        self._cache[text] = vector
        if len(self._cache) > self.maxsize:
            self._cache.popitem(last=False)
        return vector
