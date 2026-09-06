"""LLM backend registry: load ``backends.toml``, resolve ``model_ref`` values, redact secrets.

The judging logic (``judge_one``) lives in a later task; this module only covers the
registry: parsing, visibility rules, resolution, and secret redaction.
"""

import os
import re
import tomllib
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

# model_ref format is "<backend>|<model>" -- separator is "|", never ":", because
# Ollama model names contain ":" (e.g. "qwen2.5-coder:7b").
MODEL_REF_RE = re.compile(r"^[a-z0-9_-]+\|[A-Za-z0-9._:-]{1,128}$")

_SECRET_RE = re.compile(r"(sk-ant-[A-Za-z0-9_-]+|sk-[A-Za-z0-9_-]+|AIza[A-Za-z0-9_-]+)")


def redact(text: str) -> str:
    """Replace API-key-looking substrings with a placeholder."""
    return _SECRET_RE.sub("«redacted»", text or "")


@dataclass
class BackendSpec:
    id: str
    label: str
    base_url: str
    models: list[str]
    supports_response_format: bool
    api_key: str | None = None


def load_backends(path: Path, env: Mapping[str, str] | None = None) -> list[BackendSpec]:
    """Load backend definitions from a TOML file and apply visibility rules.

    Rules: drop ``enabled = false`` entries; drop entries whose ``api_key_env`` is set
    but empty/missing in ``env``; for kept hosted entries set ``api_key`` from the env value.
    """
    env = os.environ if env is None else env
    raw = tomllib.loads(Path(path).read_text())
    out: list[BackendSpec] = []
    for entry in raw.get("backend", []):
        if not entry.get("enabled", True):
            continue
        key: str | None = None
        key_env = entry.get("api_key_env")
        if key_env is not None:
            key = env.get(key_env) or None
            if not key:
                continue
        out.append(
            BackendSpec(
                id=entry["id"],
                label=entry["label"],
                base_url=entry["base_url"].rstrip("/"),
                models=list(entry["models"]),
                supports_response_format=bool(entry.get("supports_response_format", True)),
                api_key=key,
            )
        )
    return out


def resolve(model_ref: str, backends: list[BackendSpec]) -> tuple[BackendSpec, str]:
    """Resolve ``"<backend>|<model>"`` to a visible backend. Fails closed with ``ValueError``."""
    if not MODEL_REF_RE.match(model_ref or ""):
        raise ValueError(f"model_ref inválido: {model_ref!r}")
    backend_id, model = model_ref.split("|", 1)
    spec = next((b for b in backends if b.id == backend_id), None)
    if spec is None:
        raise ValueError(f"backend no disponible: {backend_id!r}")
    if model not in spec.models:
        raise ValueError(f"modelo no permitido para {backend_id}: {model!r}")
    return spec, model
