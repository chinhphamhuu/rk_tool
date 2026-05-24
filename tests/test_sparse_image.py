import inspect

import pytest

from core import sparse_image
from core.sparse_image import (
    ANDROID_SPARSE_MAGIC,
    SparseImageError,
    classify_image_format,
    is_android_sparse_image,
    read_magic,
)


def test_sparse_magic_detects_android_sparse(tmp_path):
    image = tmp_path / "super.img"
    image.write_bytes(ANDROID_SPARSE_MAGIC + b"payload")

    assert read_magic(image) == ANDROID_SPARSE_MAGIC
    assert is_android_sparse_image(image) is True
    assert classify_image_format(image) == "android_sparse"


def test_raw_file_is_not_sparse(tmp_path):
    image = tmp_path / "super.raw.img"
    image.write_bytes(b"RAW!" + b"payload")

    assert is_android_sparse_image(image) is False
    assert classify_image_format(image) == "raw_or_unknown"


def test_too_small_file_raises_error(tmp_path):
    image = tmp_path / "tiny.img"
    image.write_bytes(b"\x3a\xff")

    with pytest.raises(SparseImageError, match="too small"):
        read_magic(image)


def test_missing_file_raises_error(tmp_path):
    with pytest.raises(SparseImageError, match="does not exist"):
        read_magic(tmp_path / "missing.img")


def test_no_subprocess_wsl_or_simg2img_calls():
    source = inspect.getsource(sparse_image)

    assert "subprocess" not in source
    assert "wsl.exe" not in source
    assert "simg2img" not in source
