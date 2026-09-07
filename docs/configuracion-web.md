# Configuración de la interfaz web

La interfaz web se configura por dos vías independientes:

| Superficie | Archivo | Qué controla |
| --- | --- | --- |
| Backends del juez LLM | `backends.toml` | Qué modelos y proveedores están disponibles para el juez LLM |
| Parámetros de operación | `.env` (variables de entorno) | Secretos, límites de subida, rate limit, cupos, retención, topes del juez LLM |

Ninguna de las dos es obligatoria para el análisis base: sin `backends.toml`
utilizable el juez LLM queda deshabilitado, y todas las variables de `.env`
excepto `APP_SECRET_KEY` tienen un valor por defecto.

---

## `backends.toml`

Parte de `backends.example.toml`:

```bash
cp backends.example.toml backends.toml
```

El contenedor lo monta en `/config/backends.toml` (solo lectura). Tras editarlo
hay que reiniciar el servicio: `docker compose restart analyzer`.

### Estructura

El archivo es una lista de tablas `[[backend]]`. Cada una describe un proveedor
compatible con la API de OpenAI (`/chat/completions`):

```toml
[[backend]]
id                       = "lmstudio"
label                    = "LM Studio (host)"
base_url                 = "http://host.docker.internal:1234/v1"
models                   = ["qwen2.5-coder-7b-instruct"]
supports_response_format = true
enabled                  = true
```

### Campos

| Campo | Obligatorio | Descripción |
| --- | --- | --- |
| `id` | sí | Identificador interno único. Es lo que se pasa a `--backend` en el CLI y lo que selecciona el formulario web. |
| `label` | sí | Nombre visible en el desplegable de la interfaz web. |
| `base_url` | sí | Raíz de la API compatible con OpenAI, incluido el sufijo de versión (`/v1`, `/v1beta/openai`, …). El cliente le añade `/chat/completions`. |
| `models` | sí | Lista **estática** de identificadores de modelo que se ofrecen para este backend. En la v1 no se consulta al proveedor: lo que pongas aquí es lo que aparece. |
| `api_key_env` | no | Nombre de la variable de entorno que contiene la API key. Si se define, el backend **permanece oculto** hasta que esa variable exista y no esté vacía. Omítelo para servidores locales sin autenticación. |
| `supports_response_format` | no (por defecto `true`) | `true` si el proveedor respeta `response_format: json_object`. Ponlo en `false` cuando el endpoint lo ignora (p. ej. el modo compatibilidad de Claude): el juez cae entonces a extraer el JSON del texto de la respuesta. |
| `enabled` | no (por defecto `true`) | `false` deja el backend definido pero fuera del desplegable. Útil para desactivarlo temporalmente sin borrar la configuración. |

### Agregar un backend

Añade otra tabla `[[backend]]` al final del archivo. Para un proveedor hospedado,
define `api_key_env` y exporta esa variable en `.env`:

```toml
[[backend]]
id          = "deepseek"
label       = "DeepSeek"
base_url    = "https://api.deepseek.com/v1"
api_key_env = "DEEPSEEK_API_KEY"
models      = ["deepseek-chat"]
```

```bash
# .env
DEEPSEEK_API_KEY=sk-...
```

Y pásale la variable al contenedor añadiéndola al bloque `environment:` de
`compose.yaml` (las claves listadas ahí se reenvían por nombre) o dejando que
`env_file` la inyecte automáticamente.

### Quitar un backend

Borra su tabla `[[backend]]`, o pon `enabled = false` si quieres conservarla.

---

## Variables de entorno

### Cómo se aplican

Forma recomendada — un archivo `.env` en la raíz del repo:

```bash
cp .env.example .env
# edita .env
docker compose up -d
```

`docker compose` carga `.env` de forma automática. El servicio `analyzer`
declara `env_file: .env` (marcado `required: false`, así que su ausencia no
rompe nada), de modo que **cualquier** variable del archivo llega al contenedor.

Alternativa — editar directamente el bloque `environment:` de `compose.yaml`.
Los valores ahí tienen precedencia sobre `.env`.

Tras cambiar la configuración: `docker compose up -d` (recrea el contenedor).

### Referencia

Los nombres son insensibles a mayúsculas. Los defaults salen de
`src/dmoj_contest_analyzer/web/config.py`.

#### Secretos y rutas

| Variable | Default | Descripción |
| --- | --- | --- |
| `APP_SECRET_KEY` | — (obligatorio) | Clave para firmar la cookie de sesión. Genera con `openssl rand -hex 32`. Cambiarla invalida todas las sesiones. |
| `DATA_DIR` | `/data` | Directorio de estado dentro del contenedor: `state.db`, tokens, trabajos, reportes. Se monta desde `./data` del host. |
| `BACKENDS_CONFIG` | `/config/backends.toml` | Ruta al `backends.toml` dentro del contenedor. |
| `JPLAG_JAR` | `/opt/jplag/jplag.jar` | Ruta al jar de JPlag (ya viene en la imagen). |

#### Límites de subida y archivo

| Variable | Default | Descripción |
| --- | --- | --- |
| `MAX_UPLOAD_MB` | `50` | Tamaño máximo del `.zip` subido. |
| `MAX_UNZIPPED_MB` | `300` | Tamaño máximo del contenido ya descomprimido. Protege contra zip bombs. |
| `MAX_ZIP_ENTRIES` | `20000` | Número máximo de archivos dentro del `.zip`. |
| `MAX_COMPRESSION_RATIO` | `100` | Ratio máximo descomprimido/comprimido antes de rechazar el archivo. |
| `MAX_USERS` | `400` | Máximo de carpetas de usuario en el export. |
| `MAX_PROBLEMS` | `40` | Máximo de problemas distintos en el export. |
| `MAX_SUBMISSION_BYTES` | `1000000` | Tamaño máximo de un archivo de envío individual. |

#### Rate limit, cupos y planificación

| Variable | Default | Descripción |
| --- | --- | --- |
| `RATE_LIMIT_PER_HOUR` | `5` | Trabajos que un usuario puede encolar por hora. |
| `MAX_JOBS_PER_USER` | `2` | Trabajos simultáneos en cola o en ejecución por usuario. |
| `MAX_CONCURRENT_JOBS` | `1` | Trabajos que el worker procesa a la vez (global). |
| `JOB_TIMEOUT_S` | `1800` | Tiempo máximo total de un trabajo antes de abortarlo. |
| `JPLAG_PER_INVOCATION_TIMEOUT_S` | `300` | Tiempo máximo de cada invocación de JPlag dentro de un trabajo. |
| `RETENTION_H` | `12` | Horas que se conservan los reportes antes de borrarlos. Los `.zip` se borran al terminar el trabajo. |
| `CLEANUP_EVERY_MIN` | `30` | Cada cuántos minutos corre la limpieza de trabajos vencidos. |

#### Autenticación

| Variable | Default | Descripción |
| --- | --- | --- |
| `LOGIN_MAX_ATTEMPTS` | `8` | Intentos de login fallidos por cliente antes de bloquear temporalmente. Depende de que el reverse proxy envíe `X-Forwarded-For` (ver README). |

#### Juez LLM

| Variable | Default | Descripción |
| --- | --- | --- |
| `LLM_MAX_SUBMISSIONS_PER_JOB` | `200` | Máximo de pares `(usuario, problema)` que el juez evalúa en un trabajo. |
| `LLM_MAX_CALLS_PER_DAY` | `2000` | Tope global de llamadas al modelo por día. Al alcanzarlo, el juez se salta el resto. |
| `LLM_MAX_TOKENS_PER_CALL` | `1500` | Límite de tokens de salida por llamada. |
| `LLM_REQUEST_TIMEOUT_S` | `60` | Timeout de cada petición HTTP al proveedor. |
| `LLM_THRESHOLD` | `70` | `llm_ai_score` a partir del cual se considera señal fuerte (solo informativo; no suma a `score_sospecha`). |

#### API keys de proveedores

| Variable | Default | Descripción |
| --- | --- | --- |
| `OPENAI_API_KEY` | vacío | Habilita el backend cuyo `api_key_env` sea `OPENAI_API_KEY`. |
| `ANTHROPIC_API_KEY` | vacío | Ídem para Claude. |
| `GEMINI_API_KEY` | vacío | Ídem para Gemini. |

Para un proveedor no listado, usa el nombre de variable que hayas puesto en
`api_key_env` y añádelo también al bloque `environment:` de `compose.yaml`.

---

## Ejemplos

**Subir el límite de tamaño de subida a 150 MB:**

```bash
# .env
MAX_UPLOAD_MB=150
MAX_UNZIPPED_MB=800
```

**Endurecer el rate limit (concurso pequeño, un solo jurado):**

```bash
# .env
RATE_LIMIT_PER_HOUR=2
MAX_JOBS_PER_USER=1
```

**Conservar los reportes tres días:**

```bash
# .env
RETENTION_H=72
```

**Acotar el gasto del juez LLM:**

```bash
# .env
LLM_MAX_CALLS_PER_DAY=300
LLM_MAX_SUBMISSIONS_PER_JOB=80
```

En todos los casos, aplica con `docker compose up -d`.
