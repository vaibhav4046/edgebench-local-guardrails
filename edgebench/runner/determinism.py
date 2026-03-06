from __future__ import annotations

from typing import Any

from edgebench.utils.hashing import sha256_hexdigest
from edgebench.utils.json_normalize import normalize_json_text


def hash_normalized_json(payload: dict[str, Any]) -> str:
    return sha256_hexdigest(normalize_json_text(payload))


def exact_match_rate(hashes: list[str | None]) -> float:
    valid = [item for item in hashes if item]
    if not valid:
        return 0.0
    first = valid[0]
    matches = sum(1 for item in valid if item == first)
    return matches / len(valid)
