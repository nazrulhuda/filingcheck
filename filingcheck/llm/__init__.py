"""Language-model clients and their prices."""

from filingcheck.llm.chat import (
    ChatModel,
    Completion,
    IncompleteAnswer,
    Message,
    Mode,
    ProviderError,
    ProviderUnavailable,
    UnknownCostError,
)
from filingcheck.llm.fake import FakeChat
from filingcheck.llm.openai_compatible import OpenAICompatibleChat
from filingcheck.llm.registry import (
    describe_settings,
    load_registry,
    make_chat,
    router_from_env,
)
from filingcheck.llm.router import ModelRouter

__all__ = [
    "ChatModel",
    "Completion",
    "FakeChat",
    "IncompleteAnswer",
    "Message",
    "Mode",
    "ModelRouter",
    "OpenAICompatibleChat",
    "ProviderError",
    "ProviderUnavailable",
    "UnknownCostError",
    "describe_settings",
    "load_registry",
    "make_chat",
    "router_from_env",
]
