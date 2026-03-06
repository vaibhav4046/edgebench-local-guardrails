from __future__ import annotations

import hashlib


def sha256_hexdigest(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()
