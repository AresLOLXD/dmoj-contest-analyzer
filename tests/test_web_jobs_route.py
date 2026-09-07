import os
import re

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


def _create_job(client, token):
    r = client.post(
        "/jobs", data={"csrf": token, "run_jplag": "false"}, follow_redirects=False
    )
    assert r.status_code == 303
    return r.headers["location"].rsplit("/", 1)[-1]


def test_post_job_success(client, settings):
    assert _login(client).status_code == 303
    token = _csrf(client.get("/").text)
    jid = _create_job(client, token)

    c = connect(settings.db_path())
    assert jobs.get_job(c, jid)["status"] == "awaiting_upload"
    zip_bytes = make_zip(GOOD)
    up = client.put(
        f"/jobs/{jid}/upload",
        content=zip_bytes,
        headers={"X-CSRF-Token": token, "Content-Length": str(len(zip_bytes))},
    )
    assert up.status_code == 204
    assert jobs.get_job(c, jid)["status"] == "queued"
    assert (settings.data_dir / jid / "input.zip").read_bytes() == zip_bytes
    c.close()


def test_index_form_has_no_file_input(client):
    """C1: the `/` form posts options only; the file picker lives on the job page."""
    _login(client)
    html = client.get("/").text
    assert 'type="file"' not in html
    assert "enctype=" not in html


def test_post_job_rejects_oversize_options_form(client):
    """C2: a body above the small options cap is rejected before form parsing."""
    _login(client)
    token = _csrf(client.get("/").text)
    r = client.post(
        "/jobs",
        data={"csrf": token, "junk": "x" * (17 * 1024)},
        follow_redirects=False,
    )
    assert r.status_code == 413


def test_security_headers_present(client):
    r = client.get("/login")
    assert r.headers["x-content-type-options"] == "nosniff"
    assert r.headers["x-frame-options"] == "DENY"
    assert "frame-ancestors 'none'" in r.headers["content-security-policy"]


def test_upload_rejects_oversize(client, settings):
    """A Content-Length above the cap is rejected with 413 before streaming."""
    assert _login(client).status_code == 303
    token = _csrf(client.get("/").text)
    jid = _create_job(client, token)
    big = b"x" * (settings.max_upload_mb * 1024 * 1024 + 1)
    r = client.put(
        f"/jobs/{jid}/upload",
        content=big,
        headers={"X-CSRF-Token": token, "Content-Length": str(len(big))},
    )
    assert r.status_code == 413


def test_upload_rejects_wrong_state(client, settings):
    _login(client)
    token = _csrf(client.get("/").text)
    jid = _create_job(client, token)
    zb = make_zip(GOOD)
    hdr = {"X-CSRF-Token": token, "Content-Length": str(len(zb))}
    assert client.put(f"/jobs/{jid}/upload", content=zb, headers=hdr).status_code == 204
    assert client.put(f"/jobs/{jid}/upload", content=zb, headers=hdr).status_code == 409


def test_upload_rejects_foreign_owner(client, settings):
    _login(client)
    token = _csrf(client.get("/").text)
    jid = _create_job(client, token)
    client.post("/logout", data={"csrf": token})
    r = client.put(
        f"/jobs/{jid}/upload",
        content=b"x",
        headers={"X-CSRF-Token": token, "Content-Length": "1"},
        follow_redirects=False,
    )
    assert r.status_code == 303
    assert r.headers["location"] == "/login"


def test_job_id_validation(client):
    _login(client)
    assert client.get("/jobs/not-a-hex-id").status_code == 404


def test_csrf_required_on_post_jobs(client):
    _login(client)
    r = client.post("/jobs", data={"csrf": "wrong"}, follow_redirects=False)
    assert r.status_code == 403


def test_csrf_required_on_upload(client):
    _login(client)
    token = _csrf(client.get("/").text)
    jid = _create_job(client, token)
    zb = make_zip(GOOD)
    r = client.put(
        f"/jobs/{jid}/upload",
        content=zb,
        headers={"X-CSRF-Token": "wrong", "Content-Length": str(len(zb))},
    )
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


def test_upload_large_body_streams_to_disk(client, settings):
    # A multi-MB raw body on PUT .../upload is streamed straight to input.zip
    # (no multipart spooling). Under the cap it succeeds.
    assert _login(client).status_code == 303
    token = _csrf(client.get("/").text)
    jid = _create_job(client, token)
    entries = dict(GOOD)
    entries["userA/p1/pad.bin"] = os.urandom(2 * 1024 * 1024)  # incompressible
    zip_bytes = make_zip(entries)
    r = client.put(
        f"/jobs/{jid}/upload",
        content=zip_bytes,
        headers={"X-CSRF-Token": token, "Content-Length": str(len(zip_bytes))},
    )
    assert r.status_code == 204
    assert (settings.data_dir / jid / "input.zip").read_bytes() == zip_bytes


def test_upload_over_cap_streams_413(client, settings):
    assert _login(client).status_code == 303
    token = _csrf(client.get("/").text)
    jid = _create_job(client, token)
    settings.max_upload_mb = 1
    body = os.urandom(2 * 1024 * 1024)
    r = client.put(
        f"/jobs/{jid}/upload",
        content=body,
        headers={"X-CSRF-Token": token, "Content-Length": str(len(body))},
    )
    assert r.status_code == 413


def test_cancel_awaiting_upload_job(client, settings):
    _login(client)
    token = _csrf(client.get("/").text)
    jid = _create_job(client, token)
    r = client.post(
        f"/jobs/{jid}/cancel", data={"csrf": token}, follow_redirects=False
    )
    assert r.status_code == 303
    c = connect(settings.db_path())
    assert jobs.get_job(c, jid)["status"] == "cancelled"
    c.close()


def test_job_page_awaiting_upload_renders_upload_widget(client, settings):
    _login(client)
    token = _csrf(client.get("/").text)
    jid = _create_job(client, token)
    html = client.get(f"/jobs/{jid}").text
    assert 'id="upload"' in html
    assert f'data-job-id="{jid}"' in html
    assert "data-csrf=" in html
    assert "/static/upload.js" in html


def test_job_page_queued_has_no_upload_widget(client, settings):
    _login(client)
    token = _csrf(client.get("/").text)
    jid = _create_job(client, token)
    zb = make_zip(GOOD)
    client.put(
        f"/jobs/{jid}/upload",
        content=zb,
        headers={"X-CSRF-Token": token, "Content-Length": str(len(zb))},
    )
    html = client.get(f"/jobs/{jid}").text
    assert 'id="upload"' not in html
    assert "/static/upload.js" not in html


def test_job_page_shows_elapsed_and_last_signal(client, settings):
    _login(client)
    token = _csrf(client.get("/").text)
    jid = _create_job(client, token)
    c = connect(settings.db_path())
    c.execute(
        "UPDATE jobs SET status='running', started_at=?, progress='timing y estilo', "
        "progress_at=? WHERE id=?",
        ("2000-01-01T00:00:00.000000Z", "2000-01-01T00:00:00.000000Z", jid),
    )
    c.close()
    html = client.get(f"/jobs/{jid}").text
    assert "En curso desde hace" in html
    assert "Última señal hace" in html
    assert "pueden tardar varios minutos" in html


def test_seconds_between_handles_none():
    from dmoj_contest_analyzer.web.routes import _seconds_between

    assert _seconds_between(None, "2026-01-01T00:00:00.000000Z") is None
    assert (
        _seconds_between(
            "2026-01-01T00:00:00.000000Z", "2026-01-01T00:00:10.000000Z"
        )
        == 10
    )


def test_healthz_unhealthy_without_jar(client):
    assert client.get("/healthz").status_code == 503


def test_healthz_ok_with_jar(client, settings):
    settings.jplag_jar.write_text("x")
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.text == "ok"
