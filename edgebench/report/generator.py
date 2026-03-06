from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from edgebench.report.markdown import MarkdownRenderer


def _resolve_results_dir(results_dir: str | Path) -> Path:
    path = Path(results_dir)
    marker = path / "LATEST.txt"
    if marker.exists():
        target = marker.read_text(encoding="utf-8").strip()
        if target:
            return Path(target)
    return path


def load_summary(results_dir: str | Path) -> dict[str, Any]:
    root = _resolve_results_dir(results_dir)
    path = root / "summary.json"
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError("summary.json must contain a JSON object")
    return payload


def load_records(results_dir: str | Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    root = _resolve_results_dir(results_dir)
    path = root / "results.jsonl"
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))
    return records


def _rows_from_summary_blocks(block: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for key, metrics in block.items():
        row: dict[str, Any] = {"group": key}
        for metric_name, stats in metrics.items():
            row[f"{metric_name}_mean"] = stats.get("mean", 0.0)
            row[f"{metric_name}_p50"] = stats.get("p50", 0.0)
            row[f"{metric_name}_p95"] = stats.get("p95", 0.0)
        rows.append(row)
    return rows


def _temperature_rows(summary: dict[str, Any]) -> list[dict[str, Any]]:
    block = summary.get("by_model_temperature", {})
    determinism = (summary.get("determinism") or {}).get("by_model_temperature", {})
    rows: list[dict[str, Any]] = []

    for key, metrics in block.items():
        row: dict[str, Any] = {"group": key}
        for metric_name, stats in metrics.items():
            if isinstance(stats, dict) and {"mean", "p50", "p95"}.issubset(stats.keys()):
                row[f"{metric_name}_mean"] = stats.get("mean", 0.0)
                row[f"{metric_name}_p50"] = stats.get("p50", 0.0)
                row[f"{metric_name}_p95"] = stats.get("p95", 0.0)

        row["schema_pass_rate"] = metrics.get("schema_pass_rate", 0.0)
        row["retry_rate"] = metrics.get("retry_rate", 0.0)
        row["failure_rate"] = metrics.get("failure_rate", 0.0)
        row["determinism_exact_match_rate"] = (determinism.get(key) or {}).get("exact_match_rate", 0.0)
        row["error_type_counts"] = metrics.get("error_type_counts", {})
        rows.append(row)

    rows.sort(key=lambda item: str(item.get("group", "")))
    return rows


def generate_report_markdown(results_dir: str | Path, template_dir: str | Path) -> str:
    summary = load_summary(results_dir)
    records = load_records(results_dir)

    context = {
        "summary": summary,
        "records_count": len(records),
        "model_rows": _rows_from_summary_blocks(summary.get("by_model", {})),
        "model_temp_rows": _temperature_rows(summary),
        "determinism": summary.get("determinism", {}),
        "memory": summary.get("memory_usage", {}),
        "gpu": summary.get("gpu_usage", {}),
    }

    renderer = MarkdownRenderer(template_dir=template_dir)
    return renderer.render("template.md.j2", context)


def write_report(results_dir: str | Path, out_path: str | Path, template_dir: str | Path) -> None:
    content = generate_report_markdown(results_dir, template_dir)
    target = Path(out_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
