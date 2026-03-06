# ADR-0001: Architecture and Security Posture

## Context
We need a local, offline-first benchmark and guardrails system for Ollama models on Windows.

## Decision
Use a layered architecture:
1. `edgebench/` for benchmark engine, schema validation, retries, metrics, scoring, and report generation.
2. `backend/` FastAPI for job orchestration, queue control, uploads, exports, and SSE event streaming.
3. `frontend/` React/Vite for local dashboards and controls.

## Security posture
- Backend binds to `127.0.0.1` only in run scripts.
- CORS allow-list is locked to `http://localhost:5173` and `http://127.0.0.1:5173`.
- No external API calls at runtime beyond local Ollama.
- Results and prompts stay local by default.

## Consequences
- Strong local privacy and predictable runtime behavior.
- Easy local operations and reproducibility.
- Cross-platform expansion can reuse core Python package and swap shell scripts.
