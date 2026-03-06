from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class TemperatureSweepPlan:
    enabled: bool
    values: list[float]

    def effective_values(self, default_temperature: float) -> list[float]:
        if not self.enabled:
            return [default_temperature]
        values = sorted({float(v) for v in self.values})
        return values if values else [default_temperature]
