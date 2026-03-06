from __future__ import annotations

import json
from collections.abc import Iterator
from queue import Empty
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from backend.app.deps import get_event_bus, get_run_service
from backend.app.schemas.request import CancelRunRequest, RunRequest
from backend.app.services.run_service import RunService
from backend.app.sse.event_bus import EventBus
from edgebench.types import RunJob

router = APIRouter(prefix="/api/v1/runs", tags=["runs"])


def _job_to_dict(job: RunJob) -> dict[str, Any]:
    return {
        "job_id": job.job_id,
        "status": str(job.status),
        "progress_current": job.progress_current,
        "progress_total": job.progress_total,
        "result_dir": job.result_dir,
        "error_message": job.error_message,
        "cancel_requested": job.cancel_requested,
        "created_at_utc": job.created_at_utc.isoformat(),
        "updated_at_utc": job.updated_at_utc.isoformat(),
        "payload": job.payload,
    }


@router.post("")
def create_run(
    request: RunRequest,
    run_service: Annotated[RunService, Depends(get_run_service)],
) -> dict[str, Any]:
    job = run_service.create_run(request)
    return {"ok": True, "job": _job_to_dict(job)}


@router.get("")
def list_runs(run_service: Annotated[RunService, Depends(get_run_service)]) -> dict[str, Any]:
    jobs = [_job_to_dict(job) for job in run_service.list_runs()]
    return {"ok": True, "jobs": jobs}


@router.get("/{run_id}")
def get_run(run_id: str, run_service: Annotated[RunService, Depends(get_run_service)]) -> dict[str, Any]:
    job = run_service.get_run(run_id)
    if not job:
        raise HTTPException(status_code=404, detail="Run not found")
    return {"ok": True, "job": _job_to_dict(job)}


@router.post("/{run_id}/cancel")
def cancel_run(
    run_id: str,
    request: CancelRunRequest,
    run_service: Annotated[RunService, Depends(get_run_service)],
) -> dict[str, Any]:
    _ = request
    ok = run_service.cancel_run(run_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Run not found")
    return {"ok": True, "message": "Cancel requested"}


@router.get("/{run_id}/events")
def stream_run_events(
    run_id: str,
    event_bus: Annotated[EventBus, Depends(get_event_bus)],
) -> StreamingResponse:
    listener = event_bus.subscribe(run_id)

    def gen() -> Iterator[str]:
        try:
            while True:
                try:
                    payload = listener.get(timeout=10)
                    yield f"data: {json.dumps(payload)}\\n\\n"
                except Empty:
                    yield "event: heartbeat\\ndata: {}\\n\\n"
        finally:
            event_bus.unsubscribe(run_id, listener)

    return StreamingResponse(gen(), media_type="text/event-stream")
