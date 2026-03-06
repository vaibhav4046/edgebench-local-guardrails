from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class FailureType(StrEnum):
    JSON_PARSE_ERROR = "JSON_PARSE_ERROR"
    SCHEMA_VALIDATION_ERROR = "SCHEMA_VALIDATION_ERROR"
    TIMEOUT = "TIMEOUT"
    OLLAMA_ERROR = "OLLAMA_ERROR"
    UNKNOWN = "UNKNOWN"


class EdgeBenchError(Exception):
    """Base exception for benchmark failures."""


@dataclass(slots=True)
class OllamaError(EdgeBenchError):
    message: str
    status_code: int | None = None

    def __str__(self) -> str:
        if self.status_code is None:
            return self.message
        return f"{self.message} (status={self.status_code})"


@dataclass(slots=True)
class TimeoutError(EdgeBenchError):
    message: str


@dataclass(slots=True)
class SchemaError(EdgeBenchError):
    message: str


@dataclass(slots=True)
class JsonParseError(EdgeBenchError):
    message: str
