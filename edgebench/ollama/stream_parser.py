from __future__ import annotations

import json
from typing import Any


def parse_stream_line(raw_line: str) -> dict[str, Any] | None:
    line = raw_line.strip()
    if not line:
        return None
    payload = json.loads(line)
    if not isinstance(payload, dict):
        return None
    return payload
