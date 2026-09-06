"""Shared fixtures for web-layer tests: a tmp-path Settings and a migrated DB."""

import io
import zipfile

import pytest

from dmoj_contest_analyzer.web.config import Settings
from dmoj_contest_analyzer.web.db import connect, migrate


def make_zip(entries: dict[str, bytes]) -> bytes:
    """Build a ZIP_DEFLATED archive from a name -> bytes mapping."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, data in entries.items():
            zf.writestr(name, data)
    return buf.getvalue()


def zip_bomb(ratio_target: int = 500) -> bytes:
    """A single highly-compressible entry whose real output dwarfs its packed size."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(
            "userA/p1/1_userA_2026-01-01_10-00-00_AC.cpp",
            b"0" * (ratio_target * 4096),
        )
    return buf.getvalue()


@pytest.fixture
def settings(tmp_path):
    return Settings(
        app_secret_key="test",
        data_dir=tmp_path,
        backends_config=tmp_path / "backends.toml",
        jplag_jar=tmp_path / "jplag.jar",
    )


@pytest.fixture
def conn(settings):
    c = connect(settings.db_path())
    migrate(c)
    c.execute(
        "INSERT INTO users(username, password_hash, token_version, created_at) "
        "VALUES ('alice', 'x', 0, '2026-01-01T00:00:00.000000Z')"
    )
    c.commit()
    yield c
    c.close()
