"""Build lpmake command previews from parsed super metadata."""

from __future__ import annotations

import shlex
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from core.lpdump_parser import DynamicPartition, SuperMetadata


class LpMakeBuildError(ValueError):
    """Raised when an lpmake command cannot be built safely."""


@dataclass(frozen=True)
class LpMakeImageSource:
    path: str | Path
    size_override: int | None = None


@dataclass(frozen=True)
class LpMakeCommand:
    args: tuple[str, ...]
    command_string: str


ImageSourceValue = str | Path | LpMakeImageSource


def build_lpmake_command(
    metadata: SuperMetadata,
    image_sources: Mapping[str, ImageSourceValue],
    output_path: str | Path,
    sparse: bool = True,
    allow_missing: bool = False,
) -> LpMakeCommand:
    normalized_sources = _normalize_sources(image_sources)
    effective_sizes = _effective_partition_sizes(metadata.partitions, normalized_sources)
    _validate_group_sizes(metadata, effective_sizes)

    args: list[str] = [
        "lpmake",
        "--metadata-size",
        str(metadata.metadata_size),
        "--metadata-slots",
        str(metadata.metadata_slots),
        "--device-size",
        str(metadata.device_size),
        "--block-size",
        str(metadata.block_size),
    ]

    if metadata.alignment is not None:
        args.extend(["--alignment", str(metadata.alignment)])

    for group in metadata.groups:
        args.extend(["--group", f"{group.name}:{group.maximum_size}"])

    for partition in metadata.partitions:
        args.extend(
            [
                "--partition",
                _partition_spec(partition, effective_sizes[partition.name]),
            ]
        )

        source = normalized_sources.get(partition.name)
        if source is None:
            if allow_missing:
                continue
            raise LpMakeBuildError(f"Missing image source for partition: {partition.name}")
        args.extend(["--image", f"{partition.name}={source.path}"])

    if sparse:
        args.append("--sparse")

    args.extend(["--output", str(output_path)])
    return LpMakeCommand(args=tuple(args), command_string=_quote_command(args))


def _normalize_sources(image_sources: Mapping[str, ImageSourceValue]) -> dict[str, LpMakeImageSource]:
    normalized: dict[str, LpMakeImageSource] = {}
    for partition_name, source in image_sources.items():
        if isinstance(source, LpMakeImageSource):
            normalized[partition_name] = source
        else:
            normalized[partition_name] = LpMakeImageSource(path=source)
    return normalized


def _effective_partition_sizes(
    partitions: tuple[DynamicPartition, ...],
    image_sources: Mapping[str, LpMakeImageSource],
) -> dict[str, int]:
    effective: dict[str, int] = {}
    for partition in partitions:
        source = image_sources.get(partition.name)
        size = source.size_override if source and source.size_override is not None else partition.size
        if size <= 0:
            raise LpMakeBuildError(f"Invalid size for partition {partition.name}: {size}")
        effective[partition.name] = size
    return effective


def _validate_group_sizes(metadata: SuperMetadata, effective_sizes: Mapping[str, int]) -> None:
    group_maximums = {group.name: group.maximum_size for group in metadata.groups}
    group_totals = {group.name: 0 for group in metadata.groups}

    for partition in metadata.partitions:
        if partition.group_name not in group_maximums:
            raise LpMakeBuildError(
                f"Partition {partition.name} references unknown group {partition.group_name}."
            )
        group_totals[partition.group_name] += effective_sizes[partition.name]

    for group_name, total_size in group_totals.items():
        maximum_size = group_maximums[group_name]
        if total_size > maximum_size:
            raise LpMakeBuildError(
                f"Partition sizes exceed group {group_name}: total {total_size}, maximum {maximum_size}."
            )


def _partition_spec(partition: DynamicPartition, size: int) -> str:
    attributes = "readonly" if partition.readonly else "none"
    return f"{partition.name}:{attributes}:{size}:{partition.group_name}"


def _quote_command(args: list[str]) -> str:
    return " ".join(shlex.quote(arg) for arg in args)
