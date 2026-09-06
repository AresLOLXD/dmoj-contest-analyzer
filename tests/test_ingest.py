import zipfile
from pathlib import Path

import pytest

from dmoj_contest_analyzer.ingest import ExportStructureError, resolve_export
from dmoj_contest_analyzer.submissions import parse_submissions


def test_resolve_plain_folder(mini_export_tree):
    with resolve_export(mini_export_tree) as root:
        assert len(parse_submissions(root)) == 6


def test_resolve_flat_zip(flat_zip):
    with resolve_export(flat_zip) as root:
        assert root.is_dir()
        assert len(parse_submissions(root)) == 6


def test_resolve_wrapped_zip(wrapped_zip):
    with resolve_export(wrapped_zip) as root:
        assert root.name == "concurso-x"
        assert len(parse_submissions(root)) == 6


def test_temp_dir_cleaned_up(flat_zip):
    with resolve_export(flat_zip) as root:
        saved = root
    assert not saved.exists()


def test_missing_path_raises():
    with pytest.raises(FileNotFoundError):
        with resolve_export(Path("/no/such/path.zip")):
            pass


def test_unrecognizable_zip_raises(tmp_path):
    bad = tmp_path / "bad.zip"
    with zipfile.ZipFile(bad, "w") as zf:
        zf.writestr("readme.txt", "nothing useful here")
    with pytest.raises(ExportStructureError):
        with resolve_export(bad):
            pass
