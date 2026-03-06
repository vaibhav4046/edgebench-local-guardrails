from __future__ import annotations

import argparse
import json
import platform
import sys
from pathlib import Path
from uuid import uuid4

import httpx

from edgebench.config import (
    load_benchmark_config,
    load_models_config,
    load_sampling_config,
)
from edgebench.ollama.client import OllamaClient
from edgebench.report.generator import write_report
from edgebench.runner.benchmark_runner import run_benchmark
from edgebench.types import PromptRecord


def _parse_temps(raw: str) -> list[float]:
    return [float(item.strip()) for item in raw.split(",") if item.strip()]


def _generate_synthetic_prompts(out_path: str, count: int) -> None:
    categories = [
        "summarization",
        "classification",
        "extraction",
        "reasoning",
        "qa",
    ]
    target = Path(out_path)
    target.parent.mkdir(parents=True, exist_ok=True)

    with target.open("w", encoding="utf-8") as handle:
        for i in range(count):
            category = categories[i % len(categories)]
            record = {
                "id": f"synthetic-{i+1:04d}",
                "prompt": (
                    f"Category {category}. Provide a concise response for item {i+1}. "
                    "Return structured output according to provided JSON schema."
                ),
                "category": category,
            }
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def _validate_dataset(path: str) -> tuple[int, int]:
    valid = 0
    invalid = 0
    with Path(path).open("r", encoding="utf-8-sig") as handle:
        for line_no, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
                PromptRecord.model_validate(payload)
                valid += 1
            except Exception:
                invalid += 1
                print(f"Invalid row at line {line_no}")
    return valid, invalid


def cmd_benchmark(args: argparse.Namespace) -> None:
    models = load_models_config(args.models)
    cfg = load_benchmark_config(args.benchmark_config)

    if args.dataset:
        cfg.dataset_path = args.dataset
    if args.results_root:
        cfg.results_root = args.results_root
    if args.repeats is not None:
        cfg.repeats = int(args.repeats)
    if args.request_timeout_seconds is not None:
        cfg.request_timeout_seconds = int(args.request_timeout_seconds)
    if args.job_timeout_seconds is not None:
        cfg.job_timeout_seconds = int(args.job_timeout_seconds)

    if args.deterministic:
        det_sampling = load_sampling_config(args.deterministic_config)
        cfg.sampling = det_sampling
        cfg.deterministic_mode = True

    cfg.temperature_sweep.enabled = False
    run_id = args.run_id or f"run_{uuid4().hex[:12]}"

    result = run_benchmark(
        run_id=run_id,
        dataset_path=cfg.dataset_path,
        models=models,
        benchmark_config=cfg,
        scorer_name=args.scorer,
    )
    print(json.dumps(result, indent=2, default=str))


def cmd_sweep(args: argparse.Namespace) -> None:
    models = load_models_config(args.models)
    cfg = load_benchmark_config(args.benchmark_config)

    if args.dataset:
        cfg.dataset_path = args.dataset
    if args.results_root:
        cfg.results_root = args.results_root
    if args.repeats is not None:
        cfg.repeats = int(args.repeats)
    if args.request_timeout_seconds is not None:
        cfg.request_timeout_seconds = int(args.request_timeout_seconds)
    if args.job_timeout_seconds is not None:
        cfg.job_timeout_seconds = int(args.job_timeout_seconds)

    cfg.temperature_sweep.enabled = True
    cfg.temperature_sweep.values = _parse_temps(args.temps)

    run_id = args.run_id or f"run_{uuid4().hex[:12]}"
    result = run_benchmark(
        run_id=run_id,
        dataset_path=cfg.dataset_path,
        models=models,
        benchmark_config=cfg,
        scorer_name=args.scorer,
    )
    print(json.dumps(result, indent=2, default=str))


def cmd_report(args: argparse.Namespace) -> None:
    write_report(results_dir=args.results, out_path=args.out, template_dir=args.template_dir)
    print(f"Report written to {args.out}")


def cmd_synth_dataset(args: argparse.Namespace) -> None:
    _generate_synthetic_prompts(out_path=args.out, count=args.count)
    print(f"Synthetic dataset written to {args.out}")


def cmd_validate_dataset(args: argparse.Namespace) -> None:
    valid, invalid = _validate_dataset(args.dataset)
    print(json.dumps({"valid": valid, "invalid": invalid}, indent=2))


def cmd_doctor(args: argparse.Namespace) -> None:
    models_exists = Path(args.models).exists()
    benchmark_exists = Path(args.benchmark_config).exists()
    dataset_exists = Path(args.dataset).exists() if args.dataset else None

    ollama = OllamaClient(base_url=args.base_url)
    ollama_reachable = ollama.check_health(timeout_seconds=args.timeout_seconds)
    local_model_tags: list[str] = []
    ollama_error: str | None = None

    if ollama_reachable:
        try:
            with httpx.Client(timeout=args.timeout_seconds) as client:
                response = client.get(f"{args.base_url.rstrip('/')}/api/tags")
                response.raise_for_status()
                payload = response.json()
                models = payload.get("models", []) if isinstance(payload, dict) else []
                for model in models:
                    if isinstance(model, dict):
                        name = model.get("name")
                        if isinstance(name, str):
                            local_model_tags.append(name)
        except Exception as exc:
            ollama_error = str(exc)

    payload = {
        "python_version": sys.version.split()[0],
        "platform": platform.platform(),
        "base_url": args.base_url,
        "ollama_reachable": ollama_reachable,
        "local_model_count": len(local_model_tags),
        "local_model_tags": local_model_tags,
        "ollama_error": ollama_error,
        "models_config_exists": models_exists,
        "benchmark_config_exists": benchmark_exists,
        "dataset_exists": dataset_exists,
    }
    print(json.dumps(payload, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="edgebench")
    sub = parser.add_subparsers(dest="command", required=True)

    benchmark = sub.add_parser("benchmark", help="Run benchmark")
    benchmark.add_argument("--models", required=True)
    benchmark.add_argument("--benchmark-config", default="config/benchmark.yaml")
    benchmark.add_argument("--dataset")
    benchmark.add_argument("--results-root")
    benchmark.add_argument("--repeats", type=int)
    benchmark.add_argument("--request-timeout-seconds", type=int)
    benchmark.add_argument("--job-timeout-seconds", type=int)
    benchmark.add_argument("--scorer", choices=["exact_json", "field_level"], default="exact_json")
    benchmark.add_argument("--run-id")
    benchmark.add_argument("--deterministic", action="store_true")
    benchmark.add_argument("--deterministic-config", default="config/deterministic.yaml")
    benchmark.set_defaults(func=cmd_benchmark)

    sweep = sub.add_parser("sweep", help="Run temperature sweep")
    sweep.add_argument("--models", required=True)
    sweep.add_argument("--benchmark-config", default="config/benchmark.yaml")
    sweep.add_argument("--dataset")
    sweep.add_argument("--results-root")
    sweep.add_argument("--repeats", type=int)
    sweep.add_argument("--request-timeout-seconds", type=int)
    sweep.add_argument("--job-timeout-seconds", type=int)
    sweep.add_argument("--scorer", choices=["exact_json", "field_level"], default="exact_json")
    sweep.add_argument("--temps", default="0.0,0.2,0.5,0.8")
    sweep.add_argument("--run-id")
    sweep.set_defaults(func=cmd_sweep)

    report = sub.add_parser("report", help="Generate markdown report from measured files")
    report.add_argument("--results", required=True)
    report.add_argument("--out", required=True)
    report.add_argument("--template-dir", default="report")
    report.set_defaults(func=cmd_report)

    synth = sub.add_parser("synth-dataset", help="Generate placeholder synthetic prompts")
    synth.add_argument("--out", default="data/synthetic_prompts_3250.jsonl")
    synth.add_argument("--count", type=int, default=3250)
    synth.set_defaults(func=cmd_synth_dataset)

    validate = sub.add_parser("validate-dataset", help="Validate JSONL dataset format")
    validate.add_argument("--dataset", required=True)
    validate.set_defaults(func=cmd_validate_dataset)

    doctor = sub.add_parser("doctor", help="Check local CLI readiness and Ollama reachability")
    doctor.add_argument("--base-url", default="http://127.0.0.1:11434")
    doctor.add_argument("--models", default="config/models.yaml")
    doctor.add_argument("--benchmark-config", default="config/benchmark.yaml")
    doctor.add_argument("--dataset", default="")
    doctor.add_argument("--timeout-seconds", type=int, default=3)
    doctor.set_defaults(func=cmd_doctor)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
