"""Extract dynamic partition images into editable staging folders."""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import re

from core.ext4_image import (
    Ext4ImageError,
    build_debugfs_rdump_command,
    build_dumpe2fs_command,
    build_e2fsck_readonly_command,
    parse_dumpe2fs_header,
)
from core.wsl_runner import WslCommandError, WslCommandTimeout


class EditableExtractError(ValueError):
    """Raised when editable extraction cannot continue."""


@dataclass(frozen=True)
class EditableExtractResult:
    partition_name: str
    source_image_path: Path
    editable_dir: Path
    manifest_path: Path
    e2fsck_report_path: Path
    dumpe2fs_report_path: Path
    extracted_file_count: int
    commands_run: tuple[str, ...]
    warnings: tuple[str, ...] = ()


def extract_partition_to_editable(
    partition_name: str,
    source_image_path: str | Path,
    editable_root: str | Path,
    project_work_dir: str | Path,
    reports_dir: str | Path,
    runner,
    overwrite: bool = False,
    log_callback=None,
) -> EditableExtractResult:
    """Extract one partition image to editable/<partition> using debugfs rdump."""

    safe_partition_name = _validate_partition_name(partition_name)
    source_image = Path(source_image_path)
    editable_base = Path(editable_root)
    work_dir = Path(project_work_dir)
    report_dir = Path(reports_dir)
    editable_dir = editable_base / safe_partition_name

    if not source_image.is_file():
        raise EditableExtractError(f"Source image does not exist: {source_image}")

    report_dir.mkdir(parents=True, exist_ok=True)
    work_dir.mkdir(parents=True, exist_ok=True)
    editable_base.mkdir(parents=True, exist_ok=True)
    _prepare_editable_dir(editable_dir, editable_base, overwrite=overwrite)

    commands_run: list[str] = []
    warnings: list[str] = []

    _log(log_callback, f"start extract partition: {safe_partition_name}", "info")
    for command_name in ("debugfs", "e2fsck", "dumpe2fs"):
        _run_command(
            runner,
            f"command -v {command_name}",
            commands_run,
            log_callback=log_callback,
            label=f"check {command_name}",
        )

    e2fsck_report_path = report_dir / f"e2fsck_{safe_partition_name}.txt"
    _log(log_callback, "e2fsck started", "info")
    e2fsck_result = _run_command(
        runner,
        build_e2fsck_readonly_command(source_image),
        commands_run,
        log_callback=log_callback,
        label="e2fsck",
    )
    _write_report(e2fsck_report_path, e2fsck_result)
    _log(log_callback, "e2fsck done", "ok")

    dumpe2fs_report_path = report_dir / f"dumpe2fs_{safe_partition_name}.txt"
    _log(log_callback, "dumpe2fs started", "info")
    dumpe2fs_result = _run_command(
        runner,
        build_dumpe2fs_command(source_image),
        commands_run,
        log_callback=log_callback,
        label="dumpe2fs",
    )
    dumpe2fs_text = _write_report(dumpe2fs_report_path, dumpe2fs_result)
    try:
        info = parse_dumpe2fs_header(
            dumpe2fs_text,
            image_path=source_image,
            raw_report_path=dumpe2fs_report_path,
        )
        warnings.extend(info.warnings)
    except Ext4ImageError as exc:
        warnings.append(f"dumpe2fs report parse failed: {exc}")
    _log(log_callback, "dumpe2fs done", "ok")

    _log(log_callback, "debugfs rdump started", "info")
    _run_command(
        runner,
        build_debugfs_rdump_command(source_image, editable_dir),
        commands_run,
        log_callback=log_callback,
        label="debugfs rdump",
    )
    _log(log_callback, "debugfs rdump done", "ok")

    counts = _count_editable_tree(editable_dir)
    manifest_path = editable_dir / ".rk_manifest.json"
    _write_manifest(
        manifest_path=manifest_path,
        partition_name=safe_partition_name,
        source_image_path=source_image,
        editable_dir=editable_dir,
        source_image_size=source_image.stat().st_size,
        file_count=counts["files"],
        directory_count=counts["directories"],
        symlink_count=counts["symlinks"],
    )
    _log(log_callback, "manifest written", "ok")
    _log(log_callback, "extract completed", "ok")

    return EditableExtractResult(
        partition_name=safe_partition_name,
        source_image_path=source_image,
        editable_dir=editable_dir,
        manifest_path=manifest_path,
        e2fsck_report_path=e2fsck_report_path,
        dumpe2fs_report_path=dumpe2fs_report_path,
        extracted_file_count=counts["files"],
        commands_run=tuple(commands_run),
        warnings=tuple(warnings),
    )


def _validate_partition_name(partition_name: str) -> str:
    name = partition_name.strip()
    if not name:
        raise EditableExtractError("Partition name must not be empty.")
    if name in {".", ".."} or not re.fullmatch(r"[A-Za-z0-9_.+-]+", name):
        raise EditableExtractError(f"Invalid partition name: {partition_name}")
    return name


def _prepare_editable_dir(editable_dir: Path, editable_root: Path, *, overwrite: bool) -> None:
    if editable_dir.exists() and any(editable_dir.iterdir()):
        if not overwrite:
            raise EditableExtractError(f"Editable folder already exists and is not empty: {editable_dir}")
        _safe_rmtree(editable_dir, editable_root)
    editable_dir.mkdir(parents=True, exist_ok=True)


def _safe_rmtree(target: Path, allowed_parent: Path) -> None:
    resolved_target = target.resolve()
    resolved_parent = allowed_parent.resolve()
    if resolved_target == resolved_parent or resolved_parent not in resolved_target.parents:
        raise EditableExtractError(f"Refusing to delete path outside editable root: {target}")
    shutil.rmtree(resolved_target)


def _run_command(
    runner,
    command: str,
    commands_run: list[str],
    *,
    log_callback=None,
    label: str,
):
    commands_run.append(command)
    _log(log_callback, f"command started: {label}", "info")

    def _on_output(line) -> None:
        text = getattr(line, "text", str(line))
        if text:
            _log(log_callback, text, "info")

    try:
        try:
            result = runner.run(command, on_output=_on_output if log_callback is not None else None)
        except TypeError:
            result = runner.run(command)
    except WslCommandError as exc:
        detail = exc.stderr.strip() or exc.stdout.strip() or str(exc)
        raise EditableExtractError(
            f"Command failed: {label}; exit code {exc.exit_code}; {detail}"
        ) from exc
    except WslCommandTimeout as exc:
        raise EditableExtractError(
            f"Command failed: {label}; timeout after {exc.timeout} seconds"
        ) from exc
    except Exception as exc:
        raise EditableExtractError(f"Command failed: {label}; {exc}") from exc

    _log(log_callback, f"command finished: {label}", "ok")
    return result


def _write_report(report_path: Path, command_result) -> str:
    stdout = getattr(command_result, "stdout", "") or ""
    stderr = getattr(command_result, "stderr", "") or ""
    text = stdout
    if stderr:
        text = text + ("" if text.endswith("\n") or not text else "\n") + stderr
    report_path.write_text(text, encoding="utf-8")
    return text


def _count_editable_tree(editable_dir: Path) -> dict[str, int]:
    counts = {"files": 0, "directories": 0, "symlinks": 0}
    if not editable_dir.exists():
        return counts
    for path in editable_dir.rglob("*"):
        if path.name == ".rk_manifest.json":
            continue
        if path.is_symlink():
            counts["symlinks"] += 1
        elif path.is_dir():
            counts["directories"] += 1
        elif path.is_file():
            counts["files"] += 1
    return counts


def _write_manifest(
    *,
    manifest_path: Path,
    partition_name: str,
    source_image_path: Path,
    editable_dir: Path,
    source_image_size: int,
    file_count: int,
    directory_count: int,
    symlink_count: int,
) -> None:
    manifest = {
        "partition_name": partition_name,
        "source_image_path": str(source_image_path),
        "editable_dir": str(editable_dir),
        "extracted_at": datetime.now(timezone.utc).isoformat(),
        "file_count": file_count,
        "directory_count": directory_count,
        "symlink_count": symlink_count,
        "source_image_size": source_image_size,
        "note": "extracted read-only by debugfs rdump",
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


def _log(log_callback, message: str, variant: str) -> None:
    if log_callback is not None:
        log_callback(message, variant)
