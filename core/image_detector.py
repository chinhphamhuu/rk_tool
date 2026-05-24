"""Detect images extracted from the RKAF Image directory."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


class ImageDetectorError(ValueError):
    """Raised when the Image directory cannot be scanned."""


@dataclass(frozen=True)
class DetectedImage:
    name: str
    path: Path
    size_bytes: int
    type: str
    risk_level: str
    supported_actions: tuple[str, ...]


@dataclass(frozen=True)
class ImageKind:
    type: str
    risk_level: str
    supported_actions: tuple[str, ...]
    order: int


KNOWN_IMAGES: dict[str, ImageKind] = {
    "super.img": ImageKind("dynamic_super", "safe", ("analyze", "unpack"), 10),
    "vbmeta.img": ImageKind("avb_vbmeta", "warning", ("analyze_avb",), 20),
    "boot.img": ImageKind("boot_image", "warning", ("analyze_only",), 30),
    "recovery.img": ImageKind("recovery_image", "warning", ("analyze_only",), 40),
    "dtbo.img": ImageKind("dtbo_image", "info", ("info_only",), 50),
    "uboot.img": ImageKind("bootloader_danger", "danger", ("info_only",), 60),
    "trust.img": ImageKind("bootloader_danger", "danger", ("info_only",), 70),
    "misc.img": ImageKind("misc_image", "info", ("info_only",), 80),
    "parameter.txt": ImageKind("rockchip_parameter", "warning", ("view_with_warning",), 90),
}

UNKNOWN_IMAGE = ImageKind("unknown_image", "warning", ("info_only",), 1000)


def scan_image_dir(image_dir: str | Path) -> list[DetectedImage]:
    """Scan an unpacked RKAF Image directory and return detected image metadata."""

    directory = Path(image_dir)
    if not directory.exists():
        raise ImageDetectorError(f"Image directory does not exist: {directory}")
    if not directory.is_dir():
        raise ImageDetectorError(f"Image path is not a directory: {directory}")

    detected: list[DetectedImage] = []
    for path in directory.iterdir():
        if not path.is_file():
            continue

        kind = _classify_name(path.name)
        if kind is None:
            continue

        detected.append(
            DetectedImage(
                name=path.name,
                path=path,
                size_bytes=path.stat().st_size,
                type=kind.type,
                risk_level=kind.risk_level,
                supported_actions=kind.supported_actions,
            )
        )

    return sorted(detected, key=_sort_key)


def detect_images(image_dir: str | Path) -> list[DetectedImage]:
    """Alias for scan_image_dir used by callers that prefer domain wording."""

    return scan_image_dir(image_dir)


def _classify_name(name: str) -> ImageKind | None:
    normalized_name = name.lower()
    if normalized_name in KNOWN_IMAGES:
        return KNOWN_IMAGES[normalized_name]
    if normalized_name.endswith(".img"):
        return UNKNOWN_IMAGE
    return None


def _sort_key(image: DetectedImage) -> tuple[int, str]:
    kind = KNOWN_IMAGES.get(image.name.lower(), UNKNOWN_IMAGE)
    return (kind.order, image.name.lower())
