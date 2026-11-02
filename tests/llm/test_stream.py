"""Streaming replies, and the short error codes that are safe to store (no network)."""

import json
from typing import Any

import httpx
import pytest

from filingcheck.llm import (
    Completion,
    FakeChat,
    IncompleteAnswer,
    ModelRouter,
    ProviderError,
    ProviderUnavailable,
    UnknownCostError,
)
from tests.llm.test_chat import GEMINI, GROQ, MESSAGES, USAGE, Script, chat, error, ok


def chunk(content: str | None = None, finish: str | None = None) -> dict[str, Any]:
    delta = {"content": content} if content is not None else {}
    return {"choices": [{"index": 0, "delta": delta, "finish_reason": finish}]}


def sse(*events: dict[str, Any], headers: dict[str, str] | None = None) -> httpx.Response:
    body = "".join(f"data: {json.dumps(e)}\n\n" for e in events) + "data: [DONE]\n\n"
    return httpx.Response(
        200,
        content=body.encode(),
        headers={"content-type": "text/event-stream"} | (headers or {}),
    )


USAGE_CHUNK = {"choices": [], "usage": USAGE}
ANSWER = [chunk("Peso "), chunk("swings "), chunk("[1]."), chunk(finish="stop")]


def collect(events: Any) -> tuple[list[str], Completion]:
    items = list(events)
    texts = [e for e in items if isinstance(e, str)]
    assert isinstance(items[-1], Completion) and all(isinstance(e, str) for e in items[:-1])
    return texts, items[-1]


# ---------------------------------------------------------------- the chat client


def test_a_stream_asks_for_usage_and_sends_the_same_settings() -> None:
    script = Script(sse(*ANSWER, USAGE_CHUNK))
    collect(chat(GROQ, script).stream(MESSAGES, max_tokens=700))
    assert script.body() == {
        "model": "openai/gpt-oss-20b",
        "messages": MESSAGES,
        "max_completion_tokens": 700,
        "temperature": 0.6,
        "reasoning_effort": "low",
        "include_reasoning": False,
        "stream": True,
        "stream_options": {"include_usage": True},
    }


def test_a_stream_yields_text_as_it_comes_then_the_completion_with_cost() -> None:
    script = Script(sse(*ANSWER, USAGE_CHUNK, headers={"x-ratelimit-limit-tokens": "8000"}))
    texts, completion = collect(chat(GROQ, script).stream(MESSAGES, max_tokens=700))
    assert texts == ["Peso ", "swings ", "[1]."]
    assert completion.text == "Peso swings [1]." and completion.finish_reason == "stop"
    assert (completion.prompt_tokens, completion.completion_tokens) == (1000, 200)
    assert completion.cost_usd == pytest.approx((1000 * 0.075 + 200 * 0.30) / 1_000_000)
    assert completion.model == GROQ
    assert completion.rate_limits == {"x-ratelimit-limit-tokens": "8000"}


def test_usage_inside_x_groq_on_the_last_chunk_is_read_too() -> None:
    last = chunk(finish="stop") | {"x_groq": {"usage": USAGE}}
    client = chat(GROQ, Script(sse(*ANSWER[:3], last)))
    _, completion = collect(client.stream(MESSAGES, max_tokens=7))
    assert completion.prompt_tokens == 1000 and completion.cost_usd is not None


def test_a_stream_without_usage_has_unknown_cost_live_and_stops_a_batch_run() -> None:
    client = chat(GROQ, Script(sse(*ANSWER)), mode="live")
    _, completion = collect(client.stream(MESSAGES, max_tokens=700))
    assert completion.cost_usd is None and client.unknown_cost_count == 1
    with pytest.raises(UnknownCostError):
        list(chat(GROQ, Script(sse(*ANSWER))).stream(MESSAGES, max_tokens=700))


def test_a_stream_cut_off_after_some_text_raises_at_the_end() -> None:
    events = chat(GROQ, Script(sse(chunk("Peso "), chunk(finish="length"), USAGE_CHUNK))).stream(
        MESSAGES, max_tokens=700
    )
    assert next(events) == "Peso "
    with pytest.raises(IncompleteAnswer) as caught:
        next(events)
    assert caught.value.completion.finish_reason == "length"


def test_a_stream_with_no_text_raises_before_yielding_anything() -> None:
    events = chat(GROQ, Script(sse(chunk(finish="stop"), USAGE_CHUNK))).stream(
        MESSAGES, max_tokens=700
    )
    with pytest.raises(IncompleteAnswer):
        next(events)


def test_a_stream_that_cannot_start_raises_like_a_normal_call() -> None:
    with pytest.raises(ProviderUnavailable):
        next(chat(GROQ, Script(error(401, "Invalid API Key"))).stream(MESSAGES, max_tokens=7))
    sleeps: list[float] = []
    script = Script(error(429, "rate limited", **{"retry-after": "30"}))
    with pytest.raises(ProviderUnavailable):
        next(chat(GROQ, script, mode="live", sleeps=sleeps).stream(MESSAGES, max_tokens=7))
    assert sleeps == []


def test_gemini_streams_get_max_tokens_and_no_temperature_or_reasoning() -> None:
    script = Script(sse(*ANSWER, USAGE_CHUNK))
    collect(chat(GEMINI, script).stream(MESSAGES, max_tokens=700, temperature=0.2))
    assert script.body() == {
        "model": "gemini-3.5-flash-lite",
        "messages": MESSAGES,
        "max_tokens": 700,
        "stream": True,
        "stream_options": {"include_usage": True},
    }


# ---------------------------------------------------------------- the router


def test_live_a_stream_falls_back_when_the_primary_cannot_start() -> None:
    backup = FakeChat(["From the fallback [1]."], name="fake:chat")
    router = ModelRouter(
        chat(GROQ, Script(error(401, "Invalid API Key")), mode="live"), [backup], mode="live"
    )
    texts, completion = collect(router.stream(MESSAGES, max_tokens=700))
    assert "".join(texts) == "From the fallback [1]." and completion.model == "fake:chat"
    assert router.last_model == "fake:chat" and router.fallbacks_used == 1


def test_live_a_stream_cut_off_after_text_does_not_fall_back() -> None:
    backup = FakeChat(["unused"], name="fake:chat")
    script = Script(sse(chunk("Peso "), chunk(finish="length"), USAGE_CHUNK))
    router = ModelRouter(chat(GROQ, script, mode="live"), [backup], mode="live")
    with pytest.raises(IncompleteAnswer):
        list(router.stream(MESSAGES, max_tokens=700))
    assert backup.calls == []


def test_batch_a_stream_never_falls_back() -> None:
    backup = FakeChat(["unused"], name="fake:chat")
    router = ModelRouter(chat(GROQ, Script(error(401, "Invalid API Key"))), [backup], mode="batch")
    with pytest.raises(ProviderUnavailable):
        list(router.stream(MESSAGES, max_tokens=700))
    assert backup.calls == []


def test_fake_chat_streams_its_reply_in_pieces() -> None:
    texts, completion = collect(FakeChat(["Peso swings [1]."]).stream(MESSAGES, max_tokens=5))
    assert len(texts) > 1 and "".join(texts) == completion.text == "Peso swings [1]."


# ---------------------------------------------------------------- error codes safe to store


def test_a_provider_error_keeps_provider_status_and_code_but_not_the_message() -> None:
    message = (
        "Rate limit reached for model `openai/gpt-oss-20b` in organization `org_01secret` "
        "service tier `on_demand` on tokens per minute (TPM)"
    )
    script = Script(error(429, message, "rate_limit_exceeded", **{"retry-after": "30"}))
    with pytest.raises(ProviderUnavailable) as caught:
        chat(GROQ, script, mode="live").complete(MESSAGES, max_tokens=700)
    assert caught.value.log_code == "groq 429 rate_limit_exceeded"
    assert "org_01secret" not in caught.value.log_code


@pytest.mark.parametrize(
    ("response", "expected"),
    [
        (error(401, "Invalid API Key", "invalid_api_key"), "groq 401 invalid_api_key"),
        (error(402, "Insufficient credits"), "groq 402 -"),
        (httpx.ReadTimeout("timed out"), "groq - timeout"),
        (httpx.ConnectError("refused"), "groq - connection_error"),
        (ok("Peso", finish="length", usage=USAGE), "groq - incomplete_length"),
        (ok("", usage=USAGE), "groq - incomplete_empty"),
    ],
)
def test_every_failure_has_a_short_log_code(
    response: httpx.Response | Exception, expected: str
) -> None:
    with pytest.raises(ProviderError) as caught:
        chat(GROQ, Script(response), mode="live").complete(MESSAGES, max_tokens=700)
    assert caught.value.log_code == expected


def test_a_code_with_odd_characters_is_cleaned_before_it_is_stored() -> None:
    err = ProviderError("x", provider="groq", status=400, code="bad code\n<script>" + "x" * 100)
    assert err.log_code.startswith("groq 400 bad_code__script_") and len(err.log_code) <= 80


def test_a_missing_key_has_a_log_code(monkeypatch: pytest.MonkeyPatch) -> None:
    from filingcheck.llm import make_chat

    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    with pytest.raises(ProviderUnavailable) as caught:
        make_chat(GROQ, mode="live", transport=Script().transport).complete(MESSAGES, max_tokens=7)
    assert caught.value.log_code == "groq - missing_key"
