# dmoj-contest-analyzer

Analiza el export de envíos de un concurso DMOJ en busca de patrones sospechosos
(señales de IA / plagio), opcionalmente corre [JPlag](https://github.com/jplag/JPlag),
y lo consolida todo en un único reporte Excel de varias hojas.

## Qué NO es

Esta herramienta **no emite un veredicto de plagio**. Solo produce *señales*
cuantitativas (tiempo de resolución, estilo del código, similitud reportada por
JPlag) pensadas para **priorizar la revisión manual** de un jurado. Un
`score_sospecha` alto significa "mira este caso con atención", no "esta persona
copió". Las decisiones sobre descalificaciones o sanciones son siempre humanas y
requieren evidencia adicional.

## Requisitos

- Python 3.11 o superior
- [uv](https://docs.astral.sh/uv/) para gestionar el entorno y las dependencias
- Solo si vas a usar JPlag:
  - **JPlag 6.x** (probado con la versión **6.3.0**). El parser del reporte
    `.jplag` espera el formato de la serie 6.x; versiones mayores anteriores o
    posteriores pueden no producir resultados.
  - Java 21 o superior en el `PATH` (lo exige JPlag 6.x)
  - El `.jar` de JPlag, que **no viene incluido**: descárgalo de
    <https://github.com/jplag/JPlag/releases>

## Instalación

```bash
git clone https://github.com/AresLOLXD/dmoj-contest-analyzer
cd dmoj-contest-analyzer
uv sync
```

Esto deja disponible el comando `dmoj-contest-analyzer` (equivalente a
`python -m dmoj_contest_analyzer`) a través de `uv run`.

## Uso

Sintaxis general:

```
dmoj-contest-analyzer ENTRADA [--out reporte.xlsx]
                              [--jplag-out CARPETA]
                              [--jplag-solo-ac]
                              [--jplag-jar RUTA]
                              [--run-jplag]
```

| Flag | Descripción |
| --- | --- |
| `ENTRADA` | Archivo `.zip` exportado del concurso, o carpeta ya extraída (obligatorio) |
| `--out` | Excel de salida (por defecto `reporte.xlsx`) |
| `--jplag-out` | Carpeta de trabajo de JPlag (se prepara y/o se lee de aquí) |
| `--jplag-solo-ac` | Al preparar JPlag, usa solo el último AC de cada usuario |
| `--jplag-jar` | Ruta al `.jar` de JPlag (o variable de entorno `JPLAG_JAR`) |
| `--run-jplag` | Ejecuta JPlag; si se omite, se reutilizan los `*_resultado.jplag` existentes |

### 1. Solo timing y estilo, desde el `.zip`

```bash
uv run dmoj-contest-analyzer export.zip --out reporte.xlsx
```

### 2. Preparar y correr JPlag e integrarlo al Excel

```bash
uv run dmoj-contest-analyzer export.zip --out reporte.xlsx \
    --jplag-out jplag_input --jplag-jar jplag.jar --run-jplag
```

En lugar de `--jplag-jar` puedes exportar la variable de entorno:

```bash
export JPLAG_JAR=/ruta/al/jplag.jar
uv run dmoj-contest-analyzer export.zip --out reporte.xlsx \
    --jplag-out jplag_input --run-jplag
```

### 3. Reutilizar resultados `.jplag` ya generados

Si ya corriste JPlag antes y la carpeta contiene los `*_resultado.jplag`, omite
`--run-jplag` (no hace falta Java ni el `.jar`):

```bash
uv run dmoj-contest-analyzer export.zip --out reporte.xlsx --jplag-out jplag_input
```

## Entrada esperada

La entrada es el export producido por
[dmoj-submission-downloader](https://github.com/AresLOLXD/dmoj-submission-downloader),
con este árbol:

```
usuario/
  problema/
    <n>_<usuario>_<AAAA-MM-DD>_<HH-MM-SS>_<RESULTADO>.<ext>
```

Por ejemplo: `1_alumna_2026-09-06_10-15-42_AC.cpp`. El campo `<n>` es el número
de intento y `<RESULTADO>` es el veredicto de DMOJ en mayúsculas (`AC`, `WA`,
`TLE`, ...).

Se acepta:

- el `.zip` tal cual lo entrega el downloader, o
- una carpeta ya extraída,

en ambos casos **con o sin una carpeta contenedora** (el programa desciende
hasta 2 niveles buscando la raíz del export).

## Salida

Un archivo `.xlsx` con tres hojas:

| Hoja | Contenido |
| --- | --- |
| `Resumen` | Totales del concurso: submissions procesadas, usuarios y problemas distintos, casos con `score_sospecha >= 2`, y pares JPlag con similitud `>= 70%` |
| `Timing y Estilo` | Una fila por `(usuario, problema)` con primer AC: `score_sospecha`, `un_solo_intento`, intentos antes del AC, segundos desde el primer envío del usuario, `z_tiempo_vs_grupo`, métricas de estilo y la similitud máxima de JPlag |
| `JPlag - Pares` | Una fila por comparación de JPlag: problema, lenguaje, los dos usuarios y la similitud (0-100). Se omiten los pares con similitud 0 |

### Cómo se calcula `score_sospecha`

Se evalúa por `(usuario, problema)`, tomando el primer envío AC. Parte de `0` y
suma `1` por cada condición que se cumpla:

- `un_solo_intento`: el AC llegó sin envíos previos (0 intentos antes del AC).
- `z_tiempo_vs_grupo < -1.0`: resolvió el problema mucho antes que el resto del
  grupo (z-score del tiempo hasta el AC; solo se calcula si hay más de 2
  personas que resolvieron ese problema).
- `comment_ratio > 0.15`: más del 15 % de las líneas no vacías son comentarios.
- `+1` adicional si, tras integrar JPlag, la similitud máxima de ese usuario en
  ese problema es `>= 70`.

Se marca como **alerta para revisión manual prioritaria** cuando
`score_sospecha >= 2`.

## Limitaciones conocidas

- **Parser del reporte `.jplag`**: se lee el formato de la serie **6.x** de
  JPlag (carpeta `comparisons/` y `submissionMappings.json` dentro del zip). La
  versión que generó cada reporte se toma de `runInformation.json` y se imprime
  en la salida; si el número mayor no es 6, se avisa. Si una versión nueva de
  JPlag deja de producir resultados, `src/dmoj_contest_analyzer/jplag.py` es el
  primer lugar a revisar.
- **Formato de nombres**: todo el análisis depende de que los archivos sigan
  exactamente el patrón de nombres del downloader. Archivos que no coincidan se
  ignoran en silencio.
- Las métricas de estilo (comentarios, longitud de identificadores) están
  calibradas para C/C++, Python y Java; otros lenguajes se procesan con reglas
  aproximadas.

## Desarrollo

```bash
uv sync                 # instala dependencias, incluidas las de desarrollo
uv run pytest           # tests
uv run ruff check .     # lint
```

## Licencia

MIT.
