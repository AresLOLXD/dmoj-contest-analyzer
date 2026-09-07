import re

import pytest
from fastapi.testclient import TestClient

from dmoj_contest_analyzer.web import auth
from dmoj_contest_analyzer.web.app import create_app
from dmoj_contest_analyzer.web.db import connect, migrate, utcnow

XSS = "<script>alert('pwn')</script>"


def _csrf(html: str) -> str:
    return re.search(r'name="csrf" value="([^"]+)"', html).group(1)


@pytest.fixture
def client(settings):
    (settings.data_dir / "backends.toml").write_text("")
    c = connect(settings.db_path())
    migrate(c)
    c.execute(
        "INSERT INTO users(username,password_hash,token_version,created_at) VALUES (?,?,0,?)",
        ("alice", auth.hash_password("pw123456"), utcnow()),
    )
    job_id = "a" * 32
    c.execute(
        "INSERT INTO jobs(id,owner,status,created_at,progress,error) "
        "VALUES (?,?,'failed',?,?,?)",
        (job_id, "alice", utcnow(), f"carpeta {XSS}", f"ruta inválida: {XSS}"),
    )
    c.close()
    app = create_app(settings, start_worker=False)
    with TestClient(app, base_url="https://testserver") as tc:
        token = _csrf(tc.get("/login").text)
        tc.post(
            "/login",
            data={"username": "alice", "password": "pw123456", "csrf": token},
            follow_redirects=False,
        )
        yield tc


def test_job_status_page_escapes_attacker_strings(client):
    r = client.get("/jobs/" + "a" * 32)
    assert r.status_code == 200
    assert XSS not in r.text
    assert "<script>alert" not in r.text
    assert "&lt;script&gt;alert" in r.text


def test_jobs_list_escapes_model_ref(client, settings):
    from dmoj_contest_analyzer.web.db import connect, utcnow

    c = connect(settings.db_path())
    jid = "b" * 32
    c.execute(
        "INSERT INTO jobs(id,owner,status,created_at,model_ref) "
        "VALUES (?,?,?,?,?)",
        (jid, "alice", "created", utcnow(), XSS),
    )
    c.close()

    html = client.get("/jobs").text
    assert XSS not in html
    assert "&lt;script&gt;" in html
