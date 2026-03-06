from __future__ import annotations

from typing import Any

from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/models", tags=["models"])


@router.get("/suggestions")
def model_suggestions() -> dict[str, Any]:
    return {
        "models": [
            {
                "model_key": "llama3.2-mini",
                "suggested_tags": [
                    "llama3.2:1b-instruct-q4_K_M",
                    "llama3.2:3b-instruct-q5_K_M",
                    "llama3.2:latest",
                ],
            },
            {
                "model_key": "54Mini",
                "suggested_tags": ["54Mini:latest", "54mini:q4_K_M", "54mini:fp16"],
            },
            {
                "model_key": "mistral-7b",
                "suggested_tags": ["mistral:7b-instruct", "mistral:latest", "mistral:q8_0"],
            },
        ],
        "note": "Tags are suggestions only. Use tags that exist in your local Ollama instance.",
    }
