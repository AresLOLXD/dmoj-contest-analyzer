"""Batch LLM judge loop shared by the CLI and the web worker."""

from collections.abc import Callable
from concurrent.futures import Executor, ThreadPoolExecutor
from concurrent.futures import wait as futures_wait

import httpx

from dmoj_contest_analyzer.llm import BackendSpec, JudgeItem, JudgeResult, judge_one


class DeadlineState:
    def __init__(self) -> None:
        self.hit = False


def run_judge(
    items: list[JudgeItem],
    spec: BackendSpec,
    model: str,
    *,
    max_tokens: int,
    max_source_bytes: int,
    max_workers: int = 4,
    on_call: Callable[[], bool] = lambda: True,
    executor: Executor | None = None,
    total_deadline_s: float | None = None,
    deadline_state: DeadlineState | None = None,
) -> list[JudgeResult]:
    """Judge ``items`` concurrently.

    ``on_call()`` is invoked once per item before it is scheduled; the first
    falsy return stops the loop and the remaining items are left unjudged.

    If ``executor`` is given it is used and never shut down (a process-wide
    pool owned by the caller); otherwise a local pool is created and closed.
    ``total_deadline_s`` bounds the result-collection phase: futures still
    running are cancelled and their item gets ``JudgeResult(key, None)``; when
    that happens and ``deadline_state`` was passed, ``deadline_state.hit`` is
    set.
    """
    allowed: list[JudgeItem] = []
    for item in items:
        if not on_call():
            break
        allowed.append(item)
    if not allowed:
        return []

    own_pool = executor is None
    pool: Executor = executor or ThreadPoolExecutor(
        max_workers=min(max_workers, len(allowed))
    )
    client = httpx.Client(follow_redirects=False, timeout=60)
    try:
        futures = {
            pool.submit(
                judge_one, client, spec, model, item,
                max_tokens=max_tokens, max_source_bytes=max_source_bytes,
            ): item
            for item in allowed
        }
        done, not_done = futures_wait(futures, timeout=total_deadline_s)
        results: list[JudgeResult] = []
        if not_done:
            if deadline_state is not None:
                deadline_state.hit = True
            for future in not_done:
                future.cancel()
                results.append(JudgeResult(futures[future].key, None))
        for future in done:
            try:
                results.append(future.result())
            except Exception:
                results.append(JudgeResult(futures[future].key, None))
        return results
    finally:
        client.close()
        if own_pool:
            pool.shutdown(wait=True)
