import re

import pytest
from fastapi.testclient import TestClient

from dmoj_contest_analyzer.web import auth, jobs
from dmoj_contest_analyzer.web.app import create_app
from dmoj_contest_analyzer.web.db import connect, migrate, utcnow


def _csrf(html: str) -> str:
    return re.search(r'name="csrf" value="([^"]+)"', html).group(1)


@pytest.fixture
def client(settings):
    (settings.data_dir / "backends.toml").write_text("")
    app = create_app(settings, start_worker=False)
    c = connect(settings.db_path())
    migrate(c)
    for name in ("alice", "bob"):
        c.execute(
            "INSERT INTO users(username,password_hash,token_version,created_at) "
            "VALUES (?,?,0,?)",
            (name, auth.hash_password("pw123456"), utcnow()),
        )
    c.close()
    with TestClient(app, base_url="https://testserver") as tc:
        yield tc


def _login(client, user="alice", pw="pw123456"):
    token = _csrf(client.get("/login").text)
    client.post("/login", data={"csrf": token, "username": user, "password": pw})


def _mkjob(settings, owner, status):
    import uuid

    c = connect(settings.db_path())
    jid = uuid.uuid4().hex
    jobs.create_job(
        c, job_id=jid, owner=owner, model_ref=None,
        run_jplag=False, jplag_solo_ac=False, settings=settings,
    )
    c.execute("UPDATE jobs SET status=? WHERE id=?", (status, jid))
    c.close()
    return jid


def test_jobs_list_requires_login(client):
    r = client.get("/jobs", follow_redirects=False)
    assert r.status_code in (302, 303)
    assert r.headers["location"] == "/login"


def test_jobs_list_shows_only_own_jobs(client, settings):
    mine = _mkjob(settings, "alice", "done")
    theirs = _mkjob(settings, "bob", "done")
    _login(client, "alice")
    html = client.get("/jobs").text
    assert mine in html
    assert theirs not in html


def test_jobs_list_meta_refresh_only_when_active(client, settings):
    _login(client, "alice")
    _mkjob(settings, "alice", "done")
    assert "http-equiv=\"refresh\"" not in client.get("/jobs").text
    _mkjob(settings, "alice", "running")
    assert "http-equiv=\"refresh\"" in client.get("/jobs").text


def test_jobs_list_empty_message(client):
    _login(client)
    assert "Aún no tienes trabajos" in client.get("/jobs").text


def _seed_job(settings, owner, jid, created_at):
    c = connect(settings.db_path())
    c.execute(
        "INSERT INTO jobs(id,owner,status,created_at) VALUES (?,?,?,?)",
        (jid, owner, "done", created_at),
    )
    c.close()


def test_jobs_list_orders_by_created_desc_and_caps_at_50(client, settings):
    def jid(i):
        return "a" * 30 + f"{i:02d}"

    for i in range(55):
        _seed_job(settings, "alice", jid(i), f"2026-09-06T00:{i:02d}:00.000000Z")
    _login(client, "alice")
    html = client.get("/jobs").text

    assert html.index(jid(54)) < html.index(jid(5))  # newest before oldest shown
    assert jid(4) not in html  # beyond the 50-row cap
    assert jid(54) in html
