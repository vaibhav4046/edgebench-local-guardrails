from __future__ import annotations

import json
from typing import Any


def normalize_json_text(payload: dict[str, Any]) -> str:
    """Stable JSON for deterministic hashing."""
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
