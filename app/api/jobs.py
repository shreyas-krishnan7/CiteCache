"""
In-memory upload jobs, polled by the frontend for its progress bar.

Jobs live only in this process: a server restart forgets in-flight jobs (the
documents already indexed are unaffected -- they live in Qdrant).
"""
from __future__ import annotations

import threading
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone

_KEEP_FINISHED_FOR = timedelta(hours=1)


@dataclass
class UploadJob:
    id: str
    user_id: str
    filename: str
    status: str = "queued"          # queued | processing | done | error
    stage: str = "Waiting to start"
    progress: int = 0               # 0-100
    chunks_total: int | None = None
    chunks_done: int = 0
    error: str | None = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    finished_at: str | None = None

    def public(self) -> dict:
        d = asdict(self)
        d.pop("user_id")
        return d


_jobs: dict[str, UploadJob] = {}
_lock = threading.Lock()


def _prune() -> None:
    cutoff = datetime.now(timezone.utc) - _KEEP_FINISHED_FOR
    for job_id in [j.id for j in _jobs.values()
                   if j.finished_at and datetime.fromisoformat(j.finished_at) < cutoff]:
        del _jobs[job_id]


def create_job(user_id: str, filename: str) -> UploadJob:
    job = UploadJob(id=uuid.uuid4().hex, user_id=user_id, filename=filename)
    with _lock:
        _prune()
        _jobs[job.id] = job
    return job


def update_job(job: UploadJob, **changes) -> None:
    with _lock:
        for k, v in changes.items():
            setattr(job, k, v)
        if changes.get("status") in ("done", "error"):
            job.finished_at = datetime.now(timezone.utc).isoformat()


def get_job(job_id: str, user_id: str) -> UploadJob | None:
    job = _jobs.get(job_id)
    return job if job and job.user_id == user_id else None


def jobs_for(user_id: str) -> list[UploadJob]:
    with _lock:
        mine = [j for j in _jobs.values() if j.user_id == user_id]
    return sorted(mine, key=lambda j: j.created_at, reverse=True)
