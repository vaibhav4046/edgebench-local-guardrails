# EdgeBench Technical Report

_Run ID: `fixed_cli_20260306_091028`_  
_Dataset: `data/demo_prompt_1.jsonl`_  
_Started: `2026-03-06T09:10:29.079174+00:00`_  
_Finished: `2026-03-06T09:10:32.824647+00:00`_  
_Total records: `3`_

## System Design Overview
- Offline-first local execution against Ollama (`localhost:11434`)
- Strict Pydantic structured-output guardrails with one retry max
- Append-only per-record artifacts (`results.jsonl`) plus computed summary (`summary.json`)

## Measurement Methodology
- **TTFT**: wall-clock from request start to first streamed token chunk
- **Total Latency**: wall-clock request start to stream completion
- **Tokens/sec**: `eval_count / eval_duration * 1e9` (duration in nanoseconds)
- Additional Ollama durations: prompt eval, load, total durations

## Core Quality Metrics
- Schema pass rate: `0.0000`
- Retry rate: `0.0000`
- Failure rate: `1.0000`

## Model / Quantization Summary
| Model/Tag Group | TTFT mean | TTFT p50 | TTFT p95 | Latency mean | Latency p50 | Latency p95 | TPS mean | TPS p50 | TPS p95 | Schema Pass | Retry | Failure |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|

## Temperature Sweep Comparison
| Model/Tag/Temp | TTFT mean | TTFT p95 | Latency mean | Latency p95 | TPS mean | TPS p95 | Schema Pass | Retry | Failure | Determinism |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|

## Failure + Retry Breakdown
```json
{
  "OLLAMA_ERROR": 3
}
```

## Determinism
```json
{
  "by_model_temperature": {
    "54Mini|54Mini:latest|0.2": {
      "exact_match_rate": 0.0,
      "prompt_groups": 1
    },
    "llama3.2-mini|llama3.2:1b-instruct-q4_K_M|0.2": {
      "exact_match_rate": 0.0,
      "prompt_groups": 1
    },
    "mistral-7b|mistral:7b-instruct|0.2": {
      "exact_match_rate": 0.0,
      "prompt_groups": 1
    }
  }
}
```

## Memory Usage
```json
{
  "by_model_tag": {
    "llama3.2-mini|llama3.2:1b-instruct-q4_K_M|0.2": {
      "ollama_avg_rss_bytes": 23855104.0,
      "ollama_peak_rss_bytes": 23855104,
      "runner_avg_rss_bytes": 45010944.0,
      "runner_peak_rss_bytes": 45010944
    },
    "mistral-7b|mistral:7b-instruct|0.2": {
      "ollama_avg_rss_bytes": 24469504.0,
      "ollama_peak_rss_bytes": 24469504,
      "runner_avg_rss_bytes": 51318784.0,
      "runner_peak_rss_bytes": 51318784
    }
  },
  "by_model_tag_temp": {
    "llama3.2-mini|llama3.2:1b-instruct-q4_K_M|0.2": {
      "ollama_avg_rss_bytes": 23855104.0,
      "ollama_peak_rss_bytes": 23855104,
      "runner_avg_rss_bytes": 45010944.0,
      "runner_peak_rss_bytes": 45010944
    },
    "mistral-7b|mistral:7b-instruct|0.2": {
      "ollama_avg_rss_bytes": 24469504.0,
      "ollama_peak_rss_bytes": 24469504,
      "runner_avg_rss_bytes": 51318784.0,
      "runner_peak_rss_bytes": 51318784
    }
  },
  "global": {
    "ollama_avg_rss_bytes": 24162304.0,
    "ollama_peak_rss_bytes": 24469504,
    "runner_avg_rss_bytes": 48164864.0,
    "runner_peak_rss_bytes": 51318784
  },
  "sample_count": 2
}
```

## GPU Usage (Best Effort)
```json
{
  "available": false,
  "reason": "pynvml unavailable or unsupported"
}
```

## Key Findings and Trade-Offs
1. This report contains measured local values only, sourced from run artifacts.
2. Deterministic mode and low temperature usually improve exact-match stability at the cost of diversity.
3. Quantized tags can reduce latency and memory footprint, with possible schema fidelity trade-offs depending on model tag quality.