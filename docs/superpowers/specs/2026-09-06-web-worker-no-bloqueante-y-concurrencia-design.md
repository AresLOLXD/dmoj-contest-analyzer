# Diseño (Spec 1): worker no bloqueante, concurrencia de jobs con tope, cola LLM y subida en 2 pasos

Fecha: 2026-09-06
Estado: pendiente de revisión del usuario.
Relacionado: [[2026-09-06-web-listado-y-progreso-design]] (Spec 2, se ejecuta después).

## Contexto

La interfaz web de `dmoj-contest-analyzer` corre el worker de análisis como una
`asyncio.Task` **en el mismo event loop que uvicorn** (`web/app.py`, lifespan).
Hoy `worker.process_one_job`:

- procesa **un job a la vez** (`worker_loop` hace `await process_one_job` en serie);
- llama a `_run_judge(...)` **sin `await`**: es código síncrono (peticiones HTTP al
  LLM en un `ThreadPoolExecutor` interno, pero el `.result()` se espera de forma
  bloqueante) que **congela el event loop** mientras dura el juez;
- llama a `write_excel_report(...)` de forma síncrona (openpyxl; segundos en un
  concurso grande);
- crea `mp.Manager()` y usa un `ProcessPoolExecutor` **compartido** dimensionado a
  `max_concurrent_jobs`; si un job envenena el pool (timeout / `BrokenProcessPool`),
  `_replace_pool` lo descarta entero — mataría a los jobs vecinos si hubiera.

Síntomas reportados por el operador:

1. **Al enviar un análisis, la aplicación entera deja de responder** hasta que el
   job termina ("se queda esperando poder devolver el resultado"). Causa: el
   trabajo síncrono anterior bloquea el loop.
2. El `POST /jobs` pasa por el proxy de Cloudflare (límite ~100 s de respuesta de
   origen). Subir un `.zip` grande por un enlace lento supera ese límite → **524**.
3. El juez LLM "tarda mucho" y puede dejar el job `running` sin un límite superior
   claro (sólo hay timeout por llamada, `llm_request_timeout_s=60`).

## Objetivo

Que el worker **nunca** bloquee el event loop, que pueda correr varios jobs en
paralelo hasta un tope configurable, que las llamadas al LLM se encolen con un
tope de concurrencia global configurable, y que la subida del `.zip` no pase por
el request que Cloudflare puede cortar.

## No-objetivos

- Sacar el worker a un proceso separado del de uvicorn (sigue siendo una tarea del
  mismo proceso; sólo deja de bloquear).
- Reintentos automáticos de jobs fallidos.
- Subida resumible / por chunks (un solo `PUT` con barra de progreso basta).
- Cambiar el comportamiento del CLI (`cli.py`, `llm_run.run_judge` sin executor
  externo se comporta igual que hoy).

## Sección 1 — El worker no bloquea el event loop

**Regla:** dentro de una corrutina del worker, lo único que puede correr en el
hilo del event loop son `await`s y operaciones triviales (`sqlite3` de una sola
sentencia). Todo lo demás va a un hilo (`asyncio.to_thread`) o a un proceso.

Cambios en `worker.process_one_job`:

| Trabajo | Hoy | Después |
|---|---|---|
| `_analyze_sync` (validar zip + análisis + JPlag) | `loop.run_in_executor(pool, ...)` ✔ ya no bloquea | igual |
| `_run_judge` (juez LLM) | llamada síncrona en el loop — **bloquea** | `await asyncio.to_thread(_run_judge, ...)` |
| `write_excel_report` | llamada síncrona en el loop — bloquea | `await asyncio.to_thread(write_excel_report, ...)` |
| `mp.Manager()` | creado en el loop (spawnea proceso) | creado dentro de `asyncio.to_thread` o reemplazado (ver §2) |

`_run_judge` recibe la conexión SQLite del worker (ver §2) y se ejecuta en el
hilo de `to_thread`. Como la corrutina hace `await` y no toca esa conexión
mientras el hilo corre, no hay acceso concurrente real; la conexión se abre con
`check_same_thread=False`.

**Verificación (test nuevo, `test_web_worker.py`):** lanzar un job real (con un
`judge_fn` y un `write_excel_report` que duerman ~1 s) y comprobar que
`process_one_job` cede el loop — p. ej. una segunda corrutina que hace
`await asyncio.sleep(0)` en bucle sigue avanzando, o `GET /healthz` vía
`TestClient` responde mientras el job corre.

## Sección 2 — Concurrencia de jobs con tope configurable

`worker_loop` deja de ser un solo bucle y pasa a **supervisor**:

```
async def worker_supervisor(app_state, stop):
    n = app_state.settings.max_concurrent_jobs
    workers = [asyncio.create_task(_worker(app_state, stop, i)) for i in range(n)]
    await stop.wait()
    ... cancelar y await de todos ...
```

Cada `_worker(i)`:

- Abre **su propia** conexión: `conn_i = db.connect(settings.db_path())`
  (`check_same_thread=False`). WAL ya está activo (`PRAGMA journal_mode=WAL`,
  `busy_timeout=5000`): varios lectores + un escritor serializado. Todas las
  escrituras del worker son `UPDATE` de una fila (`set_status`, `set_progress`,
  `set_pid`) → contención despreciable.
- Tiene **su propio** `ProcessPoolExecutor(max_workers=1)`. Un pool envenenado
  (timeout / `BrokenProcessPool`) sólo afecta a *ese* worker; `_replace_pool`
  reemplaza únicamente el pool del worker afectado. Coste: N procesos idle
  (aceptable para N=2–3).
- Bucle: `claim_next_job` → si `None`, espera nudge/stop (`_wait_for_work`) →
  si hay fila, `process_one_job(conn_i, settings, pool_i, ...)`.

`app.state.nudge` es un único `asyncio.Event` compartido por los N workers. Con
varios workers en espera, `_wait_for_work` no debe hacer `nudge.clear()` (uno
limpiaría el evento antes de que los demás despierten). Se cambia a: el
supervisor limpia el nudge una vez por vuelta, o cada worker hace un poll con
timeout corto (`_IDLE_WAIT_S=2`) y trata el nudge sólo como aceleración
best-effort. Se opta por lo segundo (mínimo cambio, ya hay poll con timeout).

`claim_next_job` ya es atómico (`UPDATE ... WHERE id=(SELECT ... LIMIT 1)
RETURNING *`), así que dos workers nunca reclaman el mismo job.

**Conexión compartida de los handlers HTTP:** `app.state.conn` sigue existiendo y
la usan sólo los handlers (lecturas y `create_job`). Los workers ya no la tocan.

**`reconcile_startup`:** además de fallar los `running`, falla los
`awaiting_upload` huérfanos de un proceso anterior.

**Config:**

| Var | Default | Nota |
|---|---|---|
| `max_concurrent_jobs` | `2` (antes 1) | tope de jobs en paralelo; el resto en cola |
| `max_jobs_per_user` | `2` (sin cambio) | cuenta `awaiting_upload` + `queued` + `running` |

## Sección 3 — Cola y paralelismo de llamadas al LLM

Hoy `llm_run.run_judge` crea un `ThreadPoolExecutor(max_workers=4)` **por job**.
Con N jobs en paralelo → hasta 4·N llamadas simultáneas al proveedor → rate limit.

- `web/app.py` crea **un único** `ThreadPoolExecutor(max_workers=settings.llm_concurrency)`
  en `app.state.llm_pool` (lifespan; `shutdown(wait=False)` al cerrar).
- `llm_run.run_judge` gana un parámetro opcional `executor: Executor | None = None`.
  Si se pasa, **usa ese** y no crea ni cierra ninguno; si es `None`, comportamiento
  actual (crea uno con `max_workers`, lo cierra). El CLI no pasa executor → sin
  cambios.
- El worker llama `run_judge(..., executor=app_state.llm_pool)`. Las tareas que
  exceden `llm_concurrency` quedan **encoladas** en el pool (semántica estándar de
  `ThreadPoolExecutor`).
- `run_judge` sigue creando su `httpx.Client` por invocación (un cliente por job
  está bien; los threads del pool compartido lo comparten sólo dentro de esa
  llamada a `run_judge`). Revisar que `httpx.Client` se use thread-safe: sí, un
  `Client` es seguro para uso concurrente entre threads.

**Config:**

| Var | Default | Nota |
|---|---|---|
| `llm_concurrency` | `4` | tope **global** de llamadas LLM simultáneas; `1` = secuencial |

## Sección 4 — Deadline global del juez

`_run_judge` (en el hilo `to_thread`) debe tener un tope superior de tiempo total,
no sólo por llamada.

- `llm_run.run_judge` gana `total_deadline_s: float | None = None`. Implementación:
  tras `submit` de todos los futures, recoger resultados con
  `concurrent.futures.wait(..., timeout=restante)`; los futures no terminados se
  cancelan y su ítem queda con `ai_score=None` ("no evaluado"). El
  `on_call`/tope diario existente se respeta igual.
- El worker pasa `total_deadline_s=settings.llm_judge_total_timeout_s`.
- Si se alcanza el deadline, `data.llm_partial_note` lo indica
  ("Juez con IA detenido: se alcanzó el límite de tiempo total.") y el job termina
  `done` con el Excel de lo que sí se evaluó (comportamiento ya existente para el
  tope diario).

**Config:**

| Var | Default | Nota |
|---|---|---|
| `llm_judge_total_timeout_s` | `600` | tiempo total máximo del juez por job |

## Sección 5 — Subida en 2 pasos

### Flujo

1. `POST /jobs` (formulario **sin archivo**): valida `model_ref` + flags, chequea
   cuota (`jobs.create_job`), inserta la fila con `status='awaiting_upload'`,
   `RedirectResponse(f"/jobs/{id}", 303)`. Responde en milisegundos.
2. `GET /jobs/{id}` con `status='awaiting_upload'`: `job.html` renderiza un
   `<input type=file>` + `<script src="/static/upload.js">`.
3. `upload.js`: `XMLHttpRequest` `PUT /jobs/{id}/upload`, cuerpo = el `File` crudo
   (no multipart), header `X-CSRF-Token` (token leído de un atributo `data-csrf`
   que `job.html` pone en el contenedor de la subida), `xhr.upload.onprogress` →
   barra `<progress>`. Al `200` → `location.reload()` (la página ya mostrará
   `queued`). En error (409/413/5xx) → mensaje y botón de reintento sin recargar.
4. `PUT /jobs/{id}/upload`:
   - `require_user` + `_load_owned_job` (owner-only, regex de id);
   - si `row["status"] != "awaiting_upload"` → `HttpError(409)`;
   - CSRF: aceptar `X-CSRF-Token` **o** campo de formulario (nuevo helper
     `_check_csrf_value(request, token)`);
   - `Content-Length` numérico obligatorio (como hoy en `POST /jobs`); `> max` → 413;
   - `stream_to_file(request.stream(), job_dir/"input.zip", max_bytes)` — adaptar:
     `stream_to_file` hoy espera un objeto con `.read(size)`; `request.stream()`
     es un async iterator. Añadir un pequeño adaptador o una variante
     `stream_body_to_file(request, dest, max_bytes)` en `web/upload.py`;
   - al terminar OK: `jobs.set_status(conn, id, "queued")` + `request.app.state.nudge.set()`.

### `POST /jobs` — cambios

- Ya no exige el archivo. `upload = form.get("archivo")` se elimina; la parte de
  `stream_to_file` y `job_dir.mkdir` se mueve al `PUT`. El `mkdir(0o700)` del
  `job_dir` pasa a hacerse en `create_job_route` **después** del insert, o en el
  `PUT` la primera vez — se hace en `POST` (así el `PUT` sólo escribe dentro de un
  dir que ya existe y es del job).
- El chequeo `Content-Length` de `POST /jobs` se elimina (ya no lleva cuerpo grande).

### Cuota y limpieza

- `jobs.create_job`: la consulta de "activos" incluye `'awaiting_upload'`:
  `status IN ('awaiting_upload','queued','running')`.
- `worker._cleanup_once` / `jobs.sweep_stale`: marca `failed`
  (`error='no se subió el archivo a tiempo'`) las filas `awaiting_upload` con
  `created_at` más viejo que `awaiting_upload_timeout_s`, y borra su `job_dir`.
- `reconcile_startup`: ver §2.

### Estados del job

`awaiting_upload → queued → running → (done | failed)` ; `cancelled` desde
`queued` o `awaiting_upload` (extender `job_cancel` para permitir `awaiting_upload`).

### CSP

`connect-src` no está declarado → hereda `default-src 'self'` → el `PUT` XHR al
mismo origen está permitido. `script-src 'self'` ya permite `upload.js`. Sin
cambios de CSP.

**Config:**

| Var | Default | Nota |
|---|---|---|
| `awaiting_upload_timeout_s` | `3600` | plazo para subir el `.zip` tras crear el job |

## Sección 6 — Esquema y migración

Spec 1 **no** cambia el esquema `jobs` (la columna `progress_at` es del Spec 2).
Sólo se añaden estados nuevos como valores de la columna `status` (texto libre, sin
constraint). Si se quiere una migración defensiva, dejarla para el Spec 2 que ya
abre `_migration_1`.

## Sección 7 — Estrategia de tests

No debe romperse: toda la suite `tests/` actual. Ajustes:

- **`test_web_worker.py`**
  - test de no-bloqueo (§1).
  - N=2 workers procesan 2 jobs en paralelo (dos `claim` concurrentes devuelven
    filas distintas; ambos terminan).
  - pool envenenado en un worker no afecta al otro.
  - `run_judge` recibe el executor compartido; `llm_concurrency=1` serializa.
  - deadline del juez: con `total_deadline_s` corto y un `judge_fn` lento, el job
    termina `done` con nota parcial.
- **`test_web_jobs_route.py` / `test_web_upload.py`**: reescribir al flujo 2 pasos
  (`POST /jobs` → 303 a job `awaiting_upload`; `PUT .../upload` → `queued`);
  `PUT` con estado != `awaiting_upload` → 409; `Content-Length` faltante/grande →
  411/413; CSRF por header y por campo; owner ajeno → 404.
- **`test_web_jobs.py`**: cuota cuenta `awaiting_upload`; reaper de
  `awaiting_upload` viejos.
- **`test_web_config.py`**: `max_concurrent_jobs=2`, `llm_concurrency`,
  `llm_judge_total_timeout_s`, `awaiting_upload_timeout_s`.
- **`test_llm_judge.py` / `test_llm_registry.py`**: `run_judge(executor=...)` usa
  el pool dado y no lo cierra; `run_judge()` sin executor se comporta igual;
  `total_deadline_s` cancela los pendientes.

## Riesgos y decisiones

- **`check_same_thread=False` + varias conexiones:** aceptable con WAL y escrituras
  de una sentencia. Riesgo: `create_job` (en el handler, `app.state.conn`) hace
  `BEGIN IMMEDIATE`; si un worker está escribiendo, espera hasta `busy_timeout`
  (5 s) y reintenta. Las escrituras del worker son sub-milisegundo → no se llega
  a 5 s en la práctica. Documentar.
- **Fork de proceso multihilo:** el `ProcessPoolExecutor` por worker se crea al
  arrancar (antes de que haya carga). Con `max_workers=1` y creación temprana el
  riesgo de deadlock por fork es el mismo que hoy. Si se observa, cambiar el
  `mp_context` a `"spawn"` en `make_executor` (nota, no cambio en v1).
- **Un `httpx.Client` por `run_judge` en el pool compartido:** si dos jobs corren
  el juez a la vez, hay 2 clientes y hasta `llm_concurrency` requests repartidos
  entre ellos por el pool. Correcto.

## Orden de implementación sugerido

1. §3 + §4: `run_judge(executor=, total_deadline_s=)` + `app.state.llm_pool` + config. (aislado, testeable)
2. §1: mover `_run_judge` y `write_excel_report` a `to_thread`; test de no-bloqueo.
3. §2: supervisor + workers con conexión y pool propios; `reconcile_startup`.
4. §5: subida en 2 pasos (rutas, `upload.js`, `stream_body_to_file`, cuota, reaper).
5. Barrido final de la suite + `ruff`.
