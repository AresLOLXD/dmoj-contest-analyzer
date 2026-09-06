import pytest

from dmoj_contest_analyzer.analysis import AnalysisOptions, NoSubmissionsError, run_analysis
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


def test_run_analysis_no_submissions_raises(tmp_path):
    empty = tmp_path / "empty"
    (empty / "not-a-user").mkdir(parents=True)
    with pytest.raises(NoSubmissionsError):
        run_analysis(empty, tmp_path / "r.xlsx", AnalysisOptions())
