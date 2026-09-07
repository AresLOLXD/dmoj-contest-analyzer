import asyncio
import os
import uuid
from types import SimpleNamespace

import httpx
import pytest
import respx

from dmoj_contest_analyzer.web import jobs, worker
from dmoj_contest_analyzer.web.db import connect, utcnow
from tests.test_cli_golden import read_xlsx_values
from tests.web_conftest import make_zip

GOOD = {
    "userA/p1/1_userA_2026-01-01_10-00-00_AC.cpp": b"int main(){}\n",
    "userB/p1/1_userB_2026-01-01_09-00-00_AC.cpp": b"int main(){}\n",
    "userC/p1/1_userC_2026-01-01_08-00-00_AC.cpp": b"int main(){}\n",
}

BACKENDS_TOML = """
[[backend]]
id = "openai"
label = "OpenAI"
base_url = "https://api.openai.com/v1"
models = ["gpt-4o"]
supports_response_format = true
"""


def _slow_analyze(*a, **k):
    import time
    time.sleep(5)


def _crash_analyze(*a, **k):
    os._exit(1)


def _enqueue(conn, settings, model_ref=None):
    jid = uuid.uuid4().hex
    d = settings.data_dir / jid
    d.mkdir(parents=True)
    (d / "input.zip").write_bytes(make_zip(GOOD))
    jobs.create_job(conn, job_id=jid, owner="alice", model_ref=model_ref,
                    run_jplag=False, jplag_solo_ac=False, settings=settings)
    return jid


@pytest.mark.asyncio
async def test_process_one_job_success(conn, settings):
    jid = _enqueue(conn, settings)
    ex = worker.make_executor(settings)
    try:
        assert await worker.process_one_job(conn, settings, ex) is True
    finally:
        ex.shutdown(wait=True)
    row = jobs.get_job(conn, jid)
    assert row["status"] == "done"
    assert (settings.data_dir / jid / "reporte.xlsx").exists()
    assert not (settings.data_dir / jid / "input.zip").exists()
    assert not (settings.data_dir / jid / "work").exists()


@pytest.mark.asyncio
async def test_process_one_job_none_when_empty(conn, settings):
    ex = worker.make_executor(settings)
    try:
        assert await worker.process_one_job(conn, settings, ex) is False
    finally:
        ex.shutdown(wait=True)


@pytest.mark.asyncio
async def test_timeout_marks_failed_and_frees_queue(conn, settings, monkeypatch):
    settings.job_timeout_s = 0.01
    jid = _enqueue(conn, settings)
    monkeypatch.setattr(worker, "_analyze_sync", _slow_analyze)
    ex = worker.make_executor(settings)
    state = SimpleNamespace(executor=ex)
    try:
        assert await worker.process_one_job(conn, settings, ex, app_state=state) is True
    finally:
        state.executor.shutdown(wait=False, cancel_futures=True)
    assert jobs.get_job(conn, jid)["status"] == "failed"
    assert state.executor is not ex  # poisoned pool discarded


@pytest.mark.asyncio
async def test_broken_pool_recovers(conn, settings, monkeypatch):
    jid1 = _enqueue(conn, settings)
    monkeypatch.setattr(worker, "_analyze_sync", _crash_analyze)
    ex = worker.make_executor(settings)
    state = SimpleNamespace(executor=ex)
    assert await worker.process_one_job(conn, settings, ex, app_state=state) is True
    assert jobs.get_job(conn, jid1)["status"] == "failed"
    assert state.executor is not ex  # broken pool replaced

    monkeypatch.undo()
    jid2 = _enqueue(conn, settings)
    try:
        assert await worker.process_one_job(
            conn, settings, state.executor, app_state=state) is True
    finally:
        state.executor.shutdown(wait=True)
    assert jobs.get_job(conn, jid2)["status"] == "done"


@pytest.mark.asyncio
async def test_bad_zip_marks_failed(conn, settings):
    jid = uuid.uuid4().hex
    d = settings.data_dir / jid
    d.mkdir(parents=True)
    (d / "input.zip").write_bytes(b"not a zip")
    jobs.create_job(conn, job_id=jid, owner="alice", model_ref=None,
                    run_jplag=False, jplag_solo_ac=False, settings=settings)
    ex = worker.make_executor(settings)
    try:
        assert await worker.process_one_job(conn, settings, ex) is True
    finally:
        ex.shutdown(wait=True)
    assert jobs.get_job(conn, jid)["status"] == "failed"


@respx.mock
@pytest.mark.asyncio
async def test_llm_path_writes_report(conn, settings):
    respx.post("https://api.openai.com/v1/chat/completions").mock(
        return_value=httpx.Response(200, json={"choices": [{"message": {"content":
            '{"ai_score": 77, "señales": ["comentarios tutorial"], "nota": "revisar"}'}}]})
    )
    settings.backends_config.write_text(BACKENDS_TOML)
    jid = _enqueue(conn, settings, model_ref="openai|gpt-4o")
    ex = worker.make_executor(settings)
    try:
        assert await worker.process_one_job(conn, settings, ex) is True
    finally:
        ex.shutdown(wait=True)
    assert jobs.get_job(conn, jid)["status"] == "done"
    values = read_xlsx_values(settings.data_dir / jid / "reporte.xlsx")
    ts = {(r["usuario"], r["problema"]): r for r in values["Timing y Estilo"]}
    assert all(r["llm_ai_score"] == 77 for r in ts.values())
    assert all(r["llm_modelo"] == "openai|gpt-4o" for r in ts.values())
    assert conn.execute("SELECT calls FROM llm_usage").fetchone()["calls"] == 3


@respx.mock
@pytest.mark.asyncio
async def test_llm_per_call_failures_surface_in_report(conn, settings):
    """Per-call failures (timeouts, 5xx) must show in the note, not vanish silently."""
    respx.post("https://api.openai.com/v1/chat/completions").mock(
        return_value=httpx.Response(500, headers={"Retry-After": "0"})
    )
    settings.backends_config.write_text(BACKENDS_TOML)
    jid = _enqueue(conn, settings, model_ref="openai|gpt-4o")
    ex = worker.make_executor(settings)
    try:
        assert await worker.process_one_job(conn, settings, ex) is True
    finally:
        ex.shutdown(wait=True)
    assert jobs.get_job(conn, jid)["status"] == "done"
    values = read_xlsx_values(settings.data_dir / jid / "reporte.xlsx")
    resumen = {r["Métrica"]: r["Valor"] for r in values["Resumen"]}
    assert "fallaron" in resumen["Nota juez LLM"]


@respx.mock
@pytest.mark.asyncio
async def test_llm_daily_cap_stops_judge(conn, settings):
    respx.post("https://api.openai.com/v1/chat/completions").mock(
        return_value=httpx.Response(200, json={"choices": [{"message": {"content":
            '{"ai_score": 50, "señales": [], "nota": "x"}'}}]})
    )
    settings.backends_config.write_text(BACKENDS_TOML)
    settings.llm_max_calls_per_day = 1
    jid = _enqueue(conn, settings, model_ref="openai|gpt-4o")
    ex = worker.make_executor(settings)
    try:
        await worker.process_one_job(conn, settings, ex)
    finally:
        ex.shutdown(wait=True)
    assert jobs.get_job(conn, jid)["status"] == "done"
    values = read_xlsx_values(settings.data_dir / jid / "reporte.xlsx")
    resumen = {r["Métrica"]: r["Valor"] for r in values["Resumen"]}
    assert "tope diario" in resumen["Nota juez LLM"]


@pytest.mark.asyncio
async def test_worker_does_not_block_event_loop(conn, settings, monkeypatch):
    """While a job's judge + report writing run, the loop must stay responsive."""
    settings.backends_config.write_text(BACKENDS_TOML)

    def _slow_judge(*a, **k):
        import time
        time.sleep(1.0)  # simulates a slow LLM judge

    monkeypatch.setattr(worker, "_run_judge", _slow_judge)

    real_write = worker.write_excel_report

    def _slow_write(data, path):
        import time
        time.sleep(0.5)
        return real_write(data, path)

    monkeypatch.setattr(worker, "write_excel_report", _slow_write)

    jid = _enqueue(conn, settings, model_ref="openai|gpt-4o")
    ex = worker.make_executor(settings)

    ticks = {"n": 0}

    async def ticker():
        while True:
            ticks["n"] += 1
            await asyncio.sleep(0.05)

    t = asyncio.create_task(ticker())
    try:
        assert await worker.process_one_job(conn, settings, ex) is True
    finally:
        t.cancel()
        ex.shutdown(wait=True)

    # ~1.5 s of blocking work would leave ticks near 0 if it ran on the loop.
    assert ticks["n"] > 10
    assert jobs.get_job(conn, jid)["status"] == "done"


def test_cleanup_once_reaps_expired(conn, settings):
    old = uuid.uuid4().hex
    fresh = uuid.uuid4().hex
    for jid in (old, fresh):
        (settings.data_dir / jid).mkdir(parents=True)
        (settings.data_dir / jid / "reporte.xlsx").write_bytes(b"x")
        jobs.create_job(conn, job_id=jid, owner="alice", model_ref=None,
                        run_jplag=False, jplag_solo_ac=False, settings=settings)
    conn.execute("UPDATE jobs SET status='done', finished_at=? WHERE id=?",
                 ("2000-01-01T00:00:00.000000Z", old))
    conn.execute("UPDATE jobs SET status='done', finished_at=? WHERE id=?", (utcnow(), fresh))

    worker._cleanup_once(conn, settings)

    assert jobs.get_job(conn, old) is None
    assert not (settings.data_dir / old).exists()
    assert jobs.get_job(conn, fresh) is not None
    assert (settings.data_dir / fresh).exists()


@pytest.mark.asyncio
async def test_worker_loop_processes_then_stops(conn, settings):
    jid = _enqueue(conn, settings)
    stop = asyncio.Event()
    state = SimpleNamespace(conn=conn, settings=settings,
                            executor=worker.make_executor(settings), nudge=asyncio.Event())
    task = asyncio.create_task(worker.worker_loop(state, stop))
    try:
        for _ in range(100):
            if jobs.get_job(conn, jid)["status"] in ("done", "failed"):
                break
            await asyncio.sleep(0.1)
    finally:
        stop.set()
        state.nudge.set()
        await asyncio.wait_for(task, timeout=5)
        state.executor.shutdown(wait=True)
    assert jobs.get_job(conn, jid)["status"] == "done"


@pytest.mark.asyncio
async def test_llm_judge_failure_is_visible_in_report(conn, settings, monkeypatch):
    """A judge exception must surface in the report, not vanish (I4)."""
    settings.backends_config.write_text(BACKENDS_TOML)

    def _boom(*a, **k):
        raise RuntimeError("endpoint caído")

    monkeypatch.setattr(worker, "_run_judge", _boom)
    jid = _enqueue(conn, settings, model_ref="openai|gpt-4o")
    ex = worker.make_executor(settings)
    try:
        assert await worker.process_one_job(conn, settings, ex) is True
    finally:
        ex.shutdown(wait=True)
    assert jobs.get_job(conn, jid)["status"] == "done"
    resumen = {r["Métrica"]: r["Valor"]
               for r in read_xlsx_values(settings.data_dir / jid / "reporte.xlsx")["Resumen"]}
    assert "falló" in resumen["Nota juez LLM"]


def test_cleanup_once_reaps_cancelled(conn, settings):
    """A cancelled job's row and directory must be reaped by retention (I1)."""
    jid = uuid.uuid4().hex
    (settings.data_dir / jid).mkdir(parents=True)
    (settings.data_dir / jid / "input.zip").write_bytes(b"student source")
    jobs.create_job(conn, job_id=jid, owner="alice", model_ref=None,
                    run_jplag=False, jplag_solo_ac=False, settings=settings)
    conn.execute("UPDATE jobs SET status='cancelled', finished_at=? WHERE id=?",
                 ("2000-01-01T00:00:00.000000Z", jid))

    worker._cleanup_once(conn, settings)

    assert jobs.get_job(conn, jid) is None
    assert not (settings.data_dir / jid).exists()


@pytest.mark.asyncio
async def test_cleanup_loop_does_not_spin_when_nudge_is_set(conn, settings, monkeypatch):
    """cleanup_loop must not react to the shared nudge: a set nudge (all workers
    busy) would otherwise hot-spin _cleanup_once against the SQLite write lock."""
    settings.cleanup_every_min = 60  # long interval; one pass then wait on stop
    calls = {"n": 0}

    def _count(*a, **k):
        calls["n"] += 1

    monkeypatch.setattr(worker, "_cleanup_once", _count)
    stop = asyncio.Event()
    nudge = asyncio.Event()
    nudge.set()  # simulate a handler that enqueued while every worker was busy
    state = SimpleNamespace(conn=conn, settings=settings, nudge=nudge)
    task = asyncio.create_task(worker.cleanup_loop(state, stop))
    await asyncio.sleep(0.5)
    stop.set()
    nudge.set()
    await asyncio.wait_for(task, timeout=5)

    assert calls["n"] == 1


@pytest.mark.asyncio
async def test_worker_loop_backs_off_on_persistent_failure(settings, monkeypatch):
    """A crash before the idle wait must not hot-spin the loop (I3)."""
    calls = {"n": 0}

    async def boom(*a, **k):
        calls["n"] += 1
        raise RuntimeError("persistent")

    slept: list[float] = []

    async def fake_sleep(secs):
        slept.append(secs)
        if len(slept) >= 3:
            stop.set()

    monkeypatch.setattr(worker, "process_one_job", boom)
    monkeypatch.setattr(worker.asyncio, "sleep", fake_sleep)
    stop = asyncio.Event()
    state = SimpleNamespace(conn=None, settings=settings, executor=None,
                            nudge=asyncio.Event())
    await asyncio.wait_for(worker.worker_loop(state, stop), timeout=5)

    assert calls["n"] >= 3
    assert all(s >= 1 for s in slept)


def _report_shape(work_dir: str) -> dict:
    return {
        "source_dir": str(os.path.dirname(work_dir)), "main_rows": [], "jplag_rows": [],
        "n_subs": 0, "n_users": 0, "n_problems": 0,
    }


def _slow_concurrent_probe(job_id, zip_path, work_dir, out_path, opts_dict, progress_q):
    """Module-level (picklable) analyze stub: records its start time to a shared
    file so the parent can assert the two subprocess starts overlap."""
    import time
    from pathlib import Path

    marks = Path(work_dir).parent.parent / "starts.txt"
    with marks.open("a") as fh:
        fh.write(f"{time.monotonic()}\n")
    time.sleep(1.0)
    return _report_shape(work_dir)


def _slow_report(job_id, zip_path, work_dir, out_path, opts_dict, progress_q):
    import time
    progress_q.put_nowait("procesando envíos")
    time.sleep(0.6)
    return _report_shape(work_dir)


@pytest.mark.asyncio
async def test_two_workers_process_two_jobs_concurrently(conn, settings, monkeypatch):
    settings.max_concurrent_jobs = 2

    monkeypatch.setattr(worker, "_analyze_sync", _slow_concurrent_probe)
    j1, j2 = _enqueue(conn, settings), _enqueue(conn, settings)

    stop = asyncio.Event()
    state = SimpleNamespace(settings=settings, nudge=asyncio.Event())
    sup = asyncio.create_task(worker.run_workers(state, stop))
    try:
        for _ in range(60):
            if {jobs.get_job(conn, j)["status"] for j in (j1, j2)} == {"done"}:
                break
            await asyncio.sleep(0.1)
    finally:
        stop.set()
        state.nudge.set()
        await asyncio.wait_for(sup, timeout=10)

    assert {jobs.get_job(conn, j)["status"] for j in (j1, j2)} == {"done"}
    started = [
        float(x) for x in
        (settings.data_dir / "starts.txt").read_text().split()
    ]
    # Concurrent: the two subprocess starts are < 0.5 s apart, not ~1 s serial.
    assert len(started) == 2 and abs(started[0] - started[1]) < 0.5


@pytest.mark.asyncio
async def test_worker_writes_isolated_from_handler_rollback(conn, settings, monkeypatch):
    """A separate connection's BEGIN IMMEDIATE ... ROLLBACK (a request handler)
    must not undo the worker's status/progress writes (CONTROLLER NOTE)."""
    settings.max_concurrent_jobs = 1

    monkeypatch.setattr(worker, "_analyze_sync", _slow_report)
    jid = _enqueue(conn, settings)

    stop = asyncio.Event()
    state = SimpleNamespace(settings=settings, nudge=asyncio.Event())
    sup = asyncio.create_task(worker.run_workers(state, stop))
    try:
        for _ in range(60):
            if jobs.get_job(conn, jid)["status"] == "running":
                break
            await asyncio.sleep(0.05)
        assert jobs.get_job(conn, jid)["status"] == "running"

        # Wait until the worker drained a progress line onto its own connection.
        for _ in range(40):
            if jobs.get_job(conn, jid)["progress"]:
                break
            await asyncio.sleep(0.05)
        assert jobs.get_job(conn, jid)["progress"] == "procesando envíos"

        # A request handler: open a transaction, write, then roll back. On a
        # separate connection this must not touch the worker's committed writes.
        other = connect(settings.db_path())
        try:
            other.execute("BEGIN IMMEDIATE")
            other.execute(
                "UPDATE jobs SET progress='handler garbage' WHERE id=?", (jid,)
            )
            other.execute("ROLLBACK")
        finally:
            other.close()

        for _ in range(80):
            if jobs.get_job(conn, jid)["status"] == "done":
                break
            await asyncio.sleep(0.1)
    finally:
        stop.set()
        state.nudge.set()
        await asyncio.wait_for(sup, timeout=10)

    row = jobs.get_job(conn, jid)
    assert row["status"] == "done"
    # The progress the worker wrote during the window survived the rollback.
    assert row["progress"] == "procesando envíos"


def test_cleanup_once_reaps_stale_awaiting_upload_dir(conn, settings):
    settings.awaiting_upload_timeout_s = 1
    jid = uuid.uuid4().hex
    (settings.data_dir / jid).mkdir(parents=True)
    (settings.data_dir / jid / "input.zip").write_bytes(b"partial")
    jobs.create_job(conn, job_id=jid, owner="alice", model_ref=None,
                    run_jplag=False, jplag_solo_ac=False, settings=settings,
                    status="awaiting_upload")
    conn.execute("UPDATE jobs SET created_at=? WHERE id=?",
                 ("2000-01-01T00:00:00.000000Z", jid))

    worker._cleanup_once(conn, settings)

    row = jobs.get_job(conn, jid)
    assert row["status"] == "failed"
    assert not (settings.data_dir / jid).exists()


def test_cleanup_once_keeps_dir_when_put_races_to_queued(conn, settings, monkeypatch):
    """I3: a stale awaiting_upload row flipped to 'queued' by an in-flight PUT
    during the cleanup window must keep its input.zip."""
    settings.awaiting_upload_timeout_s = 1
    jid = uuid.uuid4().hex
    (settings.data_dir / jid).mkdir(parents=True)
    (settings.data_dir / jid / "input.zip").write_bytes(b"just uploaded")
    jobs.create_job(conn, job_id=jid, owner="alice", model_ref=None,
                    run_jplag=False, jplag_solo_ac=False, settings=settings,
                    status="awaiting_upload")
    # Only mildly stale: old enough for the awaiting_upload timeout, but not the
    # much larger queued/running staleness window.
    conn.execute("UPDATE jobs SET created_at=? WHERE id=?",
                 (jobs._minus_seconds(utcnow(), 5), jid))

    real_sweep = jobs.sweep_stale

    def racing_sweep(c, s):
        jobs.mark_uploaded(c, jid)  # the PUT lands mid-cleanup
        real_sweep(c, s)

    monkeypatch.setattr(worker.jobs, "sweep_stale", racing_sweep)
    worker._cleanup_once(conn, settings)

    assert jobs.get_job(conn, jid)["status"] == "queued"
    assert (settings.data_dir / jid / "input.zip").exists()


@pytest.mark.asyncio
async def test_timeout_kills_pool_worker_processes(conn, settings, monkeypatch):
    """A timed-out subprocess must be killed, not merely abandoned (I8)."""
    settings.job_timeout_s = 0.05
    _enqueue(conn, settings)
    monkeypatch.setattr(worker, "_analyze_sync", _slow_analyze)
    ex = worker.make_executor(settings)
    ex.submit(os.getpid).result()
    procs = list(ex._processes.values())
    state = SimpleNamespace(executor=ex)
    try:
        await worker.process_one_job(conn, settings, ex, app_state=state)
    finally:
        state.executor.shutdown(wait=False, cancel_futures=True)
    for p in procs:
        p.join(timeout=5)
        assert p.exitcode is not None
