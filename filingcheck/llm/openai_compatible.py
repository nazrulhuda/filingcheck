"""Chat over any OpenAI-compatible endpoint (Groq, Gemini, OpenRouter, OpenAI), in two modes.

*Live* (the API): the total wait on 429/5xx is capped at 10 s; a longer `retry-after`, a
timeout or a connection error raises `ProviderUnavailable` at once so the router's fallback
answers. *Batch* (`make ask`, eval runs): waits out a `retry-after` up to 60 s and retries up
to 4 times; if the provider still fails the run stops. Wrong keys, missing models, Groq's
spend limit and an empty prepaid balance raise `ProviderUnavailable` in both modes.
"""

import logging
import os
import time
from collections.abc import Callable
from typing import Any

import httpx

from filingcheck.llm.chat import (
    Completion,
    IncompleteAnswer,
    Message,
    Mode,
    ProviderError,
    ProviderUnavailable,
    UnknownCostError,
)
from filingcheck.llm.pricing import chat_cost_usd, require_chat_prices

log = logging.getLogger(__name__)

TIMEOUT_SECONDS = 30.0
MAX_RETRIES = 4
BACKOFF_SECONDS = 1.0  # waits 1, 2, 4 and 8 seconds, or longer if the provider asks
LIVE_WAIT_BUDGET_SECONDS = 10.0  # live: never wait longer than this in total
BATCH_MAX_WAIT_SECONDS = 60.0  # batch: never wait longer than this at once
UNAVAILABLE_STATUSES = {401, 402, 403, 404}
UNAVAILABLE_CODES = {"blocked_api_access", "model_not_found", "model_decommissioned"}
MISSING_MODEL_WORDS = ("decommissioned", "does not exist", "not found")


class OpenAICompatibleChat:
    """One model at one OpenAI-compatible provider; settings come from the registry.

    The key is read from `api_key_env` at the first call, so a client for a provider whose
    key is absent can still be built (the router then skips it in live mode).
    """

    def __init__(
        self,
        base_url: str,
        api_key_env: str,
        model: str,
        *,
        token_limit_param: str | None,
        name: str | None = None,
        temperature: float | None = None,
        params: dict[str, Any] | None = None,
        json_schema: bool = False,
        mode: Mode = "batch",
        api_key: str | None = None,
        transport: httpx.BaseTransport | None = None,
        sleep: Callable[[float], None] = time.sleep,
        clock: Callable[[], float] = time.perf_counter,
    ) -> None:
        self.name = name or model
        require_chat_prices(self.name)
        self.url = base_url.rstrip("/") + "/chat/completions"
        self.api_key_env = api_key_env
        self.model = model
        self.token_limit_param = token_limit_param
        self.temperature = temperature
        self.params = dict(params or {})
        self.json_schema = json_schema
        self.mode = mode
        self.unknown_cost_count = 0  # live replies that came without usage
        self._api_key = api_key
        self._transport = transport
        self._sleep = sleep
        self._clock = clock
        self._http: httpx.Client | None = None

    def complete(
        self,
        messages: list[Message],
        *,
        max_tokens: int,
        temperature: float | None = None,
        json_schema: dict[str, Any] | None = None,
    ) -> Completion:
        """One reply, retried or failed over according to the mode."""
        body = self._body(messages, max_tokens, temperature, json_schema)
        http = self._client()
        waited = 0.0
        for attempt in range(MAX_RETRIES + 1):
            asked = 0.0  # how long the provider asked us to wait
            start = self._clock()
            try:
                response = http.post(self.url, json=body)
            except httpx.TimeoutException as exc:
                problem = f"timed out after {TIMEOUT_SECONDS:.0f} s"
                if self.mode == "live":
                    raise ProviderUnavailable(f"{self.name}: {problem}") from exc
            except httpx.TransportError as exc:
                problem = f"{type(exc).__name__}: {exc}"
                if self.mode == "live":
                    raise ProviderUnavailable(f"{self.name}: {problem}") from exc
            else:
                latency_ms = (self._clock() - start) * 1000
                status = response.status_code
                if _unavailable(response):
                    message = f"{self.name}: HTTP {status}: {_message(response)}"
                    log.error("provider unavailable: %s", message)
                    raise ProviderUnavailable(message)
                if status < 400:
                    return self._completion(response, latency_ms)
                if status != 429 and status < 500:
                    raise ProviderError(f"{self.name}: HTTP {status}: {_message(response)}")
                problem = f"HTTP {status}: {_message(response)}"
                asked = _retry_after(response)
            if attempt == MAX_RETRIES:
                break
            wait = max(BACKOFF_SECONDS * 2**attempt, asked)
            if self.mode == "live":
                if waited + wait > LIVE_WAIT_BUDGET_SECONDS:
                    raise ProviderUnavailable(
                        f"{self.name}: {problem}; waiting {wait:.0f} s more would pass the "
                        f"{LIVE_WAIT_BUDGET_SECONDS:.0f} s live limit"
                    )
            else:
                wait = min(wait, BATCH_MAX_WAIT_SECONDS)
            log.warning("%s: %s; retrying in %.1f s", self.name, problem, wait)
            self._sleep(wait)
            waited += wait
        if self.mode == "live":
            raise ProviderUnavailable(
                f"{self.name}: {problem}; gave up after {MAX_RETRIES} retries"
            )
        raise ProviderError(
            f"{self.name}: {problem}; gave up after {MAX_RETRIES} retries, so the run stops"
        )

    def _body(
        self,
        messages: list[Message],
        max_tokens: int,
        temperature: float | None,
        json_schema: dict[str, Any] | None,
    ) -> dict[str, Any]:
        if json_schema is not None and not self.json_schema:
            raise ValueError(f"json_schema output is not checked for {self.name} in the registry")
        body: dict[str, Any] = {"model": self.model, "messages": messages}
        if self.token_limit_param is not None:
            body[self.token_limit_param] = max_tokens
        if self.temperature is not None:
            body["temperature"] = self.temperature if temperature is None else temperature
        elif temperature is not None:
            # The registry keeps this provider's default temperature; an explicit one is not sent.
            log.info("%s keeps its default temperature; %s not sent", self.name, temperature)
        body.update(self.params)
        if json_schema is not None:
            body["response_format"] = {"type": "json_schema", "json_schema": json_schema}
        return body

    def _client(self) -> httpx.Client:
        if self._http is None:
            key = (self._api_key or os.environ.get(self.api_key_env, "")).strip()
            if not key:
                message = f"{self.name}: {self.api_key_env} is not set (see .env.example)"
                log.error("provider unavailable: %s", message)
                raise ProviderUnavailable(message)
            self._http = httpx.Client(
                headers={"Authorization": f"Bearer {key}"},
                timeout=TIMEOUT_SECONDS,
                transport=self._transport,
            )
        return self._http

    def _completion(self, response: httpx.Response, latency_ms: float) -> Completion:
        data = response.json()
        choice = data["choices"][0]
        usage = data.get("usage") or {}
        prompt = _int_or_none(usage.get("prompt_tokens"))
        output = _int_or_none(usage.get("completion_tokens"))
        billed_output = output
        total = _int_or_none(usage.get("total_tokens"))
        if output is not None and prompt is not None and total is not None:
            # Thinking tokens left out of completion_tokens are still billed as output.
            billed_output = max(output, total - prompt)
        completion = Completion(
            text=(choice.get("message") or {}).get("content") or "",
            prompt_tokens=prompt,
            completion_tokens=output,
            model=self.name,
            latency_ms=latency_ms,
            cost_usd=chat_cost_usd(self.name, prompt, billed_output),
            finish_reason=choice.get("finish_reason") or "",
            rate_limits={
                k: v for k, v in response.headers.items() if k.lower().startswith("x-ratelimit-")
            },
            usage=usage,
        )
        if not completion.text.strip() or completion.finish_reason != "stop":
            raise IncompleteAnswer(
                f"{self.name}: incomplete answer (finish_reason={completion.finish_reason!r}, "
                f"{len(completion.text)} characters, completion_tokens={output})",
                completion,
            )
        if completion.cost_usd is None:
            if self.mode == "batch":
                raise UnknownCostError(
                    f"{self.name}: the reply has no token usage, so its cost is unknown; "
                    "a batch run needs every cost"
                )
            self.unknown_cost_count += 1
            log.warning("%s: reply without token usage; cost unknown", self.name)
        return completion


def _unavailable(response: httpx.Response) -> bool:
    """Wrong or revoked key, missing model, spend limit or no credit: another model may answer."""
    if response.status_code in UNAVAILABLE_STATUSES:
        return True
    if response.status_code != 400:
        return False
    code = _error_field(response, "code") or ""
    message = _message(response).lower()
    return code in UNAVAILABLE_CODES or (
        "model" in message and any(words in message for words in MISSING_MODEL_WORDS)
    )


def _error_field(response: httpx.Response, field: str) -> str | None:
    try:
        value = response.json()["error"].get(field)
    except (ValueError, KeyError, TypeError, AttributeError):
        return None
    return str(value) if value else None


def _message(response: httpx.Response) -> str:
    return _error_field(response, "message") or response.text[:300]


def _retry_after(response: httpx.Response) -> float:
    """`retry-after` in seconds (0 if absent).

    Groq's x-ratelimit-reset-requests is the time until the daily limit resets, which can be
    hours even when the 429 was for the per-minute token limit, so only `retry-after` counts.
    """
    value = response.headers.get("retry-after", "")
    return float(value) if value.replace(".", "", 1).isdigit() else 0.0


def _int_or_none(value: Any) -> int | None:
    return int(value) if isinstance(value, int | float) else None
