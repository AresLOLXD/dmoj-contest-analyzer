"""Password hashing, server-side sessions and a login throttle.

All timestamps use ``db.utcnow()`` and the fixed
``"%Y-%m-%dT%H:%M:%S.%fZ"`` format so window math stays lexicographic.
"""

from __future__ import annotations

import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta

import argon2
from argon2.exceptions import InvalidHash, VerificationError

from .db import TIMESTAMP_FORMAT, utcnow

_ATTEMPT_WINDOW = timedelta(minutes=15)
_SESSION_TTL = timedelta(hours=12)

_hasher = argon2.PasswordHasher(time_cost=2, memory_cost=65536, parallelism=1)


def hash_password(pw: str) -> str:
    """Return an argon2id hash for ``pw``."""
    return _hasher.hash(pw)


def verify_password(hash_: str, pw: str) -> bool:
    """Return whether ``pw`` matches ``hash_``; never raises."""
    try:
        return _hasher.verify(hash_, pw)
    except (VerificationError, InvalidHash):
        # VerificationError is the base of VerifyMismatchError and other argon2
        # verify failures; InvalidHash (a ValueError) is separate.
        return False


# Precomputed hash used when the user is absent/disabled so that
# ``authenticate`` always runs one verification (no timing/branch leak).
_DUMMY_HASH = hash_password("x")


@dataclass
class User:
    username: str
    must_change_password: bool


class LoginThrottled(Exception):
    """Raised when an IP or username has too many recent failed logins."""


def _shift(ts: str, delta: timedelta) -> str:
    return (datetime.strptime(ts, TIMESTAMP_FORMAT) + delta).strftime(TIMESTAMP_FORMAT)


def authenticate(conn: sqlite3.Connection, username: str, password: str) -> User | None:
    """Return the enabled ``User`` iff credentials match, else ``None``."""
    row = conn.execute(
        "SELECT password_hash, must_change_password, disabled FROM users WHERE username = ?",
        (username,),
    ).fetchone()
    real = row is not None and not row["disabled"]
    ok = verify_password(row["password_hash"] if real else _DUMMY_HASH, password)
    if real and ok:
        return User(username=username, must_change_password=bool(row["must_change_password"]))
    return None


def check_login_throttle(
    conn: sqlite3.Connection, ip: str, username: str, settings
) -> None:
    """Prune stale attempts, then raise ``LoginThrottled`` if over the limit."""
    cutoff = _shift(utcnow(), -_ATTEMPT_WINDOW)
    conn.execute("BEGIN IMMEDIATE")
    try:
        conn.execute("DELETE FROM login_attempts WHERE ts < ?", (cutoff,))
        ip_count = conn.execute(
            "SELECT COUNT(*) FROM login_attempts WHERE key = ?", (f"ip:{ip}",)
        ).fetchone()[0]
        user_count = conn.execute(
            "SELECT COUNT(*) FROM login_attempts WHERE key = ?", (f"user:{username}",)
        ).fetchone()[0]
        conn.execute("COMMIT")
    except Exception:
        conn.execute("ROLLBACK")
        raise
    limit = settings.login_max_attempts
    if ip_count >= limit or user_count >= limit:
        raise LoginThrottled


def record_login_failure(conn: sqlite3.Connection, ip: str, username: str) -> None:
    """Record one failed attempt against both the IP and username keys."""
    ts = utcnow()
    conn.executemany(
        "INSERT INTO login_attempts(key, ts) VALUES (?, ?)",
        [(f"ip:{ip}", ts), (f"user:{username}", ts)],
    )


def create_session(conn: sqlite3.Connection, username: str, settings) -> str:
    """Create a session row for ``username`` and return its id."""
    session_id = uuid.uuid4().hex
    now = utcnow()
    token_version = conn.execute(
        "SELECT token_version FROM users WHERE username = ?", (username,)
    ).fetchone()["token_version"]
    conn.execute(
        "INSERT INTO sessions(id, username, token_version, created_at, expires_at) "
        "VALUES (?, ?, ?, ?, ?)",
        (session_id, username, token_version, now, _shift(now, _SESSION_TTL)),
    )
    return session_id


def load_session(conn: sqlite3.Connection, session_id: str) -> User | None:
    """Return the ``User`` for a valid, unexpired, non-revoked session."""
    row = conn.execute(
        "SELECT u.username, u.must_change_password "
        "FROM sessions s JOIN users u ON u.username = s.username "
        "WHERE s.id = ? AND s.expires_at > ? "
        "AND s.token_version = u.token_version AND u.disabled = 0",
        (session_id, utcnow()),
    ).fetchone()
    if row is None:
        return None
    return User(username=row["username"], must_change_password=bool(row["must_change_password"]))


def bump_token_version(conn: sqlite3.Connection, username: str) -> None:
    """Invalidate every existing session for ``username``."""
    conn.execute(
        "UPDATE users SET token_version = token_version + 1 WHERE username = ?",
        (username,),
    )
