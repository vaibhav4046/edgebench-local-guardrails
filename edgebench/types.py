from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from edgebench.errors import FailureType


class PromptRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    id: str
    prompt: str
    category: str
    expected: dict[str, Any] | None = None


class ModelEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    model_key: str
    tag: str
    base_url: str = "http://127.0.0.1:11434"
    enabled: bool = True


class SamplingOptions(BaseModel):
    model_config = ConfigDict(extra="forbid")

    temperature: float = 0.2
    top_p: float = 0.9
    top_k: int = 40
    seed: int | None = 42
    num_predict: int | None = 256


class TemperatureSweep(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: bool = False
    values: list[float] = Field(default_factory=lambda: [0.0, 0.2, 0.5, 0.8])


class BenchmarkConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dataset_path: str
    results_root: str = "results"
    repeats: int = 3
    request_timeout_seconds: int = 120
    job_timeout_seconds: int = 0
    stream: bool = True
    max_attempts: int = 2
    raw_output_max_bytes: int = 8192
    sampling: SamplingOptions = Field(default_factory=SamplingOptions)
    deterministic_mode: bool = False
    temperature_sweep: TemperatureSweep = Field(default_factory=TemperatureSweep)


class OllamaFinalStats(BaseModel):
    model_config = ConfigDict(extra="allow")

    model: str | None = None
    created_at: str | None = None
    done: bool = True
    done_reason: str | None = None
    total_duration: int | None = None
    load_duration: int | None = None
    prompt_eval_count: int | None = None
    prompt_eval_duration: int | None = None
    eval_count: int | None = None
    eval_duration: int | None = None


class AttemptMetrics(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ttft_seconds: float | None = None
    total_response_latency_seconds: float | None = None
    tokens_per_second: float | None = None
    prompt_eval_count: int | None = None
    prompt_eval_duration: int | None = None
    eval_count: int | None = None
    eval_duration: int | None = None
    load_duration: int | None = None
    total_duration: int | None = None


class AttemptResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    attempt_index: int
    raw_output: str
    parsed_json: dict[str, Any] | None = None
    validation_errors: list[dict[str, Any]] = Field(default_factory=list)
    is_valid: bool = False
    metrics: AttemptMetrics


class GradeResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    score: float
    passed: bool
    details: dict[str, Any] = Field(default_factory=dict)


class RunStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"


class ResultRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str
    timestamp_utc: datetime
    prompt_id: str
    prompt_category: str
    model_key: str
    model_tag: str
    temperature: float
    repeat_index: int
    deterministic_mode: bool
    attempt_count: int
    success: bool
    failure_type: FailureType | None = None
    validation_errors: list[dict[str, Any]] = Field(default_factory=list)
    raw_output: str | None = None
    normalized_hash: str | None = None
    parsed_output: dict[str, Any] | None = None
    metrics: AttemptMetrics
    grade: GradeResult | None = None


class BenchmarkSummary(BaseModel):
    model_config = ConfigDict(extra="allow")

    run_id: str
    dataset_path: str
    started_at_utc: datetime
    finished_at_utc: datetime
    total_records: int
    success_count: int
    failure_count: int
    retry_count: int
    schema_pass_rate: float
    retry_rate: float
    failure_rate: float
    error_type_counts: dict[str, int]
    by_model: dict[str, Any]
    by_model_temperature: dict[str, Any]
    determinism: dict[str, Any]
    memory_usage: dict[str, Any]
    gpu_usage: dict[str, Any]


class RunJob(BaseModel):
    model_config = ConfigDict(extra="forbid")

    job_id: str
    status: RunStatus
    payload: dict[str, Any]
    created_at_utc: datetime
    updated_at_utc: datetime
    progress_current: int = 0
    progress_total: int = 0
    result_dir: str | None = None
    error_message: str | None = None
    cancel_requested: bool = False
