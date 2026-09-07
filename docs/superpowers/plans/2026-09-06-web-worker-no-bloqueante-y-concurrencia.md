# Worker no bloqueante, concurrencia y subida en 2 pasos — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** El worker de análisis deja de bloquear el event loop de uvicorn, corre varios jobs en paralelo hasta un tope configurable, encola las llamadas al LLM con un tope global configurable, y la subida del `.zip` deja de pasar por el request que Cloudflare corta a los ~100 s.

**Architecture:** El worker sigue siendo tarea del mismo proceso que uvicorn, pero un *supervisor* lanza N corrutinas worker; cada una tiene su propia conexión SQLite (WAL, `check_same_thread=False`) y su propio `ProcessPoolExecutor(max_workers=1)`. El juez LLM y la escritura de Excel se ejecutan con `asyncio.to_thread`. Las llamadas HTTP al LLM se reparten en un `ThreadPoolExecutor` único a nivel de app. La subida se parte en `POST /jobs` (crea la fila `awaiting_upload` al instante) + `PUT /jobs/{id}/upload` (XHR con barra de progreso).

**Tech Stack:** Python 3.11+, FastAPI/Starlette, `asyncio`, `concurrent.futures`, `sqlite3` (WAL), `httpx`, `pytest` + `pytest-asyncio` (`asyncio_mode=auto`) + `respx`.

**Spec:** `docs/superpowers/specs/2026-09-06-web-worker-no-bloqueante-y-concurrencia-design.md`

## Global Constraints

- Todo el código, nombres y comentarios en **inglés**; textos de UI y mensajes de error visibles al usuario en **español** (patrón ya existente en `web/`).
- `ruff` limpio: `select = ["E","F","I","UP","B"]`, `line-length = 100`.
- Timestamps siempre con `db.utcnow()` / `TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"` (comparables lexicográficamente).
- No romper el CLI: `llm_run.run_judge(...)` sin `executor` se comporta exactamente igual que hoy.
- No romper la suite `tests/` existente salvo los ajustes que este plan detalla explícitamente.
- Autoescape de Jinja siempre on; nunca `|safe`. CSP: `script-src 'self'` (sin scripts inline).
- Cada tarea termina con `git commit`. Commits en la rama `feat/worker-concurrencia-listado`.

---

### Task 1: `run_judge` acepta un executor externo y un deadline total

**Files:**
- Modify: `src/dmoj_contest_analyzer/llm_run.py`
- Test: `tests/test_llm_judge.py`

**Interfaces:**
- Consumes: `llm.judge_one`, `llm.JudgeResult`, `llm.JudgeItem`, `llm.BackendSpec` (sin cambios).
- Produces:
  ```python
  class DeadlineState:
      hit: bool = False

  def run_judge(
      items: list[JudgeItem], spec: BackendSpec, model: str, *,
      max_tokens: int, max_source_bytes: int,
      max_workers: int = 4,
      on_call: Callable[[], bool] = lambda: True,
      executor: concurrent.futures.Executor | None = None,
      total_deadline_s: float | None = None,
      deadline_state: "DeadlineState | None" = None,
  ) -> list[JudgeResult]
  ```
  - `executor is None` → comportamiento actual (crea y cierra un `ThreadPoolExecutor`).
  - `executor` dado → lo usa y **no** lo cierra (ni lo dimensiona).
  - `total_deadline_s` acota la fase de recolección de resultados; los futures no terminados se cancelan y su ítem queda con `JudgeResult(key, None)`.
  - Si hubo futures sin terminar y se pasó `deadline_state`, se pone `deadline_state.hit = True`.

- [ ] **Step 1: Escribir el test que falla — executor externo no se cierra**

En `tests/test_llm_judge.py`, añadir al final:

```python
from concurrent.futures import ThreadPoolExecutor

from dmoj_contest_analyzer.llm_run import DeadlineState


@respx.mock
def test_run_judge_uses_external_executor_without_closing_it():
    respx.post("https://api.openai.com/v1/chat/completions").mock(
        return_value=_chat('{"ai_score": 7, "señales": [], "nota": ""}')
    )
    spec = BackendSpec("openai", "OpenAI", "https://api.openai.com/v1", ["gpt-4o"], True, "sk-x")
    items = [JudgeItem((f"u{i}", "p"), "p", "cpp", "x") for i in range(3)]
    pool = ThreadPoolExecutor(max_workers=2)
    try:
        results = run_judge(items, spec, "gpt-4o", max_tokens=100, max_source_bytes=100,
                            executor=pool)
        assert len(results) == 3
        # Still usable: the pool was not shut down by run_judge.
        assert pool.submit(lambda: 42).result() == 42
    finally:
        pool.shutdown(wait=True)


@respx.mock
def test_run_judge_total_deadline_cancels_pending():
    def _slow(request):
        import time
        time.sleep(0.4)
        return _chat('{"ai_score": 3, "señales": [], "nota": ""}')

    respx.post("https://api.openai.com/v1/chat/completions").mock(side_effect=_slow)
    spec = BackendSpec("openai", "OpenAI", "https://api.openai.com/v1", ["gpt-4o"], True, "sk-x")
    items = [JudgeItem((f"u{i}", "p"), "p", "cpp", "x") for i in range(4)]
    state = DeadlineState()
    results = run_judge(items, spec, "gpt-4o", max_tokens=100, max_source_bytes=100,
                        max_workers=1, total_deadline_s=0.1, deadline_state=state)
    assert len(results) == 4
    assert any(r.ai_score is None for r in results)
    assert state.hit is True
```

- [ ] **Step 2: Correr los tests nuevos y verlos fallar**

Run: `uv run pytest tests/test_llm_judge.py -k "external_executor or total_deadline" -v`
Expected: FAIL — `ImportError: cannot import name 'DeadlineState'`.

- [ ] **Step 3: Reescribir `run_judge`**

Reemplazar el cuerpo de `src/dmoj_contest_analyzer/llm_run.py` por:

```python
"""Batch LLM judge loop shared by the CLI and the web worker."""

import time
from collections.abc import Callable
from concurrent.futures import Executor, ThreadPoolExecutor
from concurrent.futures import wait as futures_wait

import httpx

from dmoj_contest_analyzer.llm import BackendSpec, JudgeItem, JudgeResult, judge_one


class DeadlineState:
    """Set ``hit`` to True when the total deadline cancelled pending calls."""

    def __init__(self) -> None:
        self.hit = False


def run_judge(
    items: list[JudgeItem],
    spec: BackendSpec,
    model: str,
    *,
    max_tokens: int,
    max_source_bytes: int,
    max_workers: int = 4,
    on_call: Callable[[], bool] = lambda: True,
    executor: Executor | None = None,
    total_deadline_s: float | None = None,
    deadline_state: DeadlineState | None = None,
) -> list[JudgeResult]:
    """Judge ``items`` concurrently.

    ``on_call()`` is invoked once per item before it is scheduled; the first
    falsy return stops the loop and the remaining items are left unjudged.

    If ``executor`` is given it is used and never shut down (a process-wide
    pool owned by the caller); otherwise a local pool is created and closed.
    ``total_deadline_s`` bounds the result-collection phase: futures still
    running are cancelled and their item gets ``JudgeResult(key, None)``; when
    that happens and ``deadline_state`` was passed, ``deadline_state.hit`` is
    set.
    """
    allowed: list[JudgeItem] = []
    for item in items:
        if not on_call():
            break
        allowed.append(item)
    if not allowed:
        return []

    own_pool = executor is None
    pool: Executor = executor or ThreadPoolExecutor(
        max_workers=min(max_workers, len(allowed))
    )
    client = httpx.Client(follow_redirects=False, timeout=60)
    try:
        futures = {
            pool.submit(
                judge_one, client, spec, model, item,
                max_tokens=max_tokens, max_source_bytes=max_source_bytes,
            ): item
            for item in allowed
        }
        timeout = total_deadline_s
        done, not_done = futures_wait(futures, timeout=timeout)
        results: list[JudgeResult] = []
        if not_done:
            if deadline_state is not None:
                deadline_state.hit = True
            for future in not_done:
                future.cancel()
                results.append(JudgeResult(futures[future].key, None))
        for future in done:
            try:
                results.append(future.result())
            except Exception:
                # A single failing call must not abort the batch.
                results.append(JudgeResult(futures[future].key, None))
        return results
    finally:
        client.close()
        if own_pool:
            pool.shutdown(wait=True)


# ``time`` is imported for callers that want a monotonic reference; keep it
# available even though the deadline is passed as a relative value.
_ = time
```

(Quitar la última línea `_ = time` y el `import time` si `ruff` marca F401 — no se usa; se dejó por si un cambio futuro lo necesita. **Decisión: quitarlo ahora**, no hace falta.)

Versión final sin `time`:

```python
"""Batch LLM judge loop shared by the CLI and the web worker."""

from collections.abc import Callable
from concurrent.futures import Executor, ThreadPoolExecutor
from concurrent.futures import wait as futures_wait

import httpx

from dmoj_contest_analyzer.llm import BackendSpec, JudgeItem, JudgeResult, judge_one


class DeadlineState:
    def __init__(self) -> None:
        self.hit = False


def run_judge(
    items: list[JudgeItem],
    spec: BackendSpec,
    model: str,
    *,
    max_tokens: int,
    max_source_bytes: int,
    max_workers: int = 4,
    on_call: Callable[[], bool] = lambda: True,
    executor: Executor | None = None,
    total_deadline_s: float | None = None,
    deadline_state: DeadlineState | None = None,
) -> list[JudgeResult]:
    allowed: list[JudgeItem] = []
    for item in items:
        if not on_call():
            break
        allowed.append(item)
    if not allowed:
        return []

    own_pool = executor is None
    pool: Executor = executor or ThreadPoolExecutor(
        max_workers=min(max_workers, len(allowed))
    )
    client = httpx.Client(follow_redirects=False, timeout=60)
    try:
        futures = {
            pool.submit(
                judge_one, client, spec, model, item,
                max_tokens=max_tokens, max_source_bytes=max_source_bytes,
            ): item
            for item in allowed
        }
        done, not_done = futures_wait(futures, timeout=total_deadline_s)
        results: list[JudgeResult] = []
        if not_done:
            if deadline_state is not None:
                deadline_state.hit = True
            for future in not_done:
                future.cancel()
                results.append(JudgeResult(futures[future].key, None))
        for future in done:
            try:
                results.append(future.result())
            except Exception:
                results.append(JudgeResult(futures[future].key, None))
        return results
    finally:
        client.close()
        if own_pool:
            pool.shutdown(wait=True)
```

- [ ] **Step 4: Correr los tests de `llm_run` completos**

Run: `uv run pytest tests/test_llm_judge.py tests/test_llm_registry.py -v`
Expected: PASS (incluidos `test_run_judge_stops_when_on_call_false`, `test_run_judge_one_failure_does_not_abort_batch`, y los dos nuevos).

- [ ] **Step 5: `ruff` y commit**

```bash
uv run ruff check src/dmoj_contest_analyzer/llm_run.py tests/test_llm_judge.py
git add src/dmoj_contest_analyzer/llm_run.py tests/test_llm_judge.py
git commit -m "feat(llm): run_judge acepta executor externo y deadline total"
```

---

### Task 2: Config nueva + pool LLM compartido en el app state

**Files:**
- Modify: `src/dmoj_contest_analyzer/web/config.py:35-42` (bloque "Job scheduling / rate limiting") y `:47-52` (bloque LLM)
- Modify: `src/dmoj_contest_analyzer/web/app.py:40-71` (lifespan)
- Test: `tests/test_web_config.py`, `tests/test_web_setup.py`

**Interfaces:**
- Produces:
  - `Settings.max_concurrent_jobs: int = 2` (antes `1`)
  - `Settings.llm_concurrency: int = 4`
  - `Settings.llm_judge_total_timeout_s: float = 600`
  - `Settings.awaiting_upload_timeout_s: float = 3600`
  - `app.state.llm_pool: concurrent.futures.ThreadPoolExecutor` (creado en lifespan cuando `start_worker=True`; `shutdown(wait=False)` al cerrar)

- [ ] **Step 1: Test que falla — los nuevos campos existen con sus defaults**

En `tests/test_web_config.py`, añadir:

```python
def test_new_scheduling_and_llm_defaults(monkeypatch, tmp_path):
    monkeypatch.setenv("APP_SECRET_KEY", "x")
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    from dmoj_contest_analyzer.web.config import Settings
    s = Settings()
    assert s.max_concurrent_jobs == 2
    assert s.llm_concurrency == 4
    assert s.llm_judge_total_timeout_s == 600
    assert s.awaiting_upload_timeout_s == 3600


def test_llm_concurrency_env_override(monkeypatch, tmp_path):
    monkeypatch.setenv("APP_SECRET_KEY", "x")
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("LLM_CONCURRENCY", "1")
    from dmoj_contest_analyzer.web.config import Settings
    assert Settings().llm_concurrency == 1
```

(Si `test_web_config.py` ya tiene un patrón de fixture distinto para instanciar `Settings`, seguirlo; el objetivo es sólo verificar defaults y override por env.)

- [ ] **Step 2: Correr y ver fallar**

Run: `uv run pytest tests/test_web_config.py -k "new_scheduling or llm_concurrency_env" -v`
Expected: FAIL — `AttributeError` / `assert 1 == 2` en `max_concurrent_jobs`.

- [ ] **Step 3: Añadir los campos a `config.py`**

En el bloque `# Job scheduling / rate limiting`:

```python
    rate_limit_per_hour: int = 5
    max_jobs_per_user: int = 2
    max_concurrent_jobs: int = 2
    job_timeout_s: float = 1800
    jplag_per_invocation_timeout_s: int = 300
    retention_h: int = 12
    cleanup_every_min: int = 30
    awaiting_upload_timeout_s: float = 3600
```

En el bloque `# LLM judge`:

```python
    llm_max_submissions_per_job: int = 200
    llm_max_calls_per_day: int = 2000
    llm_max_tokens_per_call: int = 1500
    llm_request_timeout_s: float = 60
    llm_threshold: int = 70
    llm_concurrency: int = 4
    llm_judge_total_timeout_s: float = 600
```

- [ ] **Step 4: Crear el pool LLM en el lifespan de `app.py`**

En `create_app`, dentro de `lifespan`, en el bloque `if start_worker:` (después de `app.state.executor = make_executor(settings)`):

```python
        if start_worker:
            app.state.executor = make_executor(settings)
            app.state.llm_pool = ThreadPoolExecutor(
                max_workers=settings.llm_concurrency,
                thread_name_prefix="llm",
            )
            app.state.stop = asyncio.Event()
            tasks = [
                asyncio.create_task(worker_loop(app.state, app.state.stop)),
                asyncio.create_task(cleanup_loop(app.state, app.state.stop)),
            ]
```

Y en el `finally`, tras `app.state.executor.shutdown(...)`:

```python
                app.state.executor.shutdown(wait=False, cancel_futures=True)
                app.state.llm_pool.shutdown(wait=False, cancel_futures=True)
```

Import arriba del archivo:

```python
from concurrent.futures import ThreadPoolExecutor
```

(Task 5 cambia `worker_loop` por el supervisor; por ahora déjalo como está — este paso sólo añade el pool.)

- [ ] **Step 5: Correr config + arranque de la app**

Run: `uv run pytest tests/test_web_config.py tests/test_web_setup.py -v`
Expected: PASS.

- [ ] **Step 6: `ruff` y commit**

```bash
uv run ruff check src/dmoj_contest_analyzer/web/config.py src/dmoj_contest_analyzer/web/app.py tests/test_web_config.py
git add src/dmoj_contest_analyzer/web/config.py src/dmoj_contest_analyzer/web/app.py tests/test_web_config.py
git commit -m "feat(web): config de concurrencia + pool LLM compartido en app.state"
```

---

### Task 3: El worker no bloquea el event loop

**Files:**
- Modify: `src/dmoj_contest_analyzer/web/db.py:25-33` (`connect`)
- Modify: `src/dmoj_contest_analyzer/web/worker.py:135-228` (`process_one_job`), `:231-289` (`_run_judge`)
- Test: `tests/test_web_worker.py`

**Interfaces:**
- Consumes: `Settings.llm_judge_total_timeout_s` (Task 2); `run_judge(executor=, total_deadline_s=, deadline_state=)`, `DeadlineState` (Task 1).
- Produces:
  - `db.connect(path)` abre con `check_same_thread=False`.
  - `process_one_job(conn, settings, executor, *, judge_fn=run_judge, app_state=None)` — misma firma; internamente `await asyncio.to_thread(...)` para el juez y para `write_excel_report`.
  - `_run_judge(conn, settings, data, source_dir, model_ref, judge_fn, *, llm_pool=None, total_deadline_s=None)` — nuevos kwargs opcionales.

- [ ] **Step 1: Test que falla — `/healthz` responde mientras un job corre**

En `tests/test_web_worker.py`, añadir:

```python
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
```

- [ ] **Step 2: Correr y ver fallar**

Run: `uv run pytest tests/test_web_worker.py -k "does_not_block" -v`
Expected: FAIL — `assert ticks["n"] > 10` (queda en 0–2 porque el juez/escritura bloquean el loop).

- [ ] **Step 3: `check_same_thread=False` en `db.connect`**

En `src/dmoj_contest_analyzer/web/db.py`, dentro de `connect`:

```python
    conn = sqlite3.connect(path, isolation_level=None, check_same_thread=False)
```

Añadir al docstring de `connect` una línea:

```
    ``check_same_thread=False``: the connection is handed to ``asyncio.to_thread``
    workers (Excel writing, LLM judge). Python's sqlite3 serializes statements
    across threads, and the owning coroutine always ``await``s the thread, so
    there is no concurrent use.
```

- [ ] **Step 4: Mover el juez y la escritura de Excel fuera del loop**

En `worker.process_one_job`, el bloque final (hoy `:210-225`):

```python
    if row["model_ref"]:
        llm_pool = getattr(app_state, "llm_pool", None) if app_state is not None else None
        try:
            await asyncio.to_thread(
                _run_judge, conn, settings, data, Path(result["source_dir"]),
                row["model_ref"], judge_fn,
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
```

`_run_judge` gana los kwargs y los pasa a `judge_fn`:

```python
def _run_judge(conn, settings, data: ReportData, source_dir: Path, model_ref: str,
               judge_fn, *, llm_pool=None, total_deadline_s=None) -> None:
    ...
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
    ...
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
```

Pasar los kwargs desde `process_one_job` en la llamada `await asyncio.to_thread(_run_judge, ...)`:

```python
            await asyncio.to_thread(
                functools.partial(
                    _run_judge, conn, settings, data, Path(result["source_dir"]),
                    row["model_ref"], judge_fn,
                    llm_pool=llm_pool,
                    total_deadline_s=settings.llm_judge_total_timeout_s,
                ),
            )
```

Import en `worker.py`:

```python
from dmoj_contest_analyzer.llm_run import DeadlineState, run_judge
```

Nota: el test `test_llm_judge_failure_is_visible_in_report` mockea `worker._run_judge` con un `_boom` sin kwargs → `to_thread(functools.partial(_run_judge, ..., llm_pool=..., total_deadline_s=...))` le pasaría kwargs que `_boom` no acepta. **Actualizar ese test**: `def _boom(*a, **k):` (ya usa `*a, **k` — OK, no hay cambio).

`test_worker_does_not_block_event_loop` mockea `_run_judge` con `_slow_judge(*a, **k)` — OK.

- [ ] **Step 5: Correr toda la suite del worker + llm**

Run: `uv run pytest tests/test_web_worker.py tests/test_llm_judge.py -v`
Expected: PASS (incluido `does_not_block`, `test_llm_path_writes_report`, `test_llm_daily_cap_stops_judge`, `test_llm_judge_failure_is_visible_in_report`).

- [ ] **Step 6: Correr la suite web completa (regresión de `check_same_thread`)**

Run: `uv run pytest tests/ -q`
Expected: PASS.

- [ ] **Step 7: `ruff` y commit**

```bash
uv run ruff check src/dmoj_contest_analyzer/web/db.py src/dmoj_contest_analyzer/web/worker.py tests/test_web_worker.py
git add src/dmoj_contest_analyzer/web/db.py src/dmoj_contest_analyzer/web/worker.py tests/test_web_worker.py
git commit -m "fix(web): el worker no bloquea el event loop (juez y Excel en to_thread)"
```

---

### Task 4: Supervisor de N workers con conexión y pool propios

**Files:**
- Modify: `src/dmoj_contest_analyzer/web/worker.py:49-51` (`make_executor`), `:310-324` (`_replace_pool`), `:345-358` (`worker_loop`)
- Modify: `src/dmoj_contest_analyzer/web/app.py:54-61` (wiring del supervisor)
- Modify: `src/dmoj_contest_analyzer/web/jobs.py:120-127` (`reconcile_startup`)
- Test: `tests/test_web_worker.py`

**Interfaces:**
- Consumes: `Settings.max_concurrent_jobs` (Task 2).
- Produces:
  - `make_executor(settings) -> ProcessPoolExecutor` con `max_workers=1` (uno por worker).
  - `async def run_workers(app_state, stop) -> None` — supervisor: crea `settings.max_concurrent_jobs` corrutinas `_worker`, cada una con `db.connect(...)` y `make_executor(...)` propios; al `stop`, cancela y cierra todo.
  - `async def worker_loop(worker_ns, stop) -> None` — un solo worker; `worker_ns` es un `SimpleNamespace(settings, conn, executor, nudge)`. (Se conserva el nombre `worker_loop` para los tests existentes; cambia el objeto que recibe.)
  - `reconcile_startup(conn)` también falla filas `awaiting_upload`.

- [ ] **Step 1: Tests que fallan — 2 workers en paralelo + aislamiento de pool**

En `tests/test_web_worker.py`:

```python
@pytest.mark.asyncio
async def test_two_workers_process_two_jobs_concurrently(conn, settings, monkeypatch):
    settings.max_concurrent_jobs = 2

    started: list[float] = []

    def _slow(*a, **k):
        import time
        started.append(time.monotonic())
        time.sleep(1.0)
        # minimal ReportData-shaped dict expected by process_one_job
        return {
            "source_dir": str(settings.data_dir), "main_rows": [], "jplag_rows": [],
            "n_subs": 0, "n_users": 0, "n_problems": 0,
        }

    monkeypatch.setattr(worker, "_analyze_sync", _slow)
    j1, j2 = _enqueue(conn, settings), _enqueue(conn, settings)

    stop = asyncio.Event()
    state = SimpleNamespace(settings=settings, nudge=asyncio.Event(),
                            db_path=settings.db_path())
    sup = asyncio.create_task(worker.run_workers(state, stop))
    try:
        for _ in range(60):
            done = {jobs.get_job(conn, j)["status"] for j in (j1, j2)}
            if done == {"done"}:
                break
            await asyncio.sleep(0.1)
    finally:
        stop.set()
        state.nudge.set()
        await asyncio.wait_for(sup, timeout=10)

    assert {jobs.get_job(conn, j)["status"] for j in (j1, j2)} == {"done"}
    # Concurrent: the two subprocess starts are < 0.5 s apart, not ~1 s serial.
    assert len(started) == 2 and abs(started[0] - started[1]) < 0.5
```

- [ ] **Step 2: Correr y ver fallar**

Run: `uv run pytest tests/test_web_worker.py -k "two_workers_process" -v`
Expected: FAIL — `AttributeError: module 'dmoj_contest_analyzer.web.worker' has no attribute 'run_workers'`.

- [ ] **Step 3: `make_executor` → 1 proceso**

```python
def make_executor(settings) -> ProcessPoolExecutor:
    # One subprocess per worker coroutine: a poisoned pool only affects its own
    # worker. Concurrency across jobs comes from N worker coroutines, not from
    # this pool's width.
    return ProcessPoolExecutor(max_workers=1)
```

(`settings` se conserva en la firma por compatibilidad con las llamadas existentes.)

- [ ] **Step 4: `worker_loop` recibe un `worker_ns`; añadir `run_workers`**

Reemplazar `worker_loop` y añadir el supervisor:

```python
async def worker_loop(ns, stop: asyncio.Event) -> None:
    """One worker: claim + run jobs from ``ns.conn`` using ``ns.executor``."""
    while not stop.is_set():
        try:
            ran = await process_one_job(
                ns.conn, ns.settings, ns.executor, app_state=ns,
            )
            if not ran:
                await _wait_for_work(stop, ns.nudge, _IDLE_WAIT_S)
        except Exception:
            log.exception("worker loop iteration failed")
            await asyncio.sleep(5)
            continue


async def run_workers(app_state, stop: asyncio.Event) -> None:
    """Supervisor: N worker coroutines, each with its own connection and pool."""
    from types import SimpleNamespace

    from .db import connect

    n = max(1, app_state.settings.max_concurrent_jobs)
    namespaces = []
    for _ in range(n):
        ns = SimpleNamespace(
            settings=app_state.settings,
            conn=connect(app_state.settings.db_path()),
            executor=make_executor(app_state.settings),
            nudge=app_state.nudge,
            llm_pool=getattr(app_state, "llm_pool", None),
        )
        namespaces.append(ns)
    tasks = [asyncio.create_task(worker_loop(ns, stop)) for ns in namespaces]
    try:
        await stop.wait()
    finally:
        for t in tasks:
            t.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        for ns in namespaces:
            ns.executor.shutdown(wait=False, cancel_futures=True)
            ns.conn.close()
```

`_wait_for_work`: quitar el `nudge.clear()` (varios workers comparten el evento). Nueva versión:

```python
async def _wait_for_work(stop: asyncio.Event, nudge: asyncio.Event, timeout: float) -> None:
    waiters = [asyncio.ensure_future(stop.wait()), asyncio.ensure_future(nudge.wait())]
    try:
        await asyncio.wait(waiters, timeout=timeout, return_when=asyncio.FIRST_COMPLETED)
    finally:
        for w in waiters:
            w.cancel()
    # Do not clear ``nudge`` here: it is shared by N workers and one clear would
    # hide the wake-up from the others. A stale-set nudge just means one extra
    # non-blocking poll, which is harmless.
```

Añadir un limpiador del nudge en el supervisor loop para que no quede permanentemente set (opcional pero limpio): tras `await stop.wait()` no hace falta. En su lugar, cada worker limpia el nudge **después de reclamar con éxito** un job (señal consumida):

En `worker_loop`, tras `ran = await process_one_job(...)`:

```python
            if ran:
                app_state_nudge = ns.nudge
                if app_state_nudge.is_set():
                    app_state_nudge.clear()
```

Simplificar: dentro de `worker_loop`:

```python
        try:
            ran = await process_one_job(ns.conn, ns.settings, ns.executor, app_state=ns)
            if ran:
                ns.nudge.clear()
            else:
                await _wait_for_work(stop, ns.nudge, _IDLE_WAIT_S)
```

(Un `clear()` de más sólo cuesta un poll extra a otro worker; aceptable.)

- [ ] **Step 5: `app.py` usa `run_workers`**

En `create_app` → `lifespan` → bloque `if start_worker:`:

```python
            tasks = [
                asyncio.create_task(run_workers(app.state, app.state.stop)),
                asyncio.create_task(cleanup_loop(app.state, app.state.stop)),
            ]
```

Import: `from .worker import cleanup_loop, make_executor, run_workers`.
Quitar `worker_loop` del import de `app.py` (ya no lo usa).
`app.state.executor` (el pool global viejo) **ya no se usa** por los workers, pero `cleanup_loop` no lo toca. Quitar `app.state.executor = make_executor(settings)` y su `shutdown` del `finally` — los pools ahora viven en cada `ns`. `cleanup_loop` no necesita executor.

Revisar `cleanup_loop(app_state, stop)`: usa `app_state.conn` y `app_state.settings` y `app_state.nudge`. Sigue con la conexión global `app.state.conn` — correcto (es un consumidor más).

- [ ] **Step 6: `reconcile_startup` incluye `awaiting_upload`**

En `jobs.reconcile_startup`:

```python
def reconcile_startup(conn: sqlite3.Connection) -> int:
    """Fail every job left mid-flight by a previous process. Returns the count."""
    cur = conn.execute(
        "UPDATE jobs SET status='failed', "
        "error='interrumpido por reinicio', finished_at=? "
        "WHERE status IN ('running', 'awaiting_upload')",
        (utcnow(),),
    )
    return cur.rowcount
```

- [ ] **Step 7: Actualizar tests existentes del worker al nuevo `worker_loop`**

`test_worker_loop_processes_then_stops` y `test_worker_loop_backs_off_on_persistent_failure` pasan un `state = SimpleNamespace(conn=, settings=, executor=, nudge=)`. El nuevo `worker_loop(ns, stop)` espera exactamente esos atributos (`ns.conn`, `ns.settings`, `ns.executor`, `ns.nudge`) → **siguen funcionando sin cambios**. Verificar. Si `test_worker_loop_backs_off...` mockea `process_one_job` como `async def boom(*a, **k)` — el `worker_loop` la llama con `(ns.conn, ns.settings, ns.executor, app_state=ns)` → OK.

`test_worker_loop_backs_off_on_persistent_failure` usa `state = SimpleNamespace(conn=None, settings=settings, executor=None, nudge=...)` — OK con la nueva firma.

- [ ] **Step 8: Correr worker + suite completa**

Run: `uv run pytest tests/test_web_worker.py -v`
Expected: PASS (incluido `two_workers_process`, los `worker_loop` viejos, timeout/broken-pool).

Run: `uv run pytest tests/ -q`
Expected: PASS.

- [ ] **Step 9: `ruff` y commit**

```bash
uv run ruff check src/dmoj_contest_analyzer/web/ tests/test_web_worker.py
git add src/dmoj_contest_analyzer/web/worker.py src/dmoj_contest_analyzer/web/app.py src/dmoj_contest_analyzer/web/jobs.py tests/test_web_worker.py
git commit -m "feat(web): supervisor de N workers con conexión y pool propios"
```

---

### Task 5: `jobs.create_job` acepta estado inicial y cuenta `awaiting_upload`

**Files:**
- Modify: `src/dmoj_contest_analyzer/web/jobs.py:30-67` (`create_job`), `:130-139` (`sweep_stale`)
- Test: `tests/test_web_jobs.py`

**Interfaces:**
- Produces:
  - `create_job(conn, *, job_id, owner, model_ref, run_jplag, jplag_solo_ac, settings, status="queued")` — nuevo kwarg `status`.
  - La comprobación de "activos" cuenta `('awaiting_upload','queued','running')`.
  - `sweep_stale(conn, settings)` además falla filas `awaiting_upload` con `created_at` más viejo que `settings.awaiting_upload_timeout_s` (borrado de dir lo hace `_cleanup_once`, ver Task 8).

- [ ] **Step 1: Tests que fallan**

En `tests/test_web_jobs.py`:

```python
def test_create_job_awaiting_upload_status_and_quota(conn, settings):
    jobs.create_job(conn, job_id="a"*32, owner="alice", model_ref=None,
                    run_jplag=False, jplag_solo_ac=False, settings=settings,
                    status="awaiting_upload")
    assert jobs.get_job(conn, "a"*32)["status"] == "awaiting_upload"

    settings.max_jobs_per_user = 1
    with pytest.raises(jobs.QuotaExceeded):
        jobs.create_job(conn, job_id="b"*32, owner="alice", model_ref=None,
                        run_jplag=False, jplag_solo_ac=False, settings=settings,
                        status="awaiting_upload")


def test_sweep_stale_fails_old_awaiting_upload(conn, settings):
    settings.awaiting_upload_timeout_s = 1
    jobs.create_job(conn, job_id="c"*32, owner="alice", model_ref=None,
                    run_jplag=False, jplag_solo_ac=False, settings=settings,
                    status="awaiting_upload")
    conn.execute("UPDATE jobs SET created_at=? WHERE id=?",
                 ("2000-01-01T00:00:00.000000Z", "c"*32))
    jobs.sweep_stale(conn, settings)
    row = jobs.get_job(conn, "c"*32)
    assert row["status"] == "failed"
    assert "no se subió" in row["error"]
```

- [ ] **Step 2: Correr y ver fallar**

Run: `uv run pytest tests/test_web_jobs.py -k "awaiting_upload" -v`
Expected: FAIL — `create_job() got an unexpected keyword argument 'status'`.

- [ ] **Step 3: Implementar**

`create_job`:

```python
def create_job(
    conn: sqlite3.Connection,
    *,
    job_id: str,
    owner: str,
    model_ref: str | None,
    run_jplag: bool,
    jplag_solo_ac: bool,
    settings: Settings,
    status: str = "queued",
) -> None:
    """Insert a job after checking quotas in one transaction."""
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
            "SELECT COUNT(*) FROM jobs WHERE owner=? AND "
            "status IN ('awaiting_upload', 'queued', 'running')",
            (owner,),
        ).fetchone()[0]
        if active >= settings.max_jobs_per_user:
            raise QuotaExceeded("ya tienes el máximo de trabajos activos")

        conn.execute(
            "INSERT INTO jobs(id, owner, status, created_at, model_ref, run_jplag, "
            "jplag_solo_ac) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (job_id, owner, status, now, model_ref, int(run_jplag), int(jplag_solo_ac)),
        )
    except BaseException:
        conn.execute("ROLLBACK")
        raise
    conn.execute("COMMIT")
```

`sweep_stale`: añadir tras el UPDATE existente:

```python
    conn.execute(
        "UPDATE jobs SET status='failed', error='no se subió el archivo a tiempo', "
        "finished_at=? WHERE status='awaiting_upload' AND created_at < ?",
        (utcnow(), _minus_seconds(utcnow(), settings.awaiting_upload_timeout_s)),
    )
```

- [ ] **Step 4: Correr `tests/test_web_jobs.py` completo**

Run: `uv run pytest tests/test_web_jobs.py -v`
Expected: PASS. (Verificar que los tests que llaman `create_job` sin `status` siguen creando `queued`.)

- [ ] **Step 5: `ruff` y commit**

```bash
uv run ruff check src/dmoj_contest_analyzer/web/jobs.py tests/test_web_jobs.py
git add src/dmoj_contest_analyzer/web/jobs.py tests/test_web_jobs.py
git commit -m "feat(web): create_job acepta estado inicial y la cuota cuenta awaiting_upload"
```

---

### Task 6: `stream_body_to_file` — volcar el cuerpo crudo de un request a disco

**Files:**
- Modify: `src/dmoj_contest_analyzer/web/upload.py:42-73` (junto a `stream_to_file`)
- Test: `tests/test_web_upload.py`

**Interfaces:**
- Produces:
  ```python
  async def stream_body_to_file(request: "starlette.requests.Request",
                                dest: Path, max_bytes: int) -> int
  ```
  Itera `request.stream()` (async iterator de `bytes`), escribe en `dest` en trozos, y al superar `max_bytes` borra el parcial y lanza `UploadRejected(413, ...)`. Devuelve los bytes escritos.

- [ ] **Step 1: Test que falla**

En `tests/test_web_upload.py`:

```python
@pytest.mark.asyncio
async def test_stream_body_to_file_writes_and_caps(tmp_path):
    from dmoj_contest_analyzer.web.upload import UploadRejected, stream_body_to_file

    class _Req:
        def __init__(self, chunks):
            self._chunks = chunks
        async def stream(self):
            for c in self._chunks:
                yield c

    dest = tmp_path / "out.bin"
    n = await stream_body_to_file(_Req([b"ab", b"cd"]), dest, max_bytes=10)
    assert n == 4 and dest.read_bytes() == b"abcd"

    with pytest.raises(UploadRejected) as ei:
        await stream_body_to_file(_Req([b"x" * 6, b"x" * 6]), dest, max_bytes=10)
    assert ei.value.status == 413
    assert not dest.exists()
```

- [ ] **Step 2: Correr y ver fallar**

Run: `uv run pytest tests/test_web_upload.py -k "stream_body_to_file" -v`
Expected: FAIL — `ImportError: cannot import name 'stream_body_to_file'`.

- [ ] **Step 3: Implementar**

En `web/upload.py`, tras `stream_to_file`:

```python
async def stream_body_to_file(request, dest: Path, max_bytes: int) -> int:
    """Stream ``request``'s raw body to ``dest`` in chunks under ``max_bytes``.

    Returns the byte count. On overflow the partial file is unlinked and
    ``UploadRejected(413, ...)`` is raised. Used by the two-step upload's
    ``PUT /jobs/{id}/upload`` (raw body, not multipart).
    """
    dest.parent.mkdir(parents=True, exist_ok=True)
    written = 0
    try:
        with dest.open("wb") as fh:
            async for chunk in request.stream():
                if not chunk:
                    continue
                written += len(chunk)
                if written > max_bytes:
                    raise UploadRejected(
                        413, f"El archivo supera el límite de {max_bytes} bytes."
                    )
                fh.write(chunk)
    except UploadRejected:
        dest.unlink(missing_ok=True)
        raise
    return written
```

- [ ] **Step 4: Correr**

Run: `uv run pytest tests/test_web_upload.py -v`
Expected: PASS.

- [ ] **Step 5: `ruff` y commit**

```bash
uv run ruff check src/dmoj_contest_analyzer/web/upload.py tests/test_web_upload.py
git add src/dmoj_contest_analyzer/web/upload.py tests/test_web_upload.py
git commit -m "feat(web): stream_body_to_file para la subida en 2 pasos"
```

---

### Task 7: Rutas de la subida en 2 pasos

**Files:**
- Modify: `src/dmoj_contest_analyzer/web/routes.py:97-107` (helpers CSRF), `:309-361` (`create_job_route`), `:383-395` (`job_cancel`); añadir `job_upload`
- Test: `tests/test_web_jobs_route.py`

**Interfaces:**
- Consumes: `jobs.create_job(status=)` (Task 5), `upload.stream_body_to_file` (Task 6).
- Produces:
  - `POST /jobs`: valida modelo + flags, `create_job(status="awaiting_upload")`, crea `job_dir` (0o700), `303 → /jobs/{id}`. **Sin** archivo, **sin** `Content-Length` grande.
  - `PUT /jobs/{id}/upload`: owner-only; `409` si `status != awaiting_upload`; CSRF por header `X-CSRF-Token` o campo; `Content-Length` numérico obligatorio (`411` si falta, `413` si excede); `stream_body_to_file` → `input.zip`; `set_status(id,"queued")`; `nudge.set()`; `204`.
  - `_check_csrf_value(request, token: str) -> None` — helper compartido.
  - `job_cancel` acepta cancelar desde `queued` **o** `awaiting_upload`.

- [ ] **Step 1: Tests que fallan**

En `tests/test_web_jobs_route.py` (usa el fixture `client` + `_login` ya presentes):

```python
def test_two_step_upload_happy_path(client, settings):
    _login(client)
    page = client.get("/").text
    csrf = _csrf(page)
    r = client.post("/jobs", data={"csrf": csrf}, follow_redirects=False)
    assert r.status_code == 303
    job_url = r.headers["location"]
    jid = job_url.rsplit("/", 1)[-1]

    from dmoj_contest_analyzer.web import jobs as jobs_mod
    c = connect(settings.db_path())
    assert jobs_mod.get_job(c, jid)["status"] == "awaiting_upload"

    zip_bytes = make_zip(GOOD)
    up = client.put(f"/jobs/{jid}/upload", content=zip_bytes,
                    headers={"X-CSRF-Token": csrf, "Content-Length": str(len(zip_bytes))})
    assert up.status_code == 204
    assert jobs_mod.get_job(c, jid)["status"] == "queued"
    assert (settings.data_dir / jid / "input.zip").read_bytes() == zip_bytes
    c.close()


def test_upload_rejects_wrong_state(client, settings):
    _login(client)
    csrf = _csrf(client.get("/").text)
    jid = client.post("/jobs", data={"csrf": csrf},
                      follow_redirects=False).headers["location"].rsplit("/", 1)[-1]
    zb = make_zip(GOOD)
    hdr = {"X-CSRF-Token": csrf, "Content-Length": str(len(zb))}
    assert client.put(f"/jobs/{jid}/upload", content=zb, headers=hdr).status_code == 204
    # second upload: job is now queued
    assert client.put(f"/jobs/{jid}/upload", content=zb, headers=hdr).status_code == 409


def test_upload_rejects_missing_content_length(client, settings):
    _login(client)
    csrf = _csrf(client.get("/").text)
    jid = client.post("/jobs", data={"csrf": csrf},
                      follow_redirects=False).headers["location"].rsplit("/", 1)[-1]
    # TestClient sets Content-Length automatically; simulate absence via a header
    # the route treats as missing by sending Transfer-Encoding chunked is not
    # feasible here — instead assert the >max branch:
    settings_max = settings.max_upload_mb * 1024 * 1024
    big = b"x" * (settings_max + 1)
    r = client.put(f"/jobs/{jid}/upload", content=big,
                   headers={"X-CSRF-Token": csrf, "Content-Length": str(len(big))})
    assert r.status_code == 413


def test_upload_rejects_foreign_owner(client, settings):
    _login(client)
    csrf = _csrf(client.get("/").text)
    jid = client.post("/jobs", data={"csrf": csrf},
                      follow_redirects=False).headers["location"].rsplit("/", 1)[-1]
    client.post("/logout", data={"csrf": csrf})
    # a fresh unauthenticated client
    r = client.put(f"/jobs/{jid}/upload", content=b"x",
                   headers={"X-CSRF-Token": csrf, "Content-Length": "1"})
    assert r.status_code in (302, 303)  # redirected to /login
```

(Ajustar los asserts de redirección al patrón real de `AuthRequired` → `RedirectResponse("/login", 303)`.)

- [ ] **Step 2: Correr y ver fallar**

Run: `uv run pytest tests/test_web_jobs_route.py -k "two_step or upload_rejects" -v`
Expected: FAIL (405 Method Not Allowed en `PUT .../upload`, o el `POST /jobs` sigue exigiendo archivo).

- [ ] **Step 3: Helper CSRF compartido**

En `routes.py`:

```python
def _check_csrf_value(request: Request, token: str) -> None:
    expected = request.session.get("csrf", "")
    if not expected or not hmac.compare_digest(str(token), expected):
        raise HttpError(403)


async def _check_csrf(request: Request, form) -> None:
    _check_csrf_value(request, str(form.get("csrf", "")))
```

- [ ] **Step 4: `POST /jobs` sin archivo**

Reemplazar `create_job_route`:

```python
@router.post("/jobs")
async def create_job_route(request: Request) -> Response:
    user = require_user(request)
    settings = _settings(request)
    conn = _conn(request)

    form = await request.form()
    await _check_csrf(request, form)

    model_ref = str(form.get("model_ref", "")).strip()
    if model_ref in ("", "none"):
        model_ref = None
    elif not _model_ref_ok(model_ref, _visible_backends(request)):
        raise HttpError(422, "El modelo seleccionado no está disponible.")

    run_jplag = _truthy(form.get("run_jplag"))
    jplag_solo_ac = _truthy(form.get("jplag_solo_ac"))

    job_id = uuid.uuid4().hex
    try:
        jobs.create_job(
            conn, job_id=job_id, owner=user.username, model_ref=model_ref,
            run_jplag=run_jplag, jplag_solo_ac=jplag_solo_ac, settings=settings,
            status="awaiting_upload",
        )
    except jobs.QuotaExceeded as exc:
        raise HttpError(429, exc.reason) from exc

    job_dir = Path(settings.data_dir) / job_id
    job_dir.mkdir(parents=True, exist_ok=False)
    job_dir.chmod(0o700)

    return RedirectResponse(f"/jobs/{job_id}", status_code=303)
```

- [ ] **Step 5: `PUT /jobs/{id}/upload`**

Añadir tras `job_page` (o junto a `job_cancel`):

```python
@router.put("/jobs/{job_id}/upload")
async def job_upload(request: Request, job_id: str) -> Response:
    user = require_user(request)
    settings = _settings(request)
    conn = _conn(request)
    row = _load_owned_job(request, job_id, user.username)

    token = request.headers.get("x-csrf-token", "")
    _check_csrf_value(request, token)

    if row["status"] != "awaiting_upload":
        raise HttpError(409)

    max_bytes = settings.max_upload_mb * 1024 * 1024
    content_length = request.headers.get("content-length")
    if content_length is None or not content_length.isdigit():
        raise HttpError(411, "Falta el encabezado Content-Length.")
    if int(content_length) > max_bytes:
        raise HttpError(413)

    dest = Path(settings.data_dir) / job_id / "input.zip"
    try:
        await stream_body_to_file(request, dest, max_bytes)
    except UploadRejected as exc:
        dest.unlink(missing_ok=True)
        raise HttpError(exc.status, exc.reason) from exc

    jobs.set_status(conn, job_id, "queued")
    request.app.state.nudge.set()
    return Response(status_code=204)
```

Import en `routes.py`: `from .upload import UploadRejected, stream_body_to_file, stream_to_file` (mantener `stream_to_file` si algún otro sitio lo usa; si no, quitarlo).

- [ ] **Step 6: `job_cancel` acepta `awaiting_upload`**

```python
    if row["status"] not in ("queued", "awaiting_upload"):
        raise HttpError(409)
```

- [ ] **Step 7: `HttpError` 411 tiene mensaje ES**

Verificar `_ERROR_ES` — añadir `411: "Falta el encabezado Content-Length."` si no está (hoy se pasa el mensaje explícito, así que opcional).

- [ ] **Step 8: Correr `tests/test_web_jobs_route.py` completo**

Run: `uv run pytest tests/test_web_jobs_route.py -v`
Expected: PASS. Reescribir/ajustar los tests viejos que hacían `POST /jobs` con archivo multipart (ahora es 2 pasos): buscar `client.post("/jobs"` con `files=` y migrarlos al flujo `POST` + `PUT`.

- [ ] **Step 9: `ruff` y commit**

```bash
uv run ruff check src/dmoj_contest_analyzer/web/routes.py tests/test_web_jobs_route.py
git add src/dmoj_contest_analyzer/web/routes.py tests/test_web_jobs_route.py
git commit -m "feat(web): subida en 2 pasos (POST /jobs + PUT /jobs/{id}/upload)"
```

---

### Task 8: Reaper de `awaiting_upload` en `_cleanup_once` + `job.html` estado `awaiting_upload` + `upload.js`

**Files:**
- Modify: `src/dmoj_contest_analyzer/web/worker.py:371-382` (`_cleanup_once`)
- Modify: `src/dmoj_contest_analyzer/web/templates/job.html`
- Create: `src/dmoj_contest_analyzer/web/static/upload.js`
- Modify: `src/dmoj_contest_analyzer/web/static/style.css` (barra `<progress>`, mensajes)
- Test: `tests/test_web_worker.py`, `tests/test_web_jobs_route.py`

**Interfaces:**
- Consumes: `jobs.sweep_stale` (Task 5, ya falla las filas viejas); este task añade el **borrado del directorio** de las filas `awaiting_upload` recién falladas.
- Produces: `job.html` renderiza, para `status == "awaiting_upload"`, un `<input type=file>` + `<progress>` + `<script src="/static/upload.js">` con `data-job-id` y `data-csrf`.

- [ ] **Step 1: Test que falla — el dir de un `awaiting_upload` viejo se borra**

En `tests/test_web_worker.py`:

```python
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
    # retention has not elapsed for finished_at, but the source dir must be gone
    assert not (settings.data_dir / jid).exists()
```

- [ ] **Step 2: Correr y ver fallar**

Run: `uv run pytest tests/test_web_worker.py -k "stale_awaiting_upload" -v`
Expected: FAIL — el directorio sigue existiendo (`sweep_stale` sólo cambia el estado).

- [ ] **Step 3: `_cleanup_once` borra dirs de `awaiting_upload` fallados**

En `worker._cleanup_once`, antes de `jobs.sweep_stale(conn, settings)`:

```python
    stale_uploads = conn.execute(
        "SELECT id FROM jobs WHERE status='awaiting_upload' AND created_at < ?",
        (_minus_seconds(utcnow(), settings.awaiting_upload_timeout_s),),
    ).fetchall()
    for r in stale_uploads:
        shutil.rmtree(settings.data_dir / r["id"], ignore_errors=True)
    jobs.sweep_stale(conn, settings)
```

Import de `_minus_seconds`: está en `jobs.py` como privado. Reutilizar: `from .jobs import _minus_seconds` o replicar el cálculo con `datetime`. **Decisión:** exponer un helper público `db.minus_seconds(now, secs)` no; en su lugar `worker` ya importa `from datetime import datetime, timedelta` y `TIMESTAMP_FORMAT`. Usar:

```python
    upload_cutoff = (
        datetime.strptime(utcnow(), TIMESTAMP_FORMAT)
        - timedelta(seconds=settings.awaiting_upload_timeout_s)
    ).strftime(TIMESTAMP_FORMAT)
    stale_uploads = conn.execute(
        "SELECT id FROM jobs WHERE status='awaiting_upload' AND created_at < ?",
        (upload_cutoff,),
    ).fetchall()
    for r in stale_uploads:
        shutil.rmtree(settings.data_dir / r["id"], ignore_errors=True)
    jobs.sweep_stale(conn, settings)
```

- [ ] **Step 4: `job.html` — rama `awaiting_upload`**

```html
{% extends "base.html" %}
{% block title %}Trabajo {{ job.id }}{% endblock %}
{% block head %}
{% if job.status in ("queued", "running") %}<meta http-equiv="refresh" content="3">{% endif %}
{% if job.status == "awaiting_upload" %}<script src="/static/upload.js" defer></script>{% endif %}
{% endblock %}
{% block content %}
<h1>Trabajo</h1>
<p class="mono">{{ job.id }}</p>
<p>Estado: <strong>{{ job.status }}</strong></p>

{% if job.status == "awaiting_upload" %}
<div id="upload" data-job-id="{{ job.id }}" data-csrf="{{ csrf }}">
  <p>Selecciona el <code>.zip</code> del export para empezar el análisis.</p>
  <input type="file" id="zipfile" accept=".zip">
  <button type="button" id="uploadbtn">Subir</button>
  <progress id="uploadprogress" max="100" value="0" hidden></progress>
  <p id="uploadmsg" class="error" hidden></p>
</div>
{% endif %}

{% if job.progress %}<p>Progreso: {{ job.progress }}</p>{% endif %}
{% if job.error %}<p class="error">{{ job.error }}</p>{% endif %}
{% if job.status == "done" %}
<p><a href="/jobs/{{ job.id }}/report">Descargar reporte (.xlsx)</a></p>
{% endif %}
{% if job.status in ("queued", "awaiting_upload") %}
<form method="post" action="/jobs/{{ job.id }}/cancel">
  <input type="hidden" name="csrf" value="{{ csrf }}">
  <button type="submit">Cancelar</button>
</form>
{% endif %}
{% endblock %}
```

- [ ] **Step 5: `static/upload.js`**

```javascript
// Two-step upload: PUT the raw .zip with a progress bar. External file to
// satisfy CSP `script-src 'self'` (no inline scripts).
(function () {
  "use strict";
  var box = document.getElementById("upload");
  if (!box) return;
  var jobId = box.dataset.jobId;
  var csrf = box.dataset.csrf;
  var input = document.getElementById("zipfile");
  var btn = document.getElementById("uploadbtn");
  var bar = document.getElementById("uploadprogress");
  var msg = document.getElementById("uploadmsg");

  function fail(text) {
    msg.textContent = text;
    msg.hidden = false;
    btn.disabled = false;
    input.disabled = false;
  }

  btn.addEventListener("click", function () {
    var file = input.files && input.files[0];
    if (!file) { fail("Elige un archivo .zip primero."); return; }
    msg.hidden = true;
    btn.disabled = true;
    input.disabled = true;
    bar.hidden = false;

    var xhr = new XMLHttpRequest();
    xhr.open("PUT", "/jobs/" + jobId + "/upload");
    xhr.setRequestHeader("X-CSRF-Token", csrf);
    xhr.upload.addEventListener("progress", function (e) {
      if (e.lengthComputable) bar.value = Math.round((e.loaded / e.total) * 100);
    });
    xhr.addEventListener("load", function () {
      if (xhr.status === 204) {
        window.location.reload();
      } else if (xhr.status === 413) {
        fail("El archivo es demasiado grande.");
      } else if (xhr.status === 409) {
        fail("Este trabajo ya no acepta una subida. Recarga la página.");
      } else {
        fail("La subida falló (código " + xhr.status + "). Intenta de nuevo.");
      }
    });
    xhr.addEventListener("error", function () {
      fail("Error de red durante la subida. Intenta de nuevo.");
    });
    xhr.send(file);
  });
})();
```

- [ ] **Step 6: `style.css` — mínimo para `<progress>` y el bloque**

Añadir al final de `static/style.css`:

```css
#upload { margin: 1rem 0; padding: 1rem; border: 1px solid #ccc; border-radius: 4px; }
#uploadprogress { display: block; width: 100%; margin-top: 0.5rem; }
```

- [ ] **Step 7: Test de render de `job.html` en `awaiting_upload`**

En `tests/test_web_jobs_route.py`:

```python
def test_job_page_awaiting_upload_renders_upload_widget(client, settings):
    _login(client)
    csrf = _csrf(client.get("/").text)
    jid = client.post("/jobs", data={"csrf": csrf},
                      follow_redirects=False).headers["location"].rsplit("/", 1)[-1]
    html = client.get(f"/jobs/{jid}").text
    assert 'id="upload"' in html
    assert 'data-job-id="%s"' % jid in html
    assert "/static/upload.js" in html
```

- [ ] **Step 8: Correr suite web completa**

Run: `uv run pytest tests/ -q`
Expected: PASS.

- [ ] **Step 9: `ruff` y commit**

```bash
uv run ruff check src/dmoj_contest_analyzer/web/ tests/
git add src/dmoj_contest_analyzer/web/worker.py src/dmoj_contest_analyzer/web/templates/job.html src/dmoj_contest_analyzer/web/static/upload.js src/dmoj_contest_analyzer/web/static/style.css tests/
git commit -m "feat(web): reaper de awaiting_upload + widget de subida con barra de progreso"
```

---

### Task 9: Barrido final, docs y verificación end-to-end

**Files:**
- Modify: `README.md` (sección de config web: `MAX_CONCURRENT_JOBS`, `LLM_CONCURRENCY`, `LLM_JUDGE_TOTAL_TIMEOUT_S`, `AWAITING_UPLOAD_TIMEOUT_S`; nota de que la subida es en 2 pasos)
- Modify: `docs/configuracion-web.md`
- Modify: `.env.example` si lista variables

**Interfaces:** ninguna nueva.

- [ ] **Step 1: Actualizar `README.md` y `docs/configuracion-web.md`**

Añadir a la tabla/lista de variables de entorno:

```
| `MAX_CONCURRENT_JOBS` | 2 | Trabajos de análisis en paralelo; el resto en cola. |
| `LLM_CONCURRENCY` | 4 | Tope global de llamadas simultáneas al LLM (1 = secuencial). |
| `LLM_JUDGE_TOTAL_TIMEOUT_S` | 600 | Tiempo total máximo del juez con IA por trabajo. |
| `AWAITING_UPLOAD_TIMEOUT_S` | 3600 | Plazo para subir el `.zip` tras crear el trabajo. |
```

Y un párrafo corto: "La subida se hace en dos pasos: al pulsar *Analizar* se crea el trabajo y la página del trabajo muestra el selector de archivo, que sube el `.zip` con una barra de progreso. Esto evita el timeout de proxies como Cloudflare en subidas lentas."

- [ ] **Step 2: `.env.example`**

Añadir las cuatro variables comentadas con sus defaults.

- [ ] **Step 3: Suite completa + ruff + lock**

Run:
```bash
uv run ruff check .
uv run pytest tests/ -q
```
Expected: todo PASS, ruff limpio.

- [ ] **Step 4: Prueba manual de humo (opcional pero recomendada)**

```bash
uv run uvicorn dmoj_contest_analyzer.web.app:create_app --factory --port 8080
```
- `POST` de un análisis desde la UI → redirige al instante a `/jobs/{id}` en estado `awaiting_upload`.
- Subir un `.zip` → barra de progreso → la página recarga en `queued` → `running` → `done`.
- Mientras un job corre, `curl localhost:8080/healthz` responde `ok` sin demora.

- [ ] **Step 5: Commit**

```bash
git add README.md docs/configuracion-web.md .env.example
git commit -m "docs: variables de concurrencia/LLM y subida en 2 pasos"
```

---

## Self-Review

**Spec coverage:**
- §1 (worker no bloquea) → Task 3.
- §2 (concurrencia con tope, conexión y pool por worker, `reconcile_startup`) → Task 4.
- §3 (cola/paralelismo LLM configurable) → Task 1 + Task 2 + Task 3 (wiring).
- §4 (deadline global del juez) → Task 1 (`total_deadline_s`) + Task 3 (nota parcial).
- §5 (subida en 2 pasos: `POST`/`PUT`, `upload.js`, `stream_body_to_file`, cuota, reaper, `job_cancel`) → Tasks 5, 6, 7, 8.
- §6 (sin cambio de esquema en Spec 1) → respetado; sólo valores nuevos de `status`.
- §7 (tests) → cubiertos en cada task + Task 9 barrido.

**Placeholder scan:** sin "TBD/TODO"; todos los pasos con código real. El único punto blando ("ajustar asserts de redirección al patrón real de `AuthRequired`") es una verificación contra código existente, no un placeholder de implementación.

**Type consistency:** `run_judge(..., executor=, total_deadline_s=, deadline_state=)` y `DeadlineState` definidos en Task 1, consumidos en Task 3. `create_job(..., status=)` definido en Task 5, consumido en Task 7. `stream_body_to_file(request, dest, max_bytes) -> int` definido en Task 6, consumido en Task 7. `worker_loop(ns, stop)` / `run_workers(app_state, stop)` definidos en Task 4, cableados en Task 4 Step 5.

**Riesgo abierto:** `test_upload_rejects_missing_content_length` no puede realmente omitir `Content-Length` con `TestClient`; el test se reorienta a la rama `> max` (413). Se documenta en el propio test.
