"""A scripted chat model for tests: no network, no cost."""

import itertools
import json
import re
from collections.abc import Iterable, Iterator
from typing import Any

from filingcheck.llm.chat import Completion, Message, ToolCall

_CALL_IDS = itertools.count(1)


def scripted_tool_calls(
    *calls: tuple[str, dict[str, Any]], model: str = "fake:chat", text: str = ""
) -> Completion:
    """A scripted reply that asks for tool calls, shaped like a provider's reply."""
    tool_calls = [
        ToolCall(id=f"call_{next(_CALL_IDS)}", name=name, arguments=json.dumps(arguments))
        for name, arguments in calls
    ]
    message = {
        "role": "assistant",
        "content": text or None,
        "tool_calls": [
            {
                "id": call.id,
                "type": "function",
                "function": {"name": call.name, "arguments": call.arguments},
            }
            for call in tool_calls
        ],
    }
    return Completion(
        text=text,
        prompt_tokens=100,
        completion_tokens=20,
        model=model,
        latency_ms=0.0,
        cost_usd=0.0,
        finish_reason="tool_calls",
        tool_calls=tool_calls,
        message=message,
    )


class FakeChat:
    """Replies with the next scripted item: a text, a whole `Completion`, or an error to raise.

    A scripted `Completion` can carry tool calls (see `scripted_tool_calls`), so the agent is
    tested without a model.
    """

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
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str | dict[str, Any] | None = None,
    ) -> Completion:
        """The next scripted reply; every call is recorded in `calls`."""
        self.calls.append(
            {
                "messages": list(messages),
                "max_tokens": max_tokens,
                "temperature": temperature,
                "json_schema": json_schema,
                "tools": tools,
                "tool_choice": tool_choice,
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
            message={"role": "assistant", "content": reply},
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
