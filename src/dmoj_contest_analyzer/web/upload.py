"""The security boundary between an attacker-controlled ``.zip`` and the
analysis pipeline.

Nothing else in the web layer is allowed to touch a raw upload: this module
streams it to disk under a byte cap, validates the archive structure, and
extracts it entry-by-entry with a real (not declared) byte counter and a
``realpath`` containment check on every target.

``ingest.resolve_export`` (used by the CLI) is explicitly *not* a security
boundary and is not involved here.
"""

from __future__ import annotations

import ntpath
import os
import zipfile
from pathlib import Path
from typing import Protocol

from dmoj_contest_analyzer import ingest
from dmoj_contest_analyzer.submissions import parse_submissions

_CHUNK = 1024 * 1024
_ZIP_MAGIC = b"PK\x03\x04"
_S_IFLNK = 0o120000


class UploadRejected(Exception):
    """A rejected upload. ``status`` is the HTTP code (413 or 422)."""

    def __init__(self, status: int, reason: str) -> None:
        super().__init__(reason)
        self.status = status
        self.reason = reason


class _AsyncReader(Protocol):
    async def read(self, size: int) -> bytes: ...


async def stream_to_file(upload: _AsyncReader, dest: Path, max_bytes: int) -> None:
    """Stream ``upload`` to ``dest`` in 1 MiB chunks.

    On exceeding ``max_bytes`` the partial file is unlinked and
    ``UploadRejected(413, ...)`` is raised.
    """
    dest.parent.mkdir(parents=True, exist_ok=True)
    written = 0
    try:
        with dest.open("wb") as fh:
            while True:
                chunk = await upload.read(_CHUNK)
                if not chunk:
                    break
                written += len(chunk)
                if written > max_bytes:
                    raise UploadRejected(
                        413,
                        f"El archivo supera el límite de {max_bytes} bytes.",
                    )
                fh.write(chunk)
    except UploadRejected:
        dest.unlink(missing_ok=True)
        raise


async def stream_body_to_file(request, dest: Path, max_bytes: int) -> int:
    """Stream ``request``'s raw body to ``dest`` in chunks under ``max_bytes``.

    Returns the byte count. On overflow the partial file is unlinked and
    ``UploadRejected(413, ...)`` is raised. Used by the two-step upload's
    ``PUT /jobs/{id}/upload`` (raw body, not multipart).
    """
    dest.parent.mkdir(parents=True, exist_ok=True)
    written = 0
    try:
        with dest.open("wb") as fh:
            async for chunk in request.stream():
                if not chunk:
                    continue
                written += len(chunk)
                if written > max_bytes:
                    raise UploadRejected(
                        413, f"El archivo supera el límite de {max_bytes} bytes."
                    )
                fh.write(chunk)
    except UploadRejected:
        dest.unlink(missing_ok=True)
        raise
    return written


def _is_unsafe_name(name: str) -> bool:
    normalized = name.replace("\\", "/")
    if normalized.startswith("/"):
        return True
    if ntpath.splitdrive(name)[0] or ntpath.isabs(name):
        return True
    return any(part == ".." for part in normalized.split("/"))


def validate_and_extract(
    zip_path: Path, work_dir: Path, settings
) -> tuple[int, int]:
    """Validate ``zip_path`` and extract it into ``work_dir``.

    Returns ``(n_users, n_problems)``. Raises ``UploadRejected(422, ...)`` on
    any structural or resource-limit violation. Checks run in a fixed order and
    fail fast.
    """
    max_unzipped = settings.max_unzipped_mb * 1024 * 1024

    with zip_path.open("rb") as fh:
        if fh.read(4) != _ZIP_MAGIC:
            raise UploadRejected(422, "El archivo no es un .zip válido.")

    try:
        zf = zipfile.ZipFile(zip_path)
    except zipfile.BadZipFile as exc:
        raise UploadRejected(422, "El archivo no es un .zip válido.") from exc

    with zf:
        infos = zf.infolist()

        if any(info.flag_bits & 0x1 for info in infos):
            raise UploadRejected(422, "El .zip está cifrado.")

        if len(infos) > settings.max_zip_entries:
            raise UploadRejected(
                422,
                f"El .zip tiene demasiadas entradas (máximo {settings.max_zip_entries}).",
            )

        declared_total = sum(info.file_size for info in infos)
        if declared_total > max_unzipped:
            raise UploadRejected(
                422,
                f"El contenido descomprimido supera {settings.max_unzipped_mb} MB.",
            )

        for info in infos:
            ratio = info.file_size / max(info.compress_size, 1)
            if ratio > settings.max_compression_ratio:
                raise UploadRejected(
                    422,
                    "Una entrada del .zip tiene una tasa de compresión sospechosa.",
                )

        for info in infos:
            if _is_unsafe_name(info.filename):
                raise UploadRejected(
                    422, "El .zip contiene una ruta no permitida."
                )
            if (info.external_attr >> 16) & 0o170000 == _S_IFLNK:
                raise UploadRejected(
                    422, "El .zip contiene un enlace simbólico."
                )

        _extract(zf, infos, work_dir, max_unzipped, settings)

    try:
        root = ingest._detect_root(work_dir)
        submissions = list(parse_submissions(root))
    except UploadRejected:
        raise
    except Exception as exc:
        # _detect_root raises ExportStructureError; parse_submissions can raise
        # ValueError on a crafted filename that matches FNAME_RE but holds an
        # impossible date. Never forward internal detail.
        raise UploadRejected(
            422, "El .zip no contiene un export de envíos DMOJ válido."
        ) from exc

    if not submissions:
        raise UploadRejected(
            422, "El .zip no contiene un export de envíos DMOJ válido."
        )

    users = {s.username for s in submissions}
    problems = {s.problem for s in submissions}
    if len(users) > settings.max_users:
        raise UploadRejected(
            422, f"El export tiene demasiados usuarios (máximo {settings.max_users})."
        )
    if len(problems) > settings.max_problems:
        raise UploadRejected(
            422,
            f"El export tiene demasiados problemas (máximo {settings.max_problems}).",
        )
    return len(users), len(problems)


def _extract(
    zf: zipfile.ZipFile,
    infos: list[zipfile.ZipInfo],
    work_dir: Path,
    max_unzipped: int,
    settings,
) -> None:
    work_dir.mkdir(parents=True, exist_ok=True)
    work_real = os.path.realpath(work_dir)
    written_total = 0

    for info in infos:
        if info.is_dir():
            continue
        dest = work_dir / info.filename
        dest_real = os.path.realpath(dest)
        if dest_real != work_real and not dest_real.startswith(work_real + os.sep):
            raise UploadRejected(
                422, "El .zip intenta escribir fuera del directorio de trabajo."
            )
        Path(dest).parent.mkdir(parents=True, exist_ok=True)
        try:
            with zf.open(info) as src, open(dest, "wb") as out:
                while True:
                    chunk = src.read(_CHUNK)
                    if not chunk:
                        break
                    written_total += len(chunk)
                    if written_total > max_unzipped:
                        raise UploadRejected(
                            422,
                            f"El contenido extraído del .zip supera el límite de "
                            f"{settings.max_unzipped_mb} MB.",
                        )
                    out.write(chunk)
        except UploadRejected:
            # Remove the partial file we were mid-write on. Sibling files
            # already extracted can stay: the caller owns the job dir and
            # discards it on rejection.
            Path(dest).unlink(missing_ok=True)
            raise
        except (zipfile.BadZipFile, EOFError, OSError, ValueError) as exc:
            # A member that lies about its size / CRC, or a truncated stream.
            Path(dest).unlink(missing_ok=True)
            raise UploadRejected(
                422, "El .zip contiene una entrada corrupta o manipulada."
            ) from exc
