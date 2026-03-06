from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from edgebench.utils.fileio import append_jsonl, write_csv, write_json


@dataclass(slots=True)
class ResultWriter:
    run_dir: Path
    results_path: Path = field(init=False)
    summary_path: Path = field(init=False)
    metrics_csv_path: Path = field(init=False)
    _metrics_rows: list[dict[str, Any]] = field(default_factory=list, init=False)

    def __post_init__(self) -> None:
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.results_path = self.run_dir / "results.jsonl"
        self.summary_path = self.run_dir / "summary.json"
        self.metrics_csv_path = self.run_dir / "metrics.csv"

    def write_record(self, record: dict[str, Any]) -> None:
        append_jsonl(self.results_path, record)
        metrics = record.get("metrics", {})
        self._metrics_rows.append(
            {
                "prompt_id": record.get("prompt_id"),
                "model_key": record.get("model_key"),
                "model_tag": record.get("model_tag"),
                "temperature": record.get("temperature"),
                "repeat_index": record.get("repeat_index"),
                "success": record.get("success"),
                "failure_type": record.get("failure_type"),
                "ttft_seconds": metrics.get("ttft_seconds"),
                "total_response_latency_seconds": metrics.get("total_response_latency_seconds"),
                "tokens_per_second": metrics.get("tokens_per_second"),
                "eval_count": metrics.get("eval_count"),
                "eval_duration": metrics.get("eval_duration"),
                "prompt_eval_count": metrics.get("prompt_eval_count"),
                "prompt_eval_duration": metrics.get("prompt_eval_duration"),
                "load_duration": metrics.get("load_duration"),
                "total_duration": metrics.get("total_duration"),
            }
        )

    def write_summary(self, summary: dict[str, Any]) -> None:
        write_json(self.summary_path, summary)
        write_csv(self.metrics_csv_path, self._metrics_rows)
