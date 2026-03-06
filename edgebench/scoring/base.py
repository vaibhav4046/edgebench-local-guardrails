from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from edgebench.types import GradeResult


class BaseScorer(ABC):
    name: str = "base"

    @abstractmethod
    def score(self, expected: dict[str, Any], actual: dict[str, Any]) -> GradeResult:
        raise NotImplementedError
