from __future__ import annotations

import queue
import threading
from collections.abc import Callable
from typing import Any

RunExecutor = Callable[[str], None]
EventCallback = Callable[[dict[str, Any]], None]


class RunQueue:
    def __init__(
        self,
        executor: RunExecutor,
        event_callback: EventCallback | None = None,
        worker_count: int = 1,
    ) -> None:
        self.executor = executor
        self.event_callback = event_callback
        self.worker_count = max(1, min(int(worker_count), 8))
        self._queue: queue.Queue[str] = queue.Queue()
        self._stop_event = threading.Event()
        self._threads: list[threading.Thread] = []
        self._cancel_map: dict[str, bool] = {}

    def start(self) -> None:
        if self._threads and all(thread.is_alive() for thread in self._threads):
            return

        self._stop_event.clear()
        self._threads = []
        for idx in range(self.worker_count):
            thread = threading.Thread(target=self._worker, daemon=True, name=f"edgebench-worker-{idx+1}")
            thread.start()
            self._threads.append(thread)

    def stop(self) -> None:
        self._stop_event.set()
        for thread in self._threads:
            thread.join(timeout=3)

    def enqueue(self, job_id: str) -> None:
        self._queue.put(job_id)

    def mark_cancel(self, job_id: str) -> None:
        self._cancel_map[job_id] = True

    def is_cancelled(self, job_id: str) -> bool:
        return bool(self._cancel_map.get(job_id, False))

    def _emit(self, payload: dict[str, Any]) -> None:
        if self.event_callback:
            self.event_callback(payload)

    def _worker(self) -> None:
        while not self._stop_event.is_set():
            try:
                job_id = self._queue.get(timeout=0.25)
            except queue.Empty:
                continue

            self._emit({"event": "queue_dequeued", "job_id": job_id})
            try:
                self.executor(job_id)
            finally:
                self._queue.task_done()
