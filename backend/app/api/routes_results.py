from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse, PlainTextResponse

router = APIRouter(prefix="/api/v1/results", tags=["results"])


def _run_dir(run_id: str) -> Path:
    return Path("results") / run_id


@router.get("")
def list_result_runs() -> dict[str, Any]:
    root = Path("results")
    root.mkdir(parents=True, exist_ok=True)

    items: list[dict[str, Any]] = []
    for entry in sorted(root.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
        if not entry.is_dir() or entry.name == "latest":
            continue
        items.append(
            {
                "run_id": entry.name,
                "summary_exists": (entry / "summary.json").exists(),
                "results_exists": (entry / "results.jsonl").exists(),
                "metrics_exists": (entry / "metrics.csv").exists(),
                "config_snapshot_exists": (entry / "config_snapshot.yaml").exists(),
            }
        )
    return {"ok": True, "runs": items}


@router.get("/{run_id}/summary")
def summary(run_id: str) -> dict[str, Any]:
    path = _run_dir(run_id) / "summary.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Summary not found")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise HTTPException(status_code=500, detail="Invalid summary format")
    return payload


@router.get("/{run_id}/records")
def records(run_id: str, limit: int = Query(200, ge=1, le=5000), offset: int = Query(0, ge=0)) -> dict[str, Any]:
    path = _run_dir(run_id) / "results.jsonl"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Results not found")

    items: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for idx, line in enumerate(handle):
            if idx < offset:
                continue
            if len(items) >= limit:
                break
            if line.strip():
                payload = json.loads(line)
                if isinstance(payload, dict):
                    items.append(payload)

    return {"ok": True, "items": items, "offset": offset, "limit": limit}


@router.get("/{run_id}/export.csv")
def export_csv(run_id: str) -> PlainTextResponse:
    path = _run_dir(run_id) / "metrics.csv"
    if not path.exists():
        raise HTTPException(status_code=404, detail="CSV export not found")
    return PlainTextResponse(path.read_text(encoding="utf-8"), media_type="text/csv")


@router.get("/{run_id}/export.json")
def export_json(run_id: str) -> JSONResponse:
    path = _run_dir(run_id) / "results.jsonl"
    if not path.exists():
        raise HTTPException(status_code=404, detail="JSON export not found")

    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                payload = json.loads(line)
                if isinstance(payload, dict):
                    rows.append(payload)
    return JSONResponse(rows)
