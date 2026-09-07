# Diseño (Spec 2): listado de "mis trabajos" y mejora de la pantalla de progreso

Fecha: 2026-09-06
Estado: pendiente de revisión del usuario.
Relacionado: [[2026-09-06-web-worker-no-bloqueante-y-concurrencia-design]] (Spec 1, se ejecuta antes).

## Contexto

Tras el Spec 1 se pueden encolar y correr varios jobs a la vez, pero en la web:

- **No hay listado.** El único acceso a un job es el enlace `/jobs/{id}` que devuelve
  el `303` de creación. Si el usuario pierde esa URL, el job es invisible.
- La **pantalla de progreso** (`job.html`) usa `<meta http-equiv="refresh" content="3">`
  y muestra `job.progress` (una sola cadena, sobrescrita). El operador reporta que
  "parece que no está haciendo nada": no hay tiempo transcurrido, no se ve cuándo
  fue la última actualización, y `analysis.py` emite pocos mensajes de etapa, así
  que el texto se queda quieto minutos.

## Objetivo

Que cada usuario vea sus propios trabajos y su estado, y que la pantalla de un job
en curso transmita que sigue trabajando, **sin añadir JavaScript** (se mantiene el
`<meta refresh>`).

## No-objetivos

- Vista admin / de todos los usuarios (no existe rol admin).
- Paginación del listado (tope fijo de 50 basta para un jurado).
- SSE / polling con JS / WebSockets.
- Panel global de contadores (descartado en brainstorming).

## Sección 1 — Migración de esquema

`web/db.py`: añadir `_migration_1`:

```sql
ALTER TABLE jobs ADD COLUMN progress_at TEXT;
```

`_MIGRATIONS = [_migration_0, _migration_1]`. `migrate()` ya aplica lo pendiente
según `PRAGMA user_version`.

## Sección 2 — `jobs.set_progress` sella la hora

`web/jobs.py`:

```python
def set_progress(conn, job_id, text):
    conn.execute(
        "UPDATE jobs SET progress=?, progress_at=? WHERE id=?",
        (redact(text), utcnow(), job_id),
    )
```

Sin otros llamadores afectados (`set_progress` sólo se usa desde `worker._drain_*`
y el fallback del juez).

## Sección 3 — Listado `GET /jobs`

`web/routes.py`, ruta nueva **antes** de `/jobs/{job_id}` (o con path fijo; FastAPI
resuelve `/jobs` exacto antes que `/jobs/{job_id}`, pero se coloca junta para
lectura):

```python
@router.get("/jobs")
async def jobs_list(request: Request) -> Response:
    user = require_user(request)
    rows = _conn(request).execute(
        "SELECT id, status, created_at, finished_at, model_ref, error "
        "FROM jobs WHERE owner=? ORDER BY created_at DESC LIMIT 50",
        (user.username,),
    ).fetchall()
    return render("jobs_list.html", request, jobs=rows)
```

Usa el índice existente `idx_jobs_owner_created`.

`web/templates/jobs_list.html` (extiende `base.html`):

- Tabla: estado (badge), creado (hora), modelo (`model_ref` o "—"), enlace "ver".
- `{% block head %}`: `<meta http-equiv="refresh" content="10">` **sólo si**
  `jobs | selectattr('status', 'in', ['awaiting_upload','queued','running']) | list`.
- Si no hay jobs: mensaje "Aún no tienes trabajos" + enlace a `/`.

`base.html`: en `<header>`, con `{% if user %}`, añadir
`<a href="/jobs">Mis trabajos</a>` junto al enlace existente.

`web/static/style.css`: clases `.badge.badge-queued`, `.badge-running`,
`.badge-done`, `.badge-failed`, `.badge-cancelled`, `.badge-awaiting_upload`
(colores planos, sin dependencias).

## Sección 4 — Pantalla de progreso (`job.html`)

Cálculos en el handler `job_page` (no en la plantilla), pasados al contexto:

- `elapsed_s`: `now - started_at` si `started_at`, si no `now - created_at`.
- `updated_ago_s`: `now - progress_at` si `progress_at`.
- Helpers en `routes.py`: `_seconds_between(a, b)` sobre `TIMESTAMP_FORMAT`.

`job.html` para `status in ('queued','running')`:

- Se mantiene `<meta http-equiv="refresh" content="3">`.
- "En curso desde hace **{{ elapsed_humano }}**" (m/s).
- `{% if updated_ago_s is not none %}` "última señal hace {{ updated_ago_s }} s".
- Línea fija: *"Los concursos grandes o JPlag pueden tardar varios minutos.
  Esta página se actualiza sola; no la recargues a mano."*
- `{% if job.progress %}` el texto de progreso como hoy.

Para `awaiting_upload` / `done` / `failed` / `cancelled`: sin cambios respecto al
estado tras Spec 1.

## Sección 5 — Mensajes de etapa más finos en `analysis.py`

`on_progress` hoy emite ~8 mensajes gruesos. Añadir, sin cambiar la firma ni el
comportamiento del CLI (sólo más llamadas `on_progress(...)`):

- En el bucle de timing/estilo: `on_progress(f"timing y estilo: problema {i}/{n}")`.
- Antes de lanzar JPlag por problema: `on_progress(f"JPlag: {problema} ({lang})")`.
- Tras cada resultado de JPlag parseado ya hay un mensaje; mantener.

Objetivo: que en un concurso normal el texto cambie al menos cada pocos segundos.
No se toca la lógica de análisis, sólo se instrumenta.

**Verificación:** `tests/test_analysis.py` — un `on_progress` de captura recibe
mensajes con el prefijo de progreso por problema.

## Sección 6 — Tests

No debe romperse: suite actual + los cambios del Spec 1.

- **`tests/test_web_jobs.py`** (allí vive `test_migrate_sets_user_version`):
  `_migration_1` añade la columna `progress_at`; `migrate()` sigue idempotente;
  `user_version >= 2` tras migrar.
- **`tests/test_web_jobs.py`**: `set_progress` escribe `progress_at`.
- **`tests/test_web_jobs_list.py`** (nuevo):
  - `GET /jobs` sin sesión → redirección a `/login`.
  - sólo muestra jobs del usuario autenticado (crea jobs de dos owners).
  - orden `created_at DESC`, tope 50.
  - `<meta refresh>` presente sólo con un job activo.
- **`tests/test_web_jobs_route.py`**: `job_page` pasa `elapsed_s` / `updated_ago_s`;
  la plantilla no falla con `progress_at` nulo.
- **`tests/test_analysis.py`**: mensajes de etapa por problema.
- **`tests/test_web_escape.py`**: el listado escapa `model_ref` / `error`
  (autoescape ya on; test de regresión con un valor con `<`).

## Riesgos y decisiones

- **`ALTER TABLE ... ADD COLUMN` sin default en SQLite:** las filas viejas quedan
  con `progress_at = NULL`; la plantilla y los cálculos ya lo contemplan.
- **`<meta refresh>` en el listado cada 10 s:** aceptable para un jurado chico;
  no hay coste de conexión persistente.
- **Coste de `analysis.py` instrumentado:** `on_progress` en el web hace un
  `UPDATE` por mensaje (vía `_drain_progress`, ya con throttle de 0.1 s de drenaje).
  Más mensajes = más `UPDATE`s pequeños; despreciable frente al análisis. El CLI
  sólo imprime a stdout.

## Orden de implementación sugerido

1. §1 + §2: migración `progress_at` + `set_progress`.
2. §3: ruta `/jobs` + plantilla + enlace en `base.html` + badges CSS.
3. §4: cálculos en `job_page` + `job.html`.
4. §5: instrumentar `analysis.py`.
5. Barrido de la suite + `ruff`.
