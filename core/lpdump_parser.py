"""Parser for lpdump text reports."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


class LpDumpParseError(ValueError):
    """Raised when an lpdump report is incomplete or malformed."""


@dataclass(frozen=True)
class DynamicGroup:
    name: str
    maximum_size: int
    flags: str | None = None


@dataclass(frozen=True)
class DynamicPartition:
    name: str
    group_name: str
    size: int
    readonly: bool
    attributes: tuple[str, ...]
    extent_count: int | None = None


@dataclass(frozen=True)
class SuperMetadata:
    metadata_size: int
    metadata_slots: int
    block_size: int
    device_size: int
    alignment: int | None
    groups: tuple[DynamicGroup, ...]
    partitions: tuple[DynamicPartition, ...]
    raw_text: str


_INT_RE = re.compile(r"[-+]?0[xX][0-9a-fA-F]+|[-+]?\d+")
_KV_RE = re.compile(r"^\s*(?P<key>[A-Za-z][A-Za-z0-9 _/-]*?)\s*[:=]\s*(?P<value>.*?)\s*$")
_GROUP_HEADER_RE = re.compile(r"^\s*(?:Group|Partition group)\s*[:=]\s*(?P<value>.+?)\s*$", re.IGNORECASE)
_PARTITION_HEADER_RE = re.compile(r"^\s*(?:Partition|Name)\s*[:=]\s*(?P<value>.+?)\s*$", re.IGNORECASE)


def parse_lpdump_text(text: str) -> SuperMetadata:
    if not text or not text.strip():
        raise LpDumpParseError("lpdump report is empty.")

    lines = text.splitlines()
    metadata_size: int | None = None
    metadata_slots: int | None = None
    block_size: int | None = None
    device_size: int | None = None
    alignment: int | None = None
    groups: list[DynamicGroup] = []
    partitions: list[DynamicPartition] = []

    index = 0
    while index < len(lines):
        line = lines[index]
        key_value = _parse_key_value(line)
        if key_value is not None:
            key, value = key_value
            normalized = _normalize_key(key)
            if normalized in {"metadatasize", "metadatamaxsize"}:
                metadata_size = _parse_int(value, key)
            elif normalized in {"metadataslots", "metadataslotcount"}:
                metadata_slots = _parse_int(value, key)
            elif normalized == "blocksize":
                block_size = _parse_int(value, key)
            elif normalized in {"devicesize", "superdevicesize"}:
                device_size = _parse_int(value, key)
            elif normalized == "alignment":
                alignment = _parse_int(value, key)

        if _is_group_header(line):
            block, index = _collect_block(lines, index, ("group", "partition"))
            groups.append(_parse_group_block(block))
            continue

        if _is_partition_header(line):
            block, index = _collect_block(lines, index, ("partition",))
            partitions.append(_parse_partition_block(block))
            continue

        index += 1

    _require(metadata_size, "metadata size")
    _require(metadata_slots, "metadata slots")
    _require(block_size, "block size")
    _require(device_size, "device size")
    if not groups:
        raise LpDumpParseError("Missing dynamic partition group in lpdump report.")
    if not partitions:
        raise LpDumpParseError("Missing dynamic partitions in lpdump report.")

    return SuperMetadata(
        metadata_size=metadata_size,
        metadata_slots=metadata_slots,
        block_size=block_size,
        device_size=device_size,
        alignment=alignment,
        groups=tuple(groups),
        partitions=tuple(partitions),
        raw_text=text,
    )


def load_lpdump_report(path: str | Path) -> SuperMetadata:
    report_path = Path(path)
    return parse_lpdump_text(report_path.read_text(encoding="utf-8"))


def _parse_group_block(lines: list[str]) -> DynamicGroup:
    first = lines[0]
    header_match = _GROUP_HEADER_RE.match(first)
    if not header_match:
        raise LpDumpParseError(f"Invalid group block header: {first!r}")

    header_value = header_match.group("value").strip()
    name = _first_token(header_value)
    maximum_size = _parse_inline_int(header_value, ("maximum size", "max size", "size"))
    flags: str | None = None

    for line in lines[1:]:
        parsed = _parse_key_value(line)
        if parsed is None:
            continue
        key, value = parsed
        normalized = _normalize_key(key)
        if normalized in {"maximumsize", "maxsize", "size"}:
            maximum_size = _parse_int(value, key)
        elif normalized == "flags":
            flags = value.strip() or None

    _require(maximum_size, f"maximum size for group {name}")
    return DynamicGroup(name=name, maximum_size=maximum_size, flags=flags)


def _parse_partition_block(lines: list[str]) -> DynamicPartition:
    first = lines[0]
    header_match = _PARTITION_HEADER_RE.match(first)
    if not header_match:
        raise LpDumpParseError(f"Invalid partition block header: {first!r}")

    name = _first_token(header_match.group("value"))
    group_name: str | None = None
    size: int | None = _parse_inline_int(header_match.group("value"), ("size",))
    attributes: tuple[str, ...] = ()
    readonly = False
    extent_count: int | None = None

    for line in lines[1:]:
        parsed = _parse_key_value(line)
        if parsed is None:
            continue
        key, value = parsed
        normalized = _normalize_key(key)
        if normalized in {"group", "groupname"}:
            group_name = _first_token(value)
        elif normalized == "size":
            size = _parse_int(value, key)
        elif normalized in {"attributes", "attribute"}:
            attributes = _parse_attributes(value)
            readonly = "readonly" in {attribute.lower() for attribute in attributes}
        elif normalized == "readonly":
            readonly = value.strip().lower() in {"1", "true", "yes", "readonly"}
        elif normalized in {"extentcount", "extents"}:
            extent_count = _parse_int(value, key)

    _require(group_name, f"group for partition {name}")
    _require(size, f"size for partition {name}")
    return DynamicPartition(
        name=name,
        group_name=group_name,
        size=size,
        readonly=readonly,
        attributes=attributes,
        extent_count=extent_count,
    )


def _collect_block(lines: list[str], start: int, block_types: tuple[str, ...]) -> tuple[list[str], int]:
    block = [lines[start]]
    index = start + 1
    while index < len(lines):
        line = lines[index]
        if "group" in block_types and _is_group_header(line):
            break
        if "partition" in block_types and _is_partition_header(line):
            break
        block.append(line)
        index += 1
    return block, index


def _parse_key_value(line: str) -> tuple[str, str] | None:
    match = _KV_RE.match(line)
    if not match:
        return None
    return match.group("key"), match.group("value")


def _normalize_key(key: str) -> str:
    return re.sub(r"[^a-z0-9]", "", key.lower())


def _parse_int(value: str, field_name: str) -> int:
    match = _INT_RE.search(value)
    if not match:
        raise LpDumpParseError(f"Could not parse integer field {field_name!r}: {value!r}")
    return int(match.group(0), 0)


def _parse_inline_int(value: str, labels: tuple[str, ...]) -> int | None:
    for label in labels:
        pattern = re.compile(rf"{re.escape(label)}\s*[=:]\s*({_INT_RE.pattern})", re.IGNORECASE)
        match = pattern.search(value)
        if match:
            return int(match.group(1), 0)
    return None


def _first_token(value: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise LpDumpParseError("Expected a name but got an empty value.")
    return cleaned.split()[0].strip(",")


def _parse_attributes(value: str) -> tuple[str, ...]:
    return tuple(attribute for attribute in re.split(r"[\s,|]+", value.strip()) if attribute)


def _is_group_header(line: str) -> bool:
    match = _GROUP_HEADER_RE.match(line)
    if not match:
        return False
    return not line.lstrip().lower().startswith("group name")


def _is_partition_header(line: str) -> bool:
    match = _PARTITION_HEADER_RE.match(line)
    if not match:
        return False
    return line.lstrip().lower().startswith("partition")


def _require(value: object | None, field: str) -> None:
    if value is None:
        raise LpDumpParseError(f"Missing required field: {field}.")
