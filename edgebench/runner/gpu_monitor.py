from __future__ import annotations

from typing import Any


def collect_gpu_metrics() -> dict[str, Any]:
    try:
        import pynvml  # type: ignore

        pynvml.nvmlInit()
        count = pynvml.nvmlDeviceGetCount()
        devices: list[dict[str, Any]] = []
        for idx in range(count):
            handle = pynvml.nvmlDeviceGetHandleByIndex(idx)
            mem = pynvml.nvmlDeviceGetMemoryInfo(handle)
            util = pynvml.nvmlDeviceGetUtilizationRates(handle)
            devices.append(
                {
                    "index": idx,
                    "name": pynvml.nvmlDeviceGetName(handle).decode("utf-8", errors="ignore"),
                    "memory_used_bytes": int(mem.used),
                    "memory_total_bytes": int(mem.total),
                    "gpu_util_percent": int(util.gpu),
                    "memory_util_percent": int(util.memory),
                }
            )

        pynvml.nvmlShutdown()
        return {"available": True, "devices": devices}
    except Exception:
        return {"available": False, "reason": "pynvml unavailable or unsupported"}
