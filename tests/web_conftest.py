"""Shared fixtures for web-layer tests: a tmp-path Settings and a migrated DB."""

import pytest

from dmoj_contest_analyzer.web.config import Settings
from dmoj_contest_analyzer.web.db import connect, migrate


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
