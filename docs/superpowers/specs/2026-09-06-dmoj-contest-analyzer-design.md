# dmoj-contest-analyzer — Diseño

Fecha: 2026-09-06
Estado: aprobado para planificación

## Objetivo

Convertir el script suelto `analiza_concurso.py` (524 líneas) en un proyecto Python
real: gestionado con `uv`, estructurado en módulos, con CLI instalable, tests,
README y publicado como repositorio público en `github.com/AresLOLXD/dmoj-contest-analyzer`.

El comportamiento del análisis **no cambia**. El único cambio funcional es que la
entrada puede ser directamente el `.zip` exportado por
[dmoj-submission-downloader](https://github.com/AresLOLXD/dmoj-submission-downloader),
además de una carpeta ya extraída.

## No objetivos

- No se agregan features nuevas (sin salida web/HTML, sin base de datos, sin
  detectores adicionales).
- No se reescribe el parser heurístico de `overview.json` de JPlag. Queda igual y
  documentado como frágil.
- No se cambia el formato de salida: sigue siendo un único Excel multi-hoja.
- No se versiona `jplag.jar` en el repo. El usuario lo provee.
- No se automatiza la ejecución de JPlag en CI (requiere Java + jar).

## Contexto del formato de entrada

El downloader produce un `.zip` con esta estructura (sin garantía de carpeta
contenedora):

```
usuario1/
├── problema_a/
│   ├── 1_usuario1_2024-01-15_14-30-45_AC.py
│   └── 2_usuario1_2024-01-15_14-35-20_WA.py
└── problema_b/
    └── 1_usuario1_2024-01-15_15-10-00_AC.cpp
```

Nombre de archivo: `{secuencia}_{usuario}_{YYYY-MM-DD}_{HH-MM-SS}_{RESULTADO}.{ext}`

El zip de ejemplo actual (`estatal2026d1mxcdmx.zip`) tiene los usuarios en la raíz,
sin carpeta contenedora. Otros exports podrían traer una carpeta
`nombre-concurso/` envolviendo todo. Ambos casos deben funcionar.

## Estructura del proyecto

```
dmoj-contest-analyzer/
├── pyproject.toml
├── uv.lock
├── README.md
├── LICENSE                       # MIT
├── .gitignore
├── .github/workflows/ci.yml
├── src/dmoj_contest_analyzer/
│   ├── __init__.py
│   ├── __main__.py               # permite `python -m dmoj_contest_analyzer`
│   ├── cli.py
│   ├── ingest.py                 # NUEVO
│   ├── submissions.py
│   ├── timing.py
│   ├── jplag.py
│   └── report.py
└── tests/
    ├── fixtures/
    │   ├── mini_export/          # export sintético extraído
    │   ├── mini_export.zip       # mismo export, comprimido, usuarios en raíz
    │   ├── mini_export_wrapped.zip  # mismo export con carpeta contenedora
    │   └── sample_resultado.jplag   # .jplag mínimo para probar el parser
    ├── test_ingest.py
    ├── test_submissions.py
    ├── test_timing.py
    └── test_jplag.py
```

### pyproject.toml

- Build backend: `hatchling` (default de `uv init --package`).
- `requires-python = ">=3.11"`.
- Dependencia de runtime: `openpyxl`.
- Grupo dev (`[dependency-groups]`): `pytest`, `ruff`.
- Script: `dmoj-contest-analyzer = "dmoj_contest_analyzer.cli:main"`.

### .gitignore

`.venv/`, `__pycache__/`, `*.xlsx`, `*.jar`, `jplag_input/`, `/*.zip`,
`reporte.csv`, `.pytest_cache/`, `dist/`.

## Reparto del código actual

La lógica se mueve **sin modificar** salvo los imports:

| Módulo | Contenido de `analiza_concurso.py` |
|---|---|
| `submissions.py` | `FNAME_RE`, `COMMENT_PATTERNS`, `EXT_TO_JPLAG_LANG`, clase `Submission`, `parse_submissions` |
| `timing.py` | `analyze_timing_style` |
| `jplag.py` | `prepare_jplag_input`, `run_jplag`, `find_existing_jplag_results`, `ID_KEY_PAIRS`, `_strip_ext`, `extract_comparisons_from_json`, `parse_jplag_result`, `merge_jplag_into_main` |
| `report.py` | `HEADER_FILL`, `HEADER_FONT`, `_write_sheet`, `write_excel_report` |
| `cli.py` | `main` (adaptado, ver abajo) |

## Nuevo módulo: `ingest.py`

Responsabilidad única: dada una ruta de entrada (zip o carpeta), entregar un
`Path` a la carpeta raíz lista para `parse_submissions()`.

```python
@contextmanager
def resolve_export(entrada: Path) -> Iterator[Path]:
    """
    Si `entrada` es un .zip: lo extrae a un directorio temporal (que se limpia
    al salir del context manager) y devuelve la raíz detectada.
    Si `entrada` es una carpeta: detecta y devuelve la raíz.
    """
```

### Detección de raíz

Se define que un directorio D es una **raíz de export válida** si al menos uno de
sus subdirectorios (nivel usuario) contiene a su vez al menos un subdirectorio
(nivel problema) que contiene al menos un archivo cuyo nombre matchea `FNAME_RE`.

Algoritmo:
1. Probar `D` = directorio extraído / la carpeta dada.
2. Si `D` es raíz válida → devolverla.
3. Si no, y `D` contiene exactamente un subdirectorio → repetir con ese
   subdirectorio (una sola vez; profundidad máxima 2 niveles de descenso).
4. Si sigue sin ser válida → `ExportStructureError` con mensaje claro
   (qué se buscaba, qué se encontró en los primeros niveles).

### Errores

- Zip corrupto / no es zip → `zipfile.BadZipFile` se captura y se re-lanza como
  `ExportStructureError` con contexto.
- Ruta inexistente → `FileNotFoundError` con mensaje.

## Cambios en `cli.py`

- Argumento posicional `carpeta` → `entrada` (help: "archivo .zip exportado del
  concurso, o carpeta ya extraída").
- El cuerpo de `main` se envuelve en `with resolve_export(args.entrada) as root:`
  y se pasa `root` a `parse_submissions`.
- `--jplag-jar`: si no se pasa por flag, se toma de la variable de entorno
  `JPLAG_JAR`. Si no hay ninguna y se pidió trabajo de JPlag (`--jplag-out`),
  error claro con el link al release de JPlag y ejemplo de uso. Sin `--jplag-out`
  el jar no se necesita (igual que hoy).
- Se mantienen todos los demás flags y textos.
- `print(...)` se conserva tal cual (no se migra a logging; fuera de alcance).

## Tests

Framework: `pytest`. Fixtures sintéticas pequeñas, deterministas, versionadas.

- **`test_ingest.py`**: raíz detectada correctamente para (a) carpeta cruda,
  (b) `mini_export.zip` con usuarios en raíz, (c) `mini_export_wrapped.zip` con
  carpeta contenedora. El temporal se limpia al salir. Zip inválido lanza
  `ExportStructureError`.
- **`test_submissions.py`**: `FNAME_RE` matchea nombres válidos y rechaza
  inválidos; `parse_submissions` arma los `Submission` esperados desde la fixture;
  `style_stats` sobre un archivo conocido da métricas esperadas.
- **`test_timing.py`**: `analyze_timing_style` sobre la fixture produce los
  `score_sospecha`, `un_solo_intento` y flags esperados; problemas con <3 tiempos
  dan `z_tiempo_vs_grupo = None`.
- **`test_jplag.py`**: `extract_comparisons_from_json` sobre un JSON de ejemplo
  con el formato conocido; `parse_jplag_result` sobre `sample_resultado.jplag`
  (zip con `overview.json` dentro) devuelve las filas esperadas;
  `merge_jplag_into_main` sube el score cuando la similitud ≥ 70.

La ejecución real de JPlag (`run_jplag`) **no** se testea automáticamente; se
documenta como verificación manual en el README con el zip de ejemplo real.

Verificación de que el refactor no rompió nada: correr el CLI contra
`estatal2026d1mxcdmx.zip` y comparar el Excel generado con uno hecho por el
script original (mismas filas, mismos scores).

## CI

`.github/workflows/ci.yml`: en `push` y `pull_request`,
`astral-sh/setup-uv`, `uv sync`, `uv run ruff check .`, `uv run pytest`.
No instala Java ni corre JPlag.

## README

Secciones:
1. Qué hace y qué NO (herramienta de señales para revisión manual, no veredicto).
2. Requisitos: Python 3.11+, uv, Java 11+ (solo si se usa JPlag), `jplag.jar`.
3. Instalación: `uv sync` / `uv tool install`.
4. Cómo obtener `jplag.jar` (link al release) y cómo pasarlo (`--jplag-jar` o
   `JPLAG_JAR`).
5. Uso: ejemplos con `.zip` directo, con y sin `--run-jplag`, reutilizando
   resultados `.jplag` previos.
6. Formato de entrada esperado (estructura del downloader).
7. Descripción de las hojas del Excel y de cómo se calcula `score_sospecha`.
8. Limitaciones conocidas: parser heurístico de `overview.json` de JPlag,
   dependencia del formato de nombres del downloader.
9. Licencia MIT.

## Publicación

1. `git init` en el directorio del proyecto ya reestructurado.
2. `LICENSE` MIT a nombre de Ares Ulises Juárez Martínez, 2026.
3. Commit inicial.
4. `gh repo create AresLOLXD/dmoj-contest-analyzer --public --source=. --push`.

El proyecto se reestructura **en este mismo directorio** (`OMI-CDMX-D1/`), que se
convierte en el repo `dmoj-contest-analyzer`.

Artefactos actuales y su destino:
- `estatal2026d1mxcdmx.zip` → **se conserva** en el directorio (gitignoreado por
  `/*.zip`). Sirve como dato real para verificación manual.
- `analiza_concurso.py` → se elimina una vez que su lógica vive en los módulos y
  los tests pasan.
- `jplag.jar` → se elimina del directorio (el usuario lo provee vía `--jplag-jar`
  / `JPLAG_JAR`).
- `estatal2026d1mxcdmx/` (carpeta extraída), `jplag_input/`, `reporte.csv`,
  `.venv/` → se eliminan; `.venv` se regenera con `uv sync`.
