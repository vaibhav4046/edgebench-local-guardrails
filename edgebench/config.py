from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from edgebench.constants import DEFAULT_MAX_ATTEMPTS
from edgebench.types import BenchmarkConfig, ModelEntry, SamplingOptions, TemperatureSweep


def _load_yaml(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def load_models_config(path: str | Path) -> list[ModelEntry]:
    raw = _load_yaml(path)
    models = raw.get("models", [])
    entries: list[ModelEntry] = []
    for item in models:
        entries.append(ModelEntry.model_validate(item))
    return entries


def load_benchmark_config(path: str | Path) -> BenchmarkConfig:
    raw = _load_yaml(path)
    cfg = BenchmarkConfig.model_validate(raw)
    if cfg.max_attempts != DEFAULT_MAX_ATTEMPTS:
        cfg.max_attempts = DEFAULT_MAX_ATTEMPTS
    return cfg


def load_sampling_config(path: str | Path) -> SamplingOptions:
    raw = _load_yaml(path)
    return SamplingOptions.model_validate(raw)


def load_temperature_sweep(path: str | Path) -> TemperatureSweep:
    raw = _load_yaml(path)
    return TemperatureSweep.model_validate(raw)


def safe_validate_benchmark_config(raw: dict[str, Any]) -> tuple[BenchmarkConfig | None, list[str]]:
    try:
        cfg = BenchmarkConfig.model_validate(raw)
    except ValidationError as exc:
        return None, [err.get("msg", "invalid") for err in exc.errors()]

    if cfg.max_attempts != DEFAULT_MAX_ATTEMPTS:
        cfg.max_attempts = DEFAULT_MAX_ATTEMPTS
    return cfg, []
