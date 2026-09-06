from datetime import datetime

from dmoj_contest_analyzer.submissions import FNAME_RE, parse_submissions


def test_submission_rel_path_is_relative(mini_export_tree):
    subs = parse_submissions(mini_export_tree)
    s = next(s for s in subs if s.username == "userA" and s.problem == "p1")
    assert s.rel_path == "userA/p1/1_userA_2026-01-01_10-00-00_AC.cpp"
    assert not s.rel_path.startswith("/")


def test_fname_re_matches_valid():
    m = FNAME_RE.match("3_some_user_2026-01-02_14-30-45_AC.cpp")
    assert m and m.group("user") == "some_user" and m.group("result") == "AC"
    assert m.group("attempt") == "3" and m.group("ext") == "cpp"


def test_fname_re_rejects_invalid():
    assert FNAME_RE.match("notes.txt") is None
    assert FNAME_RE.match("1_user_2026-01-02_AC.cpp") is None


def test_parse_submissions_reads_tree(mini_export_tree):
    subs = parse_submissions(mini_export_tree)
    assert len(subs) == 6
    a_p1 = next(s for s in subs if s.username == "userA" and s.problem == "p1")
    assert a_p1.result == "AC" and a_p1.ext == "cpp"
    assert a_p1.dt == datetime(2026, 1, 1, 10, 0, 0)


def test_style_stats_counts_comments(mini_export_tree):
    subs = parse_submissions(mini_export_tree)
    c_p1 = next(s for s in subs if s.username == "userC" and s.problem == "p1")
    stats = c_p1.style_stats()
    assert stats["n_lines"] == 5
    assert stats["comment_ratio"] == 3 / 5
