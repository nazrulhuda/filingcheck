"""Model prices, read from `pricing.yaml`, and the cost of a call."""

from pathlib import Path
from typing import Any

import yaml

PRICING_FILE = Path(__file__).resolve().parent / "pricing.yaml"
PRICING: dict[str, Any] = yaml.safe_load(PRICING_FILE.read_text(encoding="utf-8"))


class MissingPriceError(ValueError):
    """A chat model has no output price; its output must not be counted as free."""


def price_per_million(model: str, kind: str = "input") -> float:
    """The price in dollars per million tokens of `kind` ("input" or "output")."""
    models = PRICING["models"]
    if model not in models:
        raise KeyError(f"no price for model {model} in {PRICING_FILE.name}")
    return float(models[model].get(f"{kind}_per_million", 0.0))


def cost_usd(model: str, input_tokens: int, output_tokens: int = 0) -> float:
    """The dollar cost of a call from its token counts."""
    return (
        input_tokens * price_per_million(model, "input")
        + output_tokens * price_per_million(model, "output")
    ) / 1_000_000


def require_chat_prices(model: str) -> None:
    """Raise unless the chat model has both an input and an output price."""
    entry = PRICING["models"].get(model)
    if entry is None:
        raise KeyError(f"no price for model {model} in {PRICING_FILE.name}")
    for kind in ("input", "output"):
        if f"{kind}_per_million" not in entry:
            raise MissingPriceError(f"{model} has no {kind} price in {PRICING_FILE.name}")


def chat_cost_usd(model: str, input_tokens: int | None, output_tokens: int | None) -> float | None:
    """The dollar cost of a chat call, or None (unknown, never 0) when usage is missing."""
    require_chat_prices(model)
    if input_tokens is None or output_tokens is None:
        return None
    return cost_usd(model, input_tokens, output_tokens)
