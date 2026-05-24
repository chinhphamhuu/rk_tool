"""JSON project state persistence."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.partition_explorer import AvbSummary, PartitionExplorerResult


SCHEMA_VERSION = 1


class ProjectStateError(ValueError):
    """Raised when project state cannot be loaded or saved."""


@dataclass
class ProjectDetectedImage:
    name: str
    path: str
    size_bytes: int
    image_type: str
    risk_level: str
    supported_actions: list[str]
    is_sparse: bool | None
    status: str
    notes: list[str] = field(default_factory=list)


@dataclass
class ProjectDynamicPartition:
    name: str
    group_name: str
    size_bytes: int
    readonly: bool
    source_image_path: str | None
    editable_dir: str | None
    supported_actions: list[str]
    risk_level: str
    extracted: bool = False
    modified: bool = False


@dataclass
class ProjectAvbSummary:
    algorithm: str | None
    flags: int | None
    risk_level: str
    affected_partitions: list[str]
    has_hash_descriptor: bool
    has_hashtree_descriptor: bool
    warnings: list[str]


@dataclass
class ProjectState:
    project_name: str
    original_rom_path: str
    project_dir: str
    image_dir: str
    editable_dir: str
    work_dir: str
    output_dir: str
    reports_dir: str
    selected_apk_path: str | None = None
    detected_images: list[ProjectDetectedImage] = field(default_factory=list)
    dynamic_partitions: list[ProjectDynamicPartition] = field(default_factory=list)
    avb_summary: ProjectAvbSummary | None = None
    modified_partitions: list[str] = field(default_factory=list)
    extracted_partitions: dict[str, str] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: _utc_now())
    updated_at: str = field(default_factory=lambda: _utc_now())
    schema_version: int = SCHEMA_VERSION


def create_project_state(
    project_name: str,
    original_rom_path: str | Path,
    project_dir: str | Path,
    image_dir: str | Path | None = None,
    editable_dir: str | Path | None = None,
    work_dir: str | Path | None = None,
    output_dir: str | Path | None = None,
    reports_dir: str | Path | None = None,
    selected_apk_path: str | Path | None = None,
) -> ProjectState:
    base_dir = Path(project_dir)
    return ProjectState(
        project_name=project_name,
        original_rom_path=str(original_rom_path),
        project_dir=str(base_dir),
        image_dir=str(Path(image_dir) if image_dir is not None else base_dir / "Image"),
        editable_dir=str(Path(editable_dir) if editable_dir is not None else base_dir / "editable"),
        work_dir=str(Path(work_dir) if work_dir is not None else base_dir / "work"),
        output_dir=str(Path(output_dir) if output_dir is not None else base_dir / "output"),
        reports_dir=str(Path(reports_dir) if reports_dir is not None else base_dir / "reports"),
        selected_apk_path=str(selected_apk_path) if selected_apk_path else None,
    )


def save_project_state(state: ProjectState, path: str | Path) -> None:
    state.updated_at = _utc_now()
    state_path = Path(path)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(
        json.dumps(_state_to_dict(state), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def load_project_state(path: str | Path) -> ProjectState:
    state_path = Path(path)
    if not state_path.exists():
        raise ProjectStateError(f"Project state file does not exist: {state_path}")
    try:
        data = json.loads(state_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ProjectStateError(f"Project state file is invalid JSON: {state_path}") from exc
    except OSError as exc:
        raise ProjectStateError(f"Could not read project state file: {state_path}") from exc

    try:
        return _state_from_dict(data)
    except (KeyError, TypeError, ValueError) as exc:
        raise ProjectStateError(f"Project state file has invalid schema: {state_path}") from exc


def update_partition_explorer_state(
    state: ProjectState,
    explorer_result: PartitionExplorerResult,
) -> ProjectState:
    state.image_dir = str(explorer_result.image_dir)
    state.detected_images = [
        ProjectDetectedImage(
            name=image.name,
            path=str(image.path),
            size_bytes=image.size_bytes,
            image_type=image.image_type,
            risk_level=image.risk_level,
            supported_actions=list(image.supported_actions),
            is_sparse=image.is_sparse,
            status=image.status,
            notes=list(image.notes),
        )
        for image in explorer_result.detected_images
    ]
    state.dynamic_partitions = [
        ProjectDynamicPartition(
            name=partition.name,
            group_name=partition.group_name,
            size_bytes=partition.size_bytes,
            readonly=partition.readonly,
            source_image_path=str(partition.source_image_path) if partition.source_image_path else None,
            editable_dir=str(partition.editable_dir) if partition.editable_dir else None,
            supported_actions=list(partition.supported_actions),
            risk_level=partition.risk_level,
            extracted=partition.name in state.extracted_partitions,
            modified=partition.name in state.modified_partitions,
        )
        for partition in explorer_result.dynamic_partitions
    ]
    state.avb_summary = _project_avb_summary(explorer_result.avb_summary)
    state.updated_at = _utc_now()
    return state


def mark_partition_extracted(
    state: ProjectState,
    partition_name: str,
    editable_dir: str | Path,
) -> ProjectState:
    editable_path = str(editable_dir)
    state.extracted_partitions[partition_name] = editable_path
    for partition in state.dynamic_partitions:
        if partition.name == partition_name:
            partition.extracted = True
            partition.editable_dir = editable_path
    state.updated_at = _utc_now()
    return state


def mark_partition_modified(state: ProjectState, partition_name: str) -> ProjectState:
    if partition_name not in state.modified_partitions:
        state.modified_partitions.append(partition_name)
    for partition in state.dynamic_partitions:
        if partition.name == partition_name:
            partition.modified = True
    state.updated_at = _utc_now()
    return state


def get_partition_source_image(state: ProjectState, partition_name: str) -> Path:
    base_dir = Path(state.project_dir)
    image_root = "modified" if partition_name in state.modified_partitions else "parts"
    return base_dir / image_root / f"{partition_name}.img"


def _state_to_dict(state: ProjectState) -> dict[str, Any]:
    return asdict(state)


def _state_from_dict(data: dict[str, Any]) -> ProjectState:
    return ProjectState(
        project_name=data["project_name"],
        original_rom_path=data["original_rom_path"],
        project_dir=data["project_dir"],
        image_dir=data["image_dir"],
        editable_dir=data["editable_dir"],
        work_dir=data["work_dir"],
        output_dir=data["output_dir"],
        reports_dir=data["reports_dir"],
        selected_apk_path=data.get("selected_apk_path"),
        detected_images=[
            ProjectDetectedImage(**image) for image in data.get("detected_images", [])
        ],
        dynamic_partitions=[
            ProjectDynamicPartition(**partition)
            for partition in data.get("dynamic_partitions", [])
        ],
        avb_summary=(
            ProjectAvbSummary(**data["avb_summary"])
            if data.get("avb_summary") is not None
            else None
        ),
        modified_partitions=list(data.get("modified_partitions", [])),
        extracted_partitions=dict(data.get("extracted_partitions", {})),
        created_at=data["created_at"],
        updated_at=data["updated_at"],
        schema_version=int(data.get("schema_version", SCHEMA_VERSION)),
    )


def _project_avb_summary(summary: AvbSummary | None) -> ProjectAvbSummary | None:
    if summary is None:
        return None
    return ProjectAvbSummary(
        algorithm=summary.algorithm,
        flags=summary.flags,
        risk_level=summary.risk_level,
        affected_partitions=list(summary.affected_partitions),
        has_hash_descriptor=summary.has_hash_descriptor,
        has_hashtree_descriptor=summary.has_hashtree_descriptor,
        warnings=list(summary.warnings),
    )


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()
