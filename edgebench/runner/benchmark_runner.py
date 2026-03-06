from __future__ import annotations

import json
import logging
import time
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Any
from uuid import uuid4

import yaml
from pydantic import ValidationError

from edgebench.constants import DEFAULT_MAX_ATTEMPTS, RESULTS_LATEST_LINK
from edgebench.errors import FailureType
from edgebench.ollama.client import OllamaClient
from edgebench.runner.determinism import hash_normalized_json
from edgebench.runner.gpu_monitor import collect_gpu_metrics
from edgebench.runner.memory_monitor import MemoryMonitor
from edgebench.runner.result_writer import ResultWriter
from edgebench.runner.retry_pipeline import classify_exception, run_with_retry
from edgebench.runner.summarizer import SummaryBuilder
from edgebench.scoring.registry import ScoringRegistry
from edgebench.types import BenchmarkConfig, ModelEntry, PromptRecord, SamplingOptions
from edgebench.utils.clock import now_utc
from edgebench.utils.fileio import safe_symlink_or_copy_latest

LOGGER = logging.getLogger(__name__)


def _iter_prompts(dataset_path: str) -> Iterable[PromptRecord]:
    with Path(dataset_path).open("r", encoding="utf-8-sig") as handle:
        for line_no, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
                yield PromptRecord.model_validate(payload)
            except (json.JSONDecodeError, ValidationError) as exc:
                raise ValueError(f"Invalid dataset row at line {line_no}: {exc}") from exc


def count_prompts(dataset_path: str) -> int:
    count = 0
    with Path(dataset_path).open("r", encoding="utf-8-sig") as handle:
        for line in handle:
            if line.strip():
                count += 1
    return count


def _emit(callback: Callable[[dict[str, Any]], None] | None, event: dict[str, Any]) -> None:
    if callback:
        callback(event)


def _failure_to_str(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, FailureType):
        return value.value
    return str(value)


def _write_config_snapshot(
    run_dir: Path,
    dataset_path: str,
    models: list[ModelEntry],
    cfg: BenchmarkConfig,
    scorer_name: str,
) -> None:
    snapshot = {
        "generated_at_utc": now_utc().isoformat(),
        "dataset_path": dataset_path,
        "models": [model.model_dump(mode="json") for model in models],
        "benchmark_config": cfg.model_dump(mode="json"),
        "scorer_name": scorer_name,
    }
    target = run_dir / "config_snapshot.yaml"
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(snapshot, handle, sort_keys=False)


def run_benchmark(
    run_id: str | None,
    dataset_path: str,
    models: list[ModelEntry],
    benchmark_config: BenchmarkConfig,
    on_event: Callable[[dict[str, Any]], None] | None = None,
    is_cancelled: Callable[[], bool] | None = None,
    scorer_name: str = "exact_json",
) -> dict[str, Any]:
    active_models = [m for m in models if m.enabled]
    if not active_models:
        raise ValueError("No enabled models configured")

    prompt_count = count_prompts(dataset_path)
    if prompt_count == 0:
        raise ValueError("Dataset is empty")

    run_id = run_id or f"run_{uuid4().hex[:12]}"
    results_root = Path(benchmark_config.results_root)
    run_dir = results_root / run_id

    writer = ResultWriter(run_dir=run_dir)
    _write_config_snapshot(
        run_dir=run_dir,
        dataset_path=dataset_path,
        models=active_models,
        cfg=benchmark_config,
        scorer_name=scorer_name,
    )

    monitor = MemoryMonitor(sample_interval_seconds=0.5)
    monitor.start()

    started_at = now_utc()
    summary_builder = SummaryBuilder(run_id=run_id, dataset_path=dataset_path, started_at_utc=started_at)
    scorer_registry = ScoringRegistry()
    scorer = scorer_registry.get(scorer_name)

    temps = benchmark_config.temperature_sweep.values if benchmark_config.temperature_sweep.enabled else [benchmark_config.sampling.temperature]
    repeats = benchmark_config.repeats
    total_records = prompt_count * len(active_models) * len(temps) * repeats
    completed = 0
    canceled = False
    timed_out = False

    deadline = None
    if benchmark_config.job_timeout_seconds and benchmark_config.job_timeout_seconds > 0:
        deadline = time.monotonic() + benchmark_config.job_timeout_seconds

    _emit(
        on_event,
        {
            "event": "run_started",
            "run_id": run_id,
            "prompt_count": prompt_count,
            "total_records": total_records,
        },
    )

    try:
        for model in active_models:
            client = OllamaClient(base_url=model.base_url)
            for temperature in temps:
                for repeat_index in range(repeats):
                    for prompt in _iter_prompts(dataset_path):
                        if deadline is not None and time.monotonic() > deadline:
                            timed_out = True
                            canceled = True
                            _emit(
                                on_event,
                                {
                                    "event": "job_timeout",
                                    "run_id": run_id,
                                    "message": f"Job timeout exceeded ({benchmark_config.job_timeout_seconds}s)",
                                },
                            )
                            break

                        if is_cancelled and is_cancelled():
                            canceled = True
                            break

                        options = SamplingOptions.model_validate(benchmark_config.sampling.model_dump(mode="json"))
                        options.temperature = float(temperature)

                        monitor.set_context(f"{model.model_key}|{model.tag}|{temperature}")

                        try:
                            outcome = run_with_retry(
                                client=client,
                                model_tag=model.tag,
                                user_prompt=prompt.prompt,
                                options=options,
                                timeout_seconds=benchmark_config.request_timeout_seconds,
                                raw_output_max_bytes=benchmark_config.raw_output_max_bytes,
                                max_attempts=DEFAULT_MAX_ATTEMPTS,
                            )
                            success = bool(outcome.get("success"))
                            parsed_output = outcome.get("final_output")
                            normalized_hash = hash_normalized_json(parsed_output) if (success and parsed_output) else None
                            grade = None
                            if success and prompt.expected is not None and parsed_output is not None:
                                grade = scorer.score(prompt.expected, parsed_output).model_dump(mode="json")

                            record = {
                                "run_id": run_id,
                                "timestamp_utc": now_utc().isoformat(),
                                "prompt_id": prompt.id,
                                "prompt_category": prompt.category,
                                "model_key": model.model_key,
                                "model_tag": model.tag,
                                "temperature": float(temperature),
                                "repeat_index": repeat_index,
                                "deterministic_mode": benchmark_config.deterministic_mode,
                                "scorer_name": scorer_name,
                                "attempt_count": int(outcome.get("attempt_count", 1)),
                                "success": success,
                                "failure_type": _failure_to_str(outcome.get("failure_type")),
                                "validation_errors": outcome.get("validation_errors", []),
                                "raw_output": outcome.get("raw_output"),
                                "normalized_hash": normalized_hash,
                                "parsed_output": parsed_output,
                                "metrics": outcome.get("metrics", {}),
                                "grade": grade,
                            }
                        except Exception as exc:  # pragma: no cover - defensive path
                            failure_type = classify_exception(exc)
                            record = {
                                "run_id": run_id,
                                "timestamp_utc": now_utc().isoformat(),
                                "prompt_id": prompt.id,
                                "prompt_category": prompt.category,
                                "model_key": model.model_key,
                                "model_tag": model.tag,
                                "temperature": float(temperature),
                                "repeat_index": repeat_index,
                                "deterministic_mode": benchmark_config.deterministic_mode,
                                "scorer_name": scorer_name,
                                "attempt_count": 1,
                                "success": False,
                                "failure_type": _failure_to_str(failure_type),
                                "validation_errors": [{"msg": str(exc)}],
                                "raw_output": "",
                                "normalized_hash": None,
                                "parsed_output": None,
                                "metrics": {
                                    "ttft_seconds": None,
                                    "total_response_latency_seconds": None,
                                    "tokens_per_second": None,
                                    "prompt_eval_count": None,
                                    "prompt_eval_duration": None,
                                    "eval_count": None,
                                    "eval_duration": None,
                                    "load_duration": None,
                                    "total_duration": None,
                                },
                                "grade": None,
                            }
                            LOGGER.exception("Record failed: %s", exc)

                        writer.write_record(record)
                        summary_builder.add_record(record)

                        completed += 1
                        _emit(
                            on_event,
                            {
                                "event": "progress",
                                "run_id": run_id,
                                "completed": completed,
                                "total": total_records,
                                "model_key": model.model_key,
                                "model_tag": model.tag,
                                "temperature": float(temperature),
                                "repeat_index": repeat_index,
                                "prompt_id": prompt.id,
                                "success": record["success"],
                                "failure_type": record.get("failure_type"),
                            },
                        )

                    if canceled:
                        break
                if canceled:
                    break
            if canceled:
                break
    finally:
        monitor.stop()

    finished_at = now_utc()
    summary = summary_builder.build(
        finished_at_utc=finished_at,
        memory_usage=monitor.summary(),
        gpu_usage=collect_gpu_metrics(),
    )
    summary["canceled"] = canceled
    summary["job_timeout_triggered"] = timed_out

    writer.write_summary(summary)
    safe_symlink_or_copy_latest(RESULTS_LATEST_LINK, run_dir)

    _emit(
        on_event,
        {
            "event": "run_finished",
            "run_id": run_id,
            "completed": completed,
            "total": total_records,
            "canceled": canceled,
            "run_dir": str(run_dir),
        },
    )

    return {
        "run_id": run_id,
        "run_dir": str(run_dir),
        "summary": summary,
        "completed": completed,
        "total": total_records,
        "canceled": canceled,
    }
