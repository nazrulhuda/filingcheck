"""The provider registry (`providers.yaml`) and building chat models and the router from it."""

import os
import time
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

import httpx
import yaml
from pydantic import BaseModel, Field

from filingcheck.llm.chat import Mode
from filingcheck.llm.openai_compatible import OpenAICompatibleChat
from filingcheck.llm.router import ModelRouter

REGISTRY_FILE = Path(__file__).resolve().parent / "providers.yaml"
DEFAULT_CHAT_MODEL = "groq:openai/gpt-oss-20b"
DEFAULT_FALLBACK_MODELS = "gemini:gemini-3.5-flash-lite"


class ProviderConfig(BaseModel):
    """Where a provider lives and which name it takes for the token limit (None: send none)."""

    base_url: str
    api_key_env: str
    token_limit_param: str | None
    source: str


class ModelConfig(BaseModel):
    """Per-model settings; `temperature` None keeps the provider's default and is never sent."""

    temperature: float | None = None
    params: dict[str, Any] = Field(default_factory=dict)
    json_schema: bool = False
    source: str


class Registry(BaseModel):
    """Every provider and model the project may call, keyed "provider:model"."""

    checked_on: str
    providers: dict[str, ProviderConfig]
    models: dict[str, ModelConfig]


def load_registry(path: Path = REGISTRY_FILE) -> Registry:
    """The registry as written in `providers.yaml`."""
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    data["checked_on"] = str(data["checked_on"])
    return Registry.model_validate(data)


def make_chat(
    spec: str,
    *,
    mode: Mode,
    registry: Registry | None = None,
    api_key: str | None = None,
    transport: httpx.BaseTransport | None = None,
    sleep: Callable[[float], None] = time.sleep,
) -> OpenAICompatibleChat:
    """A client for "provider:model", refusing anything not in the registry."""
    registry = registry or load_registry()
    provider_name, _, model = spec.partition(":")
    provider = registry.providers.get(provider_name)
    settings = registry.models.get(spec)
    if not model or provider is None or settings is None:
        raise ValueError(
            f"{spec!r} is not in the provider registry ({REGISTRY_FILE.name}); "
            "read the provider's docs and add it there first"
        )
    return OpenAICompatibleChat(
        provider.base_url,
        provider.api_key_env,
        model,
        token_limit_param=provider.token_limit_param,
        name=spec,
        temperature=settings.temperature,
        params=settings.params,
        json_schema=settings.json_schema,
        mode=mode,
        api_key=api_key,
        transport=transport,
        sleep=sleep,
    )


def router_from_env(mode: Mode, env: Mapping[str, str] | None = None) -> ModelRouter:
    """The router from FC_CHAT_MODEL and FC_FALLBACK_MODELS (comma-separated)."""
    env = os.environ if env is None else env
    registry = load_registry()
    primary = env.get("FC_CHAT_MODEL") or DEFAULT_CHAT_MODEL
    fallbacks = env.get("FC_FALLBACK_MODELS") or DEFAULT_FALLBACK_MODELS
    return ModelRouter(
        make_chat(primary.strip(), mode=mode, registry=registry),
        [
            make_chat(spec.strip(), mode=mode, registry=registry)
            for spec in fallbacks.split(",")
            if spec.strip()
        ],
        mode=mode,
    )


def describe_settings(spec: str, max_tokens: int, registry: Registry | None = None) -> str:
    """One line of model settings to write next to every saved result."""
    registry = registry or load_registry()
    provider = registry.providers[spec.partition(":")[0]]
    settings = registry.models[spec]
    temperature = "provider default" if settings.temperature is None else settings.temperature
    reasoning = settings.params.get("reasoning_effort", "provider default")
    limit = (
        f"{provider.token_limit_param} {max_tokens}"
        if provider.token_limit_param
        else "no token limit sent"
    )
    return f"model {spec}, temperature {temperature}, reasoning effort {reasoning}, {limit}"
