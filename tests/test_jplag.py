import json
import zipfile

from dmoj_contest_analyzer.jplag import merge_jplag_into_main, parse_jplag_result


def test_parse_jplag_result_reads_zip(sample_jplag_file):
    rows = parse_jplag_result("p1", "cpp", sample_jplag_file)
    assert len(rows) == 1
    r = rows[0]
    assert {r["usuario_a"], r["usuario_b"]} == {"userA", "userC"}
    assert r["similitud"] == 90.0


def test_parse_jplag_result_skips_zero_similarity(sample_jplag_file):
    rows = parse_jplag_result("p1", "cpp", sample_jplag_file)
    assert all(r["similitud"] > 0 for r in rows)
    assert not any({r["usuario_a"], r["usuario_b"]} == {"userA", "userB"} for r in rows)


def test_parse_jplag_result_reports_version(sample_jplag_file, capsys):
    parse_jplag_result("p1", "cpp", sample_jplag_file, on_progress=print)
    assert "JPlag 6.3.0" in capsys.readouterr().out


def test_parse_jplag_result_wrong_format_returns_empty(tmp_path):
    bad = tmp_path / "cpp_resultado.jplag"
    with zipfile.ZipFile(bad, "w") as zf:
        zf.writestr("overview.json", json.dumps({"comparisons": []}))
    assert parse_jplag_result("p1", "cpp", bad) == []


def test_merge_bumps_score_when_similarity_high():
    main_rows = [
        {"usuario": "userA", "problema": "p1", "score_sospecha": 1,
         "jplag_max_similitud": None, "jplag_similar_con": None},
    ]
    jplag_rows = [
        {"problema": "p1", "lenguaje": "cpp", "usuario_a": "userA",
         "usuario_b": "userC", "similitud": 90.0},
    ]
    merge_jplag_into_main(main_rows, jplag_rows)
    assert main_rows[0]["jplag_max_similitud"] == 90.0
    assert main_rows[0]["jplag_similar_con"] == "userC"
    assert main_rows[0]["score_sospecha"] == 2
