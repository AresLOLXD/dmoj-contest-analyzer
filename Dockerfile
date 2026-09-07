# syntax=docker/dockerfile:1
# BuildKit is required (cache mounts, bind mounts, --chmod on COPY).

# --- JRE 21 (Debian bookworm has NO openjdk-21; JPlag 6.3.0 needs Java 21) ---
FROM eclipse-temurin:21-jre-jammy AS jre

# --- build ---
# renovate: datasource=docker depName=python versioning=docker
FROM python:3.12-slim@sha256:78387bc3881b8273120a12ebe6c1ab22b018ccc2c9adf565ae1ac9b536e184ea AS build
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
WORKDIR /app
# Dependency layer: resolves + installs only third-party deps, cached until the
# lockfile or pyproject changes.
# COPY (not --mount=type=bind) so the build works on every builder: rootless
# podman under SELinux cannot read a bind-mounted context file when the build
# runs via the podman API service (`podman compose` -> docker-compose provider),
# and fails the step with "Permission denied" reading pyproject.toml.
COPY uv.lock pyproject.toml ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --extra web --no-install-project
COPY . /app
# Project layer: installs the package itself into the venv (non-editable copy).
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --extra web --no-editable

# --- runtime ---
# Same digest pin as `build`: the copied .venv breaks if the interpreter differs.
# renovate: datasource=docker depName=python versioning=docker
FROM python:3.12-slim@sha256:78387bc3881b8273120a12ebe6c1ab22b018ccc2c9adf565ae1ac9b536e184ea
COPY --from=jre /opt/java/openjdk /opt/java/openjdk
ENV JAVA_HOME=/opt/java/openjdk \
    PATH="/opt/java/openjdk/bin:/app/.venv/bin:$PATH" \
    HOME=/tmp XDG_CACHE_HOME=/tmp/.cache \
    JAVA_TOOL_OPTIONS="-Djava.io.tmpdir=/tmp -Djava.util.prefs.userRoot=/tmp/.java -XX:MaxRAMPercentage=45 -XX:ActiveProcessorCount=1" \
    JPLAG_JAR=/opt/jplag/jplag.jar
# Vendored jar copied BEFORE the venv layer so a code change does not re-copy 83 MB.
# The package is installed non-editable into /app/.venv, so no source tree is needed.
# NOTE: no `--chmod` on the COPY -- BuildKit applies it to the auto-created parent
# dir too, leaving /opt/jplag at 0644 (no execute bit), so a non-root process gets
# EACCES stat-ing the jar. Pre-create the dir 0755; the vendored jar is 0644.
RUN mkdir -p /opt/jplag && chmod 0755 /opt/jplag
COPY vendor/jplag-6.3.0-jar-with-dependencies.jar /opt/jplag/jplag.jar
COPY --from=build /app/.venv /app/.venv
# The `.keep` file makes /data non-empty so a fresh Docker named volume mounted
# here inherits appuser ownership (an empty dir yields a root-owned volume that
# the non-root process cannot write, and /healthz then 503s forever).
RUN useradd -u 10001 -m appuser \
    && mkdir -p /data && touch /data/.keep && chown -R 10001:10001 /data
USER 10001:10001
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=25s --retries=3 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/healthz').status==200 else 1)"
# --proxy-headers + a pinned --forwarded-allow-ips are required so the per-IP login
# throttle keys on the real client, not the loopback reverse proxy. Never use "*".
CMD ["uvicorn", "dmoj_contest_analyzer.web.app:create_app", "--factory", \
     "--host", "0.0.0.0", "--port", "8000", "--workers", "1", \
     "--proxy-headers", "--forwarded-allow-ips", "127.0.0.1"]
