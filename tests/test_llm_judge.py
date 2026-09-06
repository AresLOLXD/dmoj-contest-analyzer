import httpx
import pytest
import respx

from dmoj_contest_analyzer.llm import BackendSpec, JudgeItem, judge_one

SPEC = BackendSpec("openai", "OpenAI", "https://api.openai.com/v1", ["gpt-4o"], True, "sk-x")
ITEM = JudgeItem(("u", "p"), "p", "cpp", "int main(){}")


def _chat(payload):
    return httpx.Response(200, json={"choices": [{"message": {"content": payload}}]})


@respx.mock
def test_judge_one_parses_valid_json():
    respx.post("https://api.openai.com/v1/chat/completions").mock(
        return_value=_chat('{"ai_score": 82, "señales": ["comentarios tutorial"], "nota": "x"}')
    )
    with httpx.Client() as c:
        r = judge_one(c, SPEC, "gpt-4o", ITEM, max_tokens=1500, max_source_bytes=1000)
    assert r.ai_score == 82 and r.signals == ["comentarios tutorial"]


@respx.mock
@pytest.mark.parametrize("body", ['not json', '{"ai_score": 150}', '{"ai_score": "80"}', '{}'])
def test_judge_one_bad_output_is_none(body):
    respx.post("https://api.openai.com/v1/chat/completions").mock(return_value=_chat(body))
    with httpx.Client() as c:
        r = judge_one(c, SPEC, "gpt-4o", ITEM, max_tokens=1500, max_source_bytes=1000)
    assert r.ai_score is None


@respx.mock
def test_judge_one_retries_on_429():
    route = respx.post("https://api.openai.com/v1/chat/completions")
    route.side_effect = [
        httpx.Response(429, headers={"Retry-After": "0"}),
        _chat('{"ai_score": 10, "señales": [], "nota": ""}'),
    ]
    with httpx.Client() as c:
        r = judge_one(c, SPEC, "gpt-4o", ITEM, max_tokens=1500, max_source_bytes=1000)
    assert r.ai_score == 10 and route.call_count == 2


@respx.mock
def test_judge_one_truncates_source():
    captured = {}

    def _cb(request):
        captured["body"] = request.content.decode()
        return _chat('{"ai_score": 1, "señales": [], "nota": ""}')

    respx.post("https://api.openai.com/v1/chat/completions").mock(side_effect=_cb)
    big = JudgeItem(("u", "p"), "p", "cpp", "x" * 5000)
    with httpx.Client() as c:
        judge_one(c, SPEC, "gpt-4o", big, max_tokens=1500, max_source_bytes=100)
    assert captured["body"].count("x") <= 120
