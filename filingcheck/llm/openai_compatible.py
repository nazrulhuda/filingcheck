"""Chat over any OpenAI-compatible endpoint (Groq, Gemini, OpenRouter, OpenAI), in two modes.

*Live* (the API): the total wait on 429/5xx is capped at 10 s; a longer `retry-after`, a
timeout or a connection error raises `ProviderUnavailable` at once so the router's fallback
answers. *Batch* (`make ask`, eval runs): waits out a `retry-after` up to 60 s and retries up
to 4 times; if the provider still fails the run stops. Wrong keys, missing models, Groq's
spend limit and an empty prepaid balance raise `ProviderUnavailable` in both modes.
"""

import json
import logging
import os
import time
from collections.abc import Callable, Iterator
from typing import Any

import httpx

from filingcheck.llm.chat import (
    Completion,
    IncompleteAnswer,
    Message,
    Mode,
    ProviderError,
    ProviderUnavailable,
    ToolCall,
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
        tool_calls: bool = False,
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
        self.tool_calls = tool_calls  # checked for tool calling with a real call (registry)
        self.mode = mode
        self.unknown_cost_count = 0  # live replies that came without usage
        self._api_key = api_key
        self._transport = transport
        self._sleep = sleep
        self._clock = clock
        self._http: httpx.Client | None = None

    @property
    def provider(self) -> str:
        """The provider part of the name, for example "groq"."""
        return self.name.partition(":")[0]

    def complete(
        self,
        messages: list[Message],
        *,
        max_tokens: int,
        temperature: float | None = None,
        json_schema: dict[str, Any] | None = None,
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str | dict[str, Any] | None = None,
    ) -> Completion:
        """One reply, retried or failed over according to the mode.

        With `tools`, the standard `tools` and `tool_choice` fields are sent and the reply's
        `tool_calls` are returned; the assistant message is kept exactly as returned.
        """
        body = self._body(messages, max_tokens, temperature, json_schema, tools, tool_choice)
        start = self._clock()
        response = self._send(body, stream=False)
        latency_ms = (self._clock() - start) * 1000
        data = response.json()
        choice = data["choices"][0]
        message = choice.get("message") or {}
        calls = [
            ToolCall(
                id=str(call.get("id") or ""),
                name=str((call.get("function") or {}).get("name") or ""),
                arguments=str((call.get("function") or {}).get("arguments") or "{}"),
            )
            for call in message.get("tool_calls") or []
        ]
        return self._finish(
            message.get("content") or "",
            choice.get("finish_reason") or "",
            data.get("usage") or {},
            response.headers,
            latency_ms,
            tool_calls=calls,
            # Null fields are left out: Groq rejects the next turn if "refusal": null comes
            # back. Every other field (Gemini's thought signature) is kept as returned.
            message={k: v for k, v in message.items() if v is not None or k == "content"},
        )

    def stream(
        self,
        messages: list[Message],
        *,
        max_tokens: int,
        temperature: float | None = None,
    ) -> Iterator[str | Completion]:
        """The reply's text in pieces as it arrives, then the whole `Completion`.

        Starting the stream is retried like `complete`. Once text has been sent nothing is
        retried: an empty or cut-off reply raises `IncompleteAnswer` at the end. Usage is
        asked for with `stream_options`; Groq's reference does not say where streamed usage
        appears, so both the standard `usage` and Groq's `x_groq.usage` are read.
        """
        body = self._body(messages, max_tokens, temperature, None, None, None)
        body |= {"stream": True, "stream_options": {"include_usage": True}}
        start = self._clock()
        response = self._send(body, stream=True)
        parts: list[str] = []
        finish = ""
        usage: dict[str, Any] = {}
        try:
            for line in response.iter_lines():
                if not line.startswith("data:"):
                    continue
                payload = line[len("data:") :].strip()
                if payload == "[DONE]":
                    break
                data = json.loads(payload)
                usage = data.get("usage") or (data.get("x_groq") or {}).get("usage") or usage
                for choice in data.get("choices") or []:
                    text = (choice.get("delta") or {}).get("content")
                    if text:
                        parts.append(text)
                        yield text
                    finish = choice.get("finish_reason") or finish
        except httpx.TransportError as exc:
            raise ProviderError(
                f"{self.name}: the stream broke ({type(exc).__name__})",
                provider=self.provider,
                code="stream_broken",
            ) from exc
        finally:
            response.close()
        latency_ms = (self._clock() - start) * 1000
        yield self._finish("".join(parts), finish, usage, response.headers, latency_ms)

    def _send(self, body: dict[str, Any], *, stream: bool) -> httpx.Response:
        """A successful response, after the retries and waits the mode allows."""
        http = self._client()
        waited = 0.0
        problem, status, code = "", None, None
        for attempt in range(MAX_RETRIES + 1):
            asked = 0.0  # how long the provider asked us to wait
            try:
                request = http.build_request("POST", self.url, json=body)
                response = http.send(request, stream=stream)
            except httpx.TimeoutException as exc:
                problem, status, code = f"timed out after {TIMEOUT_SECONDS:.0f} s", None, "timeout"
                if self.mode == "live":
                    raise self._unavailable(problem, status, code) from exc
            except httpx.TransportError as exc:
                problem, status, code = f"{type(exc).__name__}: {exc}", None, "connection_error"
                if self.mode == "live":
                    raise self._unavailable(problem, status, code) from exc
            else:
                if response.status_code < 400:
                    return response
                if stream:
                    response.read()
                    response.close()
                status, code = response.status_code, _error_field(response, "code")
                problem = f"HTTP {status}: {_message(response)}"
                if _unavailable(response):
                    log.error("provider unavailable: %s: %s", self.name, problem)
                    raise self._unavailable(problem, status, code)
                if status != 429 and status < 500:
                    raise ProviderError(
                        f"{self.name}: {problem}", provider=self.provider, status=status, code=code
                    )
                asked = _retry_after(response)
            if attempt == MAX_RETRIES:
                break
            wait = max(BACKOFF_SECONDS * 2**attempt, asked)
            if self.mode == "live":
                if waited + wait > LIVE_WAIT_BUDGET_SECONDS:
                    raise self._unavailable(
                        f"{problem}; waiting {wait:.0f} s more would pass the "
                        f"{LIVE_WAIT_BUDGET_SECONDS:.0f} s live limit",
                        status,
                        code,
                    )
            else:
                wait = min(wait, BATCH_MAX_WAIT_SECONDS)
            log.warning("%s: %s; retrying in %.1f s", self.name, problem, wait)
            self._sleep(wait)
            waited += wait
        if self.mode == "live":
            raise self._unavailable(f"{problem}; gave up after {MAX_RETRIES} retries", status, code)
        raise ProviderError(
            f"{self.name}: {problem}; gave up after {MAX_RETRIES} retries, so the run stops",
            provider=self.provider,
            status=status,
            code=code,
        )

    def _unavailable(
        self, problem: str, status: int | None, code: str | None
    ) -> ProviderUnavailable:
        return ProviderUnavailable(
            f"{self.name}: {problem}", provider=self.provider, status=status, code=code
        )

    def _body(
        self,
        messages: list[Message],
        max_tokens: int,
        temperature: float | None,
        json_schema: dict[str, Any] | None,
        tools: list[dict[str, Any]] | None,
        tool_choice: str | dict[str, Any] | None,
    ) -> dict[str, Any]:
        if json_schema is not None and not self.json_schema:
            raise ValueError(f"json_schema output is not checked for {self.name} in the registry")
        if tools and not self.tool_calls:
            raise ValueError(f"tool calling is not checked for {self.name} in the registry")
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
        if tools:
            body["tools"] = tools
            if tool_choice is not None:
                body["tool_choice"] = tool_choice
        return body

    def _client(self) -> httpx.Client:
        if self._http is None:
            key = (self._api_key or os.environ.get(self.api_key_env, "")).strip()
            if not key:
                message = f"{self.name}: {self.api_key_env} is not set (see .env.example)"
                log.error("provider unavailable: %s", message)
                raise ProviderUnavailable(message, provider=self.provider, code="missing_key")
            self._http = httpx.Client(
                headers={"Authorization": f"Bearer {key}"},
                timeout=TIMEOUT_SECONDS,
                transport=self._transport,
            )
        return self._http

    def _finish(
        self,
        text: str,
        finish_reason: str,
        usage: dict[str, Any],
        headers: httpx.Headers,
        latency_ms: float,
        *,
        tool_calls: list[ToolCall] | None = None,
        message: dict[str, Any] | None = None,
    ) -> Completion:
        """The completion with its cost; raise if it is incomplete or, in batch, unpriced.

        A reply with tool calls may have no text; one cut off by the token limit is still
        incomplete, because its arguments may be cut off too.
        """
        prompt = _int_or_none(usage.get("prompt_tokens"))
        output = _int_or_none(usage.get("completion_tokens"))
        billed_output = output
        total = _int_or_none(usage.get("total_tokens"))
        if output is not None and prompt is not None and total is not None:
            # Thinking tokens left out of completion_tokens are still billed as output.
            billed_output = max(output, total - prompt)
        completion = Completion(
            text=text,
            prompt_tokens=prompt,
            completion_tokens=output,
            model=self.name,
            latency_ms=latency_ms,
            cost_usd=chat_cost_usd(self.name, prompt, billed_output),
            finish_reason=finish_reason,
            rate_limits={k: v for k, v in headers.items() if k.lower().startswith("x-ratelimit-")},
            usage=usage,
            tool_calls=tool_calls or [],
            message=message if message is not None else {"role": "assistant", "content": text},
        )
        incomplete = completion.finish_reason == "length" or (
            not completion.tool_calls
            and (not completion.text.strip() or completion.finish_reason != "stop")
        )
        if incomplete:
            raise IncompleteAnswer(
                f"{self.name}: incomplete answer (finish_reason={completion.finish_reason!r}, "
                f"{len(completion.text)} characters, completion_tokens={output})",
                completion,
                provider=self.provider,
                code=(
                    f"incomplete_{finish_reason or 'none'}"
                    if completion.text.strip()
                    else "incomplete_empty"
                ),
            )
        if completion.cost_usd is None:
            if self.mode == "batch":
                raise UnknownCostError(
                    f"{self.name}: the reply has no token usage, so its cost is unknown; "
                    "a batch run needs every cost",
                    provider=self.provider,
                    code="no_usage",
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
