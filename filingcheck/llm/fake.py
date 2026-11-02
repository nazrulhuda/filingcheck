"""A scripted chat model for tests: no network, no cost."""

import re
from collections.abc import Iterable, Iterator
from typing import Any

from filingcheck.llm.chat import Completion, Message


class FakeChat:
    """Replies with the next scripted item: a text, a whole `Completion`, or an error to raise."""

    def __init__(
        self,
        replies: Iterable[str | Completion | Exception],
        *,
        name: str = "fake:chat",
        prompt_tokens: int = 100,
        completion_tokens: int = 20,
    ) -> None:
        self.name = name
        self.replies = list(replies)
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens
        self.calls: list[dict[str, Any]] = []

    def complete(
        self,
        messages: list[Message],
        *,
        max_tokens: int,
        temperature: float | None = None,
        json_schema: dict[str, Any] | None = None,
    ) -> Completion:
        """The next scripted reply; every call is recorded in `calls`."""
        self.calls.append(
            {
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "json_schema": json_schema,
            }
        )
        reply = self.replies.pop(0)
        if isinstance(reply, Exception):
            raise reply
        if isinstance(reply, Completion):
            return reply
        return Completion(
            text=reply,
            prompt_tokens=self.prompt_tokens,
            completion_tokens=self.completion_tokens,
            model=self.name,
            latency_ms=0.0,
            cost_usd=0.0,
            finish_reason="stop",
        )

    def stream(
        self,
        messages: list[Message],
        *,
        max_tokens: int,
        temperature: float | None = None,
    ) -> Iterator[str | Completion]:
        """The next scripted reply word by word, then the whole `Completion`."""
        completion = self.complete(messages, max_tokens=max_tokens, temperature=temperature)
        yield from re.findall(r"\S+\s*|\s+", completion.text)
        yield completion
