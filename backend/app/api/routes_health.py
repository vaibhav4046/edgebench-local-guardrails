from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from edgebench.ollama.client import OllamaClient

router = APIRouter(prefix="/api/v1", tags=["health"])


@router.get("/health")
def health() -> dict[str, Any]:
    client = OllamaClient()
    return {
        "ok": True,
        "service": "edgebench-backend",
        "ollama_reachable": client.check_health(),
    }
