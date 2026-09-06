import json

from dmoj_contest_analyzer.jplag import (
    extract_comparisons_from_json,
    merge_jplag_into_main,
    parse_jplag_result,
)


def test_extract_comparisons_known_shape():
    data = json.loads(
        '{"comparisons":[{"firstSubmissionId":"a.cpp","secondSubmissionId":"b.cpp",'
        '"similarities":{"AVG":0.5,"MAX":0.75}}]}'
    )
    got = extract_comparisons_from_json(data)
    assert got == [("a.cpp", "b.cpp", 0.75)]


def test_parse_jplag_result_reads_zip(sample_jplag_file):
    rows = parse_jplag_result("p1", "cpp", sample_jplag_file)
    assert len(rows) == 1
    r = rows[0]
    assert {r["usuario_a"], r["usuario_b"]} == {"userA", "userC"}
    assert r["similitud"] == 90.0


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
