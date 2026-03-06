from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _percentile(values: list[float], percentile: float) -> float:
    if not values:
        return 0.0
    sorted_vals = sorted(values)
    if len(sorted_vals) == 1:
        return sorted_vals[0]
    position = (len(sorted_vals) - 1) * percentile
    low = int(position)
    high = min(low + 1, len(sorted_vals) - 1)
    weight = position - low
    return sorted_vals[low] * (1 - weight) + sorted_vals[high] * weight


METRIC_FIELDS = [
    "ttft_seconds",
    "total_response_latency_seconds",
    "tokens_per_second",
]


@dataclass(slots=True)
class SummaryBuilder:
    run_id: str
    dataset_path: str
    started_at_utc: datetime
    _records: int = 0
    _success: int = 0
    _failure: int = 0
    _retry_count: int = 0
    _errors: Counter[str] = field(default_factory=Counter)
    _group_metrics: dict[str, dict[str, list[float]]] = field(default_factory=lambda: defaultdict(lambda: defaultdict(list)))
    _group_temp_metrics: dict[str, dict[str, list[float]]] = field(default_factory=lambda: defaultdict(lambda: defaultdict(list)))
    _group_counts: dict[str, Counter[str]] = field(default_factory=lambda: defaultdict(Counter))
    _group_temp_counts: dict[str, Counter[str]] = field(default_factory=lambda: defaultdict(Counter))
    _group_temp_errors: dict[str, Counter[str]] = field(default_factory=lambda: defaultdict(Counter))
    _determinism_hashes: dict[str, list[str | None]] = field(default_factory=lambda: defaultdict(list))

    def add_record(self, record: dict[str, Any]) -> None:
        self._records += 1
        model_key = str(record.get("model_key"))
        model_tag = str(record.get("model_tag"))
        temperature = float(record.get("temperature", 0.0))
        group_key = f"{model_key}|{model_tag}"
        group_temp_key = f"{model_key}|{model_tag}|{temperature}"

        group_counts = self._group_counts[group_key]
        group_temp_counts = self._group_temp_counts[group_temp_key]
        group_counts["records"] += 1
        group_temp_counts["records"] += 1

        if record.get("success"):
            self._success += 1
            group_counts["success"] += 1
            group_temp_counts["success"] += 1
        else:
            self._failure += 1
            group_counts["failure"] += 1
            group_temp_counts["failure"] += 1
            failure_type = record.get("failure_type") or "UNKNOWN"
            self._errors[str(failure_type)] += 1
            self._group_temp_errors[group_temp_key][str(failure_type)] += 1

        if int(record.get("attempt_count") or 1) > 1:
            self._retry_count += 1
            group_counts["retry"] += 1
            group_temp_counts["retry"] += 1

        metrics = record.get("metrics", {})
        for metric_name in METRIC_FIELDS:
            value = metrics.get(metric_name)
            if value is not None:
                self._group_metrics[group_key][metric_name].append(float(value))
                self._group_temp_metrics[group_temp_key][metric_name].append(float(value))

        prompt_id = str(record.get("prompt_id"))
        repeat_index = int(record.get("repeat_index", 0))
        _ = repeat_index
        det_key = f"{group_temp_key}|{prompt_id}"
        self._determinism_hashes[det_key].append(record.get("normalized_hash"))

    def _stats(self, values: list[float]) -> dict[str, float]:
        return {
            "mean": _mean(values),
            "p50": _percentile(values, 0.5),
            "p95": _percentile(values, 0.95),
        }

    def _metric_block(self, metric_map: dict[str, list[float]]) -> dict[str, Any]:
        output: dict[str, Any] = {}
        for metric_name in METRIC_FIELDS:
            output[metric_name] = self._stats(metric_map.get(metric_name, []))
        return output

    def _rate_block(self, counts: Counter[str]) -> dict[str, Any]:
        total = int(counts.get("records", 0))
        success = int(counts.get("success", 0))
        failure = int(counts.get("failure", 0))
        retry = int(counts.get("retry", 0))
        return {
            "record_count": total,
            "success_count": success,
            "failure_count": failure,
            "retry_count": retry,
            "schema_pass_rate": (success / total) if total else 0.0,
            "retry_rate": (retry / total) if total else 0.0,
            "failure_rate": (failure / total) if total else 0.0,
        }

    def _determinism_summary(self) -> dict[str, Any]:
        group_rates: dict[str, list[float]] = defaultdict(list)
        group_prompt_counts: Counter[str] = Counter()

        for det_key, hashes in self._determinism_hashes.items():
            group = "|".join(det_key.split("|")[:3])
            total = len(hashes)
            valid_hashes = [h for h in hashes if h is not None]
            if not valid_hashes or total == 0:
                rate = 0.0
            else:
                first = valid_hashes[0]
                rate = sum(1 for h in hashes if h == first) / total
            group_rates[group].append(rate)
            group_prompt_counts[group] += 1

        by_group: dict[str, Any] = {}
        for group, rates in group_rates.items():
            by_group[group] = {
                "exact_match_rate": _mean(rates),
                "prompt_groups": group_prompt_counts[group],
            }

        return {"by_model_temperature": by_group}

    def build(self, finished_at_utc: datetime, memory_usage: dict[str, Any], gpu_usage: dict[str, Any]) -> dict[str, Any]:
        by_model: dict[str, Any] = {}
        for key, metric_map in self._group_metrics.items():
            block = self._metric_block(metric_map)
            block.update(self._rate_block(self._group_counts.get(key, Counter())))
            by_model[key] = block

        by_model_temperature: dict[str, Any] = {}
        for key, metric_map in self._group_temp_metrics.items():
            block = self._metric_block(metric_map)
            block.update(self._rate_block(self._group_temp_counts.get(key, Counter())))
            block["error_type_counts"] = dict(self._group_temp_errors.get(key, Counter()))
            by_model_temperature[key] = block

        schema_pass_rate = (self._success / self._records) if self._records else 0.0
        retry_rate = (self._retry_count / self._records) if self._records else 0.0
        failure_rate = (self._failure / self._records) if self._records else 0.0

        return {
            "run_id": self.run_id,
            "dataset_path": self.dataset_path,
            "started_at_utc": self.started_at_utc.isoformat(),
            "finished_at_utc": finished_at_utc.isoformat(),
            "total_records": self._records,
            "success_count": self._success,
            "failure_count": self._failure,
            "retry_count": self._retry_count,
            "schema_pass_rate": schema_pass_rate,
            "retry_rate": retry_rate,
            "failure_rate": failure_rate,
            "error_type_counts": dict(self._errors),
            "by_model": by_model,
            "by_model_temperature": by_model_temperature,
            "determinism": self._determinism_summary(),
            "memory_usage": memory_usage,
            "gpu_usage": gpu_usage,
        }
