from __future__ import annotations

from collections.abc import Iterable


def mean(values: Iterable[float]) -> float:
    vals = list(values)
    return (sum(vals) / len(vals)) if vals else 0.0


def percentile(values: Iterable[float], p: float) -> float:
    vals = sorted(values)
    if not vals:
        return 0.0
    if len(vals) == 1:
        return vals[0]
    pos = (len(vals) - 1) * p
    low = int(pos)
    high = min(low + 1, len(vals) - 1)
    frac = pos - low
    return vals[low] * (1.0 - frac) + vals[high] * frac


def summary(values: Iterable[float]) -> dict[str, float]:
    vals = list(values)
    return {
        "mean": mean(vals),
        "p50": percentile(vals, 0.5),
        "p95": percentile(vals, 0.95),
    }
