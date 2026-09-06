from pathlib import Path

import pytest

from dmoj_contest_analyzer.llm import load_backends, redact, resolve

TOML = """
[[backend]]
id = "ollama"
label = "Ollama (host)"
base_url = "http://h:11434/v1"
models = ["qwen2.5-coder:7b"]
supports_response_format = true
enabled = true

[[backend]]
id = "openai"
label = "OpenAI"
base_url = "https://api.openai.com/v1"
api_key_env = "OPENAI_API_KEY"
models = ["gpt-4o"]
supports_response_format = true
enabled = true

[[backend]]
id = "claude"
label = "Claude"
base_url = "https://api.anthropic.com/v1"
api_key_env = "ANTHROPIC_API_KEY"
models = ["claude-sonnet-5"]
supports_response_format = false
enabled = false
"""


def _toml(tmp_path):
    p = tmp_path / "backends.toml"
    p.write_text(TOML)
    return p


def test_hosted_backend_hidden_without_key(tmp_path):
    b = load_backends(_toml(tmp_path), env={})
    assert [x.id for x in b] == ["ollama"]


def test_hosted_backend_visible_with_key(tmp_path):
    b = load_backends(_toml(tmp_path), env={"OPENAI_API_KEY": "sk-x"})
    ids = [x.id for x in b]
    assert ids == ["ollama", "openai"]
    assert next(x for x in b if x.id == "openai").api_key == "sk-x"
    assert "claude" not in ids  # enabled = false


def test_resolve_ok_with_colon_in_model(tmp_path):
    b = load_backends(_toml(tmp_path), env={})
    spec, model = resolve("ollama|qwen2.5-coder:7b", b)
    assert spec.id == "ollama" and model == "qwen2.5-coder:7b"


@pytest.mark.parametrize("ref", ["ollama|nope", "ghost|x", "ollama:qwen2.5-coder:7b", "bad ref"])
def test_resolve_fails_closed(tmp_path, ref):
    b = load_backends(_toml(tmp_path), env={})
    with pytest.raises(ValueError):
        resolve(ref, b)


def test_redact():
    assert "sk-ant-abc123" not in redact("key sk-ant-abc123 end")
    assert "AIzaSecret" not in redact("AIzaSecret")


def test_example_toml_parses():
    path = Path(__file__).resolve().parent.parent / "backends.example.toml"
    b = load_backends(path, env={})
    assert any(x.id == "ollama" for x in b)
