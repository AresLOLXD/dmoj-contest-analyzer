"""Job store: atomic claim and transactional quota checks over the ``jobs`` table.

Every quota check runs inside the same ``BEGIN IMMEDIATE`` transaction as the
``INSERT`` it authorizes; SQLite's single-writer guarantee makes that sufficient.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta

from dmoj_contest_analyzer.llm import redact

from .config import Settings
from .db import _TIMESTAMP_FORMAT, utcnow

# Multiplier applied to ``job_timeout_s`` to decide a queued/running job is stale
# and should be failed so it stops holding a quota slot and participant source.
_STALE_TIMEOUT_MULTIPLIER = 3


class QuotaExceeded(Exception):
    """Raised when a rate limit or per-user job cap would be violated."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


def create_job(
    conn: sqlite3.Connection,
    *,
    job_id: str,
    owner: str,
    model_ref: str | None,
    run_jplag: bool,
    jplag_solo_ac: bool,
    settings: Settings,
) -> None:
    """Insert a queued job after checking quotas in one transaction."""
    now = utcnow()
    cutoff = _minus_one_hour(now)
    conn.execute("BEGIN IMMEDIATE")
    try:
        recent = conn.execute(
            "SELECT COUNT(*) FROM jobs WHERE owner=? AND created_at > ?",
            (owner, cutoff),
        ).fetchone()[0]
        if recent >= settings.rate_limit_per_hour:
            raise QuotaExceeded("límite de trabajos por hora alcanzado")

        active = conn.execute(
            "SELECT COUNT(*) FROM jobs WHERE owner=? AND status IN ('queued', 'running')",
            (owner,),
        ).fetchone()[0]
        if active >= settings.max_jobs_per_user:
            raise QuotaExceeded("ya tienes el máximo de trabajos activos")

        conn.execute(
            "INSERT INTO jobs(id, owner, status, created_at, model_ref, run_jplag, "
            "jplag_solo_ac) VALUES (?, ?, 'queued', ?, ?, ?, ?)",
            (job_id, owner, now, model_ref, int(run_jplag), int(jplag_solo_ac)),
        )
    except BaseException:
        conn.execute("ROLLBACK")
        raise
    conn.execute("COMMIT")


def claim_next_job(conn: sqlite3.Connection) -> sqlite3.Row | None:
    """Atomically move the oldest queued job to ``running`` and return it."""
    return conn.execute(
        "UPDATE jobs SET status='running', started_at=? "
        "WHERE id=(SELECT id FROM jobs WHERE status='queued' "
        "ORDER BY created_at LIMIT 1) RETURNING *",
        (utcnow(),),
    ).fetchone()


def set_status(
    conn: sqlite3.Connection,
    job_id: str,
    status: str,
    *,
    error: str | None = None,
    finished: bool = False,
) -> None:
    fields = ["status=?"]
    params: list[object] = [status]
    if error is not None:
        fields.append("error=?")
        params.append(redact(error))
    if finished:
        fields.append("finished_at=?")
        params.append(utcnow())
    params.append(job_id)
    conn.execute(f"UPDATE jobs SET {', '.join(fields)} WHERE id=?", params)


def set_progress(conn: sqlite3.Connection, job_id: str, text: str) -> None:
    conn.execute(
        "UPDATE jobs SET progress=? WHERE id=?", (redact(text), job_id)
    )


def set_pid(conn: sqlite3.Connection, job_id: str, pid: int) -> None:
    conn.execute("UPDATE jobs SET jvm_pid=? WHERE id=?", (pid, job_id))


def get_job(
    conn: sqlite3.Connection, job_id: str, owner: str | None = None
) -> sqlite3.Row | None:
    if owner is None:
        return conn.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
    return conn.execute(
        "SELECT * FROM jobs WHERE id=? AND owner=?", (job_id, owner)
    ).fetchone()


def reconcile_startup(conn: sqlite3.Connection) -> int:
    """Fail every job left ``running`` by a previous process. Returns the count."""
    cur = conn.execute(
        "UPDATE jobs SET status='failed', error='interrumpido por reinicio' "
        "WHERE status='running'"
    )
    return cur.rowcount


def sweep_stale(conn: sqlite3.Connection, settings: Settings) -> None:
    """Fail queued/running jobs older than ``k * job_timeout_s`` (k=3)."""
    cutoff = _minus_seconds(
        utcnow(), _STALE_TIMEOUT_MULTIPLIER * settings.job_timeout_s
    )
    conn.execute(
        "UPDATE jobs SET status='failed', error='expiró por antigüedad' "
        "WHERE status IN ('queued', 'running') AND created_at < ?",
        (cutoff,),
    )


def _minus_one_hour(now: str) -> str:
    return _minus_seconds(now, 3600)


def _minus_seconds(now: str, seconds: float) -> str:
    parsed = datetime.strptime(now, _TIMESTAMP_FORMAT)
    return (parsed - timedelta(seconds=seconds)).strftime(_TIMESTAMP_FORMAT)
