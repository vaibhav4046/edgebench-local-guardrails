from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class CanonicalOutput(BaseModel):
    """Canonical structured output contract used for guardrail benchmarking."""

    model_config = ConfigDict(extra="forbid", strict=True)

    answer: str = Field(min_length=1)
    category: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)
    key_points: list[str] = Field(min_length=1, max_length=8)
