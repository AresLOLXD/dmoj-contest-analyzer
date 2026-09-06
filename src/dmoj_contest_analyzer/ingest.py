"""Resolve a contest export (a .zip from dmoj-submission-downloader, or an
already-extracted folder) to the directory that `parse_submissions` expects:
one whose children are user dirs containing problem dirs containing
`<n>_<user>_<date>_<time>_<RESULT>.<ext>` files."""

import zipfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory

from dmoj_contest_analyzer.submissions import FNAME_RE

_MAX_DESCENT = 2


class ExportStructureError(Exception):
    """The input does not look like a DMOJ submission export."""


def _is_export_root(d: Path) -> bool:
    for user_dir in d.iterdir():
        if not user_dir.is_dir():
            continue
        for prob_dir in user_dir.iterdir():
            if not prob_dir.is_dir():
                continue
            for f in prob_dir.iterdir():
                if f.is_file() and FNAME_RE.match(f.name):
                    return True
    return False


def _detect_root(start: Path) -> Path:
    current = start
    for _ in range(_MAX_DESCENT + 1):
        if _is_export_root(current):
            return current
        subdirs = [c for c in current.iterdir() if c.is_dir()]
        if len(subdirs) != 1:
            break
        current = subdirs[0]
    listing = sorted(p.name for p in start.iterdir())[:10]
    raise ExportStructureError(
        "No se encontró una estructura de export DMOJ "
        "(usuario/problema/N_usuario_fecha_hora_RESULTADO.ext). "
        f"Primer nivel encontrado en {start}: {listing}"
    )


@contextmanager
def resolve_export(entrada: Path) -> Iterator[Path]:
    entrada = Path(entrada)
    if not entrada.exists():
        raise FileNotFoundError(f"No existe: {entrada}")

    if entrada.is_dir():
        yield _detect_root(entrada)
        return

    try:
        with TemporaryDirectory(prefix="dmoj-export-") as tmp:
            with zipfile.ZipFile(entrada) as zf:
                zf.extractall(tmp)
            yield _detect_root(Path(tmp))
    except zipfile.BadZipFile as exc:
        raise ExportStructureError(f"{entrada} no es un .zip válido: {exc}") from exc
