"""SQLite connection helper and schema migrations for the web job store.

Schema version is tracked with ``PRAGMA user_version`` (not a table): atomic,
no seed row. Timestamps everywhere use the fixed UTC format
``"%Y-%m-%dT%H:%M:%S.%fZ"`` so string comparisons are lexicographic.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

_TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"


def utcnow() -> str:
    """Return the current UTC time in the fixed lexicographically-sortable format."""
    return datetime.now(UTC).strftime(_TIMESTAMP_FORMAT)


def connect(path: Path) -> sqlite3.Connection:
    """Open ``path`` with the pragmas the job store relies on."""
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def _migration_0(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE jobs (
            id             TEXT PRIMARY KEY CHECK (id GLOB '[0-9a-f]*' AND length(id)=32),
            owner          TEXT NOT NULL REFERENCES users(username),
            status         TEXT NOT NULL,
            created_at     TEXT NOT NULL,
            started_at     TEXT,
            finished_at    TEXT,
            model_ref      TEXT,
            run_jplag      INTEGER NOT NULL DEFAULT 1,
            jplag_solo_ac  INTEGER NOT NULL DEFAULT 0,
            jvm_pid        INTEGER,
            progress       TEXT NOT NULL DEFAULT '',
            error          TEXT
        );
        CREATE INDEX idx_jobs_status_created ON jobs(status, created_at);
        CREATE INDEX idx_jobs_owner_created  ON jobs(owner, created_at);

        CREATE TABLE users (
            username             TEXT PRIMARY KEY,
            password_hash        TEXT NOT NULL,
            must_change_password INTEGER NOT NULL DEFAULT 0,
            token_version        INTEGER NOT NULL DEFAULT 0,
            created_at           TEXT NOT NULL,
            disabled             INTEGER NOT NULL DEFAULT 0
        );

        CREATE TABLE sessions (
            id            TEXT PRIMARY KEY,
            username      TEXT NOT NULL REFERENCES users(username),
            token_version INTEGER NOT NULL,
            created_at    TEXT NOT NULL,
            expires_at    TEXT NOT NULL
        );

        CREATE TABLE login_attempts (
            key        TEXT NOT NULL,
            ts         TEXT NOT NULL
        );
        CREATE INDEX idx_login_attempts ON login_attempts(key, ts);

        CREATE TABLE llm_usage (
            day        TEXT PRIMARY KEY,
            calls      INTEGER NOT NULL DEFAULT 0
        );
        """
    )


_MIGRATIONS: list[Callable[[sqlite3.Connection], None]] = [_migration_0]


def migrate(conn: sqlite3.Connection) -> None:
    """Apply pending migrations in order, bumping ``PRAGMA user_version``."""
    version = conn.execute("PRAGMA user_version").fetchone()[0]
    for index, migration in enumerate(_MIGRATIONS[version:], start=version):
        migration(conn)
        conn.execute(f"PRAGMA user_version={index + 1}")
