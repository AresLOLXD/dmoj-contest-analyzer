# dmoj-contest-analyzer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert the standalone `analiza_concurso.py` script into `dmoj-contest-analyzer`, a uv-managed Python project with a module structure, installable CLI, tests, README, and a public GitHub repo — restructured in place in this directory.

**Architecture:** The analysis logic is split verbatim from `analiza_concurso.py` into focused modules under `src/dmoj_contest_analyzer/` (`submissions`, `timing`, `jplag`, `report`, `cli`). One new module, `ingest`, is added so the CLI accepts the downloader's `.zip` directly (or an already-extracted folder), extracting to a temp dir and detecting the real export root. Behavior, thresholds, and the Excel output are unchanged.

**Tech Stack:** Python 3.11+, uv, hatchling build backend, openpyxl (runtime), pytest + ruff (dev), GitHub Actions CI, `gh` CLI for publishing.

**Spec:** `docs/superpowers/specs/2026-09-06-dmoj-contest-analyzer-design.md`

## Global Constraints

- `requires-python = ">=3.11"`.
- Runtime dependencies: `openpyxl` only. Dev dependencies: `pytest`, `ruff`.
- Package name: `dmoj-contest-analyzer`; import package: `dmoj_contest_analyzer`; console script: `dmoj-contest-analyzer = "dmoj_contest_analyzer.cli:main"`.
- Layout: `src/` layout under `src/dmoj_contest_analyzer/`.
- All code, comments, identifiers, and commit messages in English. User-facing CLI strings and README prose stay in Spanish (matching the current script).
- The analysis logic (regexes, thresholds, score rules, `overview.json` heuristic parser, Excel format) is moved **verbatim** — only imports change. The heuristic `overview.json` parser is NOT rewritten.
- `jplag.jar` is NOT vendored. The user provides it via `--jplag-jar` or the `JPLAG_JAR` env var.
- `estatal2026d1mxcdmx.zip` stays in the working directory as manual-verification data; it is gitignored via `/*.zip`.
- License: MIT, "Ares Ulises Juárez Martínez", 2026.
- Commit message trailer on every commit:
  ```
  Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
  Claude-Session: https://claude.ai/code/session_01GM8n9U7HSHGroCea5CXQTE
  ```
- Git identity for commits: `user.name = "Ares Ulises Juárez Martínez"`, `user.email = "aresulises8@hotmail.com"` (repo already has commits from this identity).

---

## File Structure

| File | Responsibility |
|---|---|
| `pyproject.toml` | Project metadata, deps, console script, ruff/pytest config |
| `.gitignore` | Ignore venv, build output, generated reports, jar, test zips |
| `LICENSE` | MIT text |
| `README.md` | Usage, install, JPlag setup, Excel/score explanation, limitations |
| `.github/workflows/ci.yml` | uv sync + ruff + pytest on push/PR |
| `src/dmoj_contest_analyzer/__init__.py` | Package marker, `__version__` |
| `src/dmoj_contest_analyzer/__main__.py` | `python -m dmoj_contest_analyzer` entry |
| `src/dmoj_contest_analyzer/submissions.py` | Filename regex, `Submission`, `parse_submissions`, style stats, ext→lang maps |
| `src/dmoj_contest_analyzer/timing.py` | `analyze_timing_style` |
| `src/dmoj_contest_analyzer/jplag.py` | Prepare/run/find JPlag inputs, parse `overview.json`, merge into main rows |
| `src/dmoj_contest_analyzer/report.py` | Multi-sheet Excel writer |
| `src/dmoj_contest_analyzer/ingest.py` | **New.** Resolve a `.zip` or folder to an export root dir |
| `src/dmoj_contest_analyzer/cli.py` | Argparse + orchestration (`main`) |
| `tests/conftest.py` | Shared fixture builders (mini export tree, zips, sample `.jplag`) |
| `tests/test_ingest.py` | Root detection for folder / flat zip / wrapped zip; error paths |
| `tests/test_submissions.py` | Regex, `parse_submissions`, `style_stats` |
| `tests/test_timing.py` | Score/flags/z-score behavior |
| `tests/test_jplag.py` | `overview.json` extraction, `.jplag` parsing, merge |

---

## Task 1: Project scaffold and cleanup

**Files:**
- Create: `pyproject.toml`, `.gitignore`, `LICENSE`, `src/dmoj_contest_analyzer/__init__.py`, `src/dmoj_contest_analyzer/__main__.py`
- Delete: `jplag.jar`, `estatal2026d1mxcdmx/` (extracted folder), `jplag_input/`, `reporte.csv`, `.venv/`
- Keep untouched: `analiza_concurso.py` (removed in Task 7), `estatal2026d1mxcdmx.zip`

**Interfaces:**
- Consumes: nothing.
- Produces: importable empty package `dmoj_contest_analyzer` with `__version__ = "0.1.0"`; `uv run` environment with pytest available.

- [ ] **Step 1: Remove unneeded artifacts**

```bash
rm -rf jplag.jar estatal2026d1mxcdmx jplag_input reporte.csv .venv
```

- [ ] **Step 2: Create `pyproject.toml`**

```toml
[project]
name = "dmoj-contest-analyzer"
version = "0.1.0"
description = "Detecta patrones de envío sospechosos (IA/plagio) en exports de concursos DMOJ y corre JPlag, todo en un reporte Excel."
readme = "README.md"
requires-python = ">=3.11"
license = { text = "MIT" }
authors = [{ name = "Ares Ulises Juárez Martínez", email = "aresulises8@hotmail.com" }]
dependencies = ["openpyxl>=3.1"]

[project.scripts]
dmoj-contest-analyzer = "dmoj_contest_analyzer.cli:main"

[project.urls]
Repository = "https://github.com/AresLOLXD/dmoj-contest-analyzer"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/dmoj_contest_analyzer"]

[dependency-groups]
dev = ["pytest>=8", "ruff>=0.6"]

[tool.ruff]
line-length = 100
src = ["src", "tests"]

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B"]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

- [ ] **Step 3: Create `.gitignore`**

```gitignore
.venv/
__pycache__/
*.pyc
.pytest_cache/
.ruff_cache/
dist/
build/
*.egg-info/
*.xlsx
*.jar
jplag_input/
/*.zip
reporte.csv
```

- [ ] **Step 4: Create `LICENSE`**

Standard MIT License text, `Copyright (c) 2026 Ares Ulises Juárez Martínez`.

- [ ] **Step 5: Create package files**

`src/dmoj_contest_analyzer/__init__.py`:

```python
"""dmoj-contest-analyzer: análisis de patrones sospechosos en exports de concursos DMOJ."""

__version__ = "0.1.0"
```

`src/dmoj_contest_analyzer/__main__.py`:

```python
from dmoj_contest_analyzer.cli import main

if __name__ == "__main__":
    main()
```

- [ ] **Step 6: Sync and verify the environment**

Run: `uv sync`
Expected: creates `.venv`, writes `uv.lock`, installs openpyxl + pytest + ruff.

Run: `uv run python -c "import dmoj_contest_analyzer; print(dmoj_contest_analyzer.__version__)"`
Expected: prints `0.1.0`.

- [ ] **Step 7: Commit**

```bash
git add -A
git commit -m "chore: scaffold uv project, remove script-era artifacts

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01GM8n9U7HSHGroCea5CXQTE"
```

---

## Task 2: Shared test fixtures + `submissions` module

**Files:**
- Create: `tests/conftest.py`, `src/dmoj_contest_analyzer/submissions.py`, `tests/test_submissions.py`
- Reference: `analiza_concurso.py` lines 58-148 (source to move)

**Interfaces:**
- Consumes: nothing.
- Produces:
  - `FNAME_RE: re.Pattern`, `COMMENT_PATTERNS: dict[str, re.Pattern]`, `EXT_TO_JPLAG_LANG: dict[str, str]`
  - `class Submission` with attrs `path: Path, username: str, problem: str, attempt: int, dt: datetime, result: str, ext: str`, property `source: str`, method `style_stats() -> dict` (keys `n_lines, avg_line_len, comment_ratio, avg_ident_len`)
  - `parse_submissions(root: Path) -> list[Submission]`
  - conftest fixtures: `mini_export_tree(tmp_path_factory) -> Path` (session-scoped dir), `sample_jplag_file(tmp_path_factory) -> Path`

- [ ] **Step 1: Write `tests/conftest.py`**

```python
import json
import zipfile
from pathlib import Path

import pytest

# One AC per user on p1 so z-score has >2 samples; p2 has a retry case.
_FILES = {
    "userA/p1/1_userA_2026-01-01_10-00-00_AC.cpp": "// solA\nint main(){return 0;}\n",
    "userB/p1/1_userB_2026-01-01_09-00-00_WA.cpp": "int main(){return 1;}\n",
    "userB/p1/2_userB_2026-01-01_09-30-00_AC.cpp": "int main(){return 0;}\n",
    "userC/p1/1_userC_2026-01-01_08-00-00_AC.cpp": (
        "// comment 1\n// comment 2\n// comment 3\nint really_long_identifier_name;\nint main(){return 0;}\n"
    ),
    "userA/p2/1_userA_2026-01-01_11-00-00_AC.py": "# c\nprint(1)\n",
    "userB/p2/1_userB_2026-01-01_12-00-00_WA.py": "print(2)\n",
}


def _materialize(base: Path) -> Path:
    for rel, content in _FILES.items():
        p = base / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
    return base


@pytest.fixture(scope="session")
def mini_export_tree(tmp_path_factory) -> Path:
    return _materialize(tmp_path_factory.mktemp("mini_export"))


@pytest.fixture(scope="session")
def flat_zip(tmp_path_factory, mini_export_tree) -> Path:
    zpath = tmp_path_factory.mktemp("flat") / "export.zip"
    with zipfile.ZipFile(zpath, "w") as zf:
        for f in sorted(mini_export_tree.rglob("*")):
            if f.is_file():
                zf.write(f, f.relative_to(mini_export_tree).as_posix())
    return zpath


@pytest.fixture(scope="session")
def wrapped_zip(tmp_path_factory, mini_export_tree) -> Path:
    zpath = tmp_path_factory.mktemp("wrapped") / "export.zip"
    with zipfile.ZipFile(zpath, "w") as zf:
        for f in sorted(mini_export_tree.rglob("*")):
            if f.is_file():
                arc = Path("concurso-x") / f.relative_to(mini_export_tree)
                zf.write(f, arc.as_posix())
    return zpath


@pytest.fixture(scope="session")
def sample_jplag_file(tmp_path_factory) -> Path:
    overview = {
        "submissions": ["userA.cpp", "userC.cpp"],
        "comparisons": [
            {
                "firstSubmissionId": "userA.cpp",
                "secondSubmissionId": "userC.cpp",
                "similarities": {"AVG": 0.82, "MAX": 0.9},
            }
        ],
    }
    zpath = tmp_path_factory.mktemp("jplag") / "cpp_resultado.jplag"
    with zipfile.ZipFile(zpath, "w") as zf:
        zf.writestr("overview.json", json.dumps(overview))
    return zpath
```

- [ ] **Step 2: Write the failing test `tests/test_submissions.py`**

```python
from datetime import datetime

from dmoj_contest_analyzer.submissions import FNAME_RE, parse_submissions


def test_fname_re_matches_valid():
    m = FNAME_RE.match("3_some_user_2026-01-02_14-30-45_AC.cpp")
    assert m and m.group("user") == "some_user" and m.group("result") == "AC"
    assert m.group("attempt") == "3" and m.group("ext") == "cpp"


def test_fname_re_rejects_invalid():
    assert FNAME_RE.match("notes.txt") is None
    assert FNAME_RE.match("1_user_2026-01-02_AC.cpp") is None


def test_parse_submissions_reads_tree(mini_export_tree):
    subs = parse_submissions(mini_export_tree)
    assert len(subs) == 6
    a_p1 = next(s for s in subs if s.username == "userA" and s.problem == "p1")
    assert a_p1.result == "AC" and a_p1.ext == "cpp"
    assert a_p1.dt == datetime(2026, 1, 1, 10, 0, 0)


def test_style_stats_counts_comments(mini_export_tree):
    subs = parse_submissions(mini_export_tree)
    c_p1 = next(s for s in subs if s.username == "userC" and s.problem == "p1")
    stats = c_p1.style_stats()
    assert stats["n_lines"] == 5
    assert stats["comment_ratio"] == 3 / 5
```

- [ ] **Step 3: Run test to verify it fails**

Run: `uv run pytest tests/test_submissions.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'dmoj_contest_analyzer.submissions'`

- [ ] **Step 4: Create `src/dmoj_contest_analyzer/submissions.py`**

Copy `analiza_concurso.py` lines 58-148 **verbatim** (from `FNAME_RE = re.compile(` through the end of `parse_submissions`). Keep the module imports it needs at the top:

```python
import re
import statistics
from datetime import datetime
from pathlib import Path
```

No logic changes. The block already defines `FNAME_RE`, `COMMENT_PATTERNS`, `EXT_TO_JPLAG_LANG`, `class Submission`, and `parse_submissions`.

- [ ] **Step 5: Run tests to verify they pass**

Run: `uv run pytest tests/test_submissions.py -v`
Expected: PASS (4 tests)

- [ ] **Step 6: Lint**

Run: `uv run ruff check src/dmoj_contest_analyzer/submissions.py tests/`
Expected: no errors (fix import ordering only if flagged).

- [ ] **Step 7: Commit**

```bash
git add src/dmoj_contest_analyzer/submissions.py tests/conftest.py tests/test_submissions.py
git commit -m "feat: add submissions module (parse export tree + style stats)

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01GM8n9U7HSHGroCea5CXQTE"
```

---

## Task 3: `timing` module

**Files:**
- Create: `src/dmoj_contest_analyzer/timing.py`, `tests/test_timing.py`
- Reference: `analiza_concurso.py` lines 155-215

**Interfaces:**
- Consumes: `Submission` from `submissions.py`.
- Produces: `analyze_timing_style(subs: list[Submission]) -> list[dict]`. Each row dict has keys: `usuario, problema, intentos_antes_de_AC, segundos_desde_su_primer_envio, un_solo_intento, n_lineas, avg_line_len, comment_ratio, avg_ident_len, archivo, jplag_max_similitud (None), jplag_similar_con (None), z_tiempo_vs_grupo (float|None), score_sospecha (int)`.

- [ ] **Step 1: Write the failing test `tests/test_timing.py`**

```python
from dmoj_contest_analyzer.submissions import parse_submissions
from dmoj_contest_analyzer.timing import analyze_timing_style


def test_rows_only_for_users_with_ac(mini_export_tree):
    rows = analyze_timing_style(parse_submissions(mini_export_tree))
    keys = {(r["usuario"], r["problema"]) for r in rows}
    # userB/p2 has no AC -> excluded
    assert ("userB", "p2") not in keys
    assert ("userA", "p1") in keys and ("userB", "p1") in keys


def test_single_attempt_flag_and_score(mini_export_tree):
    rows = analyze_timing_style(parse_submissions(mini_export_tree))
    a_p1 = next(r for r in rows if r["usuario"] == "userA" and r["problema"] == "p1")
    b_p1 = next(r for r in rows if r["usuario"] == "userB" and r["problema"] == "p1")
    assert a_p1["un_solo_intento"] is True
    assert b_p1["un_solo_intento"] is False  # AC on attempt 2
    assert a_p1["intentos_antes_de_AC"] == 0


def test_zscore_present_with_three_samples(mini_export_tree):
    rows = analyze_timing_style(parse_submissions(mini_export_tree))
    p1_rows = [r for r in rows if r["problema"] == "p1"]
    assert all(r["z_tiempo_vs_grupo"] is not None for r in p1_rows)
    p2_rows = [r for r in rows if r["problema"] == "p2"]
    assert all(r["z_tiempo_vs_grupo"] is None for r in p2_rows)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_timing.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'dmoj_contest_analyzer.timing'`

- [ ] **Step 3: Create `src/dmoj_contest_analyzer/timing.py`**

Header:

```python
import statistics
from collections import defaultdict

from dmoj_contest_analyzer.submissions import Submission
```

Then copy `analiza_concurso.py` lines 155-215 **verbatim** (the entire `analyze_timing_style` function). No logic changes.

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_timing.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Lint**

Run: `uv run ruff check src/dmoj_contest_analyzer/timing.py tests/test_timing.py`
Expected: no errors.

- [ ] **Step 6: Commit**

```bash
git add src/dmoj_contest_analyzer/timing.py tests/test_timing.py
git commit -m "feat: add timing module (timing/style suspicion scoring)

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01GM8n9U7HSHGroCea5CXQTE"
```

---

## Task 4: `jplag` module

**Files:**
- Create: `src/dmoj_contest_analyzer/jplag.py`, `tests/test_jplag.py`
- Reference: `analiza_concurso.py` lines 222-396

**Interfaces:**
- Consumes: `Submission`, `EXT_TO_JPLAG_LANG` from `submissions.py`; row dicts from `timing.analyze_timing_style`.
- Produces:
  - `prepare_jplag_input(subs, jplag_out: Path, solo_ac: bool) -> dict[tuple[str,str], int]`
  - `run_jplag(jplag_out: Path, counts, jplag_jar: str) -> list[tuple[str,str,Path]]`
  - `find_existing_jplag_results(jplag_out: Path) -> list[tuple[str,str,Path]]`
  - `extract_comparisons_from_json(data) -> list[tuple[str,str,float]]`
  - `parse_jplag_result(problem: str, lang: str, jplag_file: Path) -> list[dict]` (keys `problema, lenguaje, usuario_a, usuario_b, similitud`)
  - `merge_jplag_into_main(main_rows: list[dict], jplag_rows: list[dict]) -> None` (mutates `main_rows`)

- [ ] **Step 1: Write the failing test `tests/test_jplag.py`**

```python
import json

from dmoj_contest_analyzer.jplag import (
    extract_comparisons_from_json,
    merge_jplag_into_main,
    parse_jplag_result,
)


def test_extract_comparisons_known_shape():
    data = json.loads(
        '{"comparisons":[{"firstSubmissionId":"a.cpp","secondSubmissionId":"b.cpp",'
        '"similarities":{"AVG":0.5,"MAX":0.75}}]}'
    )
    got = extract_comparisons_from_json(data)
    assert got == [("a.cpp", "b.cpp", 0.75)]


def test_parse_jplag_result_reads_zip(sample_jplag_file):
    rows = parse_jplag_result("p1", "cpp", sample_jplag_file)
    assert len(rows) == 1
    r = rows[0]
    assert {r["usuario_a"], r["usuario_b"]} == {"userA", "userC"}
    assert r["similitud"] == 90.0


def test_merge_bumps_score_when_similarity_high():
    main_rows = [
        {"usuario": "userA", "problema": "p1", "score_sospecha": 1,
         "jplag_max_similitud": None, "jplag_similar_con": None},
    ]
    jplag_rows = [
        {"problema": "p1", "lenguaje": "cpp", "usuario_a": "userA",
         "usuario_b": "userC", "similitud": 90.0},
    ]
    merge_jplag_into_main(main_rows, jplag_rows)
    assert main_rows[0]["jplag_max_similitud"] == 90.0
    assert main_rows[0]["jplag_similar_con"] == "userC"
    assert main_rows[0]["score_sospecha"] == 2
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_jplag.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'dmoj_contest_analyzer.jplag'`

- [ ] **Step 3: Create `src/dmoj_contest_analyzer/jplag.py`**

Header:

```python
import json
import re
import shutil
import subprocess
import zipfile
from collections import defaultdict
from pathlib import Path

from dmoj_contest_analyzer.submissions import EXT_TO_JPLAG_LANG
```

Then copy **verbatim** from `analiza_concurso.py`:
- lines 222-276 (`prepare_jplag_input`, `run_jplag`, `find_existing_jplag_results`)
- lines 295-396 (`ID_KEY_PAIRS`, `_strip_ext`, `extract_comparisons_from_json`, `parse_jplag_result`, `merge_jplag_into_main`)

Skip the comment-only lines 279-293. No logic changes.

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_jplag.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Lint**

Run: `uv run ruff check src/dmoj_contest_analyzer/jplag.py tests/test_jplag.py`
Expected: no errors.

- [ ] **Step 6: Commit**

```bash
git add src/dmoj_contest_analyzer/jplag.py tests/test_jplag.py
git commit -m "feat: add jplag module (prepare/run/parse/merge)

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01GM8n9U7HSHGroCea5CXQTE"
```

---

## Task 5: `report` module

**Files:**
- Create: `src/dmoj_contest_analyzer/report.py`, `tests/test_report.py`
- Reference: `analiza_concurso.py` lines 403-457

**Interfaces:**
- Consumes: main row dicts (from `timing` + `jplag` merge), jplag row dicts.
- Produces: `write_excel_report(main_rows, jplag_rows, out_path: Path, n_subs: int, n_users: int, n_problems: int) -> None` — writes an `.xlsx` with sheets `Resumen`, `Timing y Estilo`, `JPlag - Pares`.

- [ ] **Step 1: Write the failing test `tests/test_report.py`**

```python
from openpyxl import load_workbook

from dmoj_contest_analyzer.report import write_excel_report


def _main_row(**over):
    base = {
        "usuario": "userA", "problema": "p1", "score_sospecha": 2,
        "un_solo_intento": True, "intentos_antes_de_AC": 0,
        "segundos_desde_su_primer_envio": 100.0, "z_tiempo_vs_grupo": -1.5,
        "jplag_max_similitud": 80.0, "jplag_similar_con": "userC",
        "n_lineas": 10, "avg_line_len": 12.0, "comment_ratio": 0.1,
        "avg_ident_len": 4.0, "archivo": "userA/p1/x.cpp",
    }
    base.update(over)
    return base


def test_writes_three_sheets(tmp_path):
    out = tmp_path / "r.xlsx"
    write_excel_report([_main_row()], [
        {"problema": "p1", "lenguaje": "cpp", "usuario_a": "userA",
         "usuario_b": "userC", "similitud": 80.0}
    ], out, n_subs=6, n_users=3, n_problems=2)
    wb = load_workbook(out)
    assert wb.sheetnames == ["Resumen", "Timing y Estilo", "JPlag - Pares"]
    assert wb["Timing y Estilo"]["A2"].value == "userA"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_report.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'dmoj_contest_analyzer.report'`

- [ ] **Step 3: Create `src/dmoj_contest_analyzer/report.py`**

Header:

```python
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter
```

Then copy `analiza_concurso.py` lines 403-457 **verbatim** (`HEADER_FILL`, `HEADER_FONT`, `_write_sheet`, `write_excel_report`). No logic changes.

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_report.py -v`
Expected: PASS

- [ ] **Step 5: Lint**

Run: `uv run ruff check src/dmoj_contest_analyzer/report.py tests/test_report.py`
Expected: no errors.

- [ ] **Step 6: Commit**

```bash
git add src/dmoj_contest_analyzer/report.py tests/test_report.py
git commit -m "feat: add report module (multi-sheet Excel writer)

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01GM8n9U7HSHGroCea5CXQTE"
```

---

## Task 6: `ingest` module (new — zip/folder resolution)

**Files:**
- Create: `src/dmoj_contest_analyzer/ingest.py`, `tests/test_ingest.py`

**Interfaces:**
- Consumes: `FNAME_RE` from `submissions.py`.
- Produces:
  - `class ExportStructureError(Exception)`
  - `resolve_export(entrada: Path) -> ContextManager[Path]` — context manager yielding the export root directory ready for `parse_submissions`. For a `.zip`, extracts to a `TemporaryDirectory` cleaned up on exit; for a directory, yields the detected root (no temp dir). Raises `ExportStructureError` on unrecognizable input, `FileNotFoundError` on missing path.

- [ ] **Step 1: Write the failing test `tests/test_ingest.py`**

```python
import zipfile
from pathlib import Path

import pytest

from dmoj_contest_analyzer.ingest import ExportStructureError, resolve_export
from dmoj_contest_analyzer.submissions import parse_submissions


def test_resolve_plain_folder(mini_export_tree):
    with resolve_export(mini_export_tree) as root:
        assert len(parse_submissions(root)) == 6


def test_resolve_flat_zip(flat_zip):
    with resolve_export(flat_zip) as root:
        assert root.is_dir()
        assert len(parse_submissions(root)) == 6


def test_resolve_wrapped_zip(wrapped_zip):
    with resolve_export(wrapped_zip) as root:
        assert root.name == "concurso-x"
        assert len(parse_submissions(root)) == 6


def test_temp_dir_cleaned_up(flat_zip):
    with resolve_export(flat_zip) as root:
        saved = root
    assert not saved.exists()


def test_missing_path_raises():
    with pytest.raises(FileNotFoundError):
        with resolve_export(Path("/no/such/path.zip")):
            pass


def test_unrecognizable_zip_raises(tmp_path):
    bad = tmp_path / "bad.zip"
    with zipfile.ZipFile(bad, "w") as zf:
        zf.writestr("readme.txt", "nothing useful here")
    with pytest.raises(ExportStructureError):
        with resolve_export(bad):
            pass
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_ingest.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'dmoj_contest_analyzer.ingest'`

- [ ] **Step 3: Create `src/dmoj_contest_analyzer/ingest.py`**

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_ingest.py -v`
Expected: PASS (6 tests)

- [ ] **Step 5: Full suite + lint**

Run: `uv run pytest -q`
Expected: all tests pass.
Run: `uv run ruff check .`
Expected: no errors.

- [ ] **Step 6: Commit**

```bash
git add src/dmoj_contest_analyzer/ingest.py tests/test_ingest.py
git commit -m "feat: add ingest module (accept .zip or folder, detect export root)

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01GM8n9U7HSHGroCea5CXQTE"
```

---

## Task 7: `cli` module + retire the old script

**Files:**
- Create: `src/dmoj_contest_analyzer/cli.py`
- Reference: `analiza_concurso.py` lines 464-523 (the `main` function to adapt)
- Delete: `analiza_concurso.py`

**Interfaces:**
- Consumes: `resolve_export` (ingest), `parse_submissions` (submissions), `analyze_timing_style` (timing), `prepare_jplag_input`/`run_jplag`/`find_existing_jplag_results`/`parse_jplag_result`/`merge_jplag_into_main` (jplag), `write_excel_report` (report).
- Produces: `main() -> None` (console-script entry point).

- [ ] **Step 1: Write the failing test `tests/test_cli.py`**

```python
import subprocess
import sys

from openpyxl import load_workbook


def test_cli_end_to_end_with_zip(flat_zip, tmp_path):
    out = tmp_path / "reporte.xlsx"
    proc = subprocess.run(
        [sys.executable, "-m", "dmoj_contest_analyzer", str(flat_zip), "--out", str(out)],
        capture_output=True, text=True,
    )
    assert proc.returncode == 0, proc.stderr
    assert out.exists()
    wb = load_workbook(out)
    assert wb.sheetnames == ["Resumen", "Timing y Estilo", "JPlag - Pares"]


def test_cli_errors_when_jplag_requested_without_jar(flat_zip, tmp_path, monkeypatch):
    monkeypatch.delenv("JPLAG_JAR", raising=False)
    out = tmp_path / "r.xlsx"
    proc = subprocess.run(
        [sys.executable, "-m", "dmoj_contest_analyzer", str(flat_zip),
         "--out", str(out), "--jplag-out", str(tmp_path / "jp"), "--run-jplag"],
        capture_output=True, text=True,
    )
    assert proc.returncode != 0
    assert "jplag" in (proc.stderr + proc.stdout).lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_cli.py -v`
Expected: FAIL — `No module named dmoj_contest_analyzer.cli` (import in `__main__.py`).

- [ ] **Step 3: Create `src/dmoj_contest_analyzer/cli.py`**

```python
"""CLI: analiza el export de un concurso DMOJ, corre JPlag y arma un reporte Excel.

Uso básico (solo timing/estilo):
    dmoj-contest-analyzer export.zip --out reporte.xlsx

Preparar y correr JPlag e integrarlo al Excel:
    dmoj-contest-analyzer export.zip --out reporte.xlsx \\
        --jplag-out jplag_input --jplag-jar jplag.jar --run-jplag

Reutilizar resultados .jplag ya generados (sin volver a correr JPlag):
    dmoj-contest-analyzer export.zip --out reporte.xlsx --jplag-out jplag_input
"""

import argparse
import os
from pathlib import Path

from dmoj_contest_analyzer.ingest import resolve_export
from dmoj_contest_analyzer.jplag import (
    find_existing_jplag_results,
    merge_jplag_into_main,
    parse_jplag_result,
    prepare_jplag_input,
    run_jplag,
)
from dmoj_contest_analyzer.report import write_excel_report
from dmoj_contest_analyzer.submissions import parse_submissions
from dmoj_contest_analyzer.timing import analyze_timing_style

_JPLAG_RELEASES = "https://github.com/jplag/JPlag/releases"


def _build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="dmoj-contest-analyzer",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("entrada", type=Path,
                    help="Archivo .zip exportado del concurso, o carpeta ya extraída")
    ap.add_argument("--out", type=Path, default=Path("reporte.xlsx"), help="Excel de salida")
    ap.add_argument("--jplag-out", type=Path, default=None,
                    help="Carpeta de trabajo de JPlag (se prepara y/o se lee de aquí)")
    ap.add_argument("--jplag-solo-ac", action="store_true",
                    help="Al preparar JPlag, usa solo el último AC de cada usuario")
    ap.add_argument("--jplag-jar", type=str, default=None,
                    help="Ruta al .jar de JPlag (o variable de entorno JPLAG_JAR)")
    ap.add_argument("--run-jplag", action="store_true",
                    help="Ejecuta JPlag (si no se pasa, se reutilizan *_resultado.jplag existentes)")
    return ap


def _resolve_jplag_jar(cli_value: str | None) -> str:
    jar = cli_value or os.environ.get("JPLAG_JAR")
    if not jar:
        raise SystemExit(
            "Se pidió trabajo de JPlag pero no se indicó el .jar.\n"
            f"Descárgalo de {_JPLAG_RELEASES} y pásalo con --jplag-jar RUTA "
            "o exporta JPLAG_JAR=/ruta/al/jplag.jar"
        )
    if not Path(jar).is_file():
        raise SystemExit(f"No existe el .jar de JPlag: {jar}")
    return jar


def main() -> None:
    args = _build_parser().parse_args()

    jplag_jar = None
    if args.jplag_out is not None and args.run_jplag:
        jplag_jar = _resolve_jplag_jar(args.jplag_jar)

    with resolve_export(args.entrada) as root:
        subs = parse_submissions(root)
        if not subs:
            print("No se encontraron archivos que coincidan con el patrón esperado.")
            return

        n_users = len(set(s.username for s in subs))
        n_problems = len(set(s.problem for s in subs))
        print(f"{len(subs)} submissions encontradas de {n_users} usuarios en {n_problems} problemas.")

        main_rows = analyze_timing_style(subs)

        jplag_rows = []
        if args.jplag_out is not None:
            if args.run_jplag:
                counts = prepare_jplag_input(subs, args.jplag_out, args.jplag_solo_ac)
                print(f"\nEstructura de JPlag creada en: {args.jplag_out.resolve()}")
                print("\n--- JPlag ---")
                jplag_results = run_jplag(args.jplag_out, counts, jplag_jar)
            else:
                jplag_results = find_existing_jplag_results(args.jplag_out)
                print(f"\nReutilizando {len(jplag_results)} resultado(s) .jplag ya existentes "
                      f"en {args.jplag_out}")

            print("\n--- Parseando resultados de JPlag ---")
            for problem, lang, jplag_file in jplag_results:
                rows = parse_jplag_result(problem, lang, jplag_file)
                print(f"  {jplag_file.name}: {len(rows)} comparaciones extraídas")
                jplag_rows.extend(rows)

            if jplag_rows:
                merge_jplag_into_main(main_rows, jplag_rows)
            else:
                print("\n[!] No se extrajo ninguna comparación de JPlag. El Excel se genera solo "
                      "con timing/estilo.")

        write_excel_report(main_rows, jplag_rows, args.out, len(subs), n_users, n_problems)
        print(f"\nReporte escrito en {args.out.resolve()}")

        top = [r for r in main_rows if r["score_sospecha"] >= 2]
        print(f"\n{len(top)} casos con score_sospecha >= 2 (revisión manual prioritaria):")
        for r in sorted(top, key=lambda r: -r["score_sospecha"])[:20]:
            print(f"  {r['usuario']:20s} {r['problema']:15s} score={r['score_sospecha']} "
                  f"jplag_max_similitud={r['jplag_max_similitud']}")
```

Note the two intentional behavior clarifications vs the old script, both within spec ("same behavior" + the documented jar change): `entrada` replaces `carpeta` and is wrapped in `resolve_export`; the jar comes from `--jplag-jar` or `JPLAG_JAR` and is validated up front only when JPlag will actually run.

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_cli.py -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Delete the old script**

```bash
rm analiza_concurso.py
```

- [ ] **Step 6: Full suite + lint**

Run: `uv run pytest -q`
Expected: all tests pass (submissions, timing, jplag, report, ingest, cli).
Run: `uv run ruff check .`
Expected: no errors.

- [ ] **Step 7: Manual verification against real data**

Run:
```bash
uv run dmoj-contest-analyzer estatal2026d1mxcdmx.zip --out /tmp/reporte_new.xlsx
```
Expected: exits 0; prints submission counts (615 files in the zip → matches the earlier run's "submissions encontradas"); `/tmp/reporte_new.xlsx` has the 3 sheets. Spot-check that the "Timing y Estilo" rows and `score_sospecha` values match the previously generated `reporte.csv` content quoted in the spec discussion (e.g. `Tonansy_Flores_Guti_rrez_ / estatal252602d1p2` → score 2). Record the result in the commit body.

- [ ] **Step 8: Commit**

```bash
git add -A
git commit -m "feat: add CLI entry point, accept .zip directly, retire standalone script

Manual check: ran against estatal2026d1mxcdmx.zip, output matches the
pre-refactor report (row set and score_sospecha values).

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01GM8n9U7HSHGroCea5CXQTE"
```

---

## Task 8: README

**Files:**
- Create: `README.md`

**Interfaces:**
- Consumes: final CLI flags from Task 7.
- Produces: nothing (docs).

- [ ] **Step 1: Write `README.md`**

Sections (prose in Spanish):

1. **Título + una línea**: qué hace.
2. **Qué NO es**: herramienta de *señales* para revisión manual, no un veredicto de plagio.
3. **Requisitos**: Python 3.11+, [uv](https://docs.astral.sh/uv/), Java 11+ (solo si se usa JPlag), `jplag.jar` de <https://github.com/jplag/JPlag/releases>.
4. **Instalación**:
   ```bash
   git clone https://github.com/AresLOLXD/dmoj-contest-analyzer
   cd dmoj-contest-analyzer
   uv sync
   ```
5. **Uso** — tres ejemplos, con `uv run dmoj-contest-analyzer`:
   - solo timing/estilo desde el `.zip`;
   - preparar + correr JPlag (`--jplag-out jplag_input --run-jplag`, con `--jplag-jar` o `JPLAG_JAR`);
   - reutilizar `*_resultado.jplag` existentes (sin `--run-jplag`).
6. **Entrada esperada**: estructura del export de [dmoj-submission-downloader](https://github.com/AresLOLXD/dmoj-submission-downloader) (árbol `usuario/problema/N_usuario_fecha_hora_RESULTADO.ext`); acepta el `.zip` tal cual o una carpeta ya extraída, con o sin carpeta contenedora.
7. **Salida**: las tres hojas del Excel (`Resumen`, `Timing y Estilo`, `JPlag - Pares`) y cómo se calcula `score_sospecha` (un_solo_intento, `z_tiempo_vs_grupo < -1`, `comment_ratio > 0.15`, y `+1` si JPlag ≥ 70%; alerta a partir de `>= 2`).
8. **Limitaciones conocidas**: el parser de `overview.json` de JPlag es heurístico y puede romperse entre versiones de JPlag; depende del formato de nombres del downloader.
9. **Desarrollo**: `uv run pytest`, `uv run ruff check .`.
10. **Licencia**: MIT.

- [ ] **Step 2: Sanity check the commands**

Run each command block from the README against `estatal2026d1mxcdmx.zip` (skip the JPlag ones if no jar handy, but at least run the timing-only one).
Expected: no command in the README is wrong.

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs: add README

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01GM8n9U7HSHGroCea5CXQTE"
```

---

## Task 9: CI workflow

**Files:**
- Create: `.github/workflows/ci.yml`

**Interfaces:**
- Consumes: `uv.lock`, test suite.
- Produces: nothing (CI config).

- [ ] **Step 1: Write `.github/workflows/ci.yml`**

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.11", "3.12", "3.13"]
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
        with:
          python-version: ${{ matrix.python-version }}
      - run: uv sync --locked
      - run: uv run ruff check .
      - run: uv run pytest -q
```

- [ ] **Step 2: Validate locally**

Run: `uv sync --locked && uv run ruff check . && uv run pytest -q`
Expected: all green (this mirrors the CI job).

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/ci.yml
git commit -m "ci: run ruff and pytest on push and PR

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01GM8n9U7HSHGroCea5CXQTE"
```

---

## Task 10: Publish to GitHub

**Files:** none (repo operations).

**Interfaces:**
- Consumes: committed repo, `gh` authenticated as `AresLOLXD`.
- Produces: public repo `github.com/AresLOLXD/dmoj-contest-analyzer` with `main` pushed.

- [ ] **Step 1: Confirm clean state**

Run: `git status` and `git log --oneline`
Expected: working tree clean; commits from Tasks 1-9 plus the two design-doc commits present.

- [ ] **Step 2: Ensure branch is `main`**

Run: `git branch -m main` (no-op if already main).

- [ ] **Step 3: Create and push the public repo**

Run:
```bash
gh repo create AresLOLXD/dmoj-contest-analyzer \
  --public --source=. --remote=origin \
  --description "Detecta patrones de envío sospechosos (IA/plagio) en exports de concursos DMOJ y corre JPlag, todo en un reporte Excel." \
  --push
```
Expected: repo created, `origin` set, `main` pushed.

- [ ] **Step 4: Verify**

Run: `gh repo view --web` (or `gh run list` after a few seconds)
Expected: repo is public, README renders, CI workflow triggered on the push.

- [ ] **Step 5: Report**

Print the repo URL and CI status to the user. No commit needed.

---

## Self-Review

**1. Spec coverage:**

| Spec section | Task |
|---|---|
| uv project / pyproject / src layout | Task 1 |
| `requires-python >=3.11`, deps openpyxl / pytest+ruff | Task 1 (Global Constraints) |
| Console script `dmoj-contest-analyzer` | Task 1 + Task 7 |
| `.gitignore` (venv, xlsx, jar, jplag_input, zips) | Task 1 |
| Delete jplag.jar / extracted folder / jplag_input / reporte.csv / .venv; keep the zip | Task 1 |
| `submissions.py` verbatim move | Task 2 |
| `timing.py` verbatim move | Task 3 |
| `jplag.py` verbatim move (heuristic parser untouched) | Task 4 |
| `report.py` verbatim move | Task 5 |
| New `ingest.py`: accept zip or folder, temp extract + cleanup, root detection, `ExportStructureError` | Task 6 |
| CLI: `entrada` arg, `resolve_export` wrap, `--jplag-jar`/`JPLAG_JAR`, clear error, keep other flags/prints | Task 7 |
| Delete `analiza_concurso.py` after modules + tests pass | Task 7 |
| Manual verification vs original output | Task 7 Step 7 |
| Tests: ingest / submissions / timing / jplag (+ report, cli added) | Tasks 2-7 |
| JPlag real run not auto-tested, documented as manual | Task 8 README §5/§8 |
| CI: setup-uv + sync + ruff + pytest, no Java | Task 9 |
| README with all listed sections | Task 8 |
| MIT LICENSE, Ares Ulises Juárez Martínez, 2026 | Task 1 |
| `git init` (already done), initial commits, `gh repo create --public --push` | Tasks 1-10 |

No gaps. (`git init` already ran when the design doc was committed; Task 10 only adds the remote and pushes.)

**2. Placeholder scan:** No "TBD"/"handle edge cases"/"similar to Task N". Verbatim-move steps cite exact `analiza_concurso.py` line ranges (that file is present in the tree during execution). All new code (ingest, cli, tests, configs) is shown in full.

**3. Type consistency:** `resolve_export` yields `Path` and is used as a context manager in `cli.main` — consistent. `parse_submissions(root: Path)` consumed with the yielded `Path` in Tasks 2 and 6-7. `analyze_timing_style` row dict keys (incl. `jplag_max_similitud`, `jplag_similar_con`, `score_sospecha`) match what `merge_jplag_into_main` (Task 4) and `write_excel_report` (Task 5) read. `run_jplag` receives `jplag_jar: str` — Task 7 passes the validated `jplag_jar` string. Console-script path `dmoj_contest_analyzer.cli:main` matches the module/function created in Task 7.
