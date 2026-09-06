"""FastAPI application factory: lifespan, middleware and route wiring.

Run with ``uvicorn dmoj_contest_analyzer.web.app:create_app --factory``.
"""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import RedirectResponse

from . import auth, jobs
from .config import Settings, get_settings
from .db import connect, migrate
from .routes import AuthRequired, HttpError, render, router
from .worker import cleanup_loop, make_executor, worker_loop

_HERE = Path(__file__).parent

_SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Content-Security-Policy": (
        "default-src 'self'; script-src 'self'; object-src 'none'; frame-ancestors 'none'"
    ),
}

# Paths exempt from the must-change-password redirect gate.
_GATE_EXEMPT = ("/account/password", "/logout", "/healthz")

_SESSION_MAX_AGE = 43200  # 12 hours


def create_app(settings: Settings | None = None, *, start_worker: bool = True) -> FastAPI:
    settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        conn = connect(settings.db_path())
        migrate(conn)
        jobs.reconcile_startup(conn)
        app.state.settings = settings
        app.state.conn = conn
        app.state.nudge = asyncio.Event()
        tasks: list[asyncio.Task] = []
        if start_worker:
            app.state.executor = make_executor(settings)
            app.state.stop = asyncio.Event()
            tasks = [
                asyncio.create_task(worker_loop(app.state, app.state.stop)),
                asyncio.create_task(cleanup_loop(app.state, app.state.stop)),
            ]
        try:
            yield
        finally:
            if start_worker:
                app.state.stop.set()
                for task in tasks:
                    task.cancel()
                await asyncio.gather(*tasks, return_exceptions=True)
                app.state.executor.shutdown(wait=False, cancel_futures=True)
            conn.close()

    app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)
    app.state.settings = settings

    app.include_router(router)
    app.mount("/static", StaticFiles(directory=_HERE / "static"), name="static")

    @app.middleware("http")
    async def _security_and_gate(request, call_next):
        path = request.url.path
        gated = not (path in _GATE_EXEMPT or path.startswith("/static"))
        if gated:
            sid = request.session.get("sid")
            user = auth.load_session(request.app.state.conn, sid) if sid else None
            if user is not None and user.must_change_password:
                response = RedirectResponse("/account/password", status_code=303)
                response.headers.update(_SECURITY_HEADERS)
                return response
        response = await call_next(request)
        response.headers.update(_SECURITY_HEADERS)
        return response

    # SessionMiddleware is added last so it is the outermost layer and
    # ``request.session`` is populated before ``_security_and_gate`` runs.
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.app_secret_key,
        https_only=True,
        same_site="lax",
        max_age=_SESSION_MAX_AGE,
    )

    @app.exception_handler(AuthRequired)
    async def _auth_required(request, exc):
        return RedirectResponse("/login", status_code=303)

    @app.exception_handler(HttpError)
    async def _http_error(request, exc: HttpError):
        response = render(
            "error.html", request, status_code=exc.status_code,
            code=exc.status_code, message=exc.message,
        )
        response.headers.update(_SECURITY_HEADERS)
        return response

    @app.exception_handler(Exception)
    async def _unhandled(request, exc: Exception):
        # ServerErrorMiddleware wraps outside every user middleware, so an
        # otherwise-uncaught exception would return a header-less 500. Render a
        # generic Spanish page (no internal detail) with the security headers.
        response = render(
            "error.html", request, status_code=500,
            code=500, message="Ocurrió un error interno. Intenta de nuevo más tarde.",
        )
        response.headers.update(_SECURITY_HEADERS)
        return response

    return app
