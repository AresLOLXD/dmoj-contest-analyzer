from pathlib import Path

import pytest
from pydantic import ValidationError

from dmoj_contest_analyzer.web.config import Settings, get_settings


def test_defaults_and_required(tmp_path):
    s = Settings(app_secret_key="x", data_dir=tmp_path)
    assert s.max_upload_mb == 50
    assert s.max_unzipped_mb == 300
    assert s.max_zip_entries == 20000
    assert s.max_compression_ratio == 100
    assert s.max_users == 400
    assert s.max_problems == 40
    assert s.max_submission_bytes == 1000000
    assert s.rate_limit_per_hour == 5
    assert s.max_jobs_per_user == 2
    assert s.max_concurrent_jobs == 2
    assert s.job_timeout_s == 1800
    assert s.jplag_per_invocation_timeout_s == 300
    assert s.retention_h == 12
    assert s.cleanup_every_min == 30
    assert s.login_max_attempts == 8
    assert s.llm_max_submissions_per_job == 200
    assert s.llm_max_calls_per_day == 2000
    assert s.llm_max_tokens_per_call == 1500
    assert s.llm_request_timeout_s == 120
    assert s.llm_threshold == 70
    assert s.data_dir == tmp_path
    assert s.backends_config == Path("/config/backends.toml")
    assert s.jplag_jar == Path("/opt/jplag/jplag.jar")
    assert s.db_path() == tmp_path / "state.db"
    assert s.openai_api_key is None


def test_required_missing(monkeypatch):
    monkeypatch.delenv("APP_SECRET_KEY", raising=False)
    with pytest.raises(ValidationError):
        Settings()


def test_env_override(monkeypatch, tmp_path):
    monkeypatch.setenv("MAX_UPLOAD_MB", "7")
    monkeypatch.setenv("APP_SECRET_KEY", "x")
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    s = Settings()
    assert s.max_upload_mb == 7
    assert s.app_secret_key == "x"


def test_new_scheduling_and_llm_defaults(tmp_path):
    s = Settings(app_secret_key="x", data_dir=tmp_path)
    assert s.max_concurrent_jobs == 2
    assert s.llm_concurrency == 2
    assert s.llm_judge_total_timeout_s == 1800
    assert s.awaiting_upload_timeout_s == 3600


def test_llm_concurrency_env_override(monkeypatch, tmp_path):
    monkeypatch.setenv("APP_SECRET_KEY", "x")
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("LLM_CONCURRENCY", "1")
    assert Settings().llm_concurrency == 1


def test_float_timeout():
    s = Settings(app_secret_key="x", job_timeout_s=0.01, llm_request_timeout_s=0.01)
    assert s.job_timeout_s == 0.01


def test_get_settings_cached(monkeypatch):
    monkeypatch.setenv("APP_SECRET_KEY", "x")
    get_settings.cache_clear()
    assert get_settings() is get_settings()
