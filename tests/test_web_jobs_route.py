import os
import re
import tempfile

import pytest
from fastapi.testclient import TestClient

from dmoj_contest_analyzer.web import auth, jobs
from dmoj_contest_analyzer.web.app import create_app
from dmoj_contest_analyzer.web.db import connect, migrate, utcnow
from tests.web_conftest import make_zip

GOOD = {
    "userA/p1/1_userA_2026-01-01_10-00-00_AC.cpp": b"int main(){}\n",
    "userB/p1/1_userB_2026-01-01_09-00-00_AC.cpp": b"int main(){}\n",
    "userC/p1/1_userC_2026-01-01_08-00-00_AC.cpp": b"int main(){}\n",
}


def _csrf(html: str) -> str:
    return re.search(r'name="csrf" value="([^"]+)"', html).group(1)


@pytest.fixture
def client(settings):
    (settings.data_dir / "backends.toml").write_text("")
    app = create_app(settings, start_worker=False)
    c = connect(settings.db_path())
    migrate(c)
    c.execute(
        "INSERT INTO users(username,password_hash,token_version,created_at) VALUES (?,?,0,?)",
        ("alice", auth.hash_password("pw123456"), utcnow()),
    )
    c.close()
    with TestClient(app, base_url="https://testserver") as tc:
        yield tc


def _login(client, user="alice", pw="pw123456"):
    token = _csrf(client.get("/login").text)
    return client.post(
        "/login",
        data={"username": user, "password": pw, "csrf": token},
        follow_redirects=False,
    )


def test_upload_requires_auth(client):
    r = client.get("/", follow_redirects=False)
    assert r.status_code in (302, 303)
    assert "/login" in r.headers["location"]


def test_post_job_success(client):
    assert _login(client).status_code == 303
    token = _csrf(client.get("/").text)
    files = {"archivo": ("e.zip", make_zip(GOOD), "application/zip")}
    r = client.post(
        "/jobs",
        data={"csrf": token, "run_jplag": "false"},
        files=files,
        follow_redirects=False,
    )
    assert r.status_code == 303
    assert "/jobs/" in r.headers["location"]


def test_security_headers_present(client):
    r = client.get("/login")
    assert r.headers["x-content-type-options"] == "nosniff"
    assert r.headers["x-frame-options"] == "DENY"
    assert "frame-ancestors 'none'" in r.headers["content-security-policy"]


def test_job_id_validation(client):
    _login(client)
    assert client.get("/jobs/not-a-hex-id").status_code == 404


def test_csrf_required_on_post_jobs(client):
    _login(client)
    files = {"archivo": ("e.zip", make_zip(GOOD), "application/zip")}
    r = client.post("/jobs", data={"csrf": "wrong"}, files=files, follow_redirects=False)
    assert r.status_code == 403


def test_other_user_cannot_see_job(client, settings):
    c = connect(settings.db_path())
    c.execute(
        "INSERT INTO users(username,password_hash,token_version,created_at) VALUES (?,?,0,?)",
        ("bob", auth.hash_password("pw123456"), utcnow()),
    )
    bob_job = "b" * 32
    c.execute(
        "INSERT INTO jobs(id,owner,status,created_at) VALUES (?,?,'queued',?)",
        (bob_job, "bob", utcnow()),
    )
    c.close()

    _login(client, "alice", "pw123456")
    r = client.get(f"/jobs/{bob_job}", follow_redirects=False)
    assert r.status_code == 404
    assert bob_job not in r.text or "Error 404" in r.text


def test_uncaught_500_still_has_security_headers(settings, monkeypatch):
    (settings.data_dir / "backends.toml").write_text("")
    app = create_app(settings, start_worker=False)
    c = connect(settings.db_path())
    migrate(c)
    c.execute(
        "INSERT INTO users(username,password_hash,token_version,created_at) VALUES (?,?,0,?)",
        ("alice", auth.hash_password("pw123456"), utcnow()),
    )
    c.close()

    def boom(*a, **k):
        raise RuntimeError("secret internal detail: /data/state.db")

    monkeypatch.setattr(jobs, "get_job", boom)

    with TestClient(app, base_url="https://testserver", raise_server_exceptions=False) as tc:
        _login(tc)
        r = tc.get("/jobs/" + "a" * 32, follow_redirects=False)
    assert r.status_code == 500
    assert r.headers["x-content-type-options"] == "nosniff"
    assert r.headers["x-frame-options"] == "DENY"
    assert "default-src 'self'" in r.headers["content-security-policy"]
    assert "secret internal detail" not in r.text
    assert "Traceback" not in r.text


def test_lifespan_creates_data_tmp_dir(settings):
    tmp = settings.data_dir / "tmp"
    assert not tmp.exists()
    with TestClient(create_app(settings, start_worker=False), base_url="https://testserver"):
        assert tmp.is_dir()


def test_post_job_large_upload_spools_to_disk(client, settings, monkeypatch):
    # A >1 MB multipart part rolls Starlette's SpooledTemporaryFile over to
    # tempfile in $TMPDIR (= DATA_DIR/tmp under the hardened compose). Point
    # TMPDIR there: the lifespan must have created it or POST /jobs raises
    # FileNotFoundError.
    monkeypatch.setattr(tempfile, "tempdir", str(settings.data_dir / "tmp"))
    assert (settings.data_dir / "tmp").is_dir()
    assert _login(client).status_code == 303
    token = _csrf(client.get("/").text)
    entries = dict(GOOD)
    entries["userA/p1/pad.bin"] = os.urandom(2 * 1024 * 1024)  # incompressible
    files = {"archivo": ("e.zip", make_zip(entries), "application/zip")}
    r = client.post(
        "/jobs",
        data={"csrf": token, "run_jplag": "false"},
        files=files,
        follow_redirects=False,
    )
    assert r.status_code == 303
    assert "/jobs/" in r.headers["location"]


def test_healthz_unhealthy_without_jar(client):
    assert client.get("/healthz").status_code == 503


def test_healthz_ok_with_jar(client, settings):
    settings.jplag_jar.write_text("x")
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.text == "ok"
