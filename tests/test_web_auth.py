import pytest

from dmoj_contest_analyzer.web import auth
from dmoj_contest_analyzer.web.db import utcnow


def _add_user(conn, name="bob", pw="secret", disabled=0, must=0):
    conn.execute(
        "INSERT INTO users(username, password_hash, must_change_password, token_version, created_at, disabled) "  # noqa: E501
        "VALUES (?,?,?,0,?,?)",
        (name, auth.hash_password(pw), must, utcnow(), disabled))
    conn.commit()


def test_authenticate_ok_and_wrong(conn):
    _add_user(conn)
    assert auth.authenticate(conn, "bob", "secret").username == "bob"
    assert auth.authenticate(conn, "bob", "nope") is None
    assert auth.authenticate(conn, "ghost", "secret") is None  # no branch leak


def test_authenticate_disabled(conn):
    _add_user(conn, name="dan", disabled=1)
    assert auth.authenticate(conn, "dan", "secret") is None


def test_must_change_password_flag(conn):
    _add_user(conn, name="eve", must=1)
    assert auth.authenticate(conn, "eve", "secret").must_change_password is True


def test_login_throttle(conn, settings):
    settings.login_max_attempts = 3
    for _ in range(3):
        auth.record_login_failure(conn, "1.2.3.4", "bob")
    with pytest.raises(auth.LoginThrottled):
        auth.check_login_throttle(conn, "1.2.3.4", "bob", settings)


def test_login_throttle_by_username_other_ip(conn, settings):
    settings.login_max_attempts = 3
    for _ in range(3):
        auth.record_login_failure(conn, "9.9.9.9", "bob")
    with pytest.raises(auth.LoginThrottled):
        auth.check_login_throttle(conn, "1.1.1.1", "bob", settings)


def test_login_throttle_ok_below_limit(conn, settings):
    settings.login_max_attempts = 3
    auth.record_login_failure(conn, "1.2.3.4", "bob")
    auth.check_login_throttle(conn, "1.2.3.4", "bob", settings)


def test_login_throttle_prunes_old(conn, settings):
    settings.login_max_attempts = 3
    for _ in range(5):
        conn.execute(
            "INSERT INTO login_attempts(key, ts) VALUES (?, '2000-01-01T00:00:00.000000Z')",
            ("ip:1.2.3.4",))
    conn.commit()
    auth.check_login_throttle(conn, "1.2.3.4", "bob", settings)
    assert conn.execute("SELECT COUNT(*) FROM login_attempts").fetchone()[0] == 0


def test_session_roundtrip(conn, settings):
    _add_user(conn)
    sid = auth.create_session(conn, "bob", settings)
    assert len(sid) == 32
    assert auth.load_session(conn, sid).username == "bob"


def test_session_expired(conn, settings):
    _add_user(conn)
    sid = auth.create_session(conn, "bob", settings)
    conn.execute(
        "UPDATE sessions SET expires_at='2000-01-01T00:00:00.000000Z' WHERE id=?", (sid,))
    conn.commit()
    assert auth.load_session(conn, sid) is None


def test_session_unknown(conn):
    assert auth.load_session(conn, "deadbeef") is None


def test_session_revoked_by_token_version(conn, settings):
    _add_user(conn)
    sid = auth.create_session(conn, "bob", settings)
    assert auth.load_session(conn, sid).username == "bob"
    auth.bump_token_version(conn, "bob")
    assert auth.load_session(conn, sid) is None


def test_disabled_user_session_invalid(conn, settings):
    _add_user(conn, name="carl")
    sid = auth.create_session(conn, "carl", settings)
    conn.execute("UPDATE users SET disabled=1 WHERE username='carl'")
    conn.commit()
    assert auth.load_session(conn, sid) is None
