"""`make smoke-live`: the checks against a deployed API, with the API faked (no network)."""

from collections.abc import Callable
from typing import Any

import httpx
import pytest

from filingcheck.app import smoke

BASE = "https://filingcheck-api.example.test"
ANSWER = {
    "request_id": "r1",
    "cached": False,
    "example": None,
    "text": "Netflix says such claims can be costly [1].",
    "citations": [{"number": 1, "chunk_id": 32450, "ticker": "NFLX"}],
    "model_used": "openrouter:openai/gpt-oss-20b",
    "degraded": False,
}


def api(**overrides: Callable[[httpx.Request], httpx.Response]) -> httpx.Client:
    """A client for a fake API that answers every path well unless overridden."""
    routes: dict[str, Callable[[httpx.Request], httpx.Response]] = {
        "GET /health": lambda r: httpx.Response(
            200, json={"status": "ok", "model": "openrouter:openai/gpt-oss-20b"}
        ),
        "GET /companies": lambda r: httpx.Response(200, json=[{"ticker": "NFLX"}] * 25),
        "GET /examples": lambda r: httpx.Response(200, json=[{"question": "Q?"}] * 5),
        "POST /ask": lambda r: httpx.Response(200, json=ANSWER),
    }
    routes.update({k.replace("_", " /", 1): v for k, v in overrides.items()})  # POST_ask: POST /ask
    seen: list[httpx.Request] = []

    def handle(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return routes[f"{request.method} {request.url.path}"](request)

    client = httpx.Client(transport=httpx.MockTransport(handle))
    client.seen = seen  # type: ignore[attr-defined]
    return client


def failures(lines: list[tuple[bool, str]]) -> list[str]:
    return [line for ok, line in lines if not ok]


def test_a_healthy_api_passes_every_check_with_one_question() -> None:
    client = api()
    lines = smoke.run_checks(BASE + "/", client)
    assert failures(lines) == []
    assert [line.split(":")[0] for _, line in lines] == [
        "ok GET /health",
        "ok GET /companies",
        "ok GET /examples",
        "ok POST /ask",
    ]
    asks = [r for r in client.seen if r.method == "POST"]  # type: ignore[attr-defined]
    assert len(asks) == 1 and str(asks[0].url) == BASE + "/ask"
    assert "1 citation" in lines[-1][1] and "openrouter:openai/gpt-oss-20b" in lines[-1][1]


def test_an_answer_with_no_citations_fails() -> None:
    lines = smoke.run_checks(
        BASE, api(POST_ask=lambda r: httpx.Response(200, json={**ANSWER, "citations": []}))
    )
    assert failures(lines) == ["FAIL POST /ask: the answer has no citations"]


def ask_returns(**fields: Any) -> httpx.Client:
    return api(POST_ask=lambda r: httpx.Response(200, json={**ANSWER, **fields}))


@pytest.mark.parametrize(
    ("fields", "reason"),
    [
        # After the daily cap: a saved answer, so the model was not called at all.
        ({"cached": True}, "the answer is a saved example (cached), not a new model call"),
        # Keyword search only: the question could not be embedded (OpenAI key).
        ({"degraded": True}, "degraded: keyword search only, so question embedding failed"),
        # The fallback answered: the OpenRouter key or the Groq pin is not working.
        (
            {"model_used": "gemini:gemini-3.5-flash-lite"},
            "answered by gemini:gemini-3.5-flash-lite, not the primary "
            "openrouter:openai/gpt-oss-20b",
        ),
    ],
)
def test_a_cached_degraded_or_fallback_answer_fails_saying_which(
    fields: dict[str, Any], reason: str
) -> None:
    assert failures(smoke.run_checks(BASE, ask_returns(**fields))) == [f"FAIL POST /ask: {reason}"]


def test_every_problem_with_the_answer_is_named() -> None:
    client = ask_returns(cached=True, degraded=True, citations=[])
    (line,) = failures(smoke.run_checks(BASE, client))
    assert line.startswith("FAIL POST /ask: ")
    assert "no citations" in line and "cached" in line and "degraded" in line


def test_health_naming_another_primary_model_fails() -> None:
    client = api(
        GET_health=lambda r: httpx.Response(
            200, json={"status": "ok", "model": "groq:openai/gpt-oss-20b"}
        )
    )
    assert failures(smoke.run_checks(BASE, client)) == [
        "FAIL GET /health: the primary model is groq:openai/gpt-oss-20b, not "
        "openrouter:openai/gpt-oss-20b"
    ]


def test_the_expected_primary_model_can_be_given() -> None:
    client = ask_returns(model_used="gemini:gemini-3.5-flash-lite")
    expected = "gemini:gemini-3.5-flash-lite"
    lines = smoke.run_checks(BASE, client, model=expected)
    assert failures(lines) == [
        "FAIL GET /health: the primary model is "
        "openrouter:openai/gpt-oss-20b, not gemini:gemini-3.5-flash-lite"
    ]


@pytest.mark.parametrize(
    ("route", "response", "expected"),
    [
        ("GET_examples", httpx.Response(502, text="Bad Gateway"), "FAIL GET /examples: HTTP 502"),
        ("GET_companies", httpx.Response(200, json=[]), "FAIL GET /companies: empty list"),
        ("POST_ask", httpx.Response(429, json={"detail": "x"}), "FAIL POST /ask: HTTP 429"),
        (
            "GET_health",
            httpx.Response(503, json={"status": "no model key"}),
            "FAIL GET /health: HTTP 503",
        ),
    ],
)
def test_any_status_other_than_200_or_an_empty_list_fails_and_the_rest_still_run(
    route: str, response: httpx.Response, expected: str
) -> None:
    lines = smoke.run_checks(BASE, api(**{route: lambda r: response}))
    assert failures(lines) == [expected]
    assert len(lines) == 4


def test_an_unreachable_api_fails_every_check_without_crashing() -> None:
    def refuse(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    client = httpx.Client(transport=httpx.MockTransport(refuse))
    lines = smoke.run_checks(BASE, client)
    assert len(failures(lines)) == 4
    assert all("ConnectError" in line for line in failures(lines))


def test_main_needs_an_https_url_and_returns_1_on_any_failure(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    with pytest.raises(SystemExit):
        smoke.main([])
    assert smoke.main(["http://filingcheck-api.example.test"]) == 2

    bad: dict[str, Any] = {
        "POST_ask": lambda r: httpx.Response(200, json={**ANSWER, "citations": []})
    }
    monkeypatch.setattr(smoke, "make_client", lambda: api(**bad))
    assert smoke.main([BASE]) == 1
    monkeypatch.setattr(smoke, "make_client", api)
    assert smoke.main([BASE]) == 0
    assert "smoke test passed" in capsys.readouterr().out
