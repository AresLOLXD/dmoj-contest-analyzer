"""Web-layer settings loaded from environment variables.

All env vars used by the web layer live here as typed fields with the
defaults from the design spec. `get_settings` is the FastAPI dependency.
"""

from __future__ import annotations

import functools
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="", case_sensitive=False, extra="ignore"
    )

    # Secrets and paths
    app_secret_key: str
    data_dir: Path = Path("/data")
    backends_config: Path = Path("/config/backends.toml")
    jplag_jar: Path = Path("/opt/jplag/jplag.jar")

    # Upload / archive limits
    max_upload_mb: int = 50
    max_unzipped_mb: int = 300
    max_zip_entries: int = 20000
    max_compression_ratio: int = 100
    max_users: int = 400
    max_problems: int = 40
    max_submission_bytes: int = 1_000_000

    # Job scheduling / rate limiting
    rate_limit_per_hour: int = 5
    max_jobs_per_user: int = 2
    max_concurrent_jobs: int = 1
    job_timeout_s: float = 1800
    jplag_per_invocation_timeout_s: int = 300
    retention_h: int = 12
    cleanup_every_min: int = 30

    # Auth
    login_max_attempts: int = 8

    # LLM judge
    llm_max_submissions_per_job: int = 200
    llm_max_calls_per_day: int = 2000
    llm_max_tokens_per_call: int = 1500
    llm_request_timeout_s: float = 60
    llm_threshold: int = 70

    # Optional provider API keys
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    gemini_api_key: str | None = None

    def db_path(self) -> Path:
        return self.data_dir / "state.db"


@functools.lru_cache
def get_settings() -> Settings:
    return Settings()
