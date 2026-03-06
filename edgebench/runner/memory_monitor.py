from __future__ import annotations

import threading
import time
from collections import defaultdict
from dataclasses import dataclass
from typing import Any

import psutil


@dataclass(slots=True)
class MemorySample:
    runner_rss_bytes: int
    ollama_rss_bytes: int


class MemoryMonitor:
    def __init__(self, sample_interval_seconds: float = 0.5) -> None:
        self.sample_interval_seconds = sample_interval_seconds
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()
        self._samples: list[tuple[str, MemorySample]] = []
        self._context: str = "global"

    def set_context(self, context: str) -> None:
        with self._lock:
            self._context = context

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return

        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2)

    def _run(self) -> None:
        runner_proc = psutil.Process()
        while not self._stop_event.is_set():
            try:
                runner_rss = runner_proc.memory_info().rss
            except Exception:
                runner_rss = 0

            ollama_rss = 0
            for proc in psutil.process_iter(["name", "cmdline", "memory_info"]):
                try:
                    name = (proc.info.get("name") or "").lower()
                    cmdline = " ".join(proc.info.get("cmdline") or []).lower()
                    if "ollama" in name or "ollama" in cmdline:
                        info = proc.info.get("memory_info")
                        if info:
                            ollama_rss += int(info.rss)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            with self._lock:
                self._samples.append((self._context, MemorySample(runner_rss_bytes=runner_rss, ollama_rss_bytes=ollama_rss)))

            time.sleep(self.sample_interval_seconds)

    def summary(self) -> dict[str, Any]:
        with self._lock:
            samples = list(self._samples)

        global_runner = [s.runner_rss_bytes for _, s in samples]
        global_ollama = [s.ollama_rss_bytes for _, s in samples]

        by_context: dict[str, dict[str, float]] = {}
        grouped: dict[str, list[MemorySample]] = defaultdict(list)
        for context, sample in samples:
            grouped[context].append(sample)

        for context, context_samples in grouped.items():
            runner_vals = [s.runner_rss_bytes for s in context_samples]
            ollama_vals = [s.ollama_rss_bytes for s in context_samples]
            by_context[context] = {
                "runner_peak_rss_bytes": max(runner_vals) if runner_vals else 0,
                "runner_avg_rss_bytes": (sum(runner_vals) / len(runner_vals)) if runner_vals else 0,
                "ollama_peak_rss_bytes": max(ollama_vals) if ollama_vals else 0,
                "ollama_avg_rss_bytes": (sum(ollama_vals) / len(ollama_vals)) if ollama_vals else 0,
            }

        return {
            "global": {
                "runner_peak_rss_bytes": max(global_runner) if global_runner else 0,
                "runner_avg_rss_bytes": (sum(global_runner) / len(global_runner)) if global_runner else 0,
                "ollama_peak_rss_bytes": max(global_ollama) if global_ollama else 0,
                "ollama_avg_rss_bytes": (sum(global_ollama) / len(global_ollama)) if global_ollama else 0,
            },
            "by_model_tag_temp": by_context,
            "by_model_tag": by_context,
            "sample_count": len(samples),
        }
