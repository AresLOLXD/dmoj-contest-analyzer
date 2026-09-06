"""Tests for the ``dmoj-manage-users`` CLI."""

from __future__ import annotations

import sqlite3

import pytest

from dmoj_contest_analyzer import users_cli
from dmoj_contest_analyzer.web import db


def _rows(tmp_path):
    conn = db.connect(tmp_path / "state.db")
    conn.row_factory = sqlite3.Row
    return conn.execute("SELECT * FROM users").fetchall()


def test_add_then_disable_and_enable(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr("getpass.getpass", lambda *a, **k: "pw12345")

    users_cli.main(["--data-dir", str(tmp_path), "add", "eve"])
    rows = _rows(tmp_path)
    assert len(rows) == 1
    assert rows[0]["username"] == "eve"
    assert rows[0]["must_change_password"] == 1
    assert rows[0]["disabled"] == 0
    assert rows[0]["token_version"] == 0
    assert rows[0]["created_at"]
    assert rows[0]["password_hash"].startswith("$argon2")

    users_cli.main(["--data-dir", str(tmp_path), "disable", "eve"])
    assert _rows(tmp_path)[0]["disabled"] == 1

    users_cli.main(["--data-dir", str(tmp_path), "enable", "eve"])
    assert _rows(tmp_path)[0]["disabled"] == 0


def test_add_no_force_change(tmp_path, monkeypatch):
    monkeypatch.setattr("getpass.getpass", lambda *a, **k: "pw12345")
    users_cli.main(["--data-dir", str(tmp_path), "add", "bob", "--no-force-change"])
    assert _rows(tmp_path)[0]["must_change_password"] == 0


def test_add_duplicate_exits(tmp_path, monkeypatch):
    monkeypatch.setattr("getpass.getpass", lambda *a, **k: "pw12345")
    users_cli.main(["--data-dir", str(tmp_path), "add", "eve"])
    with pytest.raises(SystemExit) as exc:
        users_cli.main(["--data-dir", str(tmp_path), "add", "eve"])
    assert exc.value.code == 1


def test_add_password_mismatch_exits(tmp_path, monkeypatch):
    answers = iter(["one12345", "two12345"])
    monkeypatch.setattr("getpass.getpass", lambda *a, **k: next(answers))
    with pytest.raises(SystemExit) as exc:
        users_cli.main(["--data-dir", str(tmp_path), "add", "eve"])
    assert exc.value.code == 1


def test_reset_password(tmp_path, monkeypatch):
    monkeypatch.setattr("getpass.getpass", lambda *a, **k: "pw12345")
    users_cli.main(["--data-dir", str(tmp_path), "add", "eve", "--no-force-change"])
    old = _rows(tmp_path)[0]["password_hash"]
    monkeypatch.setattr("getpass.getpass", lambda *a, **k: "new12345")
    users_cli.main(["--data-dir", str(tmp_path), "reset-password", "eve"])
    row = _rows(tmp_path)[0]
    assert row["password_hash"] != old
    assert row["must_change_password"] == 1


def test_disable_missing_exits(tmp_path):
    with pytest.raises(SystemExit) as exc:
        users_cli.main(["--data-dir", str(tmp_path), "disable", "ghost"])
    assert exc.value.code == 1


def test_reset_missing_exits(tmp_path):
    with pytest.raises(SystemExit) as exc:
        users_cli.main(["--data-dir", str(tmp_path), "reset-password", "ghost"])
    assert exc.value.code == 1


def test_list(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr("getpass.getpass", lambda *a, **k: "pw12345")
    users_cli.main(["--data-dir", str(tmp_path), "add", "eve"])
    capsys.readouterr()
    users_cli.main(["--data-dir", str(tmp_path), "list"])
    out = capsys.readouterr().out
    assert "eve" in out
