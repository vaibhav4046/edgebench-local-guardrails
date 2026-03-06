from __future__ import annotations

from edgebench.scoring.base import BaseScorer
from edgebench.scoring.exact_json import ExactJsonScorer
from edgebench.scoring.field_level import FieldLevelScorer


class ScoringRegistry:
    def __init__(self) -> None:
        self._scorers: dict[str, BaseScorer] = {
            "exact_json": ExactJsonScorer(),
            "field_level": FieldLevelScorer(),
        }

    def get(self, name: str) -> BaseScorer:
        if name not in self._scorers:
            raise KeyError(f"Unknown scorer: {name}")
        return self._scorers[name]

    def default(self) -> BaseScorer:
        return self._scorers["exact_json"]
