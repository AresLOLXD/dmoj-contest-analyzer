from concurrent.futures import ThreadPoolExecutor

import httpx
import pytest
import respx

from dmoj_contest_analyzer.llm import BackendSpec, JudgeItem, judge_one
from dmoj_contest_analyzer.llm_run import DeadlineState, run_judge

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


@respx.mock
def test_run_judge_stops_when_on_call_false():
    respx.post("https://api.openai.com/v1/chat/completions").mock(
        return_value=_chat('{"ai_score": 5, "señales": [], "nota": ""}')
    )
    spec = BackendSpec("openai", "OpenAI", "https://api.openai.com/v1", ["gpt-4o"], True, "sk-x")
    items = [JudgeItem((f"u{i}", "p"), "p", "cpp", "x") for i in range(5)]
    calls = {"n": 0}

    def on_call():
        calls["n"] += 1
        return calls["n"] <= 2

    results = run_judge(items, spec, "gpt-4o", max_tokens=100, max_source_bytes=100,
                        max_workers=1, on_call=on_call)
    assert len(results) == 2


@respx.mock
def test_run_judge_one_failure_does_not_abort_batch():
    def _cb(request):
        if b"BOOM" in request.content:
            return httpx.Response(500, headers={"Retry-After": "0"})
        return _chat('{"ai_score": 20, "señales": [], "nota": ""}')

    respx.post("https://api.openai.com/v1/chat/completions").mock(side_effect=_cb)
    spec = BackendSpec("openai", "OpenAI", "https://api.openai.com/v1", ["gpt-4o"], True, "sk-x")
    items = [
        JudgeItem(("u0", "p"), "p", "cpp", "ok0"),
        JudgeItem(("u1", "p"), "p", "cpp", "BOOM"),
        JudgeItem(("u2", "p"), "p", "cpp", "ok2"),
    ]
    results = run_judge(items, spec, "gpt-4o", max_tokens=100, max_source_bytes=100,
                        max_workers=1)
    by_key = {r.key: r for r in results}
    assert len(results) == 3
    assert by_key[("u1", "p")].ai_score is None
    assert by_key[("u0", "p")].ai_score == 20
    assert by_key[("u2", "p")].ai_score == 20


@respx.mock
def test_run_judge_uses_external_executor_without_closing_it():
    respx.post("https://api.openai.com/v1/chat/completions").mock(
        return_value=_chat('{"ai_score": 7, "señales": [], "nota": ""}')
    )
    spec = BackendSpec("openai", "OpenAI", "https://api.openai.com/v1", ["gpt-4o"], True, "sk-x")
    items = [JudgeItem((f"u{i}", "p"), "p", "cpp", "x") for i in range(3)]
    pool = ThreadPoolExecutor(max_workers=2)
    try:
        results = run_judge(items, spec, "gpt-4o", max_tokens=100, max_source_bytes=100,
                            executor=pool)
        assert len(results) == 3
        # Still usable: the pool was not shut down by run_judge.
        assert pool.submit(lambda: 42).result() == 42
    finally:
        pool.shutdown(wait=True)


@respx.mock
def test_run_judge_marks_failed_calls_with_error():
    respx.post("https://api.openai.com/v1/chat/completions").mock(
        return_value=httpx.Response(500, headers={"Retry-After": "0"})
    )
    spec = BackendSpec("openai", "OpenAI", "https://api.openai.com/v1", ["gpt-4o"], True, "sk-x")
    items = [JudgeItem(("u0", "p"), "p", "cpp", "x")]
    results = run_judge(items, spec, "gpt-4o", max_tokens=100, max_source_bytes=100,
                        max_workers=1)
    assert results[0].ai_score is None
    assert results[0].error is not None


@respx.mock
def test_run_judge_parse_failure_leaves_error_unset():
    respx.post("https://api.openai.com/v1/chat/completions").mock(return_value=_chat("not json"))
    spec = BackendSpec("openai", "OpenAI", "https://api.openai.com/v1", ["gpt-4o"], True, "sk-x")
    items = [JudgeItem(("u0", "p"), "p", "cpp", "x")]
    results = run_judge(items, spec, "gpt-4o", max_tokens=100, max_source_bytes=100,
                        max_workers=1)
    assert results[0].ai_score is None
    assert results[0].error is None


@respx.mock
def test_run_judge_total_deadline_cancels_pending():
    def _slow(request):
        import time
        time.sleep(0.4)
        return _chat('{"ai_score": 3, "señales": [], "nota": ""}')

    respx.post("https://api.openai.com/v1/chat/completions").mock(side_effect=_slow)
    spec = BackendSpec("openai", "OpenAI", "https://api.openai.com/v1", ["gpt-4o"], True, "sk-x")
    items = [JudgeItem((f"u{i}", "p"), "p", "cpp", "x") for i in range(4)]
    state = DeadlineState()
    results = run_judge(items, spec, "gpt-4o", max_tokens=100, max_source_bytes=100,
                        max_workers=1, total_deadline_s=0.1, deadline_state=state)
    assert len(results) == 4
    assert any(r.ai_score is None for r in results)
    assert state.hit is True
