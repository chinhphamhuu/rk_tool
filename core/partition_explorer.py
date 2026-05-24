"""Partition Explorer state builder.

This module only combines existing filesystem/report metadata for the GUI.
It does not execute ROM tools.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from core.avb import AvbInfo, AvbParseError, load_avb_info_report
from core.image_detector import DetectedImage, ImageDetectorError, scan_image_dir
from core.lpdump_parser import LpDumpParseError, load_lpdump_report
from core.sparse_image import SparseImageError, is_android_sparse_image


class PartitionExplorerError(ValueError):
    """Raised when Partition Explorer state cannot be built."""


@dataclass(frozen=True)
class PartitionImageNode:
    name: str
    path: Path
    size_bytes: int
    image_type: str
    risk_level: str
    supported_actions: tuple[str, ...]
    is_sparse: bool | None
    status: str
    notes: tuple[str, ...] = ()


@dataclass(frozen=True)
class DynamicPartitionNode:
    name: str
    group_name: str
    size_bytes: int
    readonly: bool
    source_image_path: Path | None
    editable_dir: Path | None
    supported_actions: tuple[str, ...]
    risk_level: str


@dataclass(frozen=True)
class AvbSummary:
    algorithm: str | None
    flags: int | None
    risk_level: str
    affected_partitions: tuple[str, ...]
    has_hash_descriptor: bool
    has_hashtree_descriptor: bool
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class PartitionExplorerResult:
    image_dir: Path
    detected_images: tuple[PartitionImageNode, ...]
    super_images: tuple[PartitionImageNode, ...]
    vbmeta_images: tuple[PartitionImageNode, ...]
    boot_images: tuple[PartitionImageNode, ...]
    danger_images: tuple[PartitionImageNode, ...]
    dynamic_partitions: tuple[DynamicPartitionNode, ...]
    avb_summary: AvbSummary | None
    warnings: tuple[str, ...]
    errors: tuple[str, ...]


def build_partition_explorer(
    image_dir: str | Path,
    vbmeta_report_path: str | Path | None = None,
    lpdump_report_path: str | Path | None = None,
    editable_root: str | Path | None = None,
) -> PartitionExplorerResult:
    image_path = Path(image_dir)
    if not image_path.exists():
        raise PartitionExplorerError(f"Image directory does not exist: {image_path}")
    if not image_path.is_dir():
        raise PartitionExplorerError(f"Image path is not a directory: {image_path}")

    warnings: list[str] = []
    errors: list[str] = []
    detected_images = tuple(collect_detected_images(image_path))
    if not detected_images:
        warnings.append(f"Image directory is empty: {image_path}")

    avb_summary: AvbSummary | None = None
    try:
        avb_summary = load_optional_avb_summary(vbmeta_report_path)
    except PartitionExplorerError as exc:
        errors.append(str(exc))

    if avb_summary is not None:
        warnings.extend(avb_summary.warnings)

    dynamic_partitions: tuple[DynamicPartitionNode, ...] = ()
    try:
        dynamic_partitions = tuple(
            load_optional_dynamic_partitions(
                lpdump_report_path=lpdump_report_path,
                editable_root=editable_root,
            )
        )
    except PartitionExplorerError as exc:
        errors.append(str(exc))

    return PartitionExplorerResult(
        image_dir=image_path,
        detected_images=detected_images,
        super_images=tuple(image for image in detected_images if image.image_type == "dynamic_super"),
        vbmeta_images=tuple(image for image in detected_images if image.image_type == "avb_vbmeta"),
        boot_images=tuple(
            image for image in detected_images if image.image_type in {"boot_image", "recovery_image"}
        ),
        danger_images=tuple(image for image in detected_images if image.risk_level == "danger"),
        dynamic_partitions=dynamic_partitions,
        avb_summary=avb_summary,
        warnings=tuple(warnings),
        errors=tuple(errors),
    )


def collect_detected_images(image_dir: str | Path) -> list[PartitionImageNode]:
    try:
        detected_images = scan_image_dir(image_dir)
    except ImageDetectorError as exc:
        raise PartitionExplorerError(str(exc)) from exc

    return [_to_image_node(image) for image in detected_images]


def load_optional_avb_summary(vbmeta_report_path: str | Path | None) -> AvbSummary | None:
    if vbmeta_report_path is None:
        return None

    report_path = Path(vbmeta_report_path)
    try:
        info = load_avb_info_report(report_path)
    except (OSError, AvbParseError) as exc:
        raise PartitionExplorerError(f"Could not parse AVB report {report_path}: {exc}") from exc

    return _to_avb_summary(info)


def load_optional_dynamic_partitions(
    lpdump_report_path: str | Path | None,
    editable_root: str | Path | None = None,
) -> list[DynamicPartitionNode]:
    if lpdump_report_path is None:
        return []

    report_path = Path(lpdump_report_path)
    try:
        metadata = load_lpdump_report(report_path)
    except (OSError, LpDumpParseError) as exc:
        raise PartitionExplorerError(f"Could not parse lpdump report {report_path}: {exc}") from exc

    editable_base = Path(editable_root) if editable_root is not None else None
    return [
        DynamicPartitionNode(
            name=partition.name,
            group_name=partition.group_name,
            size_bytes=partition.size,
            readonly=partition.readonly,
            source_image_path=_infer_source_image_path(report_path, partition.name),
            editable_dir=editable_base / partition.name if editable_base is not None else None,
            supported_actions=("extract_tree", "view_info"),
            risk_level=classify_partition_risk(partition.name),
        )
        for partition in metadata.partitions
    ]


def classify_partition_risk(partition_name: str) -> str:
    base_name = _base_partition_name(partition_name)
    if base_name == "product":
        return "safe_to_edit_limited"
    if base_name in {"system", "system_ext"}:
        return "warning"
    if base_name in {"vendor", "odm"}:
        return "danger"
    return "warning"


def get_supported_actions_for_image(image_type: str) -> tuple[str, ...]:
    actions_by_type = {
        "dynamic_super": ("analyze", "unpack"),
        "avb_vbmeta": ("analyze_avb",),
        "boot_image": ("analyze_only",),
        "recovery_image": ("analyze_only",),
        "dtbo_image": ("info_only",),
        "bootloader_danger": ("info_only",),
        "misc_image": ("info_only",),
        "rockchip_parameter": ("view_with_warning",),
        "unknown_image": ("info_only",),
    }
    return actions_by_type.get(image_type, ("info_only",))


def _to_image_node(image: DetectedImage) -> PartitionImageNode:
    is_sparse: bool | None = None
    status = "detected"
    notes: list[str] = []
    if image.type == "dynamic_super":
        try:
            is_sparse = is_android_sparse_image(image.path)
            notes.append("android sparse image" if is_sparse else "raw or unknown image format")
        except SparseImageError as exc:
            is_sparse = False
            status = "error"
            notes.append(str(exc))

    return PartitionImageNode(
        name=image.name,
        path=image.path,
        size_bytes=image.size_bytes,
        image_type=image.type,
        risk_level=image.risk_level,
        supported_actions=get_supported_actions_for_image(image.type),
        is_sparse=is_sparse,
        status=status,
        notes=tuple(notes),
    )


def _to_avb_summary(info: AvbInfo) -> AvbSummary:
    return AvbSummary(
        algorithm=info.algorithm,
        flags=info.flags,
        risk_level=info.risk_level,
        affected_partitions=info.affected_partitions,
        has_hash_descriptor=info.has_hash_descriptor,
        has_hashtree_descriptor=info.has_hashtree_descriptor,
        warnings=info.warnings,
    )


def _infer_source_image_path(report_path: Path, partition_name: str) -> Path | None:
    if report_path.parent.name.lower() != "reports":
        return None
    return report_path.parent.parent / "parts" / f"{partition_name}.img"


def _base_partition_name(partition_name: str) -> str:
    lowered = partition_name.lower()
    if lowered.endswith("_a") or lowered.endswith("_b"):
        return lowered[:-2]
    return lowered
