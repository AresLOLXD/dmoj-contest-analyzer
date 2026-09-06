"""Batch LLM judge loop shared by the CLI and (later) the web worker."""

from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor

import httpx

from dmoj_contest_analyzer.llm import BackendSpec, JudgeItem, JudgeResult, judge_one


def run_judge(
    items: list[JudgeItem],
    spec: BackendSpec,
    model: str,
    *,
    max_tokens: int,
    max_source_bytes: int,
    max_workers: int = 4,
    on_call: Callable[[], bool] = lambda: True,
) -> list[JudgeResult]:
    """Judge ``items`` concurrently.

    ``on_call()`` is invoked once per item before it is scheduled; the first falsy
    return stops the loop and the remaining items are left unjudged.
    """
    allowed: list[JudgeItem] = []
    for item in items:
        if not on_call():
            break
        allowed.append(item)
    if not allowed:
        return []

    with httpx.Client(follow_redirects=False, timeout=60) as client:
        with ThreadPoolExecutor(max_workers=min(max_workers, len(allowed))) as pool:
            futures = [
                pool.submit(
                    judge_one, client, spec, model, item,
                    max_tokens=max_tokens, max_source_bytes=max_source_bytes,
                )
                for item in allowed
            ]
            return [f.result() for f in futures]
