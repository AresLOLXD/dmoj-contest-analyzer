from dmoj_contest_analyzer.submissions import parse_submissions
from dmoj_contest_analyzer.timing import analyze_timing_style


def test_rows_only_for_users_with_ac(mini_export_tree):
    rows = analyze_timing_style(parse_submissions(mini_export_tree))
    keys = {(r["usuario"], r["problema"]) for r in rows}
    # userB/p2 has no AC -> excluded
    assert ("userB", "p2") not in keys
    assert ("userA", "p1") in keys and ("userB", "p1") in keys


def test_single_attempt_flag_and_score(mini_export_tree):
    rows = analyze_timing_style(parse_submissions(mini_export_tree))
    a_p1 = next(r for r in rows if r["usuario"] == "userA" and r["problema"] == "p1")
    b_p1 = next(r for r in rows if r["usuario"] == "userB" and r["problema"] == "p1")
    assert a_p1["un_solo_intento"] is True
    assert b_p1["un_solo_intento"] is False  # AC on attempt 2
    assert a_p1["intentos_antes_de_AC"] == 0
    # userA/p1: un_solo_intento (+1); comment_ratio 0.5 > 0.15 (+1);
    # z ~= -0.71 (not < -1.0) -> no bonus. Total 2.
    assert a_p1["score_sospecha"] == 2
    # userB/p1: AC on attempt 2 (no single-attempt); no comments; z positive. Total 0.
    assert b_p1["score_sospecha"] == 0


def test_zscore_present_with_three_samples(mini_export_tree):
    rows = analyze_timing_style(parse_submissions(mini_export_tree))
    p1_rows = [r for r in rows if r["problema"] == "p1"]
    assert all(r["z_tiempo_vs_grupo"] is not None for r in p1_rows)
    p2_rows = [r for r in rows if r["problema"] == "p2"]
    assert all(r["z_tiempo_vs_grupo"] is None for r in p2_rows)
