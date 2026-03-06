Param(
  [Parameter(Mandatory = $true, Position = 0)]
  [ValidateSet("benchmark", "sweep", "report", "synth-dataset", "validate-dataset", "doctor")]
  [string]$Command,

  [Parameter(ValueFromRemainingArguments = $true)]
  [string[]]$CliArgs
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path .venv)) {
  throw "Missing .venv. Run .\scripts\setup_windows.ps1 first."
}

$python = ".\.venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
  throw "Python not found at $python"
}

& $python -m edgebench.cli $Command @CliArgs
