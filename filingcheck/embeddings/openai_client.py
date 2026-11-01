"""OpenAI embeddings over plain HTTP: batched, retried, with at most 4 requests in flight."""

import os
import re
import threading
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import httpx

from filingcheck.db import EMBEDDING_DIMENSIONS
from filingcheck.embeddings import MODEL, make_batches

API_URL = "https://api.openai.com/v1/embeddings"
MAX_IN_FLIGHT = 4
MAX_RETRIES = 5
BACKOFF_SECONDS = 1.0  # waits 1, 2, 4, 8 and 16 seconds, or longer if the API asks
MAX_WAIT_SECONDS = 60.0  # never wait longer than this, whatever the API asks
DURATION_RE = re.compile(r"(\d+(?:\.\d+)?)(ms|s|m|h)")
DURATION_UNITS = {"ms": 0.001, "s": 1.0, "m": 60.0, "h": 3600.0}


class MissingAPIKeyError(RuntimeError):
    """OPENAI_API_KEY is not set; it belongs in `.env`."""


class EmbeddingAPIError(RuntimeError):
    """The embeddings API refused a request or kept failing after every retry."""


class OpenAIEmbeddings:
    """`text-embedding-3-small` vectors of 1536 dimensions.

    The key is read from the environment (`.env` is loaded by the command line) when the
    first request is made, not when the client is created, so code that never embeds
    needs no key.
    """

    def __init__(
        self,
        model: str = MODEL,
        dimensions: int = EMBEDDING_DIMENSIONS,
        *,
        api_key: str | None = None,
        transport: httpx.BaseTransport | None = None,
        sleep: Callable[[float], None] = time.sleep,
        max_in_flight: int = MAX_IN_FLIGHT,
    ) -> None:
        self.model_name = model
        self.dimensions = dimensions
        self.tokens_used = 0
        self._api_key = api_key
        self._transport = transport
        self._sleep = sleep
        self._max_in_flight = max_in_flight
        self._slots = threading.Semaphore(max_in_flight)
        self._lock = threading.Lock()
        self._http: httpx.Client | None = None

    def embed(self, texts: list[str]) -> list[list[float]]:
        """One vector per text, in order; large inputs are split into batches."""
        batches = make_batches(texts)
        if len(batches) == 1:
            return self._request(batches[0])
        with ThreadPoolExecutor(max_workers=self._max_in_flight) as pool:
            results = list(pool.map(self._request, batches))
        return [vector for batch in results for vector in batch]

    def _client(self) -> httpx.Client:
        with self._lock:
            if self._http is None:
                key = (self._api_key or os.environ.get("OPENAI_API_KEY", "")).strip()
                if not key:
                    raise MissingAPIKeyError(
                        "OPENAI_API_KEY is not set. Add it to .env (see .env.example)."
                    )
                self._http = httpx.Client(
                    headers={"Authorization": f"Bearer {key}"},
                    timeout=60.0,
                    transport=self._transport,
                )
            return self._http

    def _request(self, batch: list[str]) -> list[list[float]]:
        http = self._client()
        problem = ""
        asked_wait = 0.0  # how long the API said to wait before trying again
        for attempt in range(MAX_RETRIES + 1):
            if attempt:
                backoff = BACKOFF_SECONDS * 2 ** (attempt - 1)
                self._sleep(min(max(backoff, asked_wait), MAX_WAIT_SECONDS))
            with self._slots:
                try:
                    response = http.post(API_URL, json={"model": self.model_name, "input": batch})
                except httpx.TransportError as exc:
                    problem = f"{type(exc).__name__}: {exc}"
                    asked_wait = 0.0
                    continue
            if response.status_code == 429 and _error_code(response) == "insufficient_quota":
                raise EmbeddingAPIError(f"HTTP 429, quota exhausted: {_message(response)}")
            if response.status_code == 429 or response.status_code >= 500:
                problem = f"HTTP {response.status_code}: {_message(response)}"
                asked_wait = _asked_wait(response)
                continue
            if response.status_code >= 400:
                raise EmbeddingAPIError(
                    f"HTTP {response.status_code} from the embeddings API: {_message(response)}"
                )
            return self._vectors(response.json(), len(batch))
        raise EmbeddingAPIError(f"the embeddings API kept failing ({problem}); gave up")

    def _vectors(self, body: dict[str, Any], expected: int) -> list[list[float]]:
        data = sorted(body["data"], key=lambda row: row["index"])
        vectors = [row["embedding"] for row in data]
        if len(vectors) != expected:
            raise EmbeddingAPIError(f"asked for {expected} vectors, got {len(vectors)}")
        for vector in vectors:
            if len(vector) != self.dimensions:
                raise EmbeddingAPIError(
                    f"got a vector of {len(vector)} dimensions, expected {self.dimensions}"
                )
        with self._lock:
            self.tokens_used += int(body.get("usage", {}).get("prompt_tokens", 0))
        return vectors


def _message(response: httpx.Response) -> str:
    try:
        return str(response.json()["error"]["message"])
    except (ValueError, KeyError, TypeError):
        return response.text[:300]


def _error_code(response: httpx.Response) -> str | None:
    try:
        code = response.json()["error"].get("code")
    except (ValueError, KeyError, TypeError, AttributeError):
        return None
    return str(code) if code else None


def _asked_wait(response: httpx.Response) -> float:
    """The longest wait the response asks for, in seconds (0 if it asks for none).

    `retry-after` is in seconds; the x-ratelimit-reset headers read like "35.147s" or
    "1m2s" or "6ms".
    """
    waits = []
    retry_after = response.headers.get("retry-after", "")
    if retry_after.replace(".", "", 1).isdigit():
        waits.append(float(retry_after))
    for header in ("x-ratelimit-reset-tokens", "x-ratelimit-reset-requests"):
        parts = DURATION_RE.findall(response.headers.get(header, ""))
        if parts:
            waits.append(sum(float(n) * DURATION_UNITS[unit] for n, unit in parts))
    return max(waits, default=0.0)
