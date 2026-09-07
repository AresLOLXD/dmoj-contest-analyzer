"""HTTP routes for the web UI.

Every HTML response is rendered through a Jinja2 environment with autoescape on
(never ``|safe``). Every state-changing POST validates a per-session CSRF token.
Every ``/jobs/*`` route enforces owner-only access.
"""

from __future__ import annotations

import hmac
import logging
import os
import re
import secrets
import sqlite3
import uuid
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import (
    FileResponse,
    HTMLResponse,
    JSONResponse,
    PlainTextResponse,
    RedirectResponse,
    Response,
)
from jinja2 import Environment, FileSystemLoader, select_autoescape

from dmoj_contest_analyzer import llm

from . import auth, jobs
from .db import utcnow
from .upload import UploadRejected, stream_body_to_file

log = logging.getLogger(__name__)

_HERE = Path(__file__).parent
_JOB_ID_RE = re.compile(r"^[0-9a-f]{32}$")
_XLSX_MEDIA = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

_env = Environment(
    loader=FileSystemLoader(_HERE / "templates"),
    autoescape=select_autoescape(default=True, default_for_string=True),
)

_ERROR_ES = {
    403: "Solicitud rechazada: token de seguridad inválido o faltante.",
    404: "No se encontró lo que buscas.",
    409: "El trabajo ya no puede modificarse en su estado actual.",
    413: "El archivo subido es demasiado grande.",
    422: "La solicitud no es válida.",
    429: "Alcanzaste un límite de uso. Intenta de nuevo más tarde.",
    503: "Servicio no disponible en este momento.",
}

router = APIRouter()


class AuthRequired(Exception):
    """Raised by ``require_user`` when there is no valid session."""


class HttpError(Exception):
    """A rendered HTML error page with a status code."""

    def __init__(self, status_code: int, message: str | None = None) -> None:
        super().__init__(message or "")
        self.status_code = status_code
        self.message = message or _ERROR_ES.get(status_code, "Ocurrió un error.")


def render(name: str, request: Request, *, status_code: int = 200, **ctx: object) -> HTMLResponse:
    ctx.setdefault("csrf", request.session.get("csrf", ""))
    ctx.setdefault("user", getattr(request.state, "user", None))
    html = _env.get_template(name).render(**ctx)
    return HTMLResponse(html, status_code=status_code)


def _conn(request: Request) -> sqlite3.Connection:
    return request.app.state.conn


def _settings(request: Request):
    return request.app.state.settings


def require_user(request: Request) -> auth.User:
    sid = request.session.get("sid")
    user = auth.load_session(_conn(request), sid) if sid else None
    if user is None:
        raise AuthRequired
    request.state.user = user
    return user


def _check_csrf_value(request: Request, token: str) -> None:
    expected = request.session.get("csrf", "")
    if not expected or not hmac.compare_digest(str(token), expected):
        raise HttpError(403)


async def _check_csrf(request: Request, form) -> None:
    _check_csrf_value(request, str(form.get("csrf", "")))


def _ensure_csrf(request: Request) -> None:
    if not request.session.get("csrf"):
        request.session["csrf"] = secrets.token_urlsafe(32)


def _visible_backends(request):
    return llm.load_backends(_settings(request).backends_config)


# --------------------------------------------------------------------------- #
# Health
# --------------------------------------------------------------------------- #
@router.get("/healthz")
async def healthz(request: Request) -> Response:
    settings = _settings(request)
    try:
        # Reuse the app's live connection — a separate mode=ro open of a WAL
        # database is fragile (needs -shm access). This proves the real
        # connection is alive, which is what matters.
        request.app.state.conn.execute("SELECT 1").fetchone()
        if not Path(settings.jplag_jar).exists():
            raise RuntimeError(f"jplag jar missing at {settings.jplag_jar}")
    except Exception:
        log.exception("healthz check failed")
        return PlainTextResponse("unhealthy", status_code=503)
    return PlainTextResponse("ok")


# --------------------------------------------------------------------------- #
# One-time setup
# --------------------------------------------------------------------------- #
def _users_empty(conn: sqlite3.Connection) -> bool:
    return conn.execute("SELECT 1 FROM users LIMIT 1").fetchone() is None


def _setup_token_path(request) -> Path:
    return Path(_settings(request).data_dir) / "setup_token"


@router.get("/setup")
async def setup_form(request: Request) -> Response:
    conn = _conn(request)
    if not _users_empty(conn):
        raise HttpError(404)
    token_path = _setup_token_path(request)
    if not token_path.exists():
        token = secrets.token_urlsafe(32)
        token_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            # Atomic exclusive create so the token is never briefly world-readable.
            fd = os.open(token_path, os.O_CREAT | os.O_WRONLY | os.O_EXCL, 0o600)
            try:
                os.write(fd, token.encode())
            finally:
                os.close(fd)
            print(
                f"[setup] modo de configuración inicial activo. Token: {token}",
                flush=True,
            )
        except FileExistsError:
            pass  # a concurrent GET already created it; reuse that token
    _ensure_csrf(request)
    return render("setup.html", request)


@router.post("/setup")
async def setup_submit(request: Request) -> Response:
    conn = _conn(request)
    if not _users_empty(conn):
        raise HttpError(404)
    form = await request.form()
    await _check_csrf(request, form)
    token_path = _setup_token_path(request)
    real = token_path.read_text() if token_path.exists() else ""
    if not real or not hmac.compare_digest(str(form.get("token", "")), real):
        raise HttpError(403)
    username = str(form.get("username", "")).strip()
    password = str(form.get("password", ""))
    password2 = str(form.get("password2", ""))
    if not username or len(password) < 8 or password != password2:
        _ensure_csrf(request)
        return render(
            "setup.html", request, status_code=422,
            error="Revisa el usuario y que ambas contraseñas coincidan (mínimo 8 caracteres).",
        )
    conn.execute("BEGIN IMMEDIATE")
    try:
        cur = conn.execute(
            "INSERT INTO users(username, password_hash, must_change_password, "
            "token_version, created_at) "
            "SELECT ?, ?, 1, 0, ? WHERE NOT EXISTS (SELECT 1 FROM users)",
            (username, auth.hash_password(password), _now()),
        )
        conn.execute("COMMIT")
    except BaseException:
        conn.execute("ROLLBACK")
        raise
    if cur.rowcount != 1:
        raise HttpError(403)
    token_path.unlink(missing_ok=True)
    return RedirectResponse("/login", status_code=303)


# --------------------------------------------------------------------------- #
# Auth
# --------------------------------------------------------------------------- #
@router.get("/login")
async def login_form(request: Request) -> Response:
    _ensure_csrf(request)
    return render("login.html", request)


@router.post("/login")
async def login_submit(request: Request) -> Response:
    conn = _conn(request)
    form = await request.form()
    await _check_csrf(request, form)
    username = str(form.get("username", "")).strip()
    password = str(form.get("password", ""))
    ip = request.client.host if request.client else "unknown"
    try:
        auth.check_login_throttle(conn, ip, username, _settings(request))
    except auth.LoginThrottled as exc:
        raise HttpError(
            429, "Demasiados intentos de inicio de sesión. Espera unos minutos."
        ) from exc
    user = auth.authenticate(conn, username, password)
    if user is None:
        auth.record_login_failure(conn, ip, username)
        return render(
            "login.html", request, status_code=401,
            error="Usuario o contraseña incorrectos.",
        )
    sid = auth.create_session(conn, user.username, _settings(request))
    request.session.clear()
    request.session["sid"] = sid
    request.session["csrf"] = secrets.token_urlsafe(32)
    return RedirectResponse("/", status_code=303)


@router.post("/logout")
async def logout(request: Request) -> Response:
    conn = _conn(request)
    await _check_csrf(request, await request.form())
    sid = request.session.get("sid")
    user = auth.load_session(conn, sid) if sid else None
    if user is not None:
        auth.bump_token_version(conn, user.username)
    request.session.clear()
    return RedirectResponse("/login", status_code=303)


# --------------------------------------------------------------------------- #
# Password change (gate target)
# --------------------------------------------------------------------------- #
@router.get("/account/password")
async def password_form(request: Request) -> Response:
    require_user(request)
    return render("account_password.html", request)


@router.post("/account/password")
async def password_submit(request: Request) -> Response:
    user = require_user(request)
    conn = _conn(request)
    form = await request.form()
    await _check_csrf(request, form)
    old = str(form.get("old_password", ""))
    new = str(form.get("new_password", ""))
    new2 = str(form.get("new_password2", ""))
    if len(new) < 8 or new != new2 or auth.authenticate(conn, user.username, old) is None:
        return render(
            "account_password.html", request, status_code=422,
            error="Verifica tu contraseña actual y que la nueva (mínimo 8) coincida.",
        )
    conn.execute(
        "UPDATE users SET password_hash = ?, must_change_password = 0 WHERE username = ?",
        (auth.hash_password(new), user.username),
    )
    auth.bump_token_version(conn, user.username)
    sid = auth.create_session(conn, user.username, _settings(request))
    request.session.clear()
    request.session["sid"] = sid
    request.session["csrf"] = secrets.token_urlsafe(32)
    return RedirectResponse("/", status_code=303)


# --------------------------------------------------------------------------- #
# Upload + models
# --------------------------------------------------------------------------- #
@router.get("/")
async def index(request: Request) -> Response:
    require_user(request)
    return render("upload.html", request)


@router.get("/api/models")
async def api_models(request: Request) -> Response:
    require_user(request)
    backends = _visible_backends(request)
    return JSONResponse(
        {"backends": [{"id": b.id, "label": b.label, "models": list(b.models)} for b in backends]}
    )


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


@router.put("/jobs/{job_id}/upload")
async def job_upload(request: Request, job_id: str) -> Response:
    user = require_user(request)
    settings = _settings(request)
    conn = _conn(request)
    row = _load_owned_job(request, job_id, user.username)

    token = request.headers.get("x-csrf-token")
    if token is None:
        form = await request.form()
        token = str(form.get("csrf", ""))
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


@router.get("/jobs/{job_id}")
async def job_page(request: Request, job_id: str) -> Response:
    user = require_user(request)
    row = _load_owned_job(request, job_id, user.username)
    return render("job.html", request, job=row)


@router.get("/jobs/{job_id}/report")
async def job_report(request: Request, job_id: str) -> Response:
    user = require_user(request)
    row = _load_owned_job(request, job_id, user.username)
    if row["status"] != "done":
        raise HttpError(404)
    path = Path(_settings(request).data_dir) / job_id / "reporte.xlsx"
    if not path.exists():
        raise HttpError(404)
    return FileResponse(path, filename="reporte.xlsx", media_type=_XLSX_MEDIA)


@router.post("/jobs/{job_id}/cancel")
async def job_cancel(request: Request, job_id: str) -> Response:
    user = require_user(request)
    conn = _conn(request)
    row = _load_owned_job(request, job_id, user.username)
    form = await request.form()
    await _check_csrf(request, form)
    if row["status"] not in ("queued", "awaiting_upload"):
        raise HttpError(409)
    jobs.set_status(conn, job_id, "cancelled", finished=True)
    # Drop the participant source immediately; the row is reaped later by retention.
    _rmtree(Path(_settings(request).data_dir) / job_id)
    return RedirectResponse(f"/jobs/{job_id}", status_code=303)


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _now() -> str:
    return utcnow()


def _truthy(value) -> bool:
    return str(value).strip().lower() in ("true", "on", "1", "yes")


def _model_ref_ok(model_ref: str, backends) -> bool:
    if not llm.MODEL_REF_RE.match(model_ref):
        return False
    try:
        llm.resolve(model_ref, backends)
    except ValueError:
        return False
    return True


def _load_owned_job(request: Request, job_id: str, owner: str) -> sqlite3.Row:
    if not _JOB_ID_RE.match(job_id):
        raise HttpError(404)
    row = jobs.get_job(_conn(request), job_id, owner=owner)
    if row is None:
        raise HttpError(404)
    return row


def _rmtree(path: Path) -> None:
    import shutil

    shutil.rmtree(path, ignore_errors=True)


__all__ = ["router", "AuthRequired", "HttpError", "render", "require_user"]
