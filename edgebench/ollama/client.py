from __future__ import annotations

import logging
from time import perf_counter
from typing import Any

import httpx

from edgebench.errors import OllamaError, TimeoutError
from edgebench.ollama.stream_parser import parse_stream_line

LOGGER = logging.getLogger(__name__)


class OllamaClient:
    def __init__(self, base_url: str = "http://127.0.0.1:11434") -> None:
        self.base_url = base_url.rstrip("/")

    def check_health(self, timeout_seconds: int = 3) -> bool:
        try:
            with httpx.Client(timeout=timeout_seconds) as client:
                resp = client.get(f"{self.base_url}/api/tags")
                return resp.status_code == 200
        except Exception:
            return False

    def stream_chat(
        self,
        model_tag: str,
        messages: list[dict[str, str]],
        options: dict[str, Any],
        timeout_seconds: int,
    ) -> dict[str, Any]:
        payload = {
            "model": model_tag,
            "messages": messages,
            "stream": True,
            "options": options,
        }

        full_text_parts: list[str] = []
        final_stats: dict[str, Any] = {}
        started = perf_counter()
        ttft_seconds: float | None = None

        try:
            with httpx.Client(timeout=timeout_seconds) as client:
                with client.stream("POST", f"{self.base_url}/api/chat", json=payload) as response:
                    if response.status_code >= 400:
                        body_text = response.read().decode("utf-8", errors="ignore")
                        raise OllamaError(
                            message=f"Ollama HTTP error: {body_text}",
                            status_code=response.status_code,
                        )

                    for raw_line in response.iter_lines():
                        if not raw_line:
                            continue
                        chunk = parse_stream_line(raw_line)
                        if chunk is None:
                            continue

                        if "error" in chunk and chunk["error"]:
                            raise OllamaError(message=str(chunk["error"]))

                        message = chunk.get("message") or {}
                        piece = message.get("content")
                        if piece:
                            full_text_parts.append(piece)
                            if ttft_seconds is None:
                                ttft_seconds = perf_counter() - started

                        if chunk.get("done") is True:
                            final_stats = chunk
        except httpx.TimeoutException as exc:
            raise TimeoutError(message=f"Ollama request timed out after {timeout_seconds}s") from exc
        except OllamaError:
            raise
        except Exception as exc:  # pragma: no cover
            LOGGER.exception("Unexpected Ollama stream error")
            raise OllamaError(message=str(exc)) from exc

        total_latency = perf_counter() - started
        return {
            "raw_output": "".join(full_text_parts),
            "ttft_seconds": ttft_seconds,
            "total_response_latency_seconds": total_latency,
            "final_stats": final_stats,
        }
