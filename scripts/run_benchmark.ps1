Param(
  [string]$Models = "config/models.yaml",
  [string]$Dataset = "data/synthetic_prompts_3250.jsonl",
  [string]$BenchmarkConfig = "config/benchmark.yaml"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path .venv)) {
  throw "Run scripts/setup_windows.ps1 first."
}

& .\.venv\Scripts\Activate.ps1
python -m edgebench.cli benchmark --models $Models --dataset $Dataset --benchmark-config $BenchmarkConfig
