# tests/test_jplag_timeout.py
import sys
from pathlib import Path

import pytest

from dmoj_contest_analyzer.jplag import JplagTimeout, run_jplag


def _hang_script(tmp_path: Path) -> Path:
    p = tmp_path / "hang.py"
    p.write_text("import time\nimport sys\ntime.sleep(60)\n")
    return p


def test_run_jplag_kills_on_timeout(tmp_path, monkeypatch):
    # Arrange: a counts dict with one (problem, lang) pair of 2 users.
    (tmp_path / "p1" / "cpp").mkdir(parents=True)
    counts = {("p1", "cpp"): 2}
    hang = _hang_script(tmp_path)

    # Force the command to be `python hang.py` instead of `java -jar ...`.
    monkeypatch.setattr(
        "dmoj_contest_analyzer.jplag._jplag_cmd",
        lambda in_dir, lang, result_name, jar: [sys.executable, str(hang)],
    )
    seen = []
    with pytest.raises(JplagTimeout):
        run_jplag(tmp_path, counts, "unused.jar", timeout=1,
                  on_subprocess=seen.append)
    assert seen, "on_subprocess should have been called with the Popen handle"
    proc = seen[0]
    assert proc.poll() is not None, "process must be dead after timeout"
