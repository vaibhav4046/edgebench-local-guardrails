from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from edgebench.errors import FailureType, JsonParseError, OllamaError, SchemaError, TimeoutError
from edgebench.ollama.client import OllamaClient
from edgebench.prompts.templates import build_repair_prompt, build_structured_prompt
from edgebench.schema.validator import canonical_schema, parse_json_object, validate_canonical_output, validation_errors
from edgebench.types import AttemptMetrics, AttemptResult, SamplingOptions


def _safe_truncate(value: str, max_bytes: int) -> str:
    raw = value.encode("utf-8", errors="ignore")
    return raw[:max_bytes].decode("utf-8", errors="ignore")


def _compute_tokens_per_second(eval_count: int | None, eval_duration: int | None) -> float | None:
    if eval_count is None or eval_duration is None or eval_duration == 0:
        return None
    return (eval_count / eval_duration) * 1_000_000_000


def _build_metrics(stream_result: dict[str, Any]) -> AttemptMetrics:
    final_stats = stream_result.get("final_stats") or {}
    eval_count = final_stats.get("eval_count")
    eval_duration = final_stats.get("eval_duration")
    return AttemptMetrics(
        ttft_seconds=stream_result.get("ttft_seconds"),
        total_response_latency_seconds=stream_result.get("total_response_latency_seconds"),
        tokens_per_second=_compute_tokens_per_second(eval_count, eval_duration),
        prompt_eval_count=final_stats.get("prompt_eval_count"),
        prompt_eval_duration=final_stats.get("prompt_eval_duration"),
        eval_count=eval_count,
        eval_duration=eval_duration,
        load_duration=final_stats.get("load_duration"),
        total_duration=final_stats.get("total_duration"),
    )


def _run_attempt(
    client: OllamaClient,
    model_tag: str,
    messages: list[dict[str, str]],
    options: SamplingOptions,
    timeout_seconds: int,
    attempt_index: int,
) -> tuple[AttemptResult, FailureType | None]:
    stream_result = client.stream_chat(
        model_tag=model_tag,
        messages=messages,
        options=options.model_dump(mode="json", exclude_none=True),
        timeout_seconds=timeout_seconds,
    )
    raw_output = stream_result.get("raw_output", "")
    metrics = _build_metrics(stream_result)

    try:
        parsed = parse_json_object(raw_output)
    except JsonParseError as exc:
        return (
            AttemptResult(
                attempt_index=attempt_index,
                raw_output=raw_output,
                parsed_json=None,
                validation_errors=[{"msg": str(exc)}],
                is_valid=False,
                metrics=metrics,
            ),
            FailureType.JSON_PARSE_ERROR,
        )

    errors = validation_errors(parsed)
    if errors:
        return (
            AttemptResult(
                attempt_index=attempt_index,
                raw_output=raw_output,
                parsed_json=parsed,
                validation_errors=errors,
                is_valid=False,
                metrics=metrics,
            ),
            FailureType.SCHEMA_VALIDATION_ERROR,
        )

    validated = validate_canonical_output(parsed)
    return (
        AttemptResult(
            attempt_index=attempt_index,
            raw_output=raw_output,
            parsed_json=validated.model_dump(mode="json"),
            validation_errors=[],
            is_valid=True,
            metrics=metrics,
        ),
        None,
    )


def run_with_retry(
    client: OllamaClient,
    model_tag: str,
    user_prompt: str,
    options: SamplingOptions,
    timeout_seconds: int,
    raw_output_max_bytes: int,
    max_attempts: int = 2,
) -> dict[str, Any]:
    # Mandatory contract: exactly one retry max.
    max_attempts = 2
    schema = canonical_schema()

    attempts: list[AttemptResult] = []
    failure_type: FailureType | None = None

    # Attempt 1
    attempt1, failure1 = _run_attempt(
        client=client,
        model_tag=model_tag,
        messages=build_structured_prompt(user_prompt=user_prompt, schema=schema),
        options=options,
        timeout_seconds=timeout_seconds,
        attempt_index=1,
    )
    attempts.append(attempt1)

    if attempt1.is_valid:
        return {
            "success": True,
            "attempt_count": 1,
            "attempts": [a.model_dump(mode="json") for a in attempts],
            "final_output": attempt1.parsed_json,
            "failure_type": None,
            "validation_errors": [],
            "raw_output": _safe_truncate(attempt1.raw_output, raw_output_max_bytes),
            "metrics": attempt1.metrics.model_dump(mode="json"),
        }

    failure_type = failure1
    should_retry = failure1 in {FailureType.JSON_PARSE_ERROR, FailureType.SCHEMA_VALIDATION_ERROR}

    if should_retry and max_attempts == 2:
        repair_messages = build_repair_prompt(
            original_prompt=user_prompt,
            invalid_output=attempt1.raw_output,
            validation_errors=attempt1.validation_errors,
            schema=schema,
        )
        attempt2, failure2 = _run_attempt(
            client=client,
            model_tag=model_tag,
            messages=repair_messages,
            options=options,
            timeout_seconds=timeout_seconds,
            attempt_index=2,
        )
        attempts.append(attempt2)
        failure_type = failure2

        if attempt2.is_valid:
            return {
                "success": True,
                "attempt_count": 2,
                "attempts": [a.model_dump(mode="json") for a in attempts],
                "final_output": attempt2.parsed_json,
                "failure_type": None,
                "validation_errors": [],
                "raw_output": _safe_truncate(attempt2.raw_output, raw_output_max_bytes),
                "metrics": attempt2.metrics.model_dump(mode="json"),
            }

    final_attempt = attempts[-1]
    final_failure = failure_type or FailureType.UNKNOWN
    graceful_failure_output = {
        "status": "failure",
        "error_type": final_failure.value,
        "attempt_count": len(attempts),
        "validation_errors": final_attempt.validation_errors,
    }
    return {
        "success": False,
        "attempt_count": len(attempts),
        "attempts": [a.model_dump(mode="json") for a in attempts],
        "final_output": graceful_failure_output,
        "failure_type": final_failure,
        "validation_errors": final_attempt.validation_errors,
        "raw_output": _safe_truncate(final_attempt.raw_output, raw_output_max_bytes),
        "metrics": final_attempt.metrics.model_dump(mode="json"),
    }


def classify_exception(exc: Exception) -> FailureType:
    if isinstance(exc, TimeoutError):
        return FailureType.TIMEOUT
    if isinstance(exc, OllamaError):
        return FailureType.OLLAMA_ERROR
    if isinstance(exc, JsonParseError):
        return FailureType.JSON_PARSE_ERROR
    if isinstance(exc, SchemaError):
        return FailureType.SCHEMA_VALIDATION_ERROR
    if isinstance(exc, ValidationError):
        return FailureType.SCHEMA_VALIDATION_ERROR
    return FailureType.UNKNOWN
