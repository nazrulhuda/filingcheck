"""Model prices, read from `pricing.yaml`, and the cost of a call."""

from pathlib import Path
from typing import Any

import yaml

PRICING_FILE = Path(__file__).resolve().parent / "pricing.yaml"
PRICING: dict[str, Any] = yaml.safe_load(PRICING_FILE.read_text(encoding="utf-8"))


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
