"""Android sparse image detection helpers."""

from __future__ import annotations

from pathlib import Path


ANDROID_SPARSE_MAGIC = b"\x3a\xff\x26\xed"
MAGIC_SIZE = 4


class SparseImageError(ValueError):
    """Raised when an image header cannot be read safely."""


def read_magic(path: str | Path) -> bytes:
    image_path = Path(path)
    try:
        with image_path.open("rb") as handle:
            magic = handle.read(MAGIC_SIZE)
    except FileNotFoundError as exc:
        raise SparseImageError(f"Image file does not exist: {image_path}") from exc

    if len(magic) < MAGIC_SIZE:
        raise SparseImageError(
            f"Image file is too small to read sparse magic: {image_path} has {len(magic)} bytes."
        )
    return magic


def is_android_sparse_image(path: str | Path) -> bool:
    return read_magic(path) == ANDROID_SPARSE_MAGIC


def classify_image_format(path: str | Path) -> str:
    return "android_sparse" if is_android_sparse_image(path) else "raw_or_unknown"
