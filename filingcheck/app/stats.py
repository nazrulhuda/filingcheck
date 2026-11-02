"""The /stats summary of the request log."""

from typing import Any

from filingcheck.app.store import REFUSED, RequestRow


def percentile(values: list[float], p: float) -> float | None:
    """The p-th percentile with linear interpolation between ranks; None for no values."""
    if not values:
        return None
    ordered = sorted(values)
    position = (len(ordered) - 1) * p / 100
    low = int(position)
    high = min(low + 1, len(ordered) - 1)
    return ordered[low] + (ordered[high] - ordered[low]) * (position - low)


def compute_stats(rows: list[RequestRow], primary: str) -> dict[str, Any]:
    """Counts, latency, cost, abstain rate and fallbacks for the rows given."""
    answered = [r for r in rows if r.error is None and r.model_used is not None]
    errors = [r for r in rows if r.error is not None and not r.error.startswith(REFUSED)]
    latencies = [r.latency_ms for r in answered if r.latency_ms is not None]
    return {
        "requests": len(rows),
        "answered": len(answered),
        "errors": len(errors),
        "refused_daily_cap": sum(1 for r in rows if r.error == REFUSED + "daily_cap"),
        "latency_ms_p50": percentile(latencies, 50),
        "latency_ms_p95": percentile(latencies, 95),
        "cost_usd": sum(r.cost_usd for r in answered if r.cost_usd is not None),
        "unknown_cost": sum(1 for r in answered if r.cost_usd is None),
        "abstain_rate": (
            sum(1 for r in answered if r.abstained) / len(answered) if answered else None
        ),
        "fallbacks": sum(1 for r in answered if r.model_used != primary),
        "degraded": sum(1 for r in answered if r.degraded),
    }
