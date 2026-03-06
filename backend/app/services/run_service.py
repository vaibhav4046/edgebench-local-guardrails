from __future__ import annotations

import os
import traceback
from typing import Any
from uuid import uuid4

from pydantic import ValidationError

from backend.app.schemas.request import RunRequest
from backend.app.sse.event_bus import EventBus
from edgebench.config import load_benchmark_config, load_models_config, load_sampling_config
from edgebench.constants import JOB_STORE_PATH
from edgebench.runner.benchmark_runner import run_benchmark
from edgebench.runner.job_store import JobStore
from edgebench.runner.queue import RunQueue
from edgebench.types import ModelEntry, RunJob, RunStatus, SamplingOptions
from edgebench.utils.clock import now_utc


class RunService:
    def __init__(self, event_bus: EventBus) -> None:
        self.event_bus = event_bus
        self.store = JobStore(JOB_STORE_PATH)

        workers = int(os.getenv("EDGEBENCH_WORKERS", "1"))
        self.queue = RunQueue(executor=self._execute_job, worker_count=workers)
        self.queue.start()

        for job in self.store.pending_for_restart():
            if job.status == RunStatus.QUEUED:
                self.queue.enqueue(job.job_id)

    def create_run(self, request: RunRequest) -> RunJob:
        job_id = f"job_{uuid4().hex[:12]}"
        now = now_utc()
        job = RunJob(
            job_id=job_id,
            status=RunStatus.QUEUED,
            payload=request.model_dump(mode="json"),
            created_at_utc=now,
            updated_at_utc=now,
            progress_current=0,
            progress_total=0,
            result_dir=None,
            error_message=None,
            cancel_requested=False,
        )
        self.store.upsert_job(job)
        self.queue.enqueue(job_id)
        self.event_bus.publish(job_id, {"event": "queued", "job_id": job_id})
        return job

    def list_runs(self) -> list[RunJob]:
        return self.store.list_jobs()

    def get_run(self, job_id: str) -> RunJob | None:
        return self.store.get_job(job_id)

    def cancel_run(self, job_id: str) -> bool:
        ok = self.store.request_cancel(job_id)
        if ok:
            self.queue.mark_cancel(job_id)
            self.event_bus.publish(job_id, {"event": "cancel_requested", "job_id": job_id})
        return ok

    def _execute_job(self, job_id: str) -> None:
        job = self.store.get_job(job_id)
        if not job:
            return

        if job.cancel_requested:
            self.store.update_status(job_id, RunStatus.CANCELED)
            self.event_bus.publish(job_id, {"event": "canceled", "job_id": job_id})
            return

        self.store.update_status(job_id, RunStatus.RUNNING)
        self.event_bus.publish(job_id, {"event": "started", "job_id": job_id})

        try:
            request = RunRequest.model_validate(job.payload)
            if request.model_overrides:
                models = [ModelEntry.model_validate(item.model_dump(mode="json")) for item in request.model_overrides]
            else:
                models = load_models_config(request.models_config_path)

            cfg = load_benchmark_config(request.benchmark_config_path)
            cfg.dataset_path = request.dataset_path

            if request.results_root:
                cfg.results_root = request.results_root
            if request.repeats is not None:
                cfg.repeats = request.repeats
            if request.request_timeout_seconds is not None:
                cfg.request_timeout_seconds = request.request_timeout_seconds
            if request.job_timeout_seconds is not None:
                cfg.job_timeout_seconds = request.job_timeout_seconds

            if request.sampling_override is not None:
                cfg.sampling = SamplingOptions.model_validate(request.sampling_override.model_dump(mode="json"))

            if request.deterministic_mode:
                cfg.deterministic_mode = True
                cfg.sampling = load_sampling_config(request.deterministic_config_path)

            if request.enable_temperature_sweep:
                cfg.temperature_sweep.enabled = True
                cfg.temperature_sweep.values = request.temperatures

            def on_event(event: dict[str, Any]) -> None:
                if event.get("event") == "progress":
                    self.store.update_progress(
                        job_id,
                        int(event.get("completed", 0)),
                        int(event.get("total", 0)),
                    )
                self.event_bus.publish(job_id, event)

            def is_cancelled() -> bool:
                state = self.store.get_job(job_id)
                return bool(state and state.cancel_requested)

            result = run_benchmark(
                run_id=job_id,
                dataset_path=cfg.dataset_path,
                models=models,
                benchmark_config=cfg,
                on_event=on_event,
                is_cancelled=is_cancelled,
                scorer_name=request.scorer_name,
            )

            if result.get("canceled"):
                self.store.update_status(job_id, RunStatus.CANCELED, result_dir=result.get("run_dir"))
                self.event_bus.publish(job_id, {"event": "canceled", "job_id": job_id, "run_dir": result.get("run_dir")})
            else:
                self.store.update_status(job_id, RunStatus.COMPLETED, result_dir=result.get("run_dir"))
                self.event_bus.publish(job_id, {"event": "completed", "job_id": job_id, "run_dir": result.get("run_dir")})
        except ValidationError as exc:
            self.store.update_status(job_id, RunStatus.FAILED, error_message=str(exc))
            self.event_bus.publish(job_id, {"event": "failed", "job_id": job_id, "error": str(exc)})
        except Exception as exc:  # pragma: no cover
            self.store.update_status(job_id, RunStatus.FAILED, error_message=str(exc))
            self.event_bus.publish(
                job_id,
                {
                    "event": "failed",
                    "job_id": job_id,
                    "error": str(exc),
                    "traceback": traceback.format_exc(limit=5),
                },
            )
