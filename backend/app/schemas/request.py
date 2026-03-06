from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ModelOverride(BaseModel):
    model_config = ConfigDict(extra="forbid")

    model_key: str
    tag: str
    base_url: str = "http://127.0.0.1:11434"
    enabled: bool = True


class SamplingOverride(BaseModel):
    model_config = ConfigDict(extra="forbid")

    temperature: float
    top_p: float
    top_k: int
    seed: int | None = None
    num_predict: int | None = None


class RunRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dataset_path: str
    models_config_path: str = "config/models.yaml"
    benchmark_config_path: str = "config/benchmark.yaml"
    model_overrides: list[ModelOverride] | None = None
    sampling_override: SamplingOverride | None = None
    results_root: str | None = None
    repeats: int | None = None
    request_timeout_seconds: int | None = None
    job_timeout_seconds: int | None = None
    deterministic_mode: bool = False
    deterministic_config_path: str = "config/deterministic.yaml"
    enable_temperature_sweep: bool = False
    temperatures: list[float] = Field(default_factory=lambda: [0.0, 0.2, 0.5, 0.8])
    scorer_name: Literal["exact_json", "field_level"] = "exact_json"


class CancelRunRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reason: str | None = None
