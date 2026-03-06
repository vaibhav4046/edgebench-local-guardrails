from __future__ import annotations

import json
from typing import Any

from pydantic import ValidationError

from edgebench.errors import JsonParseError, SchemaError
from edgebench.schema.canonical import CanonicalOutput


def canonical_schema() -> dict[str, Any]:
    return CanonicalOutput.model_json_schema()


def parse_json_object(raw_text: str) -> dict[str, Any]:
    try:
        payload = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise JsonParseError(str(exc)) from exc

    if not isinstance(payload, dict):
        raise JsonParseError("Root value must be a JSON object")
    return payload


def validate_canonical_output(payload: dict[str, Any]) -> CanonicalOutput:
    try:
        return CanonicalOutput.model_validate(payload)
    except ValidationError as exc:
        raise SchemaError(exc.json()) from exc


def validation_errors(payload: dict[str, Any]) -> list[dict[str, Any]]:
    try:
        CanonicalOutput.model_validate(payload)
        return []
    except ValidationError as exc:
        return [dict(item) for item in exc.errors()]
