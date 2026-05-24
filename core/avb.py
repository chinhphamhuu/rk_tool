"""AVB/vbmeta text report parser."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


class AvbParseError(ValueError):
    """Raised when an AVB info report cannot be parsed."""


@dataclass(frozen=True)
class AvbDescriptor:
    descriptor_type: str
    partition_name: str | None
    image_size: int | None
    salt: str | None
    digest: str | None
    raw_text: str


@dataclass(frozen=True)
class AvbInfo:
    algorithm: str | None
    flags: int | None
    rollback_index: int | None
    descriptors: tuple[AvbDescriptor, ...]
    risk_level: str
    warnings: tuple[str, ...]
    is_disable_verification_likely: bool
    has_hash_descriptor: bool
    has_hashtree_descriptor: bool
    affected_partitions: tuple[str, ...]


_FIELD_PATTERNS = {
    "algorithm": re.compile(r"^\s*Algorithm:\s*(?P<value>.+?)\s*$", re.IGNORECASE | re.MULTILINE),
    "flags": re.compile(r"^\s*Flags:\s*(?P<value>.+?)\s*$", re.IGNORECASE | re.MULTILINE),
    "rollback_index": re.compile(
        r"^\s*Rollback\s+Index:\s*(?P<value>.+?)\s*$",
        re.IGNORECASE | re.MULTILINE,
    ),
}
_DESCRIPTOR_HEADER_RE = re.compile(r"^\s*(?P<name>[A-Za-z][A-Za-z\s_-]*descriptor):\s*$")
_DESCRIPTORS_NONE_RE = re.compile(r"^\s*Descriptors:\s*(?:\r?\n\s*none\s*)?$", re.IGNORECASE | re.MULTILINE)
_PARTITION_RE = re.compile(r"^\s*Partition\s+Name:\s*(?P<value>.+?)\s*$", re.IGNORECASE | re.MULTILINE)
_IMAGE_SIZE_RE = re.compile(r"^\s*Image\s+Size:\s*(?P<value>.+?)\s*$", re.IGNORECASE | re.MULTILINE)
_SALT_RE = re.compile(r"^\s*Salt:\s*(?P<value>.*?)\s*$", re.IGNORECASE | re.MULTILINE)
_DIGEST_RE = re.compile(r"^\s*(?:Root\s+)?Digest:\s*(?P<value>.*?)\s*$", re.IGNORECASE | re.MULTILINE)
_INT_RE = re.compile(r"[-+]?0[xX][0-9a-fA-F]+|[-+]?\d+")


def parse_avb_info_text(text: str) -> AvbInfo:
    if not text or not text.strip():
        raise AvbParseError("AVB info report is empty.")

    algorithm = _parse_optional_string(text, "algorithm")
    flags = _parse_optional_int(text, "flags")
    rollback_index = _parse_optional_int(text, "rollback_index")
    descriptors = tuple(_parse_descriptors(text))

    recognized = any(
        [
            algorithm is not None,
            flags is not None,
            rollback_index is not None,
            descriptors,
            _DESCRIPTORS_NONE_RE.search(text) is not None,
        ]
    )
    if not recognized:
        raise AvbParseError("Text does not look like an AVB info report.")

    has_hash = any(descriptor.descriptor_type == "hash" for descriptor in descriptors)
    has_hashtree = any(descriptor.descriptor_type == "hashtree" for descriptor in descriptors)
    affected_partitions = _unique_partitions(descriptors)
    is_disable_verification_likely = _is_disable_verification_likely(algorithm, flags, descriptors)
    warnings = _build_warnings(
        descriptors=descriptors,
        has_hash=has_hash,
        has_hashtree=has_hashtree,
        is_disable_verification_likely=is_disable_verification_likely,
    )
    risk_level = _classify_parts(
        descriptors=descriptors,
        has_hash=has_hash,
        has_hashtree=has_hashtree,
        is_disable_verification_likely=is_disable_verification_likely,
    )

    return AvbInfo(
        algorithm=algorithm,
        flags=flags,
        rollback_index=rollback_index,
        descriptors=descriptors,
        risk_level=risk_level,
        warnings=warnings,
        is_disable_verification_likely=is_disable_verification_likely,
        has_hash_descriptor=has_hash,
        has_hashtree_descriptor=has_hashtree,
        affected_partitions=affected_partitions,
    )


def load_avb_info_report(path: str | Path) -> AvbInfo:
    report_path = Path(path)
    return parse_avb_info_text(report_path.read_text(encoding="utf-8"))


def classify_avb_risk(info: AvbInfo) -> str:
    return _classify_parts(
        descriptors=info.descriptors,
        has_hash=info.has_hash_descriptor,
        has_hashtree=info.has_hashtree_descriptor,
        is_disable_verification_likely=info.is_disable_verification_likely,
    )


def _parse_optional_string(text: str, field: str) -> str | None:
    match = _FIELD_PATTERNS[field].search(text)
    if not match:
        return None
    return match.group("value").strip()


def _parse_optional_int(text: str, field: str) -> int | None:
    value = _parse_optional_string(text, field)
    if value is None:
        return None

    match = _INT_RE.search(value)
    if not match:
        raise AvbParseError(f"Could not parse integer field {field!r}: {value!r}")
    return int(match.group(0), 0)


def _parse_descriptors(text: str) -> list[AvbDescriptor]:
    lines = text.splitlines()
    descriptors: list[AvbDescriptor] = []
    index = 0
    while index < len(lines):
        header_match = _DESCRIPTOR_HEADER_RE.match(lines[index])
        if not header_match:
            index += 1
            continue

        block_lines = [lines[index]]
        index += 1
        while index < len(lines) and not _DESCRIPTOR_HEADER_RE.match(lines[index]):
            block_lines.append(lines[index])
            index += 1

        descriptors.append(_parse_descriptor_block(header_match.group("name"), block_lines))

    return descriptors


def _parse_descriptor_block(header: str, lines: list[str]) -> AvbDescriptor:
    raw_text = "\n".join(lines).strip()
    descriptor_type = _normalize_descriptor_type(header)

    return AvbDescriptor(
        descriptor_type=descriptor_type,
        partition_name=_parse_block_string(raw_text, _PARTITION_RE),
        image_size=_parse_image_size(raw_text),
        salt=_parse_block_string(raw_text, _SALT_RE),
        digest=_parse_block_string(raw_text, _DIGEST_RE),
        raw_text=raw_text,
    )


def _normalize_descriptor_type(header: str) -> str:
    normalized = header.lower().replace("descriptor", "").strip()
    normalized = re.sub(r"[\s_-]+", "_", normalized)
    if normalized == "hash":
        return "hash"
    if normalized == "hashtree":
        return "hashtree"
    return normalized or "unknown"


def _parse_block_string(raw_text: str, pattern: re.Pattern[str]) -> str | None:
    match = pattern.search(raw_text)
    if not match:
        return None
    value = match.group("value").strip()
    return value or None


def _parse_image_size(raw_text: str) -> int | None:
    value = _parse_block_string(raw_text, _IMAGE_SIZE_RE)
    if value is None:
        return None
    match = _INT_RE.search(value)
    if not match:
        raise AvbParseError(f"Could not parse descriptor image size: {value!r}")
    return int(match.group(0), 0)


def _unique_partitions(descriptors: tuple[AvbDescriptor, ...]) -> tuple[str, ...]:
    partitions: list[str] = []
    seen: set[str] = set()
    for descriptor in descriptors:
        if not descriptor.partition_name:
            continue
        key = descriptor.partition_name.lower()
        if key in seen:
            continue
        partitions.append(descriptor.partition_name)
        seen.add(key)
    return tuple(partitions)


def _is_disable_verification_likely(
    algorithm: str | None,
    flags: int | None,
    descriptors: tuple[AvbDescriptor, ...],
) -> bool:
    algorithm_none = algorithm is not None and algorithm.upper() == "NONE"
    return bool((flags == 2 or algorithm_none) and not descriptors)


def _build_warnings(
    descriptors: tuple[AvbDescriptor, ...],
    has_hash: bool,
    has_hashtree: bool,
    is_disable_verification_likely: bool,
) -> tuple[str, ...]:
    warnings: list[str] = []
    if has_hash or has_hashtree:
        warnings.append(
            "ROM has AVB descriptors. Modifying listed partitions may cause bootloop unless AVB is handled correctly."
        )
    elif is_disable_verification_likely:
        warnings.append("vbmeta appears verification-disabled / no descriptors")
    elif not descriptors:
        warnings.append("AVB report has no descriptors; verification state requires attention.")

    return tuple(warnings)


def _classify_parts(
    descriptors: tuple[AvbDescriptor, ...],
    has_hash: bool,
    has_hashtree: bool,
    is_disable_verification_likely: bool,
) -> str:
    if has_hash or has_hashtree:
        return "danger"
    if descriptors:
        return "warning"
    if is_disable_verification_likely:
        return "low"
    return "warning"
