from __future__ import annotations

from functools import lru_cache

from backend.app.services.dataset_service import DatasetService
from backend.app.services.run_service import RunService
from backend.app.sse.event_bus import EventBus


@lru_cache(maxsize=1)
def get_event_bus() -> EventBus:
    return EventBus()


@lru_cache(maxsize=1)
def get_run_service() -> RunService:
    return RunService(event_bus=get_event_bus())


@lru_cache(maxsize=1)
def get_dataset_service() -> DatasetService:
    return DatasetService()
