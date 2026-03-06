from __future__ import annotations

import json
import sqlite3
import threading
from datetime import UTC, datetime
from pathlib import Path

from edgebench.types import RunJob, RunStatus


class JobStore:
    def __init__(self, db_path: str) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._init_db()

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._conn() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS jobs (
                    job_id TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at_utc TEXT NOT NULL,
                    updated_at_utc TEXT NOT NULL,
                    progress_current INTEGER NOT NULL DEFAULT 0,
                    progress_total INTEGER NOT NULL DEFAULT 0,
                    result_dir TEXT,
                    error_message TEXT,
                    cancel_requested INTEGER NOT NULL DEFAULT 0
                )
                """
            )
            conn.commit()

    def upsert_job(self, job: RunJob) -> None:
        with self._lock, self._conn() as conn:
            conn.execute(
                """
                INSERT INTO jobs (
                    job_id, status, payload_json, created_at_utc, updated_at_utc,
                    progress_current, progress_total, result_dir, error_message, cancel_requested
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(job_id) DO UPDATE SET
                    status=excluded.status,
                    payload_json=excluded.payload_json,
                    updated_at_utc=excluded.updated_at_utc,
                    progress_current=excluded.progress_current,
                    progress_total=excluded.progress_total,
                    result_dir=excluded.result_dir,
                    error_message=excluded.error_message,
                    cancel_requested=excluded.cancel_requested
                """,
                (
                    job.job_id,
                    job.status,
                    json.dumps(job.payload),
                    job.created_at_utc.isoformat(),
                    job.updated_at_utc.isoformat(),
                    job.progress_current,
                    job.progress_total,
                    job.result_dir,
                    job.error_message,
                    1 if job.cancel_requested else 0,
                ),
            )
            conn.commit()

    def get_job(self, job_id: str) -> RunJob | None:
        with self._lock, self._conn() as conn:
            row = conn.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,)).fetchone()
        if not row:
            return None
        return self._row_to_job(row)

    def list_jobs(self) -> list[RunJob]:
        with self._lock, self._conn() as conn:
            rows = conn.execute("SELECT * FROM jobs ORDER BY created_at_utc DESC").fetchall()
        return [self._row_to_job(row) for row in rows]

    def request_cancel(self, job_id: str) -> bool:
        now = datetime.now(UTC).isoformat()
        with self._lock, self._conn() as conn:
            cur = conn.execute(
                "UPDATE jobs SET cancel_requested = 1, updated_at_utc = ? WHERE job_id = ?",
                (now, job_id),
            )
            conn.commit()
            return cur.rowcount > 0

    def update_progress(self, job_id: str, current: int, total: int) -> None:
        now = datetime.now(UTC).isoformat()
        with self._lock, self._conn() as conn:
            conn.execute(
                """
                UPDATE jobs
                SET progress_current = ?, progress_total = ?, updated_at_utc = ?
                WHERE job_id = ?
                """,
                (current, total, now, job_id),
            )
            conn.commit()

    def update_status(
        self,
        job_id: str,
        status: RunStatus,
        result_dir: str | None = None,
        error_message: str | None = None,
    ) -> None:
        now = datetime.now(UTC).isoformat()
        with self._lock, self._conn() as conn:
            conn.execute(
                """
                UPDATE jobs
                SET status = ?, result_dir = ?, error_message = ?, updated_at_utc = ?
                WHERE job_id = ?
                """,
                (status, result_dir, error_message, now, job_id),
            )
            conn.commit()

    def pending_for_restart(self) -> list[RunJob]:
        with self._lock, self._conn() as conn:
            rows = conn.execute(
                """
                SELECT * FROM jobs
                WHERE status IN (?, ?)
                ORDER BY created_at_utc ASC
                """,
                (RunStatus.QUEUED, RunStatus.RUNNING),
            ).fetchall()

        items = [self._row_to_job(row) for row in rows]
        now = datetime.now(UTC)
        for job in items:
            if job.status == RunStatus.RUNNING:
                job.status = RunStatus.QUEUED
                job.updated_at_utc = now
                self.upsert_job(job)
        return items

    def _row_to_job(self, row: sqlite3.Row) -> RunJob:
        return RunJob(
            job_id=row["job_id"],
            status=RunStatus(row["status"]),
            payload=json.loads(row["payload_json"]),
            created_at_utc=datetime.fromisoformat(row["created_at_utc"]),
            updated_at_utc=datetime.fromisoformat(row["updated_at_utc"]),
            progress_current=int(row["progress_current"]),
            progress_total=int(row["progress_total"]),
            result_dir=row["result_dir"],
            error_message=row["error_message"],
            cancel_requested=bool(row["cancel_requested"]),
        )
