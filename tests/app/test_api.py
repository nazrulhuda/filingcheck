"""The API with a fake model, a fake retriever and an in-memory request log."""

import json
import time
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from fastapi.testclient import TestClient

from filingcheck.answer.baseline import ABSTAIN
from filingcheck.app.api import Services, create_app
from filingcheck.app.limits import TokenBucket, client_ip, hash_ip, nearest_example
from filingcheck.app.settings import MAX_BODY_BYTES, Settings
from filingcheck.app.stats import compute_stats, percentile
from filingcheck.app.store import CompanyInfo, ExampleAnswer, MemoryStore, RequestRow
from filingcheck.llm import ChatModel, FakeChat, IncompleteAnswer, ProviderUnavailable
from filingcheck.retrieval import Retriever
from tests.answer.test_baseline import FakeRetriever, ask

QUESTION = "What are Walmart's main risks in Mexico?"
SALT = "test-salt"
WALMART = CompanyInfo(ticker="WMT", name="Walmart Inc.", fiscal_years=[2024, 2025, 2026])


def settings(**overrides: Any) -> Settings:
    base: dict[str, Any] = {"ip_hash_salt": SALT, "cors_origins": ["http://localhost:3000"]}
    return Settings(**(base | overrides))


def make(
    model: ChatModel,
    *,
    store: MemoryStore | None = None,
    degraded: bool = False,
    model_ready: bool = True,
    **overrides: Any,
) -> tuple[TestClient, MemoryStore]:
    store = store or MemoryStore(companies=[WALMART])

    @contextmanager
    def retriever() -> Iterator[Retriever]:
        yield FakeRetriever(degraded=degraded)

    services = Services(
        model=model,
        primary_name="fake:chat",
        store=store,
        retriever=retriever,
        settings=settings(**overrides),
        model_ready=lambda: model_ready,
    )
    return TestClient(create_app(services)), store


def events(body: str) -> list[tuple[str, dict[str, Any]]]:
    """Server-sent events as (event name, data)."""
    result = []
    for block in body.strip().split("\n\n"):
        fields = dict(line.split(": ", 1) for line in block.splitlines())
        result.append((fields["event"], json.loads(fields["data"])))
    return result


# ---------------------------------------------------------------- /ask


def test_ask_returns_the_answer_with_a_request_id_and_logs_it() -> None:
    client, store = make(FakeChat(["Peso swings are a risk [1]."]))
    response = client.post("/ask", json={"question": QUESTION, "ticker": "WMT"})
    assert response.status_code == 200
    body = response.json()
    assert body["text"] == "Peso swings are a risk [1]." and body["citations"][0]["chunk_id"] == 101
    assert body["model_used"] == "fake:chat" and body["degraded"] is False
    (row,) = store.rows
    assert row.id == body["request_id"] and row.question == QUESTION and row.ticker == "WMT"
    assert row.model_used == "fake:chat" and row.prompt_tokens == 100 and row.error is None
    assert row.client_ip_hash == hash_ip("testclient", SALT)
    assert "testclient" not in row.client_ip_hash


def test_an_abstained_answer_has_no_citations_and_is_logged_as_abstained() -> None:
    client, store = make(FakeChat([ABSTAIN]))
    body = client.post("/ask", json={"question": QUESTION}).json()
    assert body["abstained"] is True and body["citations"] == []
    assert store.rows[0].abstained is True


def test_a_degraded_search_is_logged_as_degraded() -> None:
    client, store = make(FakeChat(["Peso swings [1]."]), degraded=True)
    assert client.post("/ask", json={"question": QUESTION}).json()["degraded"] is True
    assert store.rows[0].degraded is True


@pytest.mark.parametrize(
    "payload",
    [
        {"question": ""},
        {"question": "   "},
        {"question": "x" * 501},
        {"question": QUESTION, "fiscal_year": 1800},
        {"question": QUESTION, "max_tokens": 5000},
    ],
)
def test_bad_requests_are_refused_before_any_model_call(payload: dict[str, Any]) -> None:
    model = FakeChat([])
    client, store = make(model)
    assert client.post("/ask", json=payload).status_code == 422
    assert model.calls == [] and store.rows == []


# A question is at most 500 characters; a body over 16 KB is refused before it is read in full,
# so a stream of oversized posts cannot fill the small server's memory.
JSON = {"Content-Type": "application/json"}


@pytest.mark.parametrize("path", ["/ask", "/ask/stream"])
def test_a_body_over_16_kb_is_refused_by_its_length_header(path: str) -> None:
    model = FakeChat([])
    client, store = make(model)
    body = json.dumps({"question": "x" * MAX_BODY_BYTES}).encode()
    response = client.post(path, content=body, headers=JSON)
    assert response.status_code == 413
    assert "16 KB" in response.json()["detail"]
    assert model.calls == [] and store.rows == []


@pytest.mark.parametrize("path", ["/ask", "/ask/stream"])
def test_a_body_with_no_length_header_is_refused_once_it_passes_16_kb(path: str) -> None:
    model = FakeChat([])
    client, store = make(model)

    def chunks() -> Iterator[bytes]:
        yield b'{"question": "'
        for _ in range(32):
            yield b"x" * 1024
        yield b'"}'

    response = client.post(path, content=chunks(), headers=JSON)
    assert response.status_code == 413
    assert model.calls == [] and store.rows == []


def test_a_body_of_exactly_16_kb_is_read() -> None:
    client, _ = make(FakeChat(["Peso swings are a risk [1]."]))
    body = json.dumps({"question": QUESTION}).encode()
    body += b" " * (MAX_BODY_BYTES - len(body))  # JSON allows trailing spaces
    assert len(body) == 16 * 1024
    assert client.post("/ask", content=body, headers=JSON).status_code == 200


def test_the_model_gets_at_most_700_tokens() -> None:
    model = FakeChat(["Peso swings [1]."])
    client, _ = make(model)
    client.post("/ask", json={"question": QUESTION})
    assert model.calls[0]["max_tokens"] == 700


def test_a_provider_failure_returns_503_and_logs_only_provider_status_and_code() -> None:
    failure = ProviderUnavailable(
        "groq: HTTP 429: Rate limit reached in organization `org_01secret`",
        provider="groq",
        status=429,
        code="rate_limit_exceeded",
    )
    client, store = make(FakeChat([failure]))
    response = client.post("/ask", json={"question": QUESTION})
    assert response.status_code == 503 and "org_01secret" not in response.text
    assert response.json()["request_id"] == store.rows[0].id
    assert store.rows[0].error == "groq 429 rate_limit_exceeded"
    assert store.rows[0].model_used is None


# ---------------------------------------------------------------- limits


def test_the_21st_question_from_one_address_in_an_hour_gets_429() -> None:
    model = FakeChat([f"Answer {n} [1]." for n in range(21)])
    client, _ = make(model)
    codes = [client.post("/ask", json={"question": QUESTION}).status_code for _ in range(21)]
    assert codes == [200] * 20 + [429] and len(model.calls) == 20


def test_the_request_log_stops_an_address_that_the_memory_limit_forgot() -> None:
    store = MemoryStore()
    now = datetime.now(UTC)
    for n in range(20):
        store.log_request(row(n, created_at=now - timedelta(minutes=n)))
    model = FakeChat(["unused"])
    client, _ = make(model, store=store)
    assert client.post("/ask", json={"question": QUESTION}).status_code == 429
    assert model.calls == []


def test_after_the_daily_cap_the_nearest_cached_example_or_a_429_is_returned() -> None:
    cached = ask("Cached: peso swings [1].").model_dump()
    store = MemoryStore(examples=[ExampleAnswer(question=QUESTION, answer=cached)])
    model = FakeChat(["First [1].", "Second [1]."])
    client, _ = make(model, store=store, daily_cap=2)
    for _ in range(2):
        assert client.post("/ask", json={"question": "Walmart revenue?"}).status_code == 200
    reworded = "What are the main risks for Walmart in Mexico?"
    similar = client.post("/ask", json={"question": reworded})
    assert similar.status_code == 200
    assert similar.json()["cached"] is True and similar.json()["text"] == "Cached: peso swings [1]."
    unrelated = client.post("/ask", json={"question": "Who audits Nvidia?"})
    assert unrelated.status_code == 429 and "today's limit" in unrelated.json()["detail"]
    assert len(model.calls) == 2
    assert [r.error for r in store.rows[-2:]] == ["refused:daily_cap", "refused:daily_cap"]


# ---------------------------------------------------------------- /ask/stream


def test_the_stream_sends_tokens_then_a_final_event_with_citations_and_usage() -> None:
    client, store = make(FakeChat(["Peso swings are a risk [1]."]))
    response = client.post("/ask/stream", json={"question": QUESTION})
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    sent = events(response.text)
    tokens = [data["text"] for name, data in sent if name == "token"]
    name, final = sent[-1]
    assert name == "final" and "".join(tokens) == "Peso swings are a risk [1]."
    assert final["answer"]["citations"][0]["chunk_id"] == 101
    assert final["answer"]["usage"] == {"prompt_tokens": 100, "completion_tokens": 20}
    assert final["request_id"] == store.rows[0].id


def test_a_stream_that_fails_ends_with_an_error_event_and_no_raw_message() -> None:
    cut = IncompleteAnswer(
        "fake: incomplete answer in org_01secret",
        _completion(),
        provider="fake",
        code="incomplete_length",
    )
    client, store = make(FakeChat([cut]))
    sent = events(client.post("/ask/stream", json={"question": QUESTION}).text)
    assert sent[-1][0] == "error" and "org_01secret" not in json.dumps(sent)
    assert store.rows[0].error == "fake - incomplete_length"


def test_the_stream_is_refused_with_429_like_ask() -> None:
    model = FakeChat([f"A {n} [1]." for n in range(20)])
    client, _ = make(model, per_ip_per_hour=1)
    assert client.post("/ask/stream", json={"question": QUESTION}).status_code == 200
    assert client.post("/ask/stream", json={"question": QUESTION}).status_code == 429


# ------------------------------------------------------- health, companies, examples, stats


def test_health_is_cheap_and_reports_whether_a_model_is_configured() -> None:
    client, store = make(FakeChat([]))
    response = client.get("/health")
    assert response.status_code == 200 and response.json()["status"] == "ok"
    assert store.calls == []
    not_ready, _ = make(FakeChat([]), model_ready=False)
    assert not_ready.get("/health").status_code == 503


def test_deep_health_fails_when_embeddings_meta_is_empty() -> None:
    client, _ = make(FakeChat([]), store=MemoryStore(embeddings_meta=False))
    response = client.get("/health/deep")
    assert response.status_code == 503 and response.json()["embeddings"] is False
    ok, _ = make(FakeChat([]), store=MemoryStore(embeddings_meta=True))
    assert ok.get("/health/deep").status_code == 200


def test_companies_and_examples_come_from_the_store() -> None:
    cached = ask("Cached [1].").model_dump()
    example = ExampleAnswer(question=QUESTION, answer=cached)
    store = MemoryStore(companies=[WALMART], examples=[example])
    client, _ = make(FakeChat([]), store=store)
    assert client.get("/companies").json() == [
        {"ticker": "WMT", "name": "Walmart Inc.", "fiscal_years": [2024, 2025, 2026]}
    ]
    (example,) = client.get("/examples").json()
    assert example["question"] == QUESTION and example["answer"]["text"] == "Cached [1]."


def test_stats_summarize_the_last_24_hours_of_the_request_log() -> None:
    client, store = make(FakeChat(["A [1].", ABSTAIN]))
    client.post("/ask", json={"question": QUESTION})
    client.post("/ask", json={"question": QUESTION})
    store.log_request(row(99, created_at=datetime.now(UTC) - timedelta(hours=30)))
    stats = client.get("/stats").json()
    assert stats["requests"] == 2 and stats["answered"] == 2
    assert stats["abstain_rate"] == 0.5 and stats["fallbacks"] == 0 and stats["cost_usd"] == 0.0


def test_cors_allows_only_the_listed_origins() -> None:
    client, _ = make(FakeChat([]), cors_origins=["https://demo.example.app"])
    allowed = client.get("/health", headers={"Origin": "https://demo.example.app"})
    assert allowed.headers.get("access-control-allow-origin") == "https://demo.example.app"
    other = client.get("/health", headers={"Origin": "https://elsewhere.example"})
    assert "access-control-allow-origin" not in other.headers


# ---------------------------------------------------------------- the pieces


def row(n: int, **fields: Any) -> RequestRow:
    base: dict[str, Any] = {
        "id": f"00000000-0000-0000-0000-{n:012d}",
        "created_at": datetime.now(UTC),
        "question_hash": "h",
        "question": QUESTION,
        "model_used": "fake:chat",
        "retriever": "hybrid",
        "latency_ms": 100.0 * (n + 1),
        "prompt_tokens": 100,
        "completion_tokens": 20,
        "cost_usd": 0.001,
        "abstained": False,
        "client_ip_hash": hash_ip("testclient", SALT),
    }
    return RequestRow(**(base | fields))


def _completion() -> Any:
    from filingcheck.llm import Completion

    return Completion(
        text="Peso",
        prompt_tokens=10,
        completion_tokens=700,
        model="fake:chat",
        latency_ms=1.0,
        cost_usd=0.0,
        finish_reason="length",
    )


def test_stats_count_fallbacks_errors_refusals_unknown_costs_and_percentiles() -> None:
    rows = [
        row(0),
        row(1, model_used="gemini:gemini-3.5-flash-lite", cost_usd=None, degraded=True),
        row(2, abstained=True),
        row(3, model_used=None, error="groq 429 rate_limit_exceeded", latency_ms=None),
        row(4, model_used=None, error="refused:daily_cap", latency_ms=None),
    ]
    stats = compute_stats(rows, primary="fake:chat")
    assert (stats["requests"], stats["answered"], stats["errors"]) == (5, 3, 1)
    assert stats["refused_daily_cap"] == 1 and stats["fallbacks"] == 1 and stats["degraded"] == 1
    assert stats["unknown_cost"] == 1 and stats["cost_usd"] == pytest.approx(0.002)
    assert stats["abstain_rate"] == pytest.approx(1 / 3)
    assert stats["latency_ms_p50"] == 200.0 and stats["latency_ms_p95"] == pytest.approx(290.0)
    assert percentile([], 50) is None


def test_the_token_bucket_refills_over_the_hour() -> None:
    now = [0.0]
    bucket = TokenBucket(capacity=2, per_seconds=3600, clock=lambda: now[0])
    assert [bucket.take("a"), bucket.take("a"), bucket.take("a"), bucket.take("b")] == [
        True,
        True,
        False,
        True,
    ]
    now[0] = 1800.0
    assert bucket.take("a") and not bucket.take("a")


def test_the_client_address_comes_from_the_trusted_forwarding_hop_only() -> None:
    headers = {"x-forwarded-for": "1.1.1.1, 2.2.2.2, 3.3.3.3"}
    assert client_ip("10.0.0.1", headers, hops=0) == "10.0.0.1"
    assert client_ip("10.0.0.1", headers, hops=1) == "3.3.3.3"
    assert client_ip("10.0.0.1", headers, hops=2) == "2.2.2.2"
    assert client_ip("10.0.0.1", {}, hops=1) == "10.0.0.1"
    assert client_ip(None, {}, hops=0) == "unknown"
    assert hash_ip("1.1.1.1", "a") != hash_ip("1.1.1.1", "b")
    assert "1.1.1.1" not in hash_ip("1.1.1.1", "a")


CF = "cf-connecting-ip"


def test_with_a_client_ip_header_set_the_address_comes_from_that_header_only() -> None:
    # On Render, Cloudflare overwrites CF-Connecting-IP on every request but only appends to
    # X-Forwarded-For, whose first entries a caller can write.
    headers = {CF: "203.0.113.7", "x-forwarded-for": "6.6.6.6, 203.0.113.7, 10.0.0.2"}
    assert client_ip("10.0.0.1", headers, hops=0, header=CF) == "203.0.113.7"
    assert client_ip("10.0.0.1", headers, hops=2, header=CF) == "203.0.113.7"
    assert client_ip("10.0.0.1", {CF: " 203.0.113.7 "}, hops=0, header=CF) == "203.0.113.7"


def test_with_a_client_ip_header_set_but_missing_the_connection_address_is_used() -> None:
    forged_only = {"x-forwarded-for": "6.6.6.6, 7.7.7.7"}
    assert client_ip("10.0.0.1", forged_only, hops=1, header=CF) == "10.0.0.1"
    assert client_ip("10.0.0.1", {CF: "  "}, hops=0, header=CF) == "10.0.0.1"
    assert client_ip(None, {}, hops=0, header=CF) == "unknown"


def test_with_no_client_ip_header_set_the_header_is_ignored() -> None:
    headers = {CF: "6.6.6.6", "x-forwarded-for": "1.1.1.1, 2.2.2.2"}
    assert client_ip("10.0.0.1", headers, hops=0) == "10.0.0.1"
    assert client_ip("10.0.0.1", headers, hops=1, header=None) == "2.2.2.2"


def test_the_request_log_counts_the_address_from_the_client_ip_header() -> None:
    client, store = make(FakeChat(["Peso [1].", "Peso [1]."]), client_ip_header=CF)
    forged = {"CF-Connecting-IP": "203.0.113.7", "X-Forwarded-For": "6.6.6.6"}
    assert client.post("/ask", json={"question": QUESTION}, headers=forged).status_code == 200
    assert client.post("/ask", json={"question": QUESTION}).status_code == 200
    first, second = store.rows
    assert first.client_ip_hash == hash_ip("203.0.113.7", SALT)
    assert second.client_ip_hash == hash_ip("testclient", SALT)


def test_the_nearest_example_needs_most_of_its_words() -> None:
    examples = [
        ExampleAnswer(question=QUESTION, answer={}),
        ExampleAnswer(question="Who audits Apple?", answer={}),
    ]
    assert nearest_example("Walmart's main risks in Mexico?", examples) is examples[0]
    assert nearest_example("Who audits Nvidia?", examples) is None
    assert nearest_example("anything", []) is None


def test_settings_come_from_the_environment() -> None:
    env = {
        "FC_DAILY_CAP": "30",
        "FC_CORS_ORIGINS": "http://localhost:3000, https://demo.example.app",
        "FC_FORWARDED_HOPS": "1",
        "FC_IP_HASH_SALT": "s",
        "FC_CLIENT_IP_HEADER": " CF-Connecting-IP ",
    }
    s = Settings.from_env(env)
    assert (s.daily_cap, s.forwarded_hops, s.ip_hash_salt) == (30, 1, "s")
    assert s.client_ip_header == "cf-connecting-ip"
    assert s.cors_origins == ["http://localhost:3000", "https://demo.example.app"]
    defaults = Settings.from_env({})
    assert defaults.client_ip_header is None
    assert defaults.daily_cap == 65 and defaults.per_ip_per_hour == 20 and defaults.ip_hash_salt


# ---------------------------------------------------------------- review fixes


def test_an_abandoned_stream_is_logged_and_counts_toward_the_daily_cap() -> None:
    long_answer = " ".join(["Peso swings are a risk [1]."] * 20)
    client, store = make(FakeChat([long_answer]), daily_cap=1)
    with client.stream("POST", "/ask/stream", json={"question": QUESTION}) as response:
        lines = response.iter_lines()
        assert next(lines).startswith("event: token")
    for _ in range(50):  # the server notices the closed stream on its own thread
        if store.rows:
            break
        time.sleep(0.02)
    (logged,) = store.rows
    assert logged.error == "client_disconnected" and logged.latency_ms is not None
    assert store.count_model_requests(datetime.now(UTC) - timedelta(hours=1)) == 1
    refused = client.post("/ask", json={"question": "Who audits Nvidia?"})
    assert refused.status_code == 429


def test_a_stream_read_to_the_end_is_logged_once() -> None:
    client, store = make(FakeChat(["Peso swings are a risk [1]."]))
    client.post("/ask/stream", json={"question": QUESTION})
    assert len(store.rows) == 1 and store.rows[0].error is None


def test_companies_and_examples_are_read_from_the_store_once() -> None:
    client, store = make(FakeChat([]))
    for _ in range(3):
        client.get("/companies")
        client.get("/examples")
        client.get("/stats")
    assert store.calls.count("companies") == 1 and store.calls.count("examples") == 1
    assert store.calls.count("requests_since") == 3


def test_examples_carry_the_ticker_and_fiscal_year_they_were_asked_with() -> None:
    cached = ask("Cached [1].").model_dump()
    example = ExampleAnswer(question=QUESTION, ticker="WMT", fiscal_year=2026, answer=cached)
    client, _ = make(FakeChat([]), store=MemoryStore(examples=[example]))
    (served,) = client.get("/examples").json()
    assert (served["ticker"], served["fiscal_year"]) == ("WMT", 2026)


# ---------------------------------------------------------------- Day 12 review: cached answers


def capped(daily_cap: int = 0) -> tuple[TestClient, MemoryStore]:
    cached = ask("Cached: peso swings [1].").model_dump()
    example = ExampleAnswer(question=QUESTION, ticker="WMT", fiscal_year=2026, answer=cached)
    return make(FakeChat([]), store=MemoryStore(examples=[example]), daily_cap=daily_cap)


EXAMPLE_REF = {"question": QUESTION, "ticker": "WMT", "fiscal_year": 2026}


def test_a_cached_answer_names_the_example_question_it_answers() -> None:
    client, _ = capped()
    body = client.post("/ask", json={"question": "Main risks for Walmart in Mexico?"}).json()
    assert body["cached"] is True and body["example"] == EXAMPLE_REF
    assert body["text"] == "Cached: peso swings [1]."


def test_a_cached_stream_names_the_example_question_it_answers() -> None:
    client, _ = capped()
    response = client.post("/ask/stream", json={"question": "Main risks for Walmart in Mexico?"})
    sent = events(response.text)
    name, final = sent[-1]
    assert name == "final" and final["cached"] is True and final["example"] == EXAMPLE_REF
    assert final["answer"]["text"] == "Cached: peso swings [1]."


def test_a_normal_answer_is_not_cached_and_names_no_example() -> None:
    client, _ = make(FakeChat(["Peso swings [1].", "Peso swings [1]."]))
    body = client.post("/ask", json={"question": QUESTION}).json()
    assert body["cached"] is False and body["example"] is None
    final = events(client.post("/ask/stream", json={"question": QUESTION}).text)[-1][1]
    assert final["cached"] is False and final["example"] is None
