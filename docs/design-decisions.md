# Design Decisions

## ADR-0001: Python benchmark core + FastAPI + React
- Keep benchmark, guardrails, reporting, and storage logic in `edgebench/`.
- Expose orchestration through FastAPI REST + SSE.
- Use React/Vite frontend for offline local UX and rich charting.

## ADR-0002: Offline-first local-only execution
- Runtime network dependencies are prohibited except local Ollama API (`localhost:11434`).
- No telemetry or external APIs.
- All run artifacts remain under local `results/`.

## ADR-0003: Strict structured output contract
- Pydantic v2 schema is authoritative.
- `extra="forbid"` and strict type validation.
- Exactly one repair retry to control cost/latency and preserve deterministic behavior analysis.

## ADR-0004: Queue durability and single-machine scale
- Persist jobs in SQLite (`results/job_store.sqlite`).
- Worker count configurable via environment with safe default of `1`.
- Backpressure via bounded worker pool behavior, no unbounded process spawning.

## ADR-0005: Reporting from measured artifacts only
- Reports read from `results/<run_id>/results.jsonl` + `summary.json`.
- No hardcoded benchmark numbers in docs/templates.
