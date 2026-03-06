from __future__ import annotations

from typing import Any

from edgebench.scoring.base import BaseScorer
from edgebench.types import GradeResult


class ExactJsonScorer(BaseScorer):
    name = "exact_json"

    def score(self, expected: dict[str, Any], actual: dict[str, Any]) -> GradeResult:
        passed = expected == actual
        return GradeResult(
            score=1.0 if passed else 0.0,
            passed=passed,
            details={"mode": "exact_json"},
        )
