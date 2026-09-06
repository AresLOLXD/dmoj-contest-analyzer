import uuid

import pytest

from dmoj_contest_analyzer.web import jobs
from dmoj_contest_analyzer.web.db import connect, migrate, utcnow


def _mk(conn, settings, owner="alice", **kw):
    jid = uuid.uuid4().hex
    jobs.create_job(
        conn,
        job_id=jid,
        owner=owner,
        model_ref=kw.get("model_ref"),
        run_jplag=kw.get("run_jplag", True),
        jplag_solo_ac=kw.get("jplag_solo_ac", False),
        settings=settings,
    )
    return jid


def test_utcnow_format():
    s = utcnow()
    assert s.endswith("Z") and s[10] == "T" and len(s) == 27


def test_migrate_sets_user_version(settings):
    c = connect(settings.db_path())
    migrate(c)
    assert c.execute("PRAGMA user_version").fetchone()[0] >= 1
    # idempotent
    migrate(c)
    c.close()


def test_rate_limit_enforced(conn, settings):
    for _ in range(settings.rate_limit_per_hour):
        _mk(conn, settings)
        conn.execute(
            "UPDATE jobs SET status='done', finished_at='2026-01-01T00:00:00.000000Z'"
        )
    with pytest.raises(jobs.QuotaExceeded):
        _mk(conn, settings)


def test_max_jobs_per_user_enforced(conn, settings):
    for _ in range(settings.max_jobs_per_user):
        _mk(conn, settings)
    with pytest.raises(jobs.QuotaExceeded) as ei:
        _mk(conn, settings)
    assert ei.value.reason


def test_quota_rejection_rolls_back(conn, settings):
    for _ in range(settings.max_jobs_per_user):
        _mk(conn, settings)
    before = conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
    with pytest.raises(jobs.QuotaExceeded):
        _mk(conn, settings)
    assert conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0] == before


def test_claim_next_job_is_atomic(conn, settings):
    jid = _mk(conn, settings)
    row = jobs.claim_next_job(conn)
    assert row["id"] == jid and row["status"] == "running"
    assert row["started_at"] is not None
    assert jobs.claim_next_job(conn) is None


def test_claim_next_job_orders_by_created_at(conn, settings):
    first = _mk(conn, settings)
    _mk(conn, settings)
    assert jobs.claim_next_job(conn)["id"] == first


def test_set_status_and_get_job(conn, settings):
    jid = _mk(conn, settings)
    jobs.set_status(conn, jid, "failed", error="boom sk-abc123def456", finished=True)
    row = jobs.get_job(conn, jid)
    assert row["status"] == "failed"
    assert "sk-abc123def456" not in row["error"]
    assert row["finished_at"] is not None


def test_get_job_owner_scoped(conn, settings):
    jid = _mk(conn, settings)
    assert jobs.get_job(conn, jid, owner="alice") is not None
    assert jobs.get_job(conn, jid, owner="bob") is None


def test_set_progress_and_pid(conn, settings):
    jid = _mk(conn, settings)
    jobs.set_progress(conn, jid, "working AIzaSyABCDEFGHIJKLMNOP now")
    jobs.set_pid(conn, jid, 4242)
    row = jobs.get_job(conn, jid)
    assert "AIzaSy" not in row["progress"]
    assert row["jvm_pid"] == 4242


def test_reconcile_startup(conn, settings):
    jid = _mk(conn, settings)
    jobs.claim_next_job(conn)
    assert jobs.reconcile_startup(conn) == 1
    assert jobs.get_job(conn, jid)["status"] == "failed"
    assert jobs.get_job(conn, jid)["error"] == "interrumpido por reinicio"


def test_sweep_stale_fails_old_jobs(conn, settings):
    jid = _mk(conn, settings)
    conn.execute(
        "UPDATE jobs SET created_at='2000-01-01T00:00:00.000000Z' WHERE id=?", (jid,)
    )
    conn.commit()
    fresh = _mk(conn, settings)
    jobs.sweep_stale(conn, settings)
    assert jobs.get_job(conn, jid)["status"] == "failed"
    assert jobs.get_job(conn, fresh)["status"] == "queued"
