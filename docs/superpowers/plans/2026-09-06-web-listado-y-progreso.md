# Listado de "mis trabajos" y pantalla de progreso — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Cada usuario ve una lista de sus propios trabajos con su estado, y la página de un trabajo en curso transmite que sigue trabajando (tiempo transcurrido, "última señal hace Xs", mensajes de etapa más frecuentes) — sin añadir JavaScript.

**Architecture:** Una ruta `GET /jobs` que lista `jobs WHERE owner=?` con badges y `<meta refresh>`. Una columna nueva `progress_at` (migración `_migration_1`) que `set_progress` sella. La página del job calcula el tiempo transcurrido y la antigüedad de la última señal en el handler y los pasa a la plantilla. `analysis.py` gana llamadas `on_progress` más finas por problema.

**Tech Stack:** Python 3.11+, FastAPI/Starlette, Jinja2 (autoescape), SQLite (`PRAGMA user_version` para migraciones), `pytest`.

**Spec:** `docs/superpowers/specs/2026-09-06-web-listado-y-progreso-design.md`

**Depende de:** el plan `2026-09-06-web-worker-no-bloqueante-y-concurrencia.md` debe estar ya mergeado/aplicado (estados `awaiting_upload` y la subida en 2 pasos ya existen).

## Global Constraints

- Código/nombres/comentarios en **inglés**; UI y errores visibles en **español**.
- `ruff` limpio (`E,F,I,UP,B`, line-length 100).
- Timestamps con `db.utcnow()` / `TIMESTAMP_FORMAT`.
- Migraciones: añadir a `_MIGRATIONS`, nunca editar una migración ya publicada. `PRAGMA user_version` es la fuente de verdad.
- Autoescape Jinja siempre on; nunca `|safe`. Sin scripts inline (CSP `script-src 'self'`).
- Sin JavaScript nuevo en este plan (se mantiene `<meta http-equiv="refresh">`).
- Cada tarea termina en `git commit`, rama `feat/worker-concurrencia-listado` (o la rama de trabajo vigente).

---

### Task 1: Migración `progress_at` y `set_progress` la sella

**Files:**
- Modify: `src/dmoj_contest_analyzer/web/db.py:36-96` (añadir `_migration_1`, extender `_MIGRATIONS`)
- Modify: `src/dmoj_contest_analyzer/web/jobs.py:100-103` (`set_progress`)
- Test: `tests/test_web_jobs.py`

**Interfaces:**
- Produces:
  - Tabla `jobs` gana `progress_at TEXT` (NULL para filas previas).
  - `migrate()` deja `PRAGMA user_version >= 2`.
  - `set_progress(conn, job_id, text)` escribe también `progress_at = utcnow()`.

- [ ] **Step 1: Tests que fallan**

En `tests/test_web_jobs.py`:

```python
def test_migration_1_adds_progress_at(settings):
    from dmoj_contest_analyzer.web.db import connect, migrate
    c = connect(settings.db_path())
    migrate(c)
    cols = {r[1] for r in c.execute("PRAGMA table_info(jobs)").fetchall()}
    assert "progress_at" in cols
    assert c.execute("PRAGMA user_version").fetchone()[0] >= 2
    migrate(c)  # idempotent
    c.close()


def test_set_progress_stamps_progress_at(conn, settings):
    jid = "a" * 32
    jobs.create_job(conn, job_id=jid, owner="alice", model_ref=None,
                    run_jplag=False, jplag_solo_ac=False, settings=settings)
    jobs.set_progress(conn, jid, "parseando envíos")
    row = jobs.get_job(conn, jid)
    assert row["progress"] == "parseando envíos"
    assert row["progress_at"] is not None
```

- [ ] **Step 2: Correr y ver fallar**

Run: `uv run pytest tests/test_web_jobs.py -k "migration_1 or stamps_progress_at" -v`
Expected: FAIL — `progress_at` no está en `PRAGMA table_info`.

- [ ] **Step 3: Añadir `_migration_1`**

En `src/dmoj_contest_analyzer/web/db.py`, tras `_migration_0`:

```python
def _migration_1(conn: sqlite3.Connection) -> None:
    conn.execute("ALTER TABLE jobs ADD COLUMN progress_at TEXT")


_MIGRATIONS: list[Callable[[sqlite3.Connection], None]] = [_migration_0, _migration_1]
```

(Eliminar la línea `_MIGRATIONS = [_migration_0]` anterior.)

- [ ] **Step 4: `set_progress` sella la hora**

```python
def set_progress(conn: sqlite3.Connection, job_id: str, text: str) -> None:
    conn.execute(
        "UPDATE jobs SET progress=?, progress_at=? WHERE id=?",
        (redact(text), utcnow(), job_id),
    )
```

- [ ] **Step 5: Correr `tests/test_web_jobs.py` + regresión de migración**

Run: `uv run pytest tests/test_web_jobs.py -v`
Expected: PASS (incluido `test_migrate_sets_user_version`).

- [ ] **Step 6: `ruff` y commit**

```bash
uv run ruff check src/dmoj_contest_analyzer/web/db.py src/dmoj_contest_analyzer/web/jobs.py tests/test_web_jobs.py
git add src/dmoj_contest_analyzer/web/db.py src/dmoj_contest_analyzer/web/jobs.py tests/test_web_jobs.py
git commit -m "feat(web): columna progress_at (migración 1) y set_progress la sella"
```

---

### Task 2: Ruta `GET /jobs` + plantilla del listado + enlace + badges

**Files:**
- Modify: `src/dmoj_contest_analyzer/web/routes.py` (añadir `jobs_list` **antes** de `job_page`)
- Create: `src/dmoj_contest_analyzer/web/templates/jobs_list.html`
- Modify: `src/dmoj_contest_analyzer/web/templates/base.html` (enlace en `<header>`)
- Modify: `src/dmoj_contest_analyzer/web/static/style.css` (badges)
- Create: `tests/test_web_jobs_list.py`

**Interfaces:**
- Consumes: `require_user`, `render`, `_conn` (existentes).
- Produces: `GET /jobs` → `jobs_list.html` con `jobs` = lista de `sqlite3.Row` (`id, status, created_at, finished_at, model_ref, error`), del usuario, `ORDER BY created_at DESC LIMIT 50`.

- [ ] **Step 1: Tests que fallan**

Crear `tests/test_web_jobs_list.py`:

```python
import re

import pytest
from fastapi.testclient import TestClient

from dmoj_contest_analyzer.web import auth, jobs
from dmoj_contest_analyzer.web.app import create_app
from dmoj_contest_analyzer.web.db import connect, migrate, utcnow


def _csrf(html: str) -> str:
    return re.search(r'name="csrf" value="([^"]+)"', html).group(1)


@pytest.fixture
def client(settings):
    (settings.data_dir / "backends.toml").write_text("")
    app = create_app(settings, start_worker=False)
    c = connect(settings.db_path())
    migrate(c)
    for name in ("alice", "bob"):
        c.execute(
            "INSERT INTO users(username,password_hash,token_version,created_at) "
            "VALUES (?,?,0,?)",
            (name, auth.hash_password("pw123456"), utcnow()),
        )
    c.close()
    with TestClient(app, base_url="https://testserver") as tc:
        yield tc


def _login(client, user="alice", pw="pw123456"):
    token = _csrf(client.get("/login").text)
    client.post("/login", data={"csrf": token, "username": user, "password": pw})


def _mkjob(settings, owner, status):
    import uuid
    c = connect(settings.db_path())
    jid = uuid.uuid4().hex
    jobs.create_job(c, job_id=jid, owner=owner, model_ref=None,
                    run_jplag=False, jplag_solo_ac=False, settings=settings)
    c.execute("UPDATE jobs SET status=? WHERE id=?", (status, jid))
    c.close()
    return jid


def test_jobs_list_requires_login(client):
    r = client.get("/jobs", follow_redirects=False)
    assert r.status_code in (302, 303)
    assert r.headers["location"] == "/login"


def test_jobs_list_shows_only_own_jobs(client, settings):
    mine = _mkjob(settings, "alice", "done")
    theirs = _mkjob(settings, "bob", "done")
    _login(client, "alice")
    html = client.get("/jobs").text
    assert mine in html
    assert theirs not in html


def test_jobs_list_meta_refresh_only_when_active(client, settings):
    _login(client, "alice")
    _mkjob(settings, "alice", "done")
    assert "http-equiv=\"refresh\"" not in client.get("/jobs").text
    _mkjob(settings, "alice", "running")
    assert "http-equiv=\"refresh\"" in client.get("/jobs").text


def test_jobs_list_empty_message(client):
    _login(client, "alice")
    assert "Aún no tienes trabajos" in client.get("/jobs").text
```

Añadir el fixture `settings` vía `tests/web_conftest.py` (ya es un conftest compartido — comprobar que `tests/test_web_jobs_list.py` lo hereda; `web_conftest.py` no es `conftest.py`. Los otros tests hacen `from tests.web_conftest import ...` y el fixture `settings`/`conn` están **en `web_conftest.py`** pero pytest sólo auto-descubre `conftest.py`).

**Comprobar cómo llega `settings` a los tests web hoy:** si `web_conftest.py` se importa como plugin (p. ej. en `conftest.py` raíz con `pytest_plugins = ["tests.web_conftest"]`), heredarlo basta. Si no, añadir en `tests/test_web_jobs_list.py`:

```python
from tests.web_conftest import settings  # noqa: F401  (pytest fixture re-export)
```

(Verificar el mecanismo real mirando `tests/conftest.py` antes de escribir el import.)

- [ ] **Step 2: Correr y ver fallar**

Run: `uv run pytest tests/test_web_jobs_list.py -v`
Expected: FAIL — `GET /jobs` hoy cae en `job_page` (`/jobs/{job_id}` con `job_id=""`) → 404, no la lista.

- [ ] **Step 3: Ruta `jobs_list`**

En `routes.py`, **inmediatamente antes** de `@router.get("/jobs/{job_id}")`:

```python
_ACTIVE_STATUSES = ("awaiting_upload", "queued", "running")


@router.get("/jobs")
async def jobs_list(request: Request) -> Response:
    user = require_user(request)
    rows = _conn(request).execute(
        "SELECT id, status, created_at, finished_at, model_ref, error "
        "FROM jobs WHERE owner=? ORDER BY created_at DESC LIMIT 50",
        (user.username,),
    ).fetchall()
    has_active = any(r["status"] in _ACTIVE_STATUSES for r in rows)
    return render("jobs_list.html", request, jobs=rows, has_active=has_active)
```

(FastAPI hace match de rutas estáticas antes que las paramétricas, así que `/jobs` no colisiona con `/jobs/{job_id}` aunque esté declarada después; se coloca antes por legibilidad.)

- [ ] **Step 4: `templates/jobs_list.html`**

```html
{% extends "base.html" %}
{% block title %}Mis trabajos{% endblock %}
{% block head %}
{% if has_active %}<meta http-equiv="refresh" content="10">{% endif %}
{% endblock %}
{% block content %}
<h1>Mis trabajos</h1>
{% if not jobs %}
<p>Aún no tienes trabajos. <a href="/">Subir un export</a>.</p>
{% else %}
<table class="jobs">
  <thead><tr><th>Estado</th><th>Creado</th><th>Modelo</th><th></th></tr></thead>
  <tbody>
  {% for job in jobs %}
    <tr>
      <td><span class="badge badge-{{ job.status }}">{{ job.status }}</span></td>
      <td class="mono">{{ job.created_at[:19] | replace("T", " ") }}</td>
      <td>{{ job.model_ref or "—" }}</td>
      <td><a href="/jobs/{{ job.id }}">ver</a></td>
    </tr>
  {% endfor %}
  </tbody>
</table>
{% endif %}
{% endblock %}
```

- [ ] **Step 5: Enlace en `base.html`**

Dentro de `{% if user %}` en el `<header>`, antes del form de logout:

```html
    {% if user %}
    <a href="/jobs">Mis trabajos</a>
    <form method="post" action="/logout" class="inline">
```

- [ ] **Step 6: Badges en `style.css`**

Añadir al final:

```css
.badge { display: inline-block; padding: 0.1rem 0.5rem; border-radius: 3px;
         font-size: 0.85em; color: #fff; }
.badge-awaiting_upload { background: #8a6d3b; }
.badge-queued          { background: #777; }
.badge-running         { background: #2f6fbf; }
.badge-done            { background: #2e7d32; }
.badge-failed          { background: #b71c1c; }
.badge-cancelled       { background: #555; }
table.jobs { border-collapse: collapse; width: 100%; }
table.jobs th, table.jobs td { text-align: left; padding: 0.35rem 0.5rem;
                               border-bottom: 1px solid #ddd; }
```

- [ ] **Step 7: Correr listado + regresión de escapado**

Run: `uv run pytest tests/test_web_jobs_list.py tests/test_web_escape.py -v`
Expected: PASS.

- [ ] **Step 8: `ruff` y commit**

```bash
uv run ruff check src/dmoj_contest_analyzer/web/routes.py tests/test_web_jobs_list.py
git add src/dmoj_contest_analyzer/web/routes.py src/dmoj_contest_analyzer/web/templates/jobs_list.html src/dmoj_contest_analyzer/web/templates/base.html src/dmoj_contest_analyzer/web/static/style.css tests/test_web_jobs_list.py
git commit -m "feat(web): listado GET /jobs de los trabajos del usuario con badges"
```

---

### Task 3: Escapado del listado (regresión) y `model_ref`/`error` con `<`

**Files:**
- Modify: `tests/test_web_escape.py`

**Interfaces:** ninguna nueva (verificación de que el autoescape de Jinja cubre el listado).

- [ ] **Step 1: Test que falla (o pasa directo — regresión)**

En `tests/test_web_escape.py`, añadir:

```python
def test_jobs_list_escapes_model_ref(client, settings):
    # Requires the client/login helpers of that module; adapt import if needed.
    import uuid
    from dmoj_contest_analyzer.web.db import connect
    from dmoj_contest_analyzer.web import jobs
    c = connect(settings.db_path())
    jid = uuid.uuid4().hex
    jobs.create_job(c, job_id=jid, owner="alice", model_ref='x"><script>a</script>',
                    run_jplag=False, jplag_solo_ac=False, settings=settings)
    c.close()
    _login(client)
    html = client.get("/jobs").text
    assert "<script>a</script>" not in html
    assert "&lt;script&gt;" in html
```

(Ajustar a los fixtures reales de `test_web_escape.py`; si su fixture `client` no inserta al usuario `alice`, reutilizar el patrón de ese archivo.)

- [ ] **Step 2: Correr**

Run: `uv run pytest tests/test_web_escape.py -v`
Expected: PASS (el autoescape ya cubre esto; el test es una red de seguridad).

- [ ] **Step 3: Commit**

```bash
git add tests/test_web_escape.py
git commit -m "test(web): regresión de escapado en el listado de trabajos"
```

---

### Task 4: Pantalla de progreso — tiempo transcurrido y "última señal"

**Files:**
- Modify: `src/dmoj_contest_analyzer/web/routes.py` (`job_page` + helper `_seconds_between`)
- Modify: `src/dmoj_contest_analyzer/web/templates/job.html`
- Test: `tests/test_web_jobs_route.py`

**Interfaces:**
- Produces:
  - `_seconds_between(a: str | None, b: str | None) -> int | None` en `routes.py` (diferencia en segundos entre dos timestamps `TIMESTAMP_FORMAT`; `None` si falta alguno).
  - `job_page` pasa a la plantilla: `elapsed_s: int | None`, `updated_ago_s: int | None`.

- [ ] **Step 1: Tests que fallan**

En `tests/test_web_jobs_route.py`:

```python
def test_job_page_shows_elapsed_and_last_signal(client, settings):
    _login(client)
    csrf = _csrf(client.get("/").text)
    jid = client.post("/jobs", data={"csrf": csrf},
                      follow_redirects=False).headers["location"].rsplit("/", 1)[-1]
    from dmoj_contest_analyzer.web.db import connect
    c = connect(settings.db_path())
    c.execute(
        "UPDATE jobs SET status='running', started_at=?, progress='timing y estilo', "
        "progress_at=? WHERE id=?",
        ("2000-01-01T00:00:00.000000Z", "2000-01-01T00:00:00.000000Z", jid),
    )
    c.close()
    html = client.get(f"/jobs/{jid}").text
    assert "En curso desde hace" in html
    assert "última señal hace" in html
    assert "pueden tardar varios minutos" in html


def test_seconds_between_handles_none():
    from dmoj_contest_analyzer.web.routes import _seconds_between
    assert _seconds_between(None, "2026-01-01T00:00:00.000000Z") is None
    assert _seconds_between(
        "2026-01-01T00:00:00.000000Z", "2026-01-01T00:00:10.000000Z"
    ) == 10
```

- [ ] **Step 2: Correr y ver fallar**

Run: `uv run pytest tests/test_web_jobs_route.py -k "elapsed_and_last_signal or seconds_between" -v`
Expected: FAIL — `ImportError: cannot import name '_seconds_between'`.

- [ ] **Step 3: Helper + `job_page`**

En `routes.py`:

```python
from datetime import datetime

from .db import TIMESTAMP_FORMAT, utcnow


def _seconds_between(a: str | None, b: str | None) -> int | None:
    if not a or not b:
        return None
    ta = datetime.strptime(a, TIMESTAMP_FORMAT)
    tb = datetime.strptime(b, TIMESTAMP_FORMAT)
    return int(abs((tb - ta).total_seconds()))
```

`job_page`:

```python
@router.get("/jobs/{job_id}")
async def job_page(request: Request, job_id: str) -> Response:
    user = require_user(request)
    row = _load_owned_job(request, job_id, user.username)
    now = utcnow()
    elapsed_s = _seconds_between(row["started_at"] or row["created_at"], now)
    updated_ago_s = _seconds_between(row["progress_at"], now)
    return render("job.html", request, job=row,
                  elapsed_s=elapsed_s, updated_ago_s=updated_ago_s)
```

(Si `TIMESTAMP_FORMAT`/`utcnow` ya están importados en `routes.py`, no duplicar; hoy `routes.py` importa `from .db import utcnow` — añadir `TIMESTAMP_FORMAT` y `datetime`.)

- [ ] **Step 4: `job.html` — bloque de progreso enriquecido**

Reemplazar el bloque entre el estado y `{% if job.error %}`:

```html
<p>Estado: <strong>{{ job.status }}</strong></p>

{% if job.status in ("queued", "running") %}
  {% if elapsed_s is not none %}
  <p>En curso desde hace {{ (elapsed_s // 60) }} min {{ (elapsed_s % 60) }} s.</p>
  {% endif %}
  {% if updated_ago_s is not none %}
  <p>Última señal hace {{ updated_ago_s }} s.</p>
  {% endif %}
  <p class="hint">Los concursos grandes o JPlag pueden tardar varios minutos.
    Esta página se actualiza sola; no la recargues a mano.</p>
{% endif %}

{% if job.progress %}<p>Progreso: {{ job.progress }}</p>{% endif %}
```

Añadir a `style.css`: `.hint { color: #555; font-size: 0.9em; }`

- [ ] **Step 5: Correr suite de rutas**

Run: `uv run pytest tests/test_web_jobs_route.py -v`
Expected: PASS.

- [ ] **Step 6: `ruff` y commit**

```bash
uv run ruff check src/dmoj_contest_analyzer/web/routes.py tests/test_web_jobs_route.py
git add src/dmoj_contest_analyzer/web/routes.py src/dmoj_contest_analyzer/web/templates/job.html src/dmoj_contest_analyzer/web/static/style.css tests/test_web_jobs_route.py
git commit -m "feat(web): pantalla de progreso con tiempo transcurrido y última señal"
```

---

### Task 5: Mensajes de etapa más finos en `analysis.py`

**Files:**
- Modify: `src/dmoj_contest_analyzer/analysis.py:54-112` (bucle de timing y bucle de JPlag)
- Test: `tests/test_analysis.py`

**Interfaces:**
- Consumes: `on_progress: Callable[[str], None]` (parámetro ya existente de `run_analysis`).
- Produces: mensajes adicionales `f"timing y estilo: problema {i}/{n}"` y `f"JPlag: {problema} ({lang})"`. **Sin cambio de firma**; el CLI sólo imprime más líneas.

- [ ] **Step 1: Test que falla**

En `tests/test_analysis.py` (usar las fixtures / helpers de construcción de export ya presentes en ese archivo; el patrón exacto se copia de un test existente que llame a `run_analysis`):

```python
def test_run_analysis_emits_per_problem_progress(tmp_path):
    # Arrange: reuse the existing helper in this file that builds a minimal
    # export directory with >= 1 problem and runs run_analysis. Capture progress.
    msgs: list[str] = []
    # ... build `root` and `out` as the neighbouring tests do ...
    run_analysis(root, out, AnalysisOptions(run_jplag=False), on_progress=msgs.append)
    assert any(m.startswith("timing y estilo: problema ") for m in msgs)
```

(El agente que implemente esto **debe** primero leer `tests/test_analysis.py` y `src/dmoj_contest_analyzer/analysis.py` para copiar el patrón de construcción del export y la firma real de `AnalysisOptions`. El assert clave es el `any(... startswith ...)`.)

- [ ] **Step 2: Correr y ver fallar**

Run: `uv run pytest tests/test_analysis.py -k "per_problem_progress" -v`
Expected: FAIL — ningún mensaje con ese prefijo.

- [ ] **Step 3: Instrumentar `analysis.py`**

En el bucle de timing/estilo de `run_analysis` (hoy alrededor de `on_progress("timing y estilo")`), envolver la iteración por problema:

```python
    problems = sorted(...)  # la colección de problemas ya existente
    for i, problem in enumerate(problems, start=1):
        on_progress(f"timing y estilo: problema {i}/{len(problems)}")
        # ... cuerpo existente ...
```

En el bucle de JPlag, antes de lanzar la invocación por problema:

```python
        on_progress(f"JPlag: {problem} ({lang})")
```

(Sólo añadir llamadas `on_progress`; no reordenar ni cambiar la lógica. Si el timing no está hoy en un bucle explícito por problema sino vectorizado, añadir un único `on_progress(f"timing y estilo: {n} problemas")` y mover el detalle al bucle de escritura de filas — el implementador decide según el código real, manteniendo el prefijo `"timing y estilo: "`.)

- [ ] **Step 4: Correr `tests/test_analysis.py` completo**

Run: `uv run pytest tests/test_analysis.py -v`
Expected: PASS. Verificar que `tests/test_cli_golden.py` (salida estable del CLD) no se rompe — si compara stdout literal, **actualizar el golden** con las líneas nuevas.

Run: `uv run pytest tests/test_cli_golden.py -v`
Expected: PASS (posible regeneración del golden fixture — documentar en el commit).

- [ ] **Step 5: `ruff` y commit**

```bash
uv run ruff check src/dmoj_contest_analyzer/analysis.py tests/test_analysis.py
git add src/dmoj_contest_analyzer/analysis.py tests/test_analysis.py tests/test_cli_golden.py
git commit -m "feat(analysis): mensajes de progreso por problema en timing y JPlag"
```

---

### Task 6: Barrido final y docs

**Files:**
- Modify: `docs/configuracion-web.md`, `README.md` (sección web: mencionar `/jobs` como listado)

- [ ] **Step 1: Documentar el listado**

Añadir a `docs/configuracion-web.md` un párrafo: "La página *Mis trabajos* (`/jobs`, enlace en la cabecera) lista tus últimos 50 trabajos con su estado y un enlace a cada uno. Se refresca sola mientras haya alguno en cola o en curso."

- [ ] **Step 2: Suite completa + ruff**

Run:
```bash
uv run ruff check .
uv run pytest tests/ -q
```
Expected: todo PASS.

- [ ] **Step 3: Prueba manual de humo**

```bash
uv run uvicorn dmoj_contest_analyzer.web.app:create_app --factory --port 8080
```
- Cabecera muestra "Mis trabajos" → la lista aparece con badges.
- Lanzar un análisis, subir el `.zip`, abrir `/jobs/{id}` → se ve "En curso desde hace…", "Última señal hace… s", y el texto de progreso cambia cada pocos segundos.

- [ ] **Step 4: Commit**

```bash
git add docs/configuracion-web.md README.md
git commit -m "docs: página Mis trabajos y mensajes de progreso"
```

---

## Self-Review

**Spec coverage:**
- §1 (migración `progress_at`) → Task 1.
- §2 (`set_progress` sella hora) → Task 1.
- §3 (ruta `/jobs` + plantilla + enlace + badges) → Task 2.
- §4 (pantalla de progreso: `elapsed_s`, `updated_ago_s`, línea de tranquilidad) → Task 4.
- §5 (mensajes de etapa más finos en `analysis.py`) → Task 5.
- §6 (tests: migración, `set_progress`, listado sólo propio, orden/tope, `<meta refresh>` condicional, escapado, progreso, análisis por problema) → Tasks 1–5.

**Placeholder scan:** Task 5 Step 1 deja el arreglo del test dependiente de leer el archivo real — es una instrucción de "copia el patrón vecino", no un placeholder de implementación; el assert concreto está dado. Sin otros "TBD/TODO".

**Type consistency:** `_seconds_between(a, b) -> int | None` definido y consumido en Task 4. `_ACTIVE_STATUSES` en Task 2 coincide con los estados usados en Task 1 del otro plan (`awaiting_upload/queued/running`). `progress_at` (Task 1) consumido por `job_page` (Task 4) y por el test de Task 4.

**Riesgo abierto:** el mecanismo de descubrimiento del fixture `settings` para `tests/test_web_jobs_list.py` (nuevo archivo) depende de cómo `tests/web_conftest.py` se expone hoy — el implementador verifica `tests/conftest.py` antes de escribir el import (Task 2 Step 1 lo dice explícitamente).
