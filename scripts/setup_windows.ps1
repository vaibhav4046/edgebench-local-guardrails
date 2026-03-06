Param()

$ErrorActionPreference = "Stop"

function Require-Command {
  param([string]$Name)
  if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
    throw "Missing required command: $Name"
  }
}

Write-Host "Checking required tools..."
Require-Command python
Require-Command node
Require-Command npm

$pyVersion = python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
if ([version]$pyVersion -lt [version]"3.11") {
  throw "Python 3.11+ required. Found $pyVersion"
}

$nodeVersion = node -v
$nodeMajor = [int]($nodeVersion.TrimStart('v').Split('.')[0])
if ($nodeMajor -lt 18) {
  throw "Node 18+ required. Found $nodeVersion"
}

if (-not (Get-Command ollama -ErrorAction SilentlyContinue)) {
  Write-Warning "Ollama not found. Install Ollama for Windows first: https://ollama.com/download/windows"
} else {
  Write-Host "Ollama found."
  try {
    ollama list | Out-Null
    Write-Host "Ollama daemon appears reachable."
  } catch {
    Write-Warning "Ollama command exists but daemon may not be running."
  }
}

if (-not (Test-Path .venv)) {
  python -m venv .venv
}

& .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements-dev.txt

Push-Location frontend
if (Test-Path package-lock.json) {
  npm ci
} else {
  npm install
}
Pop-Location

Write-Host "Setup complete."
Write-Host "Next:"
Write-Host "  1) ollama list"
Write-Host "  2) ollama pull <your_model_tag>"
Write-Host "  3) .\scripts\first_run.ps1"
Write-Host "  4) .\scripts\run_backend.ps1"
Write-Host "  5) .\scripts\run_frontend.ps1"
Write-Host "  6) python -m edgebench.cli benchmark --models config/models.yaml --dataset data/prompts_3250.jsonl"
Write-Host "  7) python -m edgebench.cli report --results results/latest --out report/report.md"
Write-Host "CLI-only option:"
Write-Host "  .\scripts\edgebench_cli.ps1 doctor --dataset data/smoke_prompts_10.jsonl"
Write-Host "  .\scripts\edgebench_cli.ps1 benchmark --models config/models.yaml --dataset data/smoke_prompts_10.jsonl --repeats 1"
