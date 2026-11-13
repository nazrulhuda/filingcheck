"""What every chat model takes and returns, and the errors callers handle."""

import re
from collections.abc import Iterator
from typing import Any, Literal, Protocol

from pydantic import BaseModel, Field

Mode = Literal["live", "batch"]
# {"role": "system" | "user" | "assistant" | "tool", "content": ...}; an assistant message may
# carry "tool_calls", and a tool message carries "tool_call_id".
Message = dict[str, Any]
CODE_CHARS_RE = re.compile(r"[^A-Za-z0-9_.-]")
MAX_CODE_CHARS = 60


class ToolCall(BaseModel):
    """One tool call a model asked for; `arguments` is the JSON text as the model wrote it."""

    id: str
    name: str
    arguments: str


class Completion(BaseModel):
    """One chat reply with what it cost; token counts and cost are None when not reported."""

    text: str
    prompt_tokens: int | None
    completion_tokens: int | None
    model: str  # "provider:model", the model that answered
    latency_ms: float
    cost_usd: float | None
    finish_reason: str
    rate_limits: dict[str, str] = Field(default_factory=dict)  # the x-ratelimit-* headers
    usage: dict[str, Any] = Field(default_factory=dict)  # the usage object as the provider sent it
    tool_calls: list[ToolCall] = Field(default_factory=list)
    # The assistant message exactly as the provider returned it. A tool-calling turn sends it
    # back unchanged, so provider fields such as Gemini 3's thought signatures survive.
    message: dict[str, Any] = Field(default_factory=dict)


class ChatModel(Protocol):
    """A chat model the baseline, the agent and the API call through."""

    name: str

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
        """One reply; `temperature=None` means the model's setting from the registry.

        With `tools`, the reply may be tool calls instead of text (`Completion.tool_calls`).
        """
        ...

    def stream(
        self,
        messages: list[Message],
        *,
        max_tokens: int,
        temperature: float | None = None,
    ) -> Iterator[str | Completion]:
        """The reply's text in pieces as it arrives, then the whole `Completion`."""
        ...


class ProviderError(RuntimeError):
    """A provider call failed in a way another model would not fix; the run stops.

    The message may hold the provider's own text (Groq's 429 names the organization), so
    only `log_code` (provider, HTTP status, the provider's error code) may be stored or shown.
    """

    def __init__(
        self,
        message: str,
        *,
        provider: str | None = None,
        status: int | None = None,
        code: str | None = None,
    ) -> None:
        super().__init__(message)
        self.provider = provider
        self.status = status
        self.code = code

    @property
    def log_code(self) -> str:
        """For example "groq 429 rate_limit_exceeded"; "-" marks a part that is unknown."""
        code = CODE_CHARS_RE.sub("_", self.code)[:MAX_CODE_CHARS] if self.code else "-"
        provider = CODE_CHARS_RE.sub("_", self.provider)[:20] if self.provider else "-"
        return f"{provider} {self.status if self.status is not None else '-'} {code}"


class ProviderUnavailable(ProviderError):  # noqa: N818
    """The provider cannot answer now (wrong key, missing model, limits, timeout): fall back."""


class UnknownCostError(ProviderError):
    """A batch run got a reply without token usage, so its cost would be unknown."""


ERROR_KINDS = ("tool_choice_none", "rate_limit", "cut_off", "provider_5xx", "other")


def error_kind(exc: ProviderError) -> str:
    """The failure's kind, one of ERROR_KINDS, read from the error in memory.

    The provider's message may name the organization (Groq's 429 does), so it is read here to
    pick a kind and never stored: only the kind and `log_code` are.
    """
    message = str(exc).lower()
    if isinstance(exc, IncompleteAnswer):
        return "cut_off"
    if "tool choice is none" in message:
        return "tool_choice_none"
    if exc.status == 429 or "rate limit" in message or "rate_limit" in (exc.code or ""):
        return "rate_limit"
    if exc.status is not None and 500 <= exc.status < 600:
        return "provider_5xx"
    return "other"


class IncompleteAnswer(ProviderError):  # noqa: N818
    """The reply was empty or cut off (finish_reason other than "stop"); never shown."""

    def __init__(
        self,
        message: str,
        completion: Completion,
        *,
        provider: str | None = None,
        code: str | None = None,
    ) -> None:
        super().__init__(message, provider=provider, code=code)
        self.completion = completion
