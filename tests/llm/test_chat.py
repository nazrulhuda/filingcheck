"""The chat client, the provider registry, the model router and chat prices (no network)."""

import json
from collections.abc import Callable
from typing import Any

import httpx
import pytest

from filingcheck.llm import (
    Completion,
    FakeChat,
    IncompleteAnswer,
    ModelRouter,
    OpenAICompatibleChat,
    ProviderError,
    ProviderUnavailable,
    UnknownCostError,
    load_registry,
    make_chat,
    router_from_env,
)
from filingcheck.llm.pricing import PRICING, MissingPriceError, chat_cost_usd

GROQ = "groq:openai/gpt-oss-20b"
GEMINI = "gemini:gemini-3.5-flash-lite"
OPENROUTER = "openrouter:openai/gpt-oss-20b"
MESSAGES = [{"role": "user", "content": "What are Walmart's main risks in Mexico?"}]
RATE_HEADERS = {
    "x-ratelimit-limit-requests": "1000",
    "x-ratelimit-limit-tokens": "8000",
    "x-ratelimit-remaining-requests": "999",
    "x-ratelimit-remaining-tokens": "6500",
}


def ok(
    text: str = "Peso swings are a risk [1].",
    *,
    finish: str | None = "stop",
    usage: dict[str, int] | None = None,
    headers: dict[str, str] | None = None,
) -> httpx.Response:
    body: dict[str, Any] = {
        "choices": [
            {"index": 0, "message": {"role": "assistant", "content": text}, "finish_reason": finish}
        ]
    }
    if usage is not None:
        body["usage"] = usage
    return httpx.Response(200, json=body, headers=headers or {})


USAGE = {"prompt_tokens": 1000, "completion_tokens": 200, "total_tokens": 1200}


def error(
    status: int, message: str = "nope", code: str | None = None, **headers: str
) -> httpx.Response:
    err: dict[str, Any] = {"message": message, "type": "invalid_request_error"}
    if code is not None:
        err["code"] = code
    return httpx.Response(status, json={"error": err}, headers=headers)


class Script:
    """A mock transport that answers each request with the next scripted response."""

    def __init__(self, *responses: httpx.Response | Exception) -> None:
        self.responses = list(responses)
        self.requests: list[httpx.Request] = []
        self.transport = httpx.MockTransport(self._handle)

    def _handle(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        item = self.responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return item

    def body(self, n: int = 0) -> dict[str, Any]:
        result: dict[str, Any] = json.loads(self.requests[n].content)
        return result


def chat(
    spec: str, script: Script, mode: str = "batch", sleeps: list[float] | None = None
) -> OpenAICompatibleChat:
    record: Callable[[float], None] = (sleeps if sleeps is not None else []).append
    return make_chat(spec, mode=mode, api_key="test-key", transport=script.transport, sleep=record)  # type: ignore[arg-type]


# ---------------------------------------------------------------- what is sent to each provider


def test_groq_gets_its_documented_parameters_and_max_completion_tokens() -> None:
    script = Script(ok(usage=USAGE))
    chat(GROQ, script).complete(MESSAGES, max_tokens=700)
    request = script.requests[0]
    assert str(request.url) == "https://api.groq.com/openai/v1/chat/completions"
    assert request.headers["authorization"] == "Bearer test-key"
    assert script.body() == {
        "model": "openai/gpt-oss-20b",
        "messages": MESSAGES,
        "max_completion_tokens": 700,
        "temperature": 0.6,
        "reasoning_effort": "low",
        "include_reasoning": False,
    }


def test_openrouter_is_pinned_to_groq_with_no_other_host_and_gets_its_own_reasoning_setting() -> (
    None
):
    script = Script(ok(usage=USAGE))
    chat(OPENROUTER, script).complete(MESSAGES, max_tokens=700)
    request = script.requests[0]
    assert str(request.url) == "https://openrouter.ai/api/v1/chat/completions"
    assert request.headers["authorization"] == "Bearer test-key"
    assert script.body() == {
        "model": "openai/gpt-oss-20b",
        "messages": MESSAGES,
        "max_tokens": 700,
        "temperature": 0.6,
        "provider": {"only": ["groq"], "allow_fallbacks": False},
        "reasoning": {"effort": "low", "exclude": True},
    }


@pytest.mark.parametrize(
    "response",
    [
        error(404, "No allowed providers are available for the selected model."),
        error(402, "Insufficient credits"),
    ],
)
def test_live_openrouter_with_no_allowed_host_or_no_credit_falls_back(
    response: httpx.Response,
) -> None:
    backup = fallback()
    router = ModelRouter(chat(OPENROUTER, Script(response), mode="live"), [backup], mode="live")
    assert router.complete(MESSAGES, max_tokens=700).model == "fake:chat"
    assert router.fallbacks_used == 1


def test_batch_openrouter_with_no_allowed_host_stops_instead_of_falling_back() -> None:
    backup = fallback()
    script = Script(error(404, "No allowed providers are available for the selected model."))
    router = ModelRouter(chat(OPENROUTER, script), [backup], mode="batch")
    with pytest.raises(ProviderUnavailable):
        router.complete(MESSAGES, max_tokens=700)
    assert backup.calls == []


def test_gemini_gets_max_tokens_but_no_temperature_reasoning_or_groq_parameters() -> None:
    script = Script(ok(usage=USAGE))
    chat(GEMINI, script).complete(MESSAGES, max_tokens=700, temperature=0.2)
    request = script.requests[0]
    assert str(request.url) == (
        "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
    )
    assert script.body() == {
        "model": "gemini-3.5-flash-lite",
        "messages": MESSAGES,
        "max_tokens": 700,
    }


def test_an_explicit_temperature_replaces_the_registry_one_where_one_is_set() -> None:
    script = Script(ok(usage=USAGE))
    chat(GROQ, script).complete(MESSAGES, max_tokens=700, temperature=0.5)
    assert script.body()["temperature"] == 0.5


def test_json_schema_is_refused_for_a_model_not_checked_for_it() -> None:
    script = Script()
    with pytest.raises(ValueError, match="json_schema"):
        chat(GROQ, script).complete(MESSAGES, max_tokens=700, json_schema={"type": "object"})
    assert script.requests == []


# ---------------------------------------------------------------- what comes back


def test_a_completion_carries_tokens_cost_finish_reason_and_rate_limit_headers() -> None:
    script = Script(ok(usage=USAGE, headers=RATE_HEADERS | {"x-other": "1"}))
    result = chat(GROQ, script).complete(MESSAGES, max_tokens=700)
    assert result.text == "Peso swings are a risk [1]."
    assert (result.prompt_tokens, result.completion_tokens) == (1000, 200)
    assert result.finish_reason == "stop" and result.model == GROQ
    assert result.cost_usd == pytest.approx((1000 * 0.075 + 200 * 0.30) / 1_000_000)
    assert result.rate_limits == RATE_HEADERS
    assert result.latency_ms >= 0


@pytest.mark.parametrize(
    ("text", "finish"), [("", "stop"), ("   ", "stop"), ("Peso swings", "length"), ("x", None)]
)
def test_an_empty_answer_or_a_finish_reason_other_than_stop_is_an_error(
    text: str, finish: str | None
) -> None:
    script = Script(ok(text, finish=finish, usage=USAGE))
    with pytest.raises(IncompleteAnswer) as caught:
        chat(GROQ, script).complete(MESSAGES, max_tokens=700)
    assert caught.value.completion.completion_tokens == 200  # kept for the report


def test_a_response_without_usage_has_unknown_cost_in_live_mode() -> None:
    client = chat(GROQ, Script(ok(usage=None)), mode="live")
    result = client.complete(MESSAGES, max_tokens=700)
    assert result.cost_usd is None and result.prompt_tokens is None
    assert client.unknown_cost_count == 1


def test_a_response_without_usage_stops_a_batch_run() -> None:
    with pytest.raises(UnknownCostError):
        chat(GROQ, Script(ok(usage=None))).complete(MESSAGES, max_tokens=700)


def test_hidden_thinking_tokens_in_the_total_are_billed_as_output() -> None:
    usage = {"prompt_tokens": 1000, "completion_tokens": 100, "total_tokens": 1300}
    result = chat(GEMINI, Script(ok(usage=usage))).complete(MESSAGES, max_tokens=700)
    assert result.cost_usd == pytest.approx((1000 * 0.30 + 300 * 2.50) / 1_000_000)


# ---------------------------------------- errors that mean "use another model"


@pytest.mark.parametrize(
    ("status", "message", "code"),
    [
        (401, "Invalid API Key", "invalid_api_key"),
        (403, "Forbidden", None),
        (404, "The model `openai/gpt-oss-20b` does not exist", "model_not_found"),
        (400, "The model `x` has been decommissioned", "model_decommissioned"),
        (400, "Organization spend limit reached", "blocked_api_access"),
        (402, "Insufficient credits", None),
    ],
)
def test_a_wrong_key_missing_model_spend_limit_or_no_credit_is_provider_unavailable(
    status: int, message: str, code: str | None
) -> None:
    for mode in ("live", "batch"):
        script = Script(error(status, message, code))
        with pytest.raises(ProviderUnavailable):
            chat(GROQ, script, mode=mode).complete(MESSAGES, max_tokens=700)
        assert len(script.requests) == 1


def test_a_missing_key_is_provider_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    client = make_chat(GROQ, mode="live", transport=Script().transport)
    with pytest.raises(ProviderUnavailable, match="GROQ_API_KEY"):
        client.complete(MESSAGES, max_tokens=700)


def test_any_other_400_is_our_bug_and_not_a_reason_to_fall_back() -> None:
    script = Script(error(400, "unknown parameter: foo", "invalid_request_error"))
    with pytest.raises(ProviderError) as caught:
        chat(GROQ, script, mode="live").complete(MESSAGES, max_tokens=700)
    assert not isinstance(caught.value, ProviderUnavailable)


# ---------------------------------------- live mode: wait at most 10 s in total


def test_live_a_retry_after_over_10_seconds_gives_up_at_once_without_waiting() -> None:
    sleeps: list[float] = []
    script = Script(error(429, "rate limited", **{"retry-after": "30"}))
    with pytest.raises(ProviderUnavailable):
        chat(GROQ, script, mode="live", sleeps=sleeps).complete(MESSAGES, max_tokens=700)
    assert sleeps == [] and len(script.requests) == 1


def test_live_a_timeout_gives_up_at_once() -> None:
    sleeps: list[float] = []
    script = Script(httpx.ReadTimeout("timed out"))
    with pytest.raises(ProviderUnavailable, match="timed out"):
        chat(GROQ, script, mode="live", sleeps=sleeps).complete(MESSAGES, max_tokens=700)
    assert sleeps == [] and len(script.requests) == 1


def test_live_a_short_retry_after_is_waited_out() -> None:
    sleeps: list[float] = []
    script = Script(error(429, "rate limited", **{"retry-after": "2"}), ok(usage=USAGE))
    result = chat(GROQ, script, mode="live", sleeps=sleeps).complete(MESSAGES, max_tokens=700)
    assert result.text and sleeps == [2.0]


def test_live_the_total_wait_never_passes_10_seconds() -> None:
    sleeps: list[float] = []
    script = Script(*[error(503, "overloaded") for _ in range(10)])
    with pytest.raises(ProviderUnavailable):
        chat(GROQ, script, mode="live", sleeps=sleeps).complete(MESSAGES, max_tokens=700)
    assert sum(sleeps) <= 10.0 and sleeps


# ---------------------------------------- batch mode: wait up to 60 s, 4 retries


def test_batch_a_429_is_waited_out_and_retried() -> None:
    sleeps: list[float] = []
    script = Script(error(429, "rate limited", **{"retry-after": "30"}), ok(usage=USAGE))
    result = chat(GROQ, script, sleeps=sleeps).complete(MESSAGES, max_tokens=700)
    assert result.text and sleeps == [30.0] and len(script.requests) == 2


def test_batch_never_waits_more_than_60_seconds() -> None:
    sleeps: list[float] = []
    script = Script(error(429, "rate limited", **{"retry-after": "600"}), ok(usage=USAGE))
    chat(GROQ, script, sleeps=sleeps).complete(MESSAGES, max_tokens=700)
    assert sleeps == [60.0]


def test_batch_a_timeout_is_retried() -> None:
    script = Script(httpx.ReadTimeout("timed out"), ok(usage=USAGE))
    assert chat(GROQ, script).complete(MESSAGES, max_tokens=700).text


def test_batch_stops_with_an_error_after_4_retries() -> None:
    sleeps: list[float] = []
    script = Script(*[error(429, "rate limited", **{"retry-after": "1"}) for _ in range(5)])
    with pytest.raises(ProviderError, match="4 retries") as caught:
        chat(GROQ, script, sleeps=sleeps).complete(MESSAGES, max_tokens=700)
    assert not isinstance(caught.value, ProviderUnavailable)
    assert len(script.requests) == 5 and len(sleeps) == 4


# ---------------------------------------------------------------- the router


def fallback() -> FakeChat:
    return FakeChat(["From the fallback [1]."], name="fake:chat")


@pytest.mark.parametrize(
    "response",
    [
        error(401, "Invalid API Key", "invalid_api_key"),
        error(404, "The model does not exist", "model_not_found"),
        error(429, "rate limited", **{"retry-after": "45"}),
        httpx.ConnectTimeout("timed out"),
        httpx.ConnectError("connection refused"),
    ],
)
def test_live_the_router_falls_back_and_records_which_model_answered(
    response: httpx.Response | Exception,
) -> None:
    sleeps: list[float] = []
    backup = fallback()
    router = ModelRouter(
        chat(GROQ, Script(response), mode="live", sleeps=sleeps), [backup], mode="live"
    )
    result = router.complete(MESSAGES, max_tokens=700)
    assert result.model == "fake:chat" and router.last_model == "fake:chat"
    assert router.fallbacks_used == 1 and sleeps == []
    assert backup.calls[0]["max_tokens"] == 700


def test_live_the_router_uses_the_primary_when_it_answers() -> None:
    backup = fallback()
    router = ModelRouter(chat(GROQ, Script(ok(usage=USAGE)), mode="live"), [backup], mode="live")
    assert router.complete(MESSAGES, max_tokens=700).model == GROQ
    assert backup.calls == [] and router.fallbacks_used == 0


def test_live_the_router_raises_when_every_model_is_unavailable() -> None:
    router = ModelRouter(
        FakeChat([ProviderUnavailable("groq down")], name="a"),
        [FakeChat([ProviderUnavailable("gemini down")], name="b")],
        mode="live",
    )
    with pytest.raises(ProviderUnavailable, match="gemini down"):
        router.complete(MESSAGES, max_tokens=700)


def test_batch_the_router_waits_on_a_429_and_never_falls_back() -> None:
    sleeps: list[float] = []
    backup = fallback()
    script = Script(error(429, "rate limited", **{"retry-after": "20"}), ok(usage=USAGE))
    router = ModelRouter(chat(GROQ, script, sleeps=sleeps), [backup], mode="batch")
    assert router.complete(MESSAGES, max_tokens=700).model == GROQ
    assert sleeps == [20.0] and backup.calls == []


def test_batch_the_router_stops_instead_of_falling_back() -> None:
    backup = fallback()
    router = ModelRouter(chat(GROQ, Script(error(401, "Invalid API Key"))), [backup], mode="batch")
    with pytest.raises(ProviderUnavailable):
        router.complete(MESSAGES, max_tokens=700)
    assert backup.calls == []


def test_the_router_is_built_from_the_environment() -> None:
    env = {"FC_CHAT_MODEL": GROQ, "FC_FALLBACK_MODELS": f"{GEMINI}, {GROQ}"}
    router = router_from_env("live", env)
    assert router.primary.name == GROQ and [m.name for m in router.fallbacks] == [GEMINI, GROQ]
    assert router.mode == "live"
    defaults = router_from_env("batch", {})
    assert defaults.primary.name == OPENROUTER and [m.name for m in defaults.fallbacks] == [GEMINI]


def test_the_default_models_never_need_the_retired_groq_key() -> None:
    defaults = router_from_env("live", {})
    models = [defaults.primary, *defaults.fallbacks]
    keys = {m.api_key_env for m in models if isinstance(m, OpenAICompatibleChat)}
    assert len(keys) == len(models) and keys == {"OPENROUTER_API_KEY", "GEMINI_API_KEY"}


@pytest.mark.parametrize("spec", ["nowhere:some-model", "groq:not-in-the-registry", "no-colon"])
def test_a_model_missing_from_the_registry_is_refused(spec: str) -> None:
    with pytest.raises(ValueError, match="registry"):
        make_chat(spec, mode="batch")


# ---------------------------------------------------------------- prices


def test_chat_cost_counts_input_and_output_at_their_own_prices() -> None:
    assert chat_cost_usd(GROQ, 1_000_000, 1_000_000) == pytest.approx(0.075 + 0.30)
    # OpenRouter lists the Groq host's own price for this model.
    assert chat_cost_usd(OPENROUTER, 1_000_000, 1_000_000) == pytest.approx(0.075 + 0.30)
    assert chat_cost_usd(GROQ, 1000, None) is None
    assert chat_cost_usd(GROQ, None, 10) is None


def test_a_chat_model_with_no_output_price_raises() -> None:
    with pytest.raises(MissingPriceError):
        chat_cost_usd("text-embedding-3-small", 10, 10)
    with pytest.raises(MissingPriceError):
        OpenAICompatibleChat(
            "https://api.groq.com/openai/v1",
            "GROQ_API_KEY",
            "text-embedding-3-small",
            token_limit_param="max_completion_tokens",
        )


def test_every_model_in_the_registry_has_an_input_and_an_output_price_with_a_source() -> None:
    registry = load_registry()
    # The groq: entry stays: the saved example answers were made with it.
    assert set(registry.models) == {GROQ, GEMINI, OPENROUTER}
    for spec in registry.models:
        entry = PRICING["models"][spec]
        assert entry["input_per_million"] > 0 and entry["output_per_million"] > 0
        assert entry["source"].startswith("https://")


def test_fake_chat_replays_its_script_and_records_each_call() -> None:
    fake = FakeChat(
        [
            "first",
            Completion(
                text="second",
                prompt_tokens=1,
                completion_tokens=2,
                model="fake:chat",
                latency_ms=0.0,
                cost_usd=0.0,
                finish_reason="stop",
            ),
        ]
    )
    assert fake.complete(MESSAGES, max_tokens=5).text == "first"
    assert fake.complete(MESSAGES, max_tokens=6, temperature=0.1).text == "second"
    assert [c["max_tokens"] for c in fake.calls] == [5, 6]
    assert fake.calls[1]["temperature"] == 0.1 and fake.calls[0]["messages"] == MESSAGES


def cut_off(name: str = "a") -> IncompleteAnswer:
    reply = Completion(
        text="",
        prompt_tokens=10,
        completion_tokens=30,
        model=name,
        latency_ms=1.0,
        cost_usd=0.0,
        finish_reason="length",
    )
    return IncompleteAnswer(f"{name}: incomplete answer", reply)


def test_live_the_router_falls_back_on_a_cut_off_reply() -> None:
    backup = fallback()
    script = Script(ok("Peso swings", finish="length", usage=USAGE))
    router = ModelRouter(chat(GROQ, script, mode="live"), [backup], mode="live")
    result = router.complete(MESSAGES, max_tokens=700)
    assert result.model == "fake:chat" and router.fallbacks_used == 1


def test_live_the_router_falls_back_on_an_empty_reply() -> None:
    backup = fallback()
    empty = Script(ok("", usage=USAGE))
    router = ModelRouter(chat(GROQ, empty, mode="live"), [backup], mode="live")
    assert router.complete(MESSAGES, max_tokens=700).model == "fake:chat"


def test_live_when_the_last_model_is_cut_off_the_incomplete_answer_is_raised() -> None:
    router = ModelRouter(
        FakeChat([ProviderUnavailable("groq: wrong key")], name="a"),
        [FakeChat([cut_off("b")], name="b")],
        mode="live",
    )
    with pytest.raises(IncompleteAnswer) as caught:
        router.complete(MESSAGES, max_tokens=30)
    assert caught.value.completion.finish_reason == "length"


def test_batch_a_cut_off_reply_stops_the_run_and_never_falls_back() -> None:
    backup = fallback()
    script = Script(ok("Peso swings", finish="length", usage=USAGE))
    router = ModelRouter(chat(GROQ, script), [backup], mode="batch")
    with pytest.raises(IncompleteAnswer):
        router.complete(MESSAGES, max_tokens=700)
    assert backup.calls == []


def test_a_router_names_the_models_a_run_may_use_in_turn() -> None:
    from filingcheck.llm import FakeChat, ModelRouter

    primary, fallback = FakeChat([], name="a:one"), FakeChat([], name="b:two")
    live = ModelRouter(primary, [fallback], mode="live")
    batch = ModelRouter(primary, [fallback], mode="batch")
    assert live.in_turn() == [primary, fallback]
    assert batch.in_turn() == [primary]  # batch mode never falls back


# ---------------------------------------------------------------- a reply with no choices
# OpenRouter can answer 200 with {"error": {...}} and no "choices" (an upstream failure).


def no_choices(message: str = "Upstream error from Groq", code: int | None = 502) -> httpx.Response:
    err: dict[str, Any] = {"message": message}
    if code is not None:
        err["code"] = code
    return httpx.Response(200, json={"error": err})


@pytest.mark.parametrize(
    "response",
    [
        no_choices(),
        no_choices(code=None),
        httpx.Response(200, json={"choices": []}),
        httpx.Response(200, text="<html>bad gateway</html>"),
    ],
    ids=["error-body", "error-no-code", "empty-choices", "not-json"],
)
def test_live_a_reply_with_no_choices_is_provider_unavailable(response: httpx.Response) -> None:
    script = Script(response)
    with pytest.raises(ProviderUnavailable, match="no choices") as caught:
        chat(OPENROUTER, script, mode="live").complete(MESSAGES, max_tokens=700)
    assert len(script.requests) == 1
    assert caught.value.provider == "openrouter"


def test_live_the_error_message_is_kept() -> None:
    with pytest.raises(ProviderUnavailable, match="Upstream error from Groq"):
        chat(OPENROUTER, Script(no_choices()), mode="live").complete(MESSAGES, max_tokens=700)


def test_batch_a_reply_with_no_choices_is_retried() -> None:
    sleeps: list[float] = []
    script = Script(no_choices(), ok("Retried [1].", usage=USAGE))
    result = chat(OPENROUTER, script, sleeps=sleeps).complete(MESSAGES, max_tokens=700)
    assert result.text == "Retried [1]."
    assert len(script.requests) == 2 and len(sleeps) == 1


def test_batch_stops_with_an_error_after_4_replies_with_no_choices() -> None:
    script = Script(*[no_choices() for _ in range(5)])
    with pytest.raises(ProviderError, match="4 retries") as caught:
        chat(OPENROUTER, script).complete(MESSAGES, max_tokens=700)
    assert not isinstance(caught.value, ProviderUnavailable)
    assert len(script.requests) == 5


def test_live_the_router_falls_back_on_a_reply_with_no_choices() -> None:
    primary = chat(OPENROUTER, Script(no_choices()), mode="live")
    router = ModelRouter(primary, [fallback()], mode="live")
    completion = router.complete(MESSAGES, max_tokens=700)
    assert completion.text == "From the fallback [1]."
