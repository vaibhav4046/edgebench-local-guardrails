from __future__ import annotations

from pathlib import Path


class DatasetService:
    def __init__(self, uploads_dir: str = "data/uploads") -> None:
        self.uploads_dir = Path(uploads_dir)
        self.uploads_dir.mkdir(parents=True, exist_ok=True)

    def save_upload(self, filename: str, content: bytes) -> str:
        target = self.uploads_dir / filename
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        return str(target)
