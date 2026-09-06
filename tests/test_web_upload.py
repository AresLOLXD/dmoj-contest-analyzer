import asyncio
import io
import zipfile

import pytest

from dmoj_contest_analyzer.web.upload import (
    UploadRejected,
    stream_to_file,
    validate_and_extract,
)
from tests.web_conftest import make_zip, zip_bomb

GOOD = {
    "userA/p1/1_userA_2026-01-01_10-00-00_AC.cpp": b"int main(){}\n",
    "userB/p1/1_userB_2026-01-01_09-00-00_AC.cpp": b"int main(){}\n",
    "userC/p1/1_userC_2026-01-01_08-00-00_AC.cpp": b"int main(){}\n",
}


def _write(tmp_path, data, name="up.zip"):
    p = tmp_path / name
    p.write_bytes(data)
    return p


def test_good_zip_ok(tmp_path, settings):
    zp = _write(tmp_path, make_zip(GOOD))
    n_users, n_problems = validate_and_extract(zp, tmp_path / "work", settings)
    assert n_users == 3 and n_problems == 1


def test_wrapper_dir_descended(tmp_path, settings):
    wrapped = {f"export/{k}": v for k, v in GOOD.items()}
    zp = _write(tmp_path, make_zip(wrapped))
    n_users, n_problems = validate_and_extract(zp, tmp_path / "work", settings)
    assert n_users == 3 and n_problems == 1


def test_not_a_zip(tmp_path, settings):
    zp = _write(tmp_path, b"not a zip at all")
    with pytest.raises(UploadRejected) as e:
        validate_and_extract(zp, tmp_path / "work", settings)
    assert e.value.status == 422


def test_zip_bomb_rejected(tmp_path, settings):
    settings.max_unzipped_mb = 1
    zp = _write(tmp_path, zip_bomb())
    with pytest.raises(UploadRejected):
        validate_and_extract(zp, tmp_path / "work", settings)


def test_compression_ratio_rejected(tmp_path, settings):
    settings.max_compression_ratio = 3
    zp = _write(tmp_path, zip_bomb())
    with pytest.raises(UploadRejected):
        validate_and_extract(zp, tmp_path / "work", settings)


def test_too_many_entries_rejected(tmp_path, settings):
    settings.max_zip_entries = 2
    zp = _write(tmp_path, make_zip(GOOD))
    with pytest.raises(UploadRejected):
        validate_and_extract(zp, tmp_path / "work", settings)


def _mark_encrypted(data: bytes) -> bytes:
    """Flip the "encrypted" general-purpose flag bit in every header."""
    out = bytearray(data)
    for sig, off in ((b"PK\x03\x04", 6), (b"PK\x01\x02", 8)):
        pos = 0
        while True:
            pos = out.find(sig, pos)
            if pos == -1:
                break
            out[pos + off] |= 0x01
            pos += 4
    return bytes(out)


def test_encrypted_zip_rejected(tmp_path, settings):
    zp = _write(tmp_path, _mark_encrypted(make_zip(GOOD)))
    with pytest.raises(UploadRejected):
        validate_and_extract(zp, tmp_path / "work", settings)


def test_path_traversal_rejected(tmp_path, settings):
    zp = _write(tmp_path, make_zip({"../evil.txt": b"x", **GOOD}))
    with pytest.raises(UploadRejected):
        validate_and_extract(zp, tmp_path / "work", settings)


def test_absolute_path_rejected(tmp_path, settings):
    zp = _write(tmp_path, make_zip({"/etc/evil.txt": b"x", **GOOD}))
    with pytest.raises(UploadRejected):
        validate_and_extract(zp, tmp_path / "work", settings)


def test_symlink_member_rejected(tmp_path, settings):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zi = zipfile.ZipInfo("userA/p1/link")
        zi.external_attr = (0o120777 << 16) | (0xA1 << 16 & 0)
        zi.external_attr = 0o120777 << 16
        zf.writestr(zi, b"/etc/passwd")
        for name, data in GOOD.items():
            zf.writestr(name, data)
    zp = _write(tmp_path, buf.getvalue())
    with pytest.raises(UploadRejected):
        validate_and_extract(zp, tmp_path / "work", settings)


def test_no_matching_files_rejected(tmp_path, settings):
    zp = _write(tmp_path, make_zip({"readme.txt": b"hi"}))
    with pytest.raises(UploadRejected):
        validate_and_extract(zp, tmp_path / "work", settings)


def test_too_many_users(tmp_path, settings):
    settings.max_users = 2
    zp = _write(tmp_path, make_zip(GOOD))
    with pytest.raises(UploadRejected):
        validate_and_extract(zp, tmp_path / "work", settings)


def test_too_many_problems(tmp_path, settings):
    settings.max_problems = 1
    entries = dict(GOOD)
    entries["userA/p2/1_userA_2026-01-01_11-00-00_AC.cpp"] = b"int main(){}\n"
    zp = _write(tmp_path, make_zip(entries))
    with pytest.raises(UploadRejected):
        validate_and_extract(zp, tmp_path / "work", settings)


class _FakeUpload:
    def __init__(self, data: bytes):
        self._buf = io.BytesIO(data)

    async def read(self, size: int) -> bytes:
        return self._buf.read(size)


def test_stream_to_file_ok(tmp_path):
    dest = tmp_path / "out.bin"
    asyncio.run(stream_to_file(_FakeUpload(b"a" * 100), dest, max_bytes=1000))
    assert dest.read_bytes() == b"a" * 100


def test_stream_to_file_too_big(tmp_path):
    dest = tmp_path / "out.bin"
    with pytest.raises(UploadRejected) as e:
        asyncio.run(stream_to_file(_FakeUpload(b"a" * 5_000_000), dest, max_bytes=1024))
    assert e.value.status == 413
    assert not dest.exists()
