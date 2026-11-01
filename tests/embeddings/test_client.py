"""The embedding clients: batching, retries, the in-flight limit, the fake, and pricing."""

import hashlib
import json
import math
import threading
import time
from typing import Any

import httpx
import pytest

from filingcheck.embeddings import (
    MAX_BATCH_TEXTS,
    MAX_BATCH_TOKENS,
    MODEL,
    content_hash,
    estimate_tokens,
    make_batches,
)
from filingcheck.embeddings.fake import FakeEmbeddings
from filingcheck.embeddings.openai_client import (
    EmbeddingAPIError,
    MissingAPIKeyError,
    OpenAIEmbeddings,
)
from filingcheck.llm.pricing import PRICING, cost_usd

DIMS = 1536


def vectors_response(request: httpx.Request, reverse: bool = False) -> httpx.Response:
    inputs = json.loads(request.content)["input"]
    data = [{"index": i, "embedding": [float(i)] * DIMS} for i in range(len(inputs))]
    usage = {"prompt_tokens": 7 * len(inputs), "total_tokens": 7 * len(inputs)}
    return httpx.Response(200, json={"data": data[::-1] if reverse else data, "usage": usage})


def client(handler: Any, **kwargs: Any) -> OpenAIEmbeddings:
    return OpenAIEmbeddings(
        api_key="test-key", transport=httpx.MockTransport(handler), sleep=lambda s: None, **kwargs
    )


# ---------------------------------------------------------------- batching


def test_a_batch_holds_at_most_100_texts() -> None:
    texts = ["short text"] * 250
    batches = make_batches(texts)
    assert [len(b) for b in batches] == [100, 100, 50]
    assert [t for b in batches for t in b] == texts
    assert MAX_BATCH_TEXTS == 100


def test_a_batch_stays_under_8000_estimated_tokens() -> None:
    texts = [f"{i:04d}" + "x" * 2996 for i in range(20)]  # 3,000 characters = 1,000 tokens
    batches = make_batches(texts)
    assert all(sum(estimate_tokens(t) for t in b) <= MAX_BATCH_TOKENS for b in batches)
    assert [len(b) for b in batches] == [8, 8, 4]
    assert [t for b in batches for t in b] == texts


def test_a_text_over_the_token_limit_goes_alone() -> None:
    texts = ["a" * 30_000, "b" * 30]
    assert make_batches(texts) == [["a" * 30_000], ["b" * 30]]


def test_tokens_are_estimated_as_a_third_of_the_characters() -> None:
    assert estimate_tokens("x" * 900) == 300
    assert estimate_tokens("") == 1


def test_the_content_hash_is_the_sha256_hex_of_the_utf8_text() -> None:
    assert content_hash("Revenue") == hashlib.sha256(b"Revenue").hexdigest()
    assert content_hash("€ and é") == hashlib.sha256("€ and é".encode()).hexdigest()


# ---------------------------------------------------------------- the OpenAI client


def test_the_request_names_the_model_and_returns_vectors_in_input_order() -> None:
    seen: list[dict[str, Any]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(json.loads(request.content))
        assert request.headers["authorization"] == "Bearer test-key"
        assert str(request.url) == "https://api.openai.com/v1/embeddings"
        return vectors_response(request, reverse=True)

    embedder = client(handler)
    vectors = embedder.embed(["first", "second", "third"])
    assert seen[0]["model"] == MODEL == "text-embedding-3-small"
    assert seen[0]["input"] == ["first", "second", "third"]
    assert [v[0] for v in vectors] == [0.0, 1.0, 2.0]
    assert embedder.tokens_used == 21
    assert (embedder.model_name, embedder.dimensions) == (MODEL, DIMS)


def test_a_429_is_retried_with_backoff_then_succeeds() -> None:
    calls = []
    waits: list[float] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(1)
        if len(calls) <= 2:
            return httpx.Response(429, json={"error": {"message": "rate limited"}})
        return vectors_response(request)

    embedder = OpenAIEmbeddings(
        api_key="k", transport=httpx.MockTransport(handler), sleep=waits.append
    )
    assert len(embedder.embed(["a", "b"])) == 2
    assert len(calls) == 3
    assert waits == [1.0, 2.0]


def test_a_5xx_is_retried_and_gives_up_after_5_retries() -> None:
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(1)
        return httpx.Response(503, text="unavailable")

    with pytest.raises(EmbeddingAPIError, match="503"):
        client(handler).embed(["a"])
    assert len(calls) == 6  # the first try and 5 retries


def test_a_rejected_request_fails_at_once_with_the_api_message() -> None:
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(1)
        return httpx.Response(404, json={"error": {"message": "The model does not exist"}})

    with pytest.raises(EmbeddingAPIError, match="The model does not exist"):
        client(handler).embed(["a"])
    assert len(calls) == 1


def test_a_vector_of_the_wrong_size_is_refused() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"data": [{"index": 0, "embedding": [0.1] * 3}]})

    with pytest.raises(EmbeddingAPIError, match="3 dimensions"):
        client(handler).embed(["a"])


def test_a_missing_key_fails_on_first_use_not_when_created(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    embedder = OpenAIEmbeddings()  # creating it needs no key
    with pytest.raises(MissingAPIKeyError, match="OPENAI_API_KEY"):
        embedder.embed(["a"])


def test_at_most_4_requests_are_in_flight() -> None:
    lock = threading.Lock()
    state = {"now": 0, "most": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        with lock:
            state["now"] += 1
            state["most"] = max(state["most"], state["now"])
        time.sleep(0.02)
        with lock:
            state["now"] -= 1
        return vectors_response(request)

    texts = [f"text {i}" for i in range(1_000)]  # 10 batches of 100
    vectors = client(handler).embed(texts)
    assert len(vectors) == 1_000
    assert 1 < state["most"] <= 4


# ---------------------------------------------------------------- the fake


def test_the_fake_is_deterministic_and_unit_length() -> None:
    fake = FakeEmbeddings()
    a, b = fake.embed(["Walmart revenue in Mexico", "Walmart revenue in Mexico"])
    assert a == b and len(a) == DIMS
    assert math.isclose(sum(x * x for x in a), 1.0, rel_tol=1e-6)
    assert fake.calls == 1 and fake.tokens_used > 0


def test_the_fake_puts_texts_with_shared_words_closest() -> None:
    fake = FakeEmbeddings()
    query, near, far = fake.embed(
        [
            "risk factors for interest rates",
            "interest rates are a key risk factor",
            "the company sells shoes in Asia",
        ]
    )

    def cosine(x: list[float], y: list[float]) -> float:
        return sum(p * q for p, q in zip(x, y, strict=True))

    assert cosine(query, near) > cosine(query, far)


def test_the_fake_can_fail_after_a_number_of_calls() -> None:
    fake = FakeEmbeddings(fail_after_calls=2)
    fake.embed(["a"])
    fake.embed(["b"])
    with pytest.raises(RuntimeError, match="fake failure"):
        fake.embed(["c"])


# ---------------------------------------------------------------- pricing


def test_embedding_cost_comes_from_the_pricing_file() -> None:
    assert PRICING["checked_on"]
    assert cost_usd(MODEL, input_tokens=1_000_000) == pytest.approx(0.02)
    assert cost_usd(MODEL, input_tokens=11_000_000) == pytest.approx(0.22)


def test_an_unknown_model_has_no_price() -> None:
    with pytest.raises(KeyError, match="no-such-model"):
        cost_usd("no-such-model", input_tokens=10)
