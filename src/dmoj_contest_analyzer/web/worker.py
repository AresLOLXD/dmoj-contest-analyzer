"""In-process async job worker.

The analysis pipeline (timing -> JPlag -> merge -> report) runs in a killable
``ProcessPoolExecutor`` subprocess. The LLM judge runs afterwards in the worker
coroutine (so ``respx`` works in tests and the daily budget is enforceable),
then the Excel report is rewritten. A separate coroutine reaps expired rows and
their on-disk artifacts.
"""

from __future__ import annotations

import asyncio
import functools
import logging
import multiprocessing as mp
import os
import queue
import shutil
import signal
from concurrent.futures import ProcessPoolExecutor
from concurrent.futures.process import BrokenProcessPool
from datetime import datetime, timedelta
from pathlib import Path

from dmoj_contest_analyzer import ingest
from dmoj_contest_analyzer.analysis import (
    AnalysisOptions,
    NoSubmissionsError,
    ReportData,
    run_analysis,
)
from dmoj_contest_analyzer.llm import JudgeItem, load_backends, redact, resolve
from dmoj_contest_analyzer.llm_run import DeadlineState, run_judge
from dmoj_contest_analyzer.report import write_excel_report
from dmoj_contest_analyzer.submissions import EXT_TO_JPLAG_LANG

from . import jobs
from .db import TIMESTAMP_FORMAT, utcnow
from .upload import UploadRejected, validate_and_extract

log = logging.getLogger(__name__)

# Seconds the idle loop waits for a nudge/stop before re-polling the queue.
_IDLE_WAIT_S = 2.0
# Milliseconds between progress-queue drains while a subprocess runs.
_DRAIN_INTERVAL_S = 0.1


def make_executor(settings) -> ProcessPoolExecutor:
    return ProcessPoolExecutor(max_workers=settings.max_concurrent_jobs)


def _analyze_sync(
    job_id: str,
    zip_path: str,
    work_dir: str,
    out_path: str,
    opts_dict: dict,
    progress_q,
) -> dict:
    """Picklable subprocess entry point: validate, extract, run analysis (no LLM).

    Returns a plain dict of the ``ReportData`` fields plus the detected source
    root. Raises ``UploadRejected`` / ``NoSubmissionsError`` for the parent to
    classify.
    """

    def push(text: str) -> None:
        try:
            progress_q.put_nowait(text)
        except Exception:
            pass

    def on_subprocess(proc) -> None:
        # Report the JVM's process-group id so the parent coroutine can SIGKILL
        # the whole group as an outer backstop if the job times out (layer b).
        try:
            push(("jvm_pgid", os.getpgid(proc.pid)))
        except (OSError, AttributeError):
            pass

    work = Path(work_dir)
    validate_and_extract(Path(zip_path), work, _OptsSettings(opts_dict))
    root = ingest._detect_root(work)

    opts = AnalysisOptions(
        jplag_out=Path(opts_dict["jplag_out"]) if opts_dict["jplag_out"] else None,
        run_jplag=opts_dict["run_jplag"],
        jplag_solo_ac=opts_dict["jplag_solo_ac"],
        jplag_jar=opts_dict["jplag_jar"],
        # Layer a: the normal path — a stuck JVM is killed from inside this
        # subprocess after jplag_per_invocation_timeout_s.
        jplag_timeout_s=opts_dict["jplag_timeout_s"],
        llm_max_source_bytes=opts_dict["max_submission_bytes"],
    )
    data = run_analysis(root, Path(out_path), opts, on_progress=push,
                        on_subprocess=on_subprocess)
    return {
        "source_dir": str(root),
        "main_rows": data.main_rows,
        "jplag_rows": data.jplag_rows,
        "n_subs": data.n_subs,
        "n_users": data.n_users,
        "n_problems": data.n_problems,
    }


class _OptsSettings:
    """Minimal ``settings`` shim for ``validate_and_extract`` inside the subprocess."""

    def __init__(self, d: dict) -> None:
        self.__dict__.update(d["upload_limits"])


def _opts_dict(row, settings) -> dict:
    run_jplag = bool(row["run_jplag"])
    work_parent = settings.data_dir / row["id"]
    return {
        "run_jplag": run_jplag,
        "jplag_solo_ac": bool(row["jplag_solo_ac"]),
        "jplag_out": str(work_parent / "jplag") if run_jplag else None,
        "jplag_jar": str(settings.jplag_jar),
        "jplag_timeout_s": settings.jplag_per_invocation_timeout_s,
        "max_submission_bytes": settings.max_submission_bytes,
        "upload_limits": {
            "max_unzipped_mb": settings.max_unzipped_mb,
            "max_zip_entries": settings.max_zip_entries,
            "max_compression_ratio": settings.max_compression_ratio,
            "max_users": settings.max_users,
            "max_problems": settings.max_problems,
        },
    }


async def process_one_job(conn, settings, executor, *, judge_fn=run_judge, app_state=None) -> bool:
    """Claim and run one job. Returns ``False`` when the queue is empty."""
    row = jobs.claim_next_job(conn)
    if row is None:
        return False

    jid = row["id"]
    job_dir = settings.data_dir / jid
    zip_path = job_dir / "input.zip"
    work_dir = job_dir / "work"
    out_path = job_dir / "reporte.xlsx"

    manager = mp.Manager()
    progress_q = manager.Queue()
    loop = asyncio.get_running_loop()
    fut = loop.run_in_executor(
        executor,
        functools.partial(
            _analyze_sync, jid, str(zip_path), str(work_dir), str(out_path),
            _opts_dict(row, settings), progress_q,
        ),
    )
    # JVM process-group ids reported by the subprocess via the progress queue.
    jvm_pgids: set[int] = set()
    drainer = asyncio.create_task(_drain_progress(progress_q, conn, jid, jvm_pgids))
    try:
        result = await asyncio.wait_for(asyncio.shield(fut), settings.job_timeout_s)
    except TimeoutError:
        # Layer b (backstop): a ProcessPoolExecutor future cannot be cancelled
        # once running, so SIGKILL every recorded JVM process group and discard
        # the whole (potentially poisoned) pool -- it is never reused.
        for pgid in jvm_pgids:
            try:
                os.killpg(pgid, signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                pass
        _replace_pool(executor, settings, app_state)
        jobs.set_status(conn, jid, "failed", error="expiró el tiempo límite", finished=True)
        return True
    except BrokenProcessPool:
        # Subprocess crashed (segfault / OOM-kill). The pool is permanently
        # broken, so swap in a fresh one just like the timeout path.
        _replace_pool(executor, settings, app_state)
        jobs.set_status(conn, jid, "failed", error="el análisis terminó de forma anómala",
                        finished=True)
        return True
    except UploadRejected as exc:
        jobs.set_status(conn, jid, "failed", error=exc.reason, finished=True)
        return True
    except NoSubmissionsError:
        jobs.set_status(conn, jid, "failed", error="el .zip no contenía envíos válidos",
                        finished=True)
        return True
    except Exception:
        log.exception("job %s failed", jid)
        jobs.set_status(conn, jid, "failed",
                        error="error interno durante el análisis", finished=True)
        return True
    finally:
        drainer.cancel()
        try:
            await drainer
        except asyncio.CancelledError:
            pass
        _drain_remaining(progress_q, conn, jid, jvm_pgids)
        manager.shutdown()

    data = ReportData(
        main_rows=result["main_rows"],
        jplag_rows=result["jplag_rows"],
        n_subs=result["n_subs"],
        n_users=result["n_users"],
        n_problems=result["n_problems"],
    )

    if row["model_ref"]:
        llm_pool = getattr(app_state, "llm_pool", None) if app_state is not None else None
        try:
            await asyncio.to_thread(
                _run_judge, conn, settings, data, Path(result["source_dir"]),
                row["model_ref"], judge_fn,
                llm_pool=llm_pool,
                total_deadline_s=settings.llm_judge_total_timeout_s,
            )
        except Exception as exc:  # noqa: BLE001 - judge failure must not fail the job
            log.exception("LLM judge failed for job %s", jid)
            reason = redact(str(exc))[:200]
            data.llm_partial_note = f"El juez con IA falló: {reason}"
            jobs.set_progress(
                conn, jid, f"análisis completo; el juez LLM falló: {reason}"
            )
        await asyncio.to_thread(write_excel_report, data, out_path)

    jobs.set_status(conn, jid, "done", finished=True)
    zip_path.unlink(missing_ok=True)
    shutil.rmtree(work_dir, ignore_errors=True)
    return True


def _run_judge(conn, settings, data: ReportData, source_dir: Path, model_ref: str,
               judge_fn, *, llm_pool=None, total_deadline_s=None) -> None:
    backends = load_backends(settings.backends_config)
    spec, model = resolve(model_ref, backends)

    rows = data.main_rows
    partial_note = None
    if len(rows) > settings.llm_max_submissions_per_job:
        rows = [r for r in data.main_rows if r["score_sospecha"] >= 1]
        partial_note = (
            f"Juez con IA parcial: {len(rows)} de {len(data.main_rows)} envíos "
            f"(solo score_sospecha >= 1) por superar el límite de "
            f"{settings.llm_max_submissions_per_job}."
        )

    items: list[JudgeItem] = []
    for r in rows:
        src_path = source_dir / r["archivo"]
        try:
            source = src_path.read_text(errors="replace")
        except OSError:
            continue
        ext = src_path.suffix.lstrip(".").lower()
        items.append(JudgeItem(
            key=(r["usuario"], r["problema"]),
            problem=r["problema"],
            language=EXT_TO_JPLAG_LANG.get(ext, ext),
            source=source,
        ))

    stopped = _CapState()
    timed_out = DeadlineState()
    results = judge_fn(
        items, spec, model,
        max_tokens=settings.llm_max_tokens_per_call,
        max_source_bytes=settings.max_submission_bytes,
        on_call=functools.partial(_daily_cap_ok, conn, settings, stopped),
        executor=llm_pool,
        total_deadline_s=total_deadline_s,
        deadline_state=timed_out,
    )

    row_by_key = {(r["usuario"], r["problema"]): r for r in data.main_rows}
    llm_rows: list[dict] = []
    for res in results:
        target = row_by_key.get(res.key)
        if target is not None:
            target["llm_ai_score"] = res.ai_score
            target["llm_modelo"] = model_ref
        usuario, problema = res.key
        llm_rows.append({
            "usuario": usuario, "problema": problema, "ai_score": res.ai_score,
            "señales": res.signals, "nota": res.note,
        })

    data.llm_rows = llm_rows
    data.llm_model = model_ref
    if stopped.hit:
        partial_note = (
            f"Juez con IA detenido: se alcanzó el tope diario de "
            f"{settings.llm_max_calls_per_day} llamadas."
        )
    elif timed_out.hit:
        partial_note = (
            f"Juez con IA detenido: se alcanzó el límite de "
            f"{settings.llm_judge_total_timeout_s:.0f} s de tiempo total."
        )
    data.llm_partial_note = partial_note


class _CapState:
    hit = False


def _daily_cap_ok(conn, settings, state: _CapState) -> bool:
    day = utcnow()[:10]
    conn.execute("INSERT INTO llm_usage(day, calls) VALUES (?, 0) ON CONFLICT(day) DO NOTHING",
                 (day,))
    cur = conn.execute(
        "UPDATE llm_usage SET calls = calls + 1 WHERE day = ? AND calls < ?",
        (day, settings.llm_max_calls_per_day),
    )
    if cur.rowcount != 1:
        state.hit = True
        return False
    return True


def _replace_pool(executor: ProcessPoolExecutor, settings, app_state) -> None:
    """Discard a poisoned/broken pool and hand the caller a fresh one.

    ``shutdown(cancel_futures=True)`` only drops *pending* work; a worker
    process still running a timed-out job would otherwise leak. Kill them
    explicitly (CPython-internal attribute, but the alternative is a leak).
    """
    for proc in list(getattr(executor, "_processes", {}).values()):
        try:
            proc.kill()
        except (OSError, AttributeError):
            pass
    executor.shutdown(wait=False, cancel_futures=True)
    if app_state is not None:
        app_state.executor = make_executor(settings)


async def _drain_progress(progress_q, conn, jid: str, jvm_pgids: set[int]) -> None:
    while True:
        _drain_remaining(progress_q, conn, jid, jvm_pgids)
        await asyncio.sleep(_DRAIN_INTERVAL_S)


def _drain_remaining(progress_q, conn, jid: str, jvm_pgids: set[int]) -> None:
    try:
        while True:
            msg = progress_q.get_nowait()
            if isinstance(msg, tuple) and msg and msg[0] == "jvm_pgid":
                jvm_pgids.add(msg[1])
            else:
                jobs.set_progress(conn, jid, msg)
    except (queue.Empty, EOFError, OSError):
        pass


async def worker_loop(app_state, stop: asyncio.Event) -> None:
    while not stop.is_set():
        try:
            ran = await process_one_job(
                app_state.conn, app_state.settings, app_state.executor,
                app_state=app_state,
            )
            if not ran:
                await _wait_for_work(stop, app_state.nudge, _IDLE_WAIT_S)
        except Exception:
            log.exception("worker loop iteration failed")
            # Back off so a persistent failure does not become a hot spin loop.
            await asyncio.sleep(5)
            continue


async def cleanup_loop(app_state, stop: asyncio.Event) -> None:
    interval = app_state.settings.cleanup_every_min * 60
    while not stop.is_set():
        try:
            _cleanup_once(app_state.conn, app_state.settings)
        except Exception:
            log.exception("cleanup iteration failed")
        await _wait_for_work(stop, app_state.nudge, interval)


def _cleanup_once(conn, settings) -> None:
    cutoff = (datetime.strptime(utcnow(), TIMESTAMP_FORMAT)
              - timedelta(hours=settings.retention_h)).strftime(TIMESTAMP_FORMAT)
    expired = conn.execute(
        "SELECT id FROM jobs WHERE status IN ('done', 'failed', 'cancelled') "
        "AND finished_at IS NOT NULL AND finished_at < ?",
        (cutoff,),
    ).fetchall()
    for r in expired:
        shutil.rmtree(settings.data_dir / r["id"], ignore_errors=True)
        conn.execute("DELETE FROM jobs WHERE id = ?", (r["id"],))
    jobs.sweep_stale(conn, settings)


async def _wait_for_work(stop: asyncio.Event, nudge: asyncio.Event, timeout: float) -> None:
    waiters = [asyncio.ensure_future(stop.wait()), asyncio.ensure_future(nudge.wait())]
    try:
        await asyncio.wait(waiters, timeout=timeout, return_when=asyncio.FIRST_COMPLETED)
    finally:
        for w in waiters:
            w.cancel()
    if nudge.is_set():
        nudge.clear()
