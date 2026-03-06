from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict


class JobResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    job_id: str
    status: str
    progress_current: int = 0
    progress_total: int = 0
    result_dir: str | None = None
    error_message: str | None = None
    cancel_requested: bool = False


class GenericResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    ok: bool
    message: str
    data: dict[str, Any] | None = None
