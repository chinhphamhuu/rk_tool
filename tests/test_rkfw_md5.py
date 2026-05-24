import hashlib
import inspect

import pytest

from core import rkfw
from core.rkfw import (
    RKFW_HEADER_OFFSET,
    RKFW_HEADER_SIZE,
    RKFW_MD5_TAIL_SIZE,
    RkfwImageError,
    compute_body_md5,
    copy_rkfw_header,
    fix_header_and_md5_tail,
    read_md5_tail,
    read_rkfw_header,
    rewrite_md5_tail,
    verify_md5_tail,
)


def _write_rkfw_image(path, header=b"H223", fill=b"A", body_size=96):
    body = bytearray(fill * body_size)
    body[RKFW_HEADER_OFFSET : RKFW_HEADER_OFFSET + RKFW_HEADER_SIZE] = header
    md5_tail = hashlib.md5(body).hexdigest().encode("ascii")
    path.write_bytes(bytes(body) + md5_tail)
    return bytes(body), md5_tail.decode("ascii")


def test_read_header_at_offset_0x15(tmp_path):
    image = tmp_path / "update.img"
    _write_rkfw_image(image, header=b"H223")

    assert read_rkfw_header(image) == b"H223"


def test_copy_rkfw_header_from_original_to_target(tmp_path):
    original = tmp_path / "original.img"
    target = tmp_path / "target.img"
    _write_rkfw_image(original, header=b"H223")
    _write_rkfw_image(target, header=b"H033")

    copied = copy_rkfw_header(original, target)

    assert copied == b"H223"
    assert read_rkfw_header(target) == b"H223"


def test_read_md5_tail(tmp_path):
    image = tmp_path / "update.img"
    _, expected_tail = _write_rkfw_image(image)

    assert read_md5_tail(image) == expected_tail


def test_compute_body_md5(tmp_path):
    image = tmp_path / "update.img"
    body, _ = _write_rkfw_image(image)

    assert compute_body_md5(image, chunk_size=7) == hashlib.md5(body).hexdigest()


def test_verify_md5_tail_true(tmp_path):
    image = tmp_path / "update.img"
    _write_rkfw_image(image)

    assert verify_md5_tail(image) is True


def test_verify_md5_tail_false_when_body_changes(tmp_path):
    image = tmp_path / "update.img"
    _write_rkfw_image(image)

    with image.open("r+b") as handle:
        handle.seek(0)
        handle.write(b"Z")

    assert verify_md5_tail(image) is False


def test_rewrite_md5_tail_updates_tail(tmp_path):
    image = tmp_path / "update.img"
    _write_rkfw_image(image)

    with image.open("r+b") as handle:
        handle.seek(4)
        handle.write(b"ROM")

    new_tail = rewrite_md5_tail(image)

    assert read_md5_tail(image) == new_tail
    assert compute_body_md5(image) == new_tail
    assert verify_md5_tail(image) is True


def test_fix_header_and_md5_tail(tmp_path):
    original = tmp_path / "original.img"
    repacked = tmp_path / "repacked.img"
    output = tmp_path / "final.img"
    _write_rkfw_image(original, header=b"H223", fill=b"O")
    _write_rkfw_image(repacked, header=b"H033", fill=b"R")

    result = fix_header_and_md5_tail(original, repacked, output)

    assert result.original_header == b"H223"
    assert result.final_header == b"H223"
    assert result.md5_tail == read_md5_tail(output)
    assert result.md5_match is True
    assert read_rkfw_header(output) == b"H223"
    assert verify_md5_tail(output) is True


@pytest.mark.parametrize(
    "content,operation",
    [
        (b"A" * (RKFW_MD5_TAIL_SIZE - 1), read_md5_tail),
        (b"A" * (RKFW_MD5_TAIL_SIZE - 1), compute_body_md5),
        (b"A" * (RKFW_HEADER_OFFSET + RKFW_HEADER_SIZE - 1), read_rkfw_header),
    ],
)
def test_file_too_small_raises_clear_error(tmp_path, content, operation):
    image = tmp_path / "tiny.img"
    image.write_bytes(content)

    with pytest.raises(RkfwImageError, match="too small"):
        operation(image)


def test_no_wsl_subprocess_or_tool_calls():
    source = inspect.getsource(rkfw)

    assert "subprocess" not in source
    assert "wsl.exe" not in source
    assert "afptool" not in source
