"""RKFW header and MD5 tail utilities."""

from __future__ import annotations

import hashlib
import shutil
from dataclasses import dataclass
from pathlib import Path


RKFW_HEADER_OFFSET = 0x15
RKFW_HEADER_SIZE = 4
RKFW_MD5_TAIL_SIZE = 32
DEFAULT_CHUNK_SIZE = 4 * 1024 * 1024


class RkfwImageError(ValueError):
    """Raised when an RKFW image is too small or malformed."""


@dataclass(frozen=True)
class RkfwFixResult:
    original_header: bytes
    final_header: bytes
    md5_tail: str
    md5_match: bool


def read_rkfw_header(path: str | Path) -> bytes:
    image_path = Path(path)
    _ensure_min_size(image_path, RKFW_HEADER_OFFSET + RKFW_HEADER_SIZE, "RKFW header")
    with image_path.open("rb") as handle:
        handle.seek(RKFW_HEADER_OFFSET)
        header = handle.read(RKFW_HEADER_SIZE)
    if len(header) != RKFW_HEADER_SIZE:
        raise RkfwImageError(f"Could not read {RKFW_HEADER_SIZE} byte RKFW header from {image_path}.")
    return header


def copy_rkfw_header(original_path: str | Path, target_path: str | Path) -> bytes:
    header = read_rkfw_header(original_path)
    target = Path(target_path)
    _ensure_min_size(target, RKFW_HEADER_OFFSET + RKFW_HEADER_SIZE, "RKFW header")
    with target.open("r+b") as handle:
        handle.seek(RKFW_HEADER_OFFSET)
        handle.write(header)
    return header


def read_md5_tail(path: str | Path) -> str:
    image_path = Path(path)
    _ensure_min_size(image_path, RKFW_MD5_TAIL_SIZE, "RKFW MD5 tail")
    with image_path.open("rb") as handle:
        handle.seek(-RKFW_MD5_TAIL_SIZE, 2)
        tail = handle.read(RKFW_MD5_TAIL_SIZE)
    if len(tail) != RKFW_MD5_TAIL_SIZE:
        raise RkfwImageError(f"Could not read {RKFW_MD5_TAIL_SIZE} byte MD5 tail from {image_path}.")
    try:
        return tail.decode("ascii")
    except UnicodeDecodeError as exc:
        raise RkfwImageError(f"RKFW MD5 tail is not ASCII in {image_path}.") from exc


def compute_body_md5(path: str | Path, chunk_size: int = DEFAULT_CHUNK_SIZE) -> str:
    if chunk_size <= 0:
        raise RkfwImageError("chunk_size must be greater than zero.")

    image_path = Path(path)
    file_size = _ensure_min_size(image_path, RKFW_MD5_TAIL_SIZE, "RKFW MD5 tail")
    remaining = file_size - RKFW_MD5_TAIL_SIZE
    digest = hashlib.md5()
    with image_path.open("rb") as handle:
        while remaining > 0:
            data = handle.read(min(chunk_size, remaining))
            if not data:
                raise RkfwImageError(f"Unexpected EOF while reading RKFW body from {image_path}.")
            digest.update(data)
            remaining -= len(data)
    return digest.hexdigest()


def verify_md5_tail(path: str | Path) -> bool:
    return compute_body_md5(path) == read_md5_tail(path).lower()


def rewrite_md5_tail(path: str | Path) -> str:
    image_path = Path(path)
    md5_tail = compute_body_md5(image_path)
    with image_path.open("r+b") as handle:
        handle.seek(-RKFW_MD5_TAIL_SIZE, 2)
        handle.write(md5_tail.encode("ascii"))
    return md5_tail


def fix_header_and_md5_tail(
    original_path: str | Path,
    repacked_path: str | Path,
    output_path: str | Path,
) -> RkfwFixResult:
    original = Path(original_path)
    repacked = Path(repacked_path)
    output = Path(output_path)

    original_header = read_rkfw_header(original)
    _ensure_min_size(repacked, RKFW_MD5_TAIL_SIZE, "RKFW MD5 tail")
    if output.parent != Path("."):
        output.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(repacked, output)

    copy_rkfw_header(original, output)
    md5_tail = rewrite_md5_tail(output)
    final_header = read_rkfw_header(output)

    return RkfwFixResult(
        original_header=original_header,
        final_header=final_header,
        md5_tail=md5_tail,
        md5_match=verify_md5_tail(output),
    )


def _ensure_min_size(path: Path, min_size: int, purpose: str) -> int:
    try:
        file_size = path.stat().st_size
    except FileNotFoundError as exc:
        raise RkfwImageError(f"RKFW image does not exist: {path}") from exc

    if file_size < min_size:
        raise RkfwImageError(
            f"RKFW image is too small for {purpose}: {path} has {file_size} bytes, "
            f"requires at least {min_size} bytes."
        )
    return file_size
