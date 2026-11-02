"""The HTTP API: /ask, /ask/stream, /health, /companies, /examples and /stats.

Questions go through the plain-RAG baseline with the model router in live mode. Every
question that reaches the limits is logged; a provider failure is logged as a short code
(provider, HTTP status, the provider's error code) and never as the provider's message.
"""

import functools
import hashlib
import json
import logging
import os
import uuid
from collections.abc import Callable, Iterator
from contextlib import AbstractContextManager, contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, ConfigDict, Field

from filingcheck.answer.baseline import Answer, answer_question, stream_answer
from filingcheck.app.limits import BodySizeLimit, TokenBucket, client_ip, hash_ip, nearest_example
from filingcheck.app.settings import MAX_QUESTION_CHARS, Settings
from filingcheck.app.stats import compute_stats
from filingcheck.app.store import (
    REFUSED,
    CompanyInfo,
    ExampleAnswer,
    PostgresStore,
    RequestRow,
    Store,
)
from filingcheck.db import connect
from filingcheck.embeddings.openai_client import OpenAIEmbeddings
from filingcheck.llm import ChatModel, IncompleteAnswer, ProviderError, router_from_env
from filingcheck.paths import REPO_ROOT
from filingcheck.retrieval import HybridRetriever, KeywordRetriever, Retriever, VectorRetriever
from filingcheck.retrieval.query import QueryEmbedder

log = logging.getLogger(__name__)

RATE_LIMITED = "Too many questions from your address; the limit is {n} an hour."
DAILY_CAP = "The demo has reached today's limit of questions; please come back tomorrow."
UNAVAILABLE = "The language models are busy or unavailable right now; please try again soon."
CUT_OFF = "The answer was cut off before it finished; please try again."
DISCONNECTED = "client_disconnected"  # error code of a stream the visitor abandoned


@dataclass
class Services:
    """Everything the API calls; tests pass fakes."""

    model: ChatModel
    primary_name: str
    store: Store
    retriever: Callable[[], AbstractContextManager[Retriever]]
    settings: Settings
    model_ready: Callable[[], bool]


class AskRequest(BaseModel):
    """A question, optionally narrowed to one company and fiscal year."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    question: str = Field(min_length=1, max_length=MAX_QUESTION_CHARS)
    ticker: str | None = Field(default=None, pattern=r"^[A-Za-z.\-]{1,10}$")
    fiscal_year: int | None = Field(default=None, ge=1990, le=2100)


def default_services() -> Services:
    """The real model router (live mode), Postgres and hybrid search, from the environment."""
    load_dotenv(REPO_ROOT / ".env")
    router = router_from_env("live")
    embedder = QueryEmbedder(OpenAIEmbeddings())

    @contextmanager
    def retriever() -> Iterator[Retriever]:
        with connect() as conn:
            yield HybridRetriever(VectorRetriever(conn, embedder), KeywordRetriever(conn))

    key_env = getattr(router.primary, "api_key_env", "")
    return Services(
        model=router,
        primary_name=router.primary.name,
        store=PostgresStore(),
        retriever=retriever,
        settings=Settings.from_env(),
        model_ready=lambda: bool(os.environ.get(key_env, "").strip()),
    )


def create_app(services: Services | None = None) -> FastAPI:
    """The FastAPI app around the given services (the real ones when none are given)."""
    services = services or default_services()
    settings = services.settings
    store = services.store
    bucket = TokenBucket(settings.per_ip_per_hour, 3600)
    app = FastAPI(title="FilingCheck API")
    app.add_middleware(BodySizeLimit)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )

    def new_row(request_id: str, body: AskRequest, ip_hash: str, **fields: Any) -> RequestRow:
        return RequestRow(
            id=request_id,
            created_at=datetime.now(UTC),
            question_hash=hashlib.sha256(body.question.lower().encode()).hexdigest(),
            question=body.question,
            ticker=body.ticker,
            fiscal_year=body.fiscal_year,
            client_ip_hash=ip_hash,
            **fields,
        )

    def answer_fields(answer: Answer) -> dict[str, Any]:
        return {
            "model_used": answer.model_used,
            "retriever": answer.retriever_name,
            "degraded": answer.degraded,
            "latency_ms": answer.latency_ms,
            "prompt_tokens": answer.usage.get("prompt_tokens"),
            "completion_tokens": answer.usage.get("completion_tokens"),
            "cost_usd": answer.cost_usd,
            "abstained": answer.abstained,
        }

    # Companies change only on a re-pin and examples only on `make examples`; reading them
    # once per process keeps page loads and bots from waking the database (a restart reloads).
    @functools.cache
    def cached_companies() -> list[CompanyInfo]:
        return store.companies()

    @functools.cache
    def cached_examples() -> list[ExampleAnswer]:
        return store.examples()

    def save(row: RequestRow) -> None:
        try:
            store.log_request(row)
        except Exception:  # the answer still goes out if the log is down
            log.exception("could not write request %s to the request log", row.id)

    def admit(
        request: Request, body: AskRequest, request_id: str
    ) -> tuple[str, JSONResponse | ExampleAnswer | None]:
        """The hashed address, and a refusal or a cached answer if the question is not let in."""
        peer = request.client.host if request.client else None
        ip_hash = hash_ip(
            client_ip(peer, request.headers, settings.forwarded_hops, settings.client_ip_header),
            settings.ip_hash_salt,
        )
        limited = JSONResponse(
            {"detail": RATE_LIMITED.format(n=settings.per_ip_per_hour)}, status_code=429
        )
        if not bucket.take(ip_hash):
            return ip_hash, limited
        now = datetime.now(UTC)
        if (
            store.count_model_requests(now - timedelta(hours=1), ip_hash)
            >= settings.per_ip_per_hour
        ):
            return ip_hash, limited
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        if store.count_model_requests(today) < settings.daily_cap:
            return ip_hash, None
        save(new_row(request_id, body, ip_hash, error=REFUSED + "daily_cap"))
        example = nearest_example(body.question, cached_examples())
        if example is None:
            return ip_hash, JSONResponse({"detail": DAILY_CAP}, status_code=429)
        return ip_hash, example

    @app.post("/ask", response_model=None)
    def ask(body: AskRequest, request: Request) -> JSONResponse | dict[str, Any]:
        request_id = str(uuid.uuid4())
        ip_hash, refused = admit(request, body, request_id)
        if isinstance(refused, JSONResponse):
            return refused
        if refused is not None:  # a saved example's answer after the daily cap
            return {
                "request_id": request_id,
                "cached": True,
                "example": example_ref(refused),
                **refused.answer,
            }
        start = datetime.now(UTC)
        try:
            with services.retriever() as retriever:
                answer = answer_question(
                    body.question,
                    retriever=retriever,
                    model=services.model,
                    ticker=body.ticker,
                    fiscal_year=body.fiscal_year,
                )
        except ProviderError as exc:
            latency = (datetime.now(UTC) - start).total_seconds() * 1000
            save(new_row(request_id, body, ip_hash, error=exc.log_code, latency_ms=latency))
            return JSONResponse({"detail": UNAVAILABLE, "request_id": request_id}, status_code=503)
        save(new_row(request_id, body, ip_hash, **answer_fields(answer)))
        return {
            "request_id": request_id,
            "cached": False,
            "example": None,
            **answer.model_dump(),
        }

    @app.post("/ask/stream", response_model=None)
    def ask_stream(body: AskRequest, request: Request) -> JSONResponse | StreamingResponse:
        request_id = str(uuid.uuid4())
        ip_hash, refused = admit(request, body, request_id)
        if isinstance(refused, JSONResponse):
            return refused

        def events() -> Iterator[str]:
            if refused is not None:  # a saved example's answer after the daily cap
                yield sse("token", {"text": refused.answer.get("text", "")})
                yield sse(
                    "final",
                    {
                        "request_id": request_id,
                        "cached": True,
                        "example": example_ref(refused),
                        "answer": refused.answer,
                    },
                )
                return
            start = datetime.now(UTC)
            answer: Answer | None = None
            logged = False
            try:
                try:
                    with services.retriever() as retriever:
                        for event in stream_answer(
                            body.question,
                            retriever=retriever,
                            model=services.model,
                            ticker=body.ticker,
                            fiscal_year=body.fiscal_year,
                        ):
                            if isinstance(event, Answer):
                                answer = event
                            else:
                                yield sse("token", {"text": event})
                except ProviderError as exc:
                    latency = (datetime.now(UTC) - start).total_seconds() * 1000
                    logged = True
                    save(new_row(request_id, body, ip_hash, error=exc.log_code, latency_ms=latency))
                    detail = CUT_OFF if isinstance(exc, IncompleteAnswer) else UNAVAILABLE
                    yield sse("error", {"request_id": request_id, "detail": detail})
                    return
                assert answer is not None
                logged = True
                save(new_row(request_id, body, ip_hash, **answer_fields(answer)))
                yield sse(
                    "final",
                    {
                        "request_id": request_id,
                        "cached": False,
                        "example": None,
                        "answer": answer.model_dump(),
                    },
                )
            finally:
                # The visitor left before the answer was logged: the model was still called,
                # so the request counts toward the limits, with its tokens and cost if known.
                if not logged:
                    latency = (datetime.now(UTC) - start).total_seconds() * 1000
                    fields = answer_fields(answer) if answer else {"latency_ms": latency}
                    save(new_row(request_id, body, ip_hash, error=DISCONNECTED, **fields))

        return StreamingResponse(events(), media_type="text/event-stream")

    @app.get("/health", response_model=None)
    def health() -> JSONResponse:
        """Cheap: no database query, so the platform's health checks never wake the database."""
        ready = services.model_ready()
        return JSONResponse(
            {"status": "ok" if ready else "no model key", "model": services.primary_name},
            status_code=200 if ready else 503,
        )

    @app.get("/health/deep", response_model=None)
    def health_deep() -> JSONResponse:
        """The database answers and holds embeddings; for the smoke test, not for polling."""
        checks = store.deep_health()
        return JSONResponse(checks, status_code=200 if all(checks.values()) else 503)

    @app.get("/companies")
    def companies() -> list[dict[str, Any]]:
        return [c.model_dump() for c in cached_companies()]

    @app.get("/examples")
    def examples() -> list[dict[str, Any]]:
        return [e.model_dump() for e in cached_examples()]

    @app.get("/stats")
    def stats() -> dict[str, Any]:
        since = datetime.now(UTC) - timedelta(hours=24)
        summary = compute_stats(store.requests_since(since), services.primary_name)
        return {"since": since.isoformat(), **summary}

    return app


def example_ref(example: ExampleAnswer) -> dict[str, Any]:
    """The example question a cached answer belongs to, which is not the visitor's question."""
    return {
        "question": example.question,
        "ticker": example.ticker,
        "fiscal_year": example.fiscal_year,
    }


def sse(event: str, data: dict[str, Any]) -> str:
    """One server-sent event."""
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"
