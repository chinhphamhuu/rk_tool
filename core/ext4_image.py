"""ext4 image inspection command helpers."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from core.path_utils import PathConversionError, shell_quote, windows_path_to_wsl


class Ext4ImageError(ValueError):
    """Raised when an ext4 image helper cannot parse or build safely."""


@dataclass(frozen=True)
class Ext4ImageInfo:
    image_path: Path | None
    exists: bool
    size_bytes: int | None
    filesystem_type: str
    block_count: int | None
    block_size: int | None
    free_blocks: int | None
    used_blocks: int | None
    raw_report_path: Path | None = None
    volume_name: str | None = None
    filesystem_features: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()


def build_debugfs_rdump_command(image_path: str | Path, output_dir: str | Path) -> str:
    """Build a read-only debugfs rdump command for extracting an image tree."""

    image_wsl = _wsl_path(image_path)
    output_wsl = _wsl_path(output_dir)
    rdump_expression = f"rdump / {output_wsl}"
    return f"debugfs -R {shell_quote(rdump_expression)} {shell_quote(image_wsl)}"


def build_e2fsck_readonly_command(image_path: str | Path) -> str:
    """Build an e2fsck command that checks without modifying the image."""

    return f"e2fsck -fn {shell_quote(_wsl_path(image_path))}"


def build_dumpe2fs_command(image_path: str | Path) -> str:
    """Build a dumpe2fs header command."""

    return f"dumpe2fs -h {shell_quote(_wsl_path(image_path))}"


def parse_dumpe2fs_header(
    text: str,
    *,
    image_path: str | Path | None = None,
    raw_report_path: str | Path | None = None,
) -> Ext4ImageInfo:
    """Parse the useful fields from a dumpe2fs -h report."""

    if not text or not text.strip():
        raise Ext4ImageError("dumpe2fs header text is empty.")

    fields = _parse_key_values(text)
    if not fields:
        raise Ext4ImageError("dumpe2fs header text does not contain recognizable fields.")

    block_count = _parse_int(fields.get("Block count"))
    free_blocks = _parse_int(fields.get("Free blocks"))
    block_size = _parse_int(fields.get("Block size"))
    used_blocks = (
        block_count - free_blocks
        if block_count is not None and free_blocks is not None
        else None
    )
    features = tuple((fields.get("Filesystem features") or "").split())
    filesystem_type = "ext4" if features or block_size is not None else "unknown"
    warnings: list[str] = []
    if block_count is None:
        warnings.append("Block count not found in dumpe2fs report.")
    if block_size is None:
        warnings.append("Block size not found in dumpe2fs report.")

    path = Path(image_path) if image_path is not None else None
    return Ext4ImageInfo(
        image_path=path,
        exists=path.exists() if path is not None else False,
        size_bytes=path.stat().st_size if path is not None and path.exists() else None,
        filesystem_type=filesystem_type,
        block_count=block_count,
        block_size=block_size,
        free_blocks=free_blocks,
        used_blocks=used_blocks,
        raw_report_path=Path(raw_report_path) if raw_report_path is not None else None,
        volume_name=fields.get("Filesystem volume name"),
        filesystem_features=features,
        warnings=tuple(warnings),
    )


def _parse_key_values(text: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for line in text.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = re.sub(r"\s+", " ", key.strip())
        if key:
            fields[key] = value.strip()
    return fields


def _parse_int(value: str | None) -> int | None:
    if value is None:
        return None
    match = re.search(r"\d+", value.replace(",", ""))
    return int(match.group(0)) if match else None


def _wsl_path(path: str | Path) -> str:
    try:
        return windows_path_to_wsl(path)
    except PathConversionError as exc:
        raise Ext4ImageError(f"Could not convert path for WSL command: {path}") from exc
