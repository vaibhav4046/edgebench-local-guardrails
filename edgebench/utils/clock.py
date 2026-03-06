from __future__ import annotations

import time
from datetime import UTC, datetime


def now_utc() -> datetime:
    return datetime.now(UTC)


def monotonic_ns() -> int:
    return time.monotonic_ns()


def ns_to_seconds(value_ns: int | None) -> float | None:
    if value_ns is None:
        return None
    return value_ns / 1_000_000_000
