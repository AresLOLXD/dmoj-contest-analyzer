import re

import pytest
from fastapi.testclient import TestClient

from dmoj_contest_analyzer.web.app import create_app
from dmoj_contest_analyzer.web.db import connect, migrate


def _csrf(html: str) -> str:
    return re.search(r'name="csrf" value="([^"]+)"', html).group(1)


@pytest.fixture
def client(settings):
    (settings.data_dir / "backends.toml").write_text("")
    c = connect(settings.db_path())
    migrate(c)
    c.close()
    app = create_app(settings, start_worker=False)
    with TestClient(app, base_url="https://testserver") as tc:
        yield tc


def test_index_redirects_to_setup_when_no_users(client):
    r = client.get("/", follow_redirects=False)
    assert r.status_code in (302, 303)
    assert "/login" in r.headers["location"]
    # /login works, but the real bootstrap path is /setup
    assert client.get("/setup").status_code == 200


def test_setup_writes_token_file(client, settings):
    client.get("/setup")
    token_file = settings.data_dir / "setup_token"
    assert token_file.exists()
    assert oct(token_file.stat().st_mode)[-3:] == "600"


def test_setup_wrong_token_rejected(client):
    csrf = _csrf(client.get("/setup").text)
    r = client.post(
        "/setup",
        data={"token": "nope", "username": "admin", "password": "hunter22",
              "password2": "hunter22", "csrf": csrf},
        follow_redirects=False,
    )
    assert r.status_code == 403


def test_setup_creates_admin_and_then_closes(client, settings):
    csrf = _csrf(client.get("/setup").text)
    real = (settings.data_dir / "setup_token").read_text()
    r = client.post(
        "/setup",
        data={"token": real, "username": "admin", "password": "hunter22",
              "password2": "hunter22", "csrf": csrf},
        follow_redirects=False,
    )
    assert r.status_code == 303
    assert r.headers["location"] == "/login"

    c = connect(settings.db_path())
    row = c.execute("SELECT must_change_password FROM users WHERE username='admin'").fetchone()
    c.close()
    assert row["must_change_password"] == 1

    # Second attempt: users no longer empty -> 404 for both verbs.
    assert client.get("/setup").status_code == 404
    r2 = client.post(
        "/setup",
        data={"token": real, "username": "mallory", "password": "hunter22",
              "password2": "hunter22", "csrf": csrf},
        follow_redirects=False,
    )
    assert r2.status_code == 404


def test_must_change_password_gate(client, settings):
    csrf = _csrf(client.get("/setup").text)
    real = (settings.data_dir / "setup_token").read_text()
    client.post(
        "/setup",
        data={"token": real, "username": "admin", "password": "hunter22",
              "password2": "hunter22", "csrf": csrf},
        follow_redirects=False,
    )
    login_csrf = _csrf(client.get("/login").text)
    client.post(
        "/login",
        data={"username": "admin", "password": "hunter22", "csrf": login_csrf},
        follow_redirects=False,
    )
    r = client.get("/", follow_redirects=False)
    assert r.status_code == 303
    assert r.headers["location"] == "/account/password"
