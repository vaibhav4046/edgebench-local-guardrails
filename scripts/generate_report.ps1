Param(
  [Parameter(Mandatory=$true)][string]$RunId
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path .venv)) {
  throw "Run scripts/setup_windows.ps1 first."
}

& .\.venv\Scripts\Activate.ps1
python -m edgebench.cli report --results "results/$RunId" --out report/report.md
Write-Host "Report generated at report/report.md"
