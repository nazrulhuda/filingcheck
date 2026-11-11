"""The HTTP API: /ask, /ask/stream, /health, /companies, /examples and /stats.

Questions go through the plain-RAG baseline (the default) or, with `mode: "agent"`, the
agent with its checks on (what the page sends), both with the models in live mode. Every
question that reaches the limits is logged; a provider failure is logged as a short code
(provider, HTTP status, the provider's error code) and never as the provider's message.
"""

import functools
import hashlib
import json
import logging
import os
import queue
import threading
import uuid
from collections.abc import Callable, Iterator
from contextlib import AbstractContextManager, contextmanager
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any, Literal

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, ConfigDict, Field

from filingcheck.agent import (
    AgentAnswer,
    FailedAttempt,
    ToolCallRecord,
    run_agent_with_fallbacks,
)
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
from filingcheck.checks import reference_data
from filingcheck.db import connect
from filingcheck.embeddings.openai_client import OpenAIEmbeddings
from filingcheck.facts.lookup import PostgresFacts
from filingcheck.llm import ChatModel, IncompleteAnswer, ProviderError, router_from_env
from filingcheck.paths import REPO_ROOT
from filingcheck.retrieval import HybridRetriever, KeywordRetriever, Retriever, VectorRetriever
from filingcheck.retrieval.query import QueryEmbedder
from filingcheck.tools import ToolDeps
from filingcheck.tools.inputs import TICKER_NAMES

log = logging.getLogger(__name__)

RATE_LIMITED = "Too many questions from your address; the limit is {n} an hour."
DAILY_CAP = "The demo has reached today's limit of questions; please come back tomorrow."
UNAVAILABLE = "The language models are busy or unavailable right now; please try again soon."
CUT_OFF = "The answer was cut off before it finished; please try again."
DISCONNECTED = "client_disconnected"  # error code of a stream the visitor abandoned
# Sent when a provider fails mid-run and the next model starts the question again; the
# provider's code stays in the request log.
RESTARTED = "The first model stopped; starting again with another model."
# The 13 metrics in the words the page shows while the agent looks one up.
METRIC_WORDS = {
    "revenue": "revenue",
    "net_income": "net income",
    "diluted_eps": "diluted EPS",
    "operating_income": "operating income",
    "pretax_income": "pretax income",
    "total_assets": "total assets",
    "total_liabilities": "total liabilities",
    "stockholders_equity": "stockholders' equity",
    "operating_cash_flow": "operating cash flow",
    "capital_expenditures": "capital expenditures",
    "cash_and_equivalents": "cash and equivalents",
    "long_term_debt": "long-term debt",
    "shares_outstanding": "shares outstanding",
}
QUERY_CHARS = 60  # a search query longer than this is cut in the label


def tool_label(name: str, arguments: dict[str, Any]) -> str:
    """A tool call in a few words, for the page to show while the agent works.

    Built from the arguments the tool ran with; any argument missing gives a generic label.
    """
    if name == "get_financial_fact":
        ticker, year, metric = (arguments.get(k) for k in ("ticker", "fiscal_year", "metric"))
        if not (ticker and year and metric):
            return "Looking up a reported number"
        company = TICKER_NAMES.get(str(ticker), str(ticker))
        words = METRIC_WORDS.get(str(metric), str(metric).replace("_", " "))
        return f"Looking up {company} FY{year} {words}"
    if name == "search_filings":
        query = str(arguments.get("query") or "").strip()
        if not query:
            return "Searching the filings"
        if len(query) > QUERY_CHARS:
            query = query[:QUERY_CHARS].rstrip() + "…"
        scope = []
        if arguments.get("ticker"):
            scope.append(TICKER_NAMES.get(str(arguments["ticker"]), str(arguments["ticker"])))
        if arguments.get("fiscal_year"):
            scope.append(f"FY{arguments['fiscal_year']}")
        where = f" ({', '.join(scope)})" if scope else ""
        return f"Searching the filings{where} for “{query}”"
    if name == "calculate":
        return "Calculating"
    return name


@dataclass
class Services:
    """Everything the API calls; tests pass fakes."""

    model: ChatModel
    primary_name: str
    store: Store
    retriever: Callable[[], AbstractContextManager[Retriever]]
    settings: Settings
    model_ready: Callable[[], bool]
    # The agent's models, primary first: a failure mid-run restarts with the next one.
    agent_models: list[ChatModel] = field(default_factory=list)
    tools: Callable[[], AbstractContextManager[ToolDeps]] | None = None


class AskRequest(BaseModel):
    """A question, optionally narrowed to one company and fiscal year."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    question: str = Field(min_length=1, max_length=MAX_QUESTION_CHARS)
    ticker: str | None = Field(default=None, pattern=r"^[A-Za-z.\-]{1,10}$")
    fiscal_year: int | None = Field(default=None, ge=1990, le=2100)
    mode: Literal["baseline", "agent"] = "baseline"  # the page sends none: the baseline
    # The agent's skeptical checks: on unless the request says false; ignored for the baseline.
    checks: bool | None = None

    def checks_on(self) -> bool | None:
        """Whether the checks run: None for the baseline, else on by default."""
        if self.mode != "agent":
            return None
        return True if self.checks is None else self.checks


def default_services() -> Services:
    """The real model router (live mode), Postgres and hybrid search, from the environment."""
    load_dotenv(REPO_ROOT / ".env")
    router = router_from_env("live")
    embedder = QueryEmbedder(OpenAIEmbeddings())

    @contextmanager
    def retriever() -> Iterator[Retriever]:
        with connect() as conn:
            yield HybridRetriever(VectorRetriever(conn, embedder), KeywordRetriever(conn))

    @contextmanager
    def tools() -> Iterator[ToolDeps]:
        with connect() as conn:
            search = HybridRetriever(VectorRetriever(conn, embedder), KeywordRetriever(conn))
            yield ToolDeps(retriever=search, facts=PostgresFacts(conn), **_reference_data())

    key_env = getattr(router.primary, "api_key_env", "")
    return Services(
        model=router,
        primary_name=router.primary.name,
        store=PostgresStore(),
        retriever=retriever,
        settings=Settings.from_env(),
        model_ready=lambda: bool(os.environ.get(key_env, "").strip()),
        agent_models=router.in_turn(),
        tools=tools,
    )


# The company list, the not-covered list and the manifest change only with a re-pin, so
# they are read once per process.
_reference_data = functools.cache(reference_data)


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
        fields.setdefault("mode", body.mode)  # a refusal is logged with the mode asked for
        fields.setdefault("checks", body.checks_on())
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

    def agent_fields(answer: AgentAnswer) -> dict[str, Any]:
        calls = [json.loads(record.model_dump_json()) for record in answer.tool_calls]
        attempts = [json.loads(a.model_dump_json()) for a in answer.failed_attempts]
        return {
            **answer_fields(answer),
            "mode": "agent",
            "checks": answer.checks,
            "overrides": [json.loads(o.model_dump_json()) for o in answer.overrides],
            "tool_calls": {
                "calls": calls,
                "restarts": answer.restarts,
                "failed_attempts": attempts,
            },
        }

    def failure_fields(failed: list[FailedAttempt]) -> dict[str, Any]:
        """The question failed: the row still holds each attempt and what it cost.

        The last attempt is the failure that was raised; the ones before it were restarts.
        With no attempt recorded (the agent itself broke) tokens and cost stay unknown.
        """
        if not failed:
            return {"mode": "agent"}
        prompt = [a.usage.get("prompt_tokens") for a in failed]
        output = [a.usage.get("completion_tokens") for a in failed]
        costs = [a.cost_usd for a in failed]
        return {
            "mode": "agent",
            "prompt_tokens": None if None in prompt else sum(p for p in prompt if p is not None),
            "completion_tokens": None
            if None in output
            else sum(o for o in output if o is not None),
            "cost_usd": None if None in costs else sum(c for c in costs if c is not None),
            "tool_calls": {
                "calls": [],
                "restarts": [a.log_code for a in failed[:-1]],
                "failed_attempts": [json.loads(a.model_dump_json()) for a in failed],
            },
        }

    def run_agent_for(
        body: AskRequest,
        deps: ToolDeps,
        failed: list[FailedAttempt],
        on_tool_call: Callable[[ToolCallRecord], None] | None = None,
        on_restart: Callable[[str], None] | None = None,
    ) -> AgentAnswer:
        return run_agent_with_fallbacks(
            body.question,
            models=services.agent_models or [services.model],
            deps=deps,
            ticker=body.ticker,
            fiscal_year=body.fiscal_year,
            on_tool_call=on_tool_call,
            on_restart=on_restart,
            failed=failed,
            checks=bool(body.checks_on()),
        )

    def tools() -> AbstractContextManager[ToolDeps]:
        if services.tools is None:
            raise RuntimeError("agent mode needs the tools (Services.tools)")
        return services.tools()

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
        if body.mode == "agent":
            failed: list[FailedAttempt] = []
            try:
                with tools() as deps:
                    agent_answer = run_agent_for(body, deps, failed)
            except ProviderError as exc:
                latency = (datetime.now(UTC) - start).total_seconds() * 1000
                save(
                    new_row(
                        request_id,
                        body,
                        ip_hash,
                        error=exc.log_code,
                        latency_ms=latency,
                        **failure_fields(failed),
                    )
                )
                return JSONResponse(
                    {"detail": UNAVAILABLE, "request_id": request_id}, status_code=503
                )
            save(new_row(request_id, body, ip_hash, **agent_fields(agent_answer)))
            return {
                "request_id": request_id,
                "cached": False,
                "example": None,
                **json.loads(agent_answer.model_dump_json()),
            }
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
            if body.mode == "agent":
                yield from agent_events(body, request_id, ip_hash, start)
                return
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

    def agent_events(
        body: AskRequest, request_id: str, ip_hash: str, start: datetime
    ) -> Iterator[str]:
        """One "tool" event per tool call as it finishes, then the final text and answer.

        The agent runs in a worker thread so its tool calls can be sent while it works; only
        the final answer's text is sent as tokens. A "restart" event says the next model
        started the question again, so the page drops the tool calls shown so far.
        """
        events_queue: queue.Queue[tuple[str, Any]] = queue.Queue()
        failed: list[FailedAttempt] = []  # filled by the worker before it reports a failure

        def work() -> None:
            try:
                with tools() as deps:
                    result = run_agent_for(
                        body,
                        deps,
                        failed,
                        on_tool_call=lambda r: events_queue.put(("tool", r)),
                        on_restart=lambda code: events_queue.put(("restart", code)),
                    )
                events_queue.put(("answer", result))
            except ProviderError as exc:
                events_queue.put(("error", exc))
            except Exception as exc:  # the stream must end even if the agent breaks
                log.exception("agent run %s failed", request_id)
                events_queue.put(("crash", exc))

        threading.Thread(target=work, daemon=True).start()
        logged = False
        try:
            while True:
                kind, item = events_queue.get()
                if kind == "tool":
                    yield sse(
                        "tool",
                        {
                            "name": item.name,
                            "label": tool_label(item.name, item.arguments),
                            "status": item.status,
                        },
                    )
                    continue
                if kind == "restart":
                    yield sse("restart", {"detail": RESTARTED})
                    continue
                latency = (datetime.now(UTC) - start).total_seconds() * 1000
                if kind == "answer":
                    logged = True
                    save(new_row(request_id, body, ip_hash, **agent_fields(item)))
                    yield sse("token", {"text": item.text})
                    yield sse(
                        "final",
                        {
                            "request_id": request_id,
                            "cached": False,
                            "example": None,
                            "answer": json.loads(item.model_dump_json()),
                        },
                    )
                    return
                logged = True
                code = item.log_code if kind == "error" else "agent_crash"
                save(
                    new_row(
                        request_id,
                        body,
                        ip_hash,
                        error=code,
                        latency_ms=latency,
                        **failure_fields(failed),
                    )
                )
                detail = CUT_OFF if isinstance(item, IncompleteAnswer) else UNAVAILABLE
                yield sse("error", {"request_id": request_id, "detail": detail})
                return
        finally:
            if not logged:  # the visitor left; the models were still called
                latency = (datetime.now(UTC) - start).total_seconds() * 1000
                save(
                    new_row(
                        request_id,
                        body,
                        ip_hash,
                        error=DISCONNECTED,
                        latency_ms=latency,
                        mode="agent",
                    )
                )

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
