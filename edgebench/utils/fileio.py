from __future__ import annotations

import csv
import json
from collections.abc import Iterable
from pathlib import Path
from typing import Any


def ensure_parent(path: str | Path) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    return target


def write_json(path: str | Path, payload: dict[str, Any]) -> None:
    target = ensure_parent(path)
    with target.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)


def append_jsonl(path: str | Path, payload: dict[str, Any]) -> None:
    target = ensure_parent(path)
    with target.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def read_jsonl(path: str | Path) -> Iterable[dict[str, Any]]:
    source = Path(path)
    with source.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)


def write_csv(path: str | Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    target = ensure_parent(path)
    with target.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def safe_symlink_or_copy_latest(latest_path: str | Path, run_path: str | Path) -> None:
    latest = Path(latest_path)
    run = Path(run_path)
    if latest.exists() or latest.is_symlink():
        if latest.is_dir() and not latest.is_symlink():
            for item in latest.iterdir():
                if item.is_file() or item.is_symlink():
                    item.unlink(missing_ok=True)
            latest.rmdir()
        else:
            latest.unlink(missing_ok=True)

    try:
        latest.symlink_to(run.resolve(), target_is_directory=True)
    except OSError:
        latest.mkdir(parents=True, exist_ok=True)
        marker = latest / "LATEST.txt"
        marker.write_text(str(run.resolve()), encoding="utf-8")
