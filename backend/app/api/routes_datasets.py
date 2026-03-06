from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile

from backend.app.deps import get_dataset_service
from backend.app.services.dataset_service import DatasetService

router = APIRouter(prefix="/api/v1/datasets", tags=["datasets"])


@router.post("/upload")
async def upload_dataset(
    file: Annotated[UploadFile, File(...)],
    dataset_service: Annotated[DatasetService, Depends(get_dataset_service)],
) -> dict[str, str | bool]:
    content = await file.read()
    filename = file.filename or "dataset_upload.jsonl"
    path = dataset_service.save_upload(filename, content)
    return {"ok": True, "path": path}
