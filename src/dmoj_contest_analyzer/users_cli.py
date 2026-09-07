"""``dmoj-manage-users`` CLI: provision and manage web-layer user accounts.

This is the only way to create a jury before a web layer exists. It talks
directly to the SQLite job store via :mod:`dmoj_contest_analyzer.web.db` and
hashes passwords with :func:`dmoj_contest_analyzer.web.auth.hash_password`.

User-facing messages are in Spanish; code and comments stay in English.
"""

from __future__ import annotations

import argparse
import getpass
import os
import sqlite3
import sys
from pathlib import Path

from .web.auth import bump_token_version, hash_password
from .web.db import connect, migrate, utcnow


def _fail(message: str) -> None:
    print(message, file=sys.stderr)
    raise SystemExit(1)


def _prompt_password() -> str:
    first = getpass.getpass("Contraseña: ")
    second = getpass.getpass("Repite la contraseña: ")
    if first != second:
        _fail("Error: las contraseñas no coinciden.")
    if not first:
        _fail("Error: la contraseña no puede estar vacía.")
    return first


def _user_exists(conn: sqlite3.Connection, username: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM users WHERE username = ?", (username,)
    ).fetchone()
    return row is not None


def _cmd_add(conn: sqlite3.Connection, args: argparse.Namespace) -> None:
    if _user_exists(conn, args.username):
        _fail(f"Error: el usuario '{args.username}' ya existe.")
    password = _prompt_password()
    conn.execute(
        "INSERT INTO users(username, password_hash, must_change_password, "
        "token_version, created_at, disabled) VALUES (?, ?, ?, 0, ?, 0)",
        (
            args.username,
            hash_password(password),
            0 if args.no_force_change else 1,
            utcnow(),
        ),
    )
    print(f"Usuario '{args.username}' creado.")


def _set_disabled(conn: sqlite3.Connection, username: str, disabled: int) -> None:
    if not _user_exists(conn, username):
        _fail(f"Error: el usuario '{username}' no existe.")
    conn.execute(
        "UPDATE users SET disabled = ? WHERE username = ?", (disabled, username)
    )
    print(f"Usuario '{username}' {'deshabilitado' if disabled else 'habilitado'}.")


def _cmd_disable(conn: sqlite3.Connection, args: argparse.Namespace) -> None:
    _set_disabled(conn, args.username, 1)


def _cmd_enable(conn: sqlite3.Connection, args: argparse.Namespace) -> None:
    _set_disabled(conn, args.username, 0)


def _cmd_reset_password(conn: sqlite3.Connection, args: argparse.Namespace) -> None:
    if not _user_exists(conn, args.username):
        _fail(f"Error: el usuario '{args.username}' no existe.")
    password = _prompt_password()
    conn.execute(
        "UPDATE users SET password_hash = ?, must_change_password = 1 "
        "WHERE username = ?",
        (hash_password(password), args.username),
    )
    # Revoke any live sessions — the point of a reset is to lock out whoever
    # held the old credentials.
    bump_token_version(conn, args.username)
    print(f"Contraseña de '{args.username}' actualizada.")


def _cmd_list(conn: sqlite3.Connection, args: argparse.Namespace) -> None:
    rows = conn.execute(
        "SELECT username, disabled, must_change_password, created_at "
        "FROM users ORDER BY username"
    ).fetchall()
    header = f"{'username':<24} {'disabled':>8} {'must_change':>12}  created_at"
    print(header)
    for row in rows:
        print(
            f"{row['username']:<24} {row['disabled']:>8} "
            f"{row['must_change_password']:>12}  {row['created_at']}"
        )


def _default_data_dir() -> Path:
    return Path(os.environ.get("DATA_DIR", "/data"))


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dmoj-manage-users",
        description="Administra las cuentas de usuario de la capa web.",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=_default_data_dir(),
        help="Directorio de datos que contiene state.db (env DATA_DIR o /data).",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_add = sub.add_parser("add", help="Crea un usuario.")
    p_add.add_argument("username")
    p_add.add_argument(
        "--no-force-change",
        action="store_true",
        help="No exigir cambio de contraseña en el primer acceso.",
    )
    p_add.set_defaults(func=_cmd_add)

    p_disable = sub.add_parser("disable", help="Deshabilita un usuario.")
    p_disable.add_argument("username")
    p_disable.set_defaults(func=_cmd_disable)

    p_enable = sub.add_parser("enable", help="Habilita un usuario.")
    p_enable.add_argument("username")
    p_enable.set_defaults(func=_cmd_enable)

    p_reset = sub.add_parser("reset-password", help="Restablece la contraseña.")
    p_reset.add_argument("username")
    p_reset.set_defaults(func=_cmd_reset_password)

    p_list = sub.add_parser("list", help="Lista los usuarios.")
    p_list.set_defaults(func=_cmd_list)

    return parser


def main(argv: list[str] | None = None) -> None:
    args = _build_parser().parse_args(argv)
    db_path = args.data_dir / "state.db"
    conn = connect(db_path)
    try:
        migrate(conn)
        args.func(conn, args)
    finally:
        conn.close()
