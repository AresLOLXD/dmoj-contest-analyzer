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
- El CLI `dmoj-contest-analyzer` no necesita nada nuevo para timing/estilo/JPlag.
- Solo si vas a usar el juez LLM (`--run-llm`): un endpoint compatible con la API
  de OpenAI accesible (Ollama, LM Studio, OpenAI, etc.).
- Solo para la interfaz web (opcional): **Docker** y **Docker Compose** (o Podman).
  Java viene dentro de la imagen; el `.jar` de JPlag se descarga a `vendor/` al
  construir (ver [Despliegue web](#despliegue-web-opcional)).

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
                              [--run-llm]
                              [--llm-model BACKEND|MODELO]
                              [--backends-config RUTA]
```

| Flag | Descripción |
| --- | --- |
| `ENTRADA` | Archivo `.zip` exportado del concurso, o carpeta ya extraída (obligatorio) |
| `--out` | Excel de salida (por defecto `reporte.xlsx`) |
| `--jplag-out` | Carpeta de trabajo de JPlag (se prepara y/o se lee de aquí) |
| `--jplag-solo-ac` | Al preparar JPlag, usa solo el último AC de cada usuario |
| `--jplag-jar` | Ruta al `.jar` de JPlag (o variable de entorno `JPLAG_JAR`) |
| `--run-jplag` | Ejecuta JPlag; si se omite, se reutilizan los `*_resultado.jplag` existentes |
| `--run-llm` | Evalúa con un LLM el primer AC de cada `(usuario, problema)` para estimar si fue generado por IA |
| `--llm-model` | Modelo a usar en formato `backend|modelo`, con `|` como separador (p. ej. `openai|gpt-4o`, `ollama|qwen2.5-coder:7b`). Obligatorio con `--run-llm` |
| `--backends-config` | TOML con la definición de backends (por defecto `backends.toml`) |

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

### 4. Añadir el juez LLM

```bash
export OPENAI_API_KEY=sk-...
uv run dmoj-contest-analyzer export.zip --out reporte.xlsx \
    --run-llm --llm-model 'openai|gpt-4o'
```

El `backend` (`openai`, `ollama`, `claude`, ...) se define en `backends.toml`
(parte de `backends.example.toml`). Para un modelo local basta con que el backend
apunte a la URL correcta; no hace falta API key.

**Advertencia sobre el juez LLM.** Produce una **señal de priorización, no un
veredicto**. Es **influenciable adversarialmente**: un participante puede meter
texto en un comentario para bajar su propio `llm_ai_score`. Nunca debe ser el
único motivo de una revisión. No es determinista. Cuesta ~1 llamada al modelo por
cada `(usuario, problema)` con AC.

## Despliegue web (opcional)

La interfaz web es **opcional**: el CLI sigue funcionando por sí solo. Sirve para
que un jurado suba el `.zip` desde el navegador y descargue el reporte, con
autenticación y límites de abuso.

**Requisitos:** Docker y Docker Compose (o Podman ≥ 4 con `podman compose`). Java
ya viene en la imagen; el `.jar` de JPlag se descarga al construir (ver abajo).

### Puesta en marcha

```bash
cp backends.example.toml backends.toml       # modelos, URLs y backends del juez LLM
cp .env.example .env                          # y edítalo: APP_SECRET_KEY, API keys, límites
mkdir -p data && sudo chown -R 10001:10001 data   # uid del contenedor; si no, EACCES al crear la DB

# El .jar de JPlag no está en el repo; descárgalo a vendor/ antes de construir
mkdir -p vendor
curl -fsSL -o vendor/jplag-6.3.0-jar-with-dependencies.jar \
  https://github.com/jplag/JPlag/releases/download/v6.3.0/jplag-6.3.0-jar-with-dependencies.jar
echo "5f2c21e8b88ed77134effcb3a5a3ab13d188f6a3e16d401387f7479e92db9aa2  vendor/jplag-6.3.0-jar-with-dependencies.jar" | sha256sum -c -

docker compose up -d
```

**Con Podman:** usa `podman compose up -d`. Necesita el servicio activo
(`systemctl --user start podman.socket`). En hosts con SELinux en modo
enforcing, si `podman compose build` falla con `Permission denied` leyendo un
archivo del contexto, construye aparte y levanta sin reconstruir:
`podman build -t dmoj-contest-analyzer:local . && podman compose up -d --no-build`.

Genera el secreto con `openssl rand -hex 32` y pégalo en `APP_SECRET_KEY` dentro de
`.env`. Configuración detallada (esquema de `backends.toml` y todos los parámetros
ajustables) en [`docs/configuracion-web.md`](docs/configuracion-web.md).

### Primer arranque

Sin usuarios, solo `/setup` responde. El token (de un solo uso) se imprime en
`docker compose logs` y se escribe en `./data/setup_token`. Con él creas el primer
usuario; el primer login te obliga a cambiar la contraseña.

### Gestión de usuarios

```bash
docker compose exec analyzer dmoj-manage-users add <usuario>
```

También `disable`, `enable`, `reset-password` y `list`.

### LLM local en el host (Ollama / LM Studio)

Deben escuchar en `0.0.0.0`, **no** en loopback:

- Ollama: `OLLAMA_HOST=0.0.0.0`.
- LM Studio: pestaña "Server" → activar "Serve on Local Network".

El contenedor los alcanza por `host.docker.internal` (ya configurado en
`compose.yaml`; requiere Docker ≥ 20.10 en Linux). Si el host tiene firewall,
permite la subred de Docker (`172.16.0.0/12`) hacia los puertos `11434` (Ollama) y
`1234` (LM Studio). `backends.toml` ya trae esas URLs.

### Exponer a internet

El contenedor publica solo en `127.0.0.1:8000`. Pon delante un reverse proxy que
termine TLS (Caddy, nginx, Traefik). Ver `Caddyfile.example`.

El proxy **debe** enviar `X-Forwarded-For`; la imagen corre uvicorn con
`--proxy-headers --forwarded-allow-ips 127.0.0.1` para que el rate limit de login
identifique al cliente real y no al proxy. Si cambias la dirección del proxy,
ajusta `--forwarded-allow-ips` a esa dirección — **nunca uses `*`**.

Nota: la cookie de sesión es `Secure`, así que el login solo funciona sobre HTTPS
(o `127.0.0.1`). Sobre una IP de LAN en HTTP el login falla en silencio.

### Anti-abuso (resumen)

Autenticación obligatoria, límite de tamaño de subida, rate limit y cupos por
usuario, timeout por trabajo, y retención efímera: los `.zip` se borran al
terminar y los reportes a las ~12 h. El contenedor está endurecido: no-root,
rootfs de solo lectura y sin capabilities.

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

Si se corrió el juez LLM, las columnas `llm_ai_score` y `llm_modelo` son
**columnas separadas para ordenar**: **NO suman al `score_sospecha`**, que sigue
en el rango `0-4`. El detalle (señales detectadas y la nota del modelo) va en la
hoja `LLM - Notas`.

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
- **Juez LLM**: sesgo a falsos positivos con plantillas de competitive
  programming y estudiantes prolijos; es influenciable por el contenido del
  envío (ver "Uso"). No es determinista y no es evidencia.
- El endpoint compatible con OpenAI de Anthropic (backend `claude`) es **beta**.
- En Linux, `host.docker.internal` requiere Docker ≥ 20.10.

## Desarrollo

```bash
uv sync                 # instala dependencias, incluidas las de desarrollo
uv run pytest           # tests
uv run ruff check .     # lint
```

## Licencia

MIT.
