import json
import zipfile
from pathlib import Path

import pytest

pytest_plugins = ["tests.web_conftest"]

# One AC per user on p1 so z-score has >2 samples; p2 has a retry case.
_FILES = {
    "userA/p1/1_userA_2026-01-01_10-00-00_AC.cpp": "// solA\nint main(){return 0;}\n",
    "userB/p1/1_userB_2026-01-01_09-00-00_WA.cpp": "int main(){return 1;}\n",
    "userB/p1/2_userB_2026-01-01_09-30-00_AC.cpp": "int main(){return 0;}\n",
    "userC/p1/1_userC_2026-01-01_08-00-00_AC.cpp": (
        "// comment 1\n// comment 2\n// comment 3\nint really_long_identifier_name;\nint main(){return 0;}\n"  # noqa: E501
    ),
    "userA/p2/1_userA_2026-01-01_11-00-00_AC.py": "# c\nprint(1)\n",
    "userB/p2/1_userB_2026-01-01_12-00-00_WA.py": "print(2)\n",
}


def _materialize(base: Path) -> Path:
    for rel, content in _FILES.items():
        p = base / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
    return base


@pytest.fixture(scope="session")
def mini_export_tree(tmp_path_factory) -> Path:
    return _materialize(tmp_path_factory.mktemp("mini_export"))


@pytest.fixture(scope="session")
def flat_zip(tmp_path_factory, mini_export_tree) -> Path:
    zpath = tmp_path_factory.mktemp("flat") / "export.zip"
    with zipfile.ZipFile(zpath, "w") as zf:
        for f in sorted(mini_export_tree.rglob("*")):
            if f.is_file():
                zf.write(f, f.relative_to(mini_export_tree).as_posix())
    return zpath


@pytest.fixture(scope="session")
def wrapped_zip(tmp_path_factory, mini_export_tree) -> Path:
    zpath = tmp_path_factory.mktemp("wrapped") / "export.zip"
    with zipfile.ZipFile(zpath, "w") as zf:
        for f in sorted(mini_export_tree.rglob("*")):
            if f.is_file():
                arc = Path("concurso-x") / f.relative_to(mini_export_tree)
                zf.write(f, arc.as_posix())
    return zpath


@pytest.fixture(scope="session")
def sample_jplag_file(tmp_path_factory) -> Path:
    """Un reporte con el formato de la serie 6.x de JPlag."""
    mappings = {"submissionIds": {"userA.cpp": "userA.cpp", "userC.cpp": "userC.cpp"}}
    run_info = {"version": {"major": 6, "minor": 3, "patch": 0}}
    hit = {
        "firstSubmissionId": "userA.cpp",
        "secondSubmissionId": "userC.cpp",
        "similarities": {"AVG": 0.82, "MAX": 0.9, "MAXIMUM_LENGTH": 42.0, "LONGEST_MATCH": 20.0},
    }
    zero = {
        "firstSubmissionId": "userA.cpp",
        "secondSubmissionId": "userB.cpp",
        "similarities": {"AVG": 0.0, "MAX": 0.0, "MAXIMUM_LENGTH": 10.0, "LONGEST_MATCH": 0.0},
    }
    zpath = tmp_path_factory.mktemp("jplag") / "cpp_resultado.jplag"
    with zipfile.ZipFile(zpath, "w") as zf:
        zf.writestr("submissionMappings.json", json.dumps(mappings))
        zf.writestr("runInformation.json", json.dumps(run_info))
        zf.writestr("comparisons/userA.cpp-userC.cpp.json", json.dumps(hit))
        zf.writestr("comparisons/userA.cpp-userB.cpp.json", json.dumps(zero))
    return zpath
