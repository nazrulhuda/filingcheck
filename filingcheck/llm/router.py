"""The primary chat model with fallbacks, used in live mode only."""

import itertools
import logging
from collections.abc import Iterator, Sequence
from typing import Any

from filingcheck.llm.chat import (
    ChatModel,
    Completion,
    IncompleteAnswer,
    Message,
    Mode,
    ProviderUnavailable,
)

log = logging.getLogger(__name__)


class ModelRouter:
    """Tries the primary, then each fallback; records who answered.

    In live mode a model that is unavailable or whose reply is empty or cut off is skipped,
    and if every model fails the last error is raised. In batch mode only the primary is ever
    called: a baseline file or an eval row answered by two different models would measure
    nothing, so a failure stops the run instead.
    """

    def __init__(
        self, primary: ChatModel, fallbacks: Sequence[ChatModel] = (), *, mode: Mode = "batch"
    ) -> None:
        self.primary = primary
        self.fallbacks = list(fallbacks)
        self.mode = mode
        self.name = primary.name
        self.last_model: str | None = None
        self.last_completion: Completion | None = None  # tokens and rate-limit headers
        self.fallbacks_used = 0  # live answers that came from a fallback

    def in_turn(self) -> list[ChatModel]:
        """The models a whole run may use, primary first: the fallbacks too in live mode only.

        For the agent, which restarts a failed run with the next model instead of handing a
        half-finished conversation to it (see `run_agent_with_fallbacks`).
        """
        return [self.primary] if self.mode == "batch" else [self.primary, *self.fallbacks]

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
        """The first reply from the primary or, in live mode, a fallback."""
        models = [self.primary] if self.mode == "batch" else [self.primary, *self.fallbacks]
        failure: ProviderUnavailable | IncompleteAnswer | None = None
        for i, model in enumerate(models):
            try:
                completion = model.complete(
                    messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    json_schema=json_schema,
                    tools=tools,
                    tool_choice=tool_choice,
                )
            except (ProviderUnavailable, IncompleteAnswer) as exc:
                if self.mode == "batch":
                    raise
                log.warning("%s failed (%s); trying the next model", model.name, exc)
                failure = exc
                continue
            self.last_model = completion.model
            self.last_completion = completion
            if i > 0:
                self.fallbacks_used += 1
            return completion
        assert failure is not None
        raise failure

    def stream(
        self,
        messages: list[Message],
        *,
        max_tokens: int,
        temperature: float | None = None,
    ) -> Iterator[str | Completion]:
        """The reply's text in pieces, then the `Completion`.

        In live mode a model that fails before its first piece of text is skipped like in
        `complete`. Once text has been sent the answer belongs to that model: a failure after
        that is raised, because the text already shown cannot be taken back by a fallback.
        """
        models = [self.primary] if self.mode == "batch" else [self.primary, *self.fallbacks]
        failure: ProviderUnavailable | IncompleteAnswer | None = None
        for i, model in enumerate(models):
            events = model.stream(messages, max_tokens=max_tokens, temperature=temperature)
            try:
                first = next(events)
            except (ProviderUnavailable, IncompleteAnswer) as exc:
                if self.mode == "batch":
                    raise
                log.warning("%s failed (%s); trying the next model", model.name, exc)
                failure = exc
                continue
            for event in itertools.chain([first], events):
                if isinstance(event, Completion):
                    self.last_model = event.model
                    self.last_completion = event
                    if i > 0:
                        self.fallbacks_used += 1
                yield event
            return
        assert failure is not None
        raise failure
