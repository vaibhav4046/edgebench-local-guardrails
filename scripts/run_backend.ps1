Param()

$ErrorActionPreference = "Stop"

if (-not (Test-Path .venv)) {
  throw "Run scripts/setup_windows.ps1 first."
}

& .\.venv\Scripts\Activate.ps1
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
