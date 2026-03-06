from __future__ import annotations

import queue
import threading
from collections import defaultdict
from typing import Any


class EventBus:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._listeners: dict[str, list[queue.Queue[dict[str, Any]]]] = defaultdict(list)

    def publish(self, run_id: str, event: dict[str, Any]) -> None:
        with self._lock:
            listeners = list(self._listeners.get(run_id, []))
        for listener in listeners:
            listener.put(event)

    def subscribe(self, run_id: str) -> queue.Queue[dict[str, Any]]:
        q: queue.Queue[dict[str, Any]] = queue.Queue()
        with self._lock:
            self._listeners[run_id].append(q)
        return q

    def unsubscribe(self, run_id: str, listener: queue.Queue[dict[str, Any]]) -> None:
        with self._lock:
            if run_id in self._listeners:
                self._listeners[run_id] = [q for q in self._listeners[run_id] if q is not listener]
                if not self._listeners[run_id]:
                    self._listeners.pop(run_id, None)
