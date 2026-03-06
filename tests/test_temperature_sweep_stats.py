from datetime import UTC, datetime

from edgebench.runner.summarizer import SummaryBuilder


def test_summary_by_temperature_contains_entries():
    builder = SummaryBuilder(
        run_id="r1",
        dataset_path="d.jsonl",
        started_at_utc=datetime.now(UTC),
    )
    builder.add_record(
        {
            "prompt_id": "p1",
            "model_key": "m",
            "model_tag": "m:q4",
            "temperature": 0.2,
            "repeat_index": 0,
            "success": True,
            "attempt_count": 1,
            "failure_type": None,
            "normalized_hash": "abc",
            "metrics": {
                "ttft_seconds": 0.1,
                "total_response_latency_seconds": 1.0,
                "tokens_per_second": 100.0,
            },
        }
    )
    summary = builder.build(datetime.now(UTC), memory_usage={}, gpu_usage={})
    assert summary["by_model_temperature"]
    group = summary["by_model_temperature"]["m|m:q4|0.2"]
    assert group["schema_pass_rate"] == 1.0
    assert group["retry_rate"] == 0.0
    assert group["failure_rate"] == 0.0
