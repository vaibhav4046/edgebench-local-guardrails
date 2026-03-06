Param()

$ErrorActionPreference = "Stop"

if (-not (Test-Path .venv)) {
  throw "Run scripts/setup_windows.ps1 first."
}

& .\.venv\Scripts\Activate.ps1
python data/generate_synthetic_prompts.py --out data/synthetic_prompts_3250.jsonl --count 3250

Write-Host "First-run checklist:"
Write-Host "1) Ensure Ollama is running and pull model tags:"
Write-Host "   ollama pull llama3.2:1b-instruct-q4_K_M"
Write-Host "   ollama pull <54Mini tag>"
Write-Host "   ollama pull mistral:7b-instruct"
Write-Host "2) Start backend in one terminal: .\\scripts\\run_backend.ps1"
Write-Host "3) Start frontend in another terminal: .\\scripts\\run_frontend.ps1"
Write-Host "4) Run benchmark: .\\scripts\\run_benchmark.ps1"
Write-Host "5) Generate report: .\\scripts\\generate_report.ps1 -RunId <job_id>"
