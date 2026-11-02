"""What every chat model takes and returns, and the errors callers handle."""

from typing import Any, Literal, Protocol

from pydantic import BaseModel, Field

Mode = Literal["live", "batch"]
Message = dict[str, str]  # {"role": "system" | "user" | "assistant", "content": ...}


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
    ) -> Completion:
        """One reply; `temperature=None` means the model's setting from the registry."""
        ...


class ProviderError(RuntimeError):
    """A provider call failed in a way another model would not fix; the run stops."""


class ProviderUnavailable(ProviderError):  # noqa: N818
    """The provider cannot answer now (wrong key, missing model, limits, timeout): fall back."""


class UnknownCostError(ProviderError):
    """A batch run got a reply without token usage, so its cost would be unknown."""


class IncompleteAnswer(ProviderError):  # noqa: N818
    """The reply was empty or cut off (finish_reason other than "stop"); never shown."""

    def __init__(self, message: str, completion: Completion) -> None:
        super().__init__(message)
        self.completion = completion
