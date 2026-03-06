from __future__ import annotations

from edgebench.runner.retry_pipeline import run_with_retry
from edgebench.types import SamplingOptions


class StubClient:
    def __init__(self):
        self.calls = 0

    def stream_chat(self, model_tag, messages, options, timeout_seconds):
        self.calls += 1
        if self.calls == 1:
            return {
                "raw_output": "not-json",
                "ttft_seconds": 0.1,
                "total_response_latency_seconds": 0.5,
                "final_stats": {"eval_count": 10, "eval_duration": 1_000_000_000},
            }
        return {
            "raw_output": '{"answer":"ok","category":"qa","confidence":0.6,"key_points":["x"]}',
            "ttft_seconds": 0.1,
            "total_response_latency_seconds": 0.5,
            "final_stats": {"eval_count": 10, "eval_duration": 1_000_000_000},
        }


class AlwaysInvalidClient:
    def stream_chat(self, model_tag, messages, options, timeout_seconds):
        _ = model_tag, messages, options, timeout_seconds
        return {
            "raw_output": "invalid-json",
            "ttft_seconds": 0.1,
            "total_response_latency_seconds": 0.5,
            "final_stats": {"eval_count": 10, "eval_duration": 1_000_000_000},
        }


def test_retry_pipeline_uses_exactly_one_retry_on_invalid_json():
    client = StubClient()
    outcome = run_with_retry(
        client=client,
        model_tag="test",
        user_prompt="hello",
        options=SamplingOptions(),
        timeout_seconds=5,
        raw_output_max_bytes=8192,
    )
    assert outcome["success"] is True
    assert outcome["attempt_count"] == 2
    assert client.calls == 2


def test_retry_pipeline_returns_graceful_failure_json_after_retry_failure():
    outcome = run_with_retry(
        client=AlwaysInvalidClient(),
        model_tag="test",
        user_prompt="hello",
        options=SamplingOptions(),
        timeout_seconds=5,
        raw_output_max_bytes=8192,
    )
    assert outcome["success"] is False
    assert outcome["attempt_count"] == 2
    assert outcome["final_output"]["status"] == "failure"
    assert outcome["final_output"]["error_type"] == "JSON_PARSE_ERROR"
