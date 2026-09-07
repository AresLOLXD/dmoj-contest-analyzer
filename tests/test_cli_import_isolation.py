"""The base CLI must import without the optional `web` extra installed.

`analysis.py` / `cli.py` must not pull in FastAPI, Starlette, uvicorn, Jinja2,
pydantic-settings, argon2, python-multipart or itsdangerous. `httpx` is a base
dependency (the LLM judge needs it) so it stays importable.
"""

import builtins
import importlib
import sys

import pytest

_BLOCKED = {
    "fastapi", "starlette", "uvicorn", "jinja2", "pydantic_settings",
    "argon2", "multipart", "itsdangerous",
}


@pytest.fixture
def web_extra_blocked(monkeypatch):
    for name in list(sys.modules):
        if name.split(".")[0] in _BLOCKED or name.startswith("dmoj_contest_analyzer"):
            monkeypatch.delitem(sys.modules, name, raising=False)

    real_import = builtins.__import__

    def guarded(name, *args, **kwargs):
        if name.split(".")[0] in _BLOCKED:
            raise ModuleNotFoundError(f"No module named {name!r} (blocked by test)")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", guarded)
    yield


def test_cli_and_analysis_import_without_web_extra(web_extra_blocked):
    importlib.import_module("dmoj_contest_analyzer.cli")
    importlib.import_module("dmoj_contest_analyzer.analysis")
    importlib.import_module("dmoj_contest_analyzer.llm_run")
