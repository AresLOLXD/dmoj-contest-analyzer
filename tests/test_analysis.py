import httpx
import pytest
import respx

from dmoj_contest_analyzer.analysis import AnalysisOptions, NoSubmissionsError, run_analysis
from dmoj_contest_analyzer.llm import BackendSpec
from tests.test_cli_golden import read_xlsx_values


def test_run_analysis_matches_cli_output(mini_export_tree, tmp_path):
    out = tmp_path / "r.xlsx"
    msgs = []
    data = run_analysis(mini_export_tree, out, AnalysisOptions(), on_progress=msgs.append)
    assert data.n_subs == 6 and data.n_users == 3 and data.n_problems == 2
    values = read_xlsx_values(out)
    ts = {(r["usuario"], r["problema"]): r for r in values["Timing y Estilo"]}
    assert ts[("userC", "p1")]["score_sospecha"] == 2
    assert any("envío" in m or "envio" in m for m in msgs)


def test_run_analysis_emits_finer_progress(mini_export_tree, tmp_path):
    out = tmp_path / "r.xlsx"
    msgs: list[str] = []
    run_analysis(mini_export_tree, out, AnalysisOptions(), on_progress=msgs.append)
    assert any(m.startswith("timing y estilo: ") for m in msgs)


@respx.mock
def test_run_analysis_runs_llm_judge(mini_export_tree, tmp_path):
    respx.post("https://api.openai.com/v1/chat/completions").mock(
        return_value=httpx.Response(200, json={"choices": [{"message": {"content":
            '{"ai_score": 77, "señales": ["comentarios tutorial"], "nota": "revisar"}'}}]})
    )
    spec = BackendSpec("openai", "OpenAI", "https://api.openai.com/v1", ["gpt-4o"], True, "sk-x")
    out = tmp_path / "r.xlsx"
    data = run_analysis(mini_export_tree, out, AnalysisOptions(), llm=(spec, "gpt-4o"))
    assert data.llm_model == "openai|gpt-4o"
    assert data.llm_rows and all(r["ai_score"] == 77 for r in data.llm_rows)
    assert all(r["llm_ai_score"] == 77 for r in data.main_rows)
    assert all(r["llm_modelo"] == "openai|gpt-4o" for r in data.main_rows)


def test_run_analysis_forwards_jplag_timeout(mini_export_tree, tmp_path, monkeypatch):
    captured = {}

    def fake_run_jplag(jplag_out, counts, jar, *, timeout=None, on_progress, on_subprocess):
        captured["timeout"] = timeout
        return []

    monkeypatch.setattr("dmoj_contest_analyzer.analysis.run_jplag", fake_run_jplag)
    opts = AnalysisOptions(
        jplag_out=tmp_path / "j", run_jplag=True, jplag_jar="x", jplag_timeout_s=42,
    )
    run_analysis(mini_export_tree, tmp_path / "r.xlsx", opts)
    assert captured["timeout"] == 42


def test_run_analysis_no_submissions_raises(tmp_path):
    empty = tmp_path / "empty"
    (empty / "not-a-user").mkdir(parents=True)
    with pytest.raises(NoSubmissionsError):
        run_analysis(empty, tmp_path / "r.xlsx", AnalysisOptions())
