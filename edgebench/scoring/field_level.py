from __future__ import annotations

from typing import Any

from edgebench.scoring.base import BaseScorer
from edgebench.types import GradeResult


class FieldLevelScorer(BaseScorer):
    name = "field_level"

    def score(self, expected: dict[str, Any], actual: dict[str, Any]) -> GradeResult:
        if not expected:
            return GradeResult(score=0.0, passed=False, details={"error": "empty expected"})

        total = len(expected)
        matches = 0
        mismatched: list[str] = []
        for key, value in expected.items():
            if key in actual and actual[key] == value:
                matches += 1
            else:
                mismatched.append(key)

        score = matches / total if total else 0.0
        return GradeResult(
            score=score,
            passed=score == 1.0,
            details={"mismatched_fields": mismatched},
        )
