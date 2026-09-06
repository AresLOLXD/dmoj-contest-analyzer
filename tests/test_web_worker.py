import asyncio
import uuid
from types import SimpleNamespace

import httpx
import pytest
import respx

from dmoj_contest_analyzer.web import jobs, worker
from dmoj_contest_analyzer.web.db import utcnow
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
