"""Combined unpack/analyze workflow foundation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from core.partition_explorer import PartitionExplorerResult, build_partition_explorer
from core.path_utils import PathConversionError, shell_quote, windows_path_to_wsl
from core.project_state import ProjectState, save_project_state, update_partition_explorer_state
from core.rkaf import RkafWorkflowError, unpack_rkfw_rkaf
from core.super_image import SuperAnalyzeResult, SuperImageWorkflowError, analyze_super_image
from core.tool_config import BundledToolConfig, BundledToolStatus


class WorkflowError(ValueError):
    """Raised when the combined ROM workflow cannot continue."""


@dataclass(frozen=True)
class RomAnalyzeWorkflowResult:
    image_dir: Path
    reports_dir: Path
    vbmeta_report_path: Path | None
    lpdump_report_path: Path | None
    partition_explorer_result: PartitionExplorerResult
    warnings: tuple[str, ...]
    commands_run: tuple[str, ...]


def generate_vbmeta_report(
    vbmeta_img_path: str | Path,
    reports_dir: str | Path,
    tools: BundledToolConfig,
    runner,
    log_callback=None,
) -> Path | None:
    """Generate an avbtool info report for vbmeta.img if the image exists."""

    commands_run: list[str] = []
    return _generate_vbmeta_report(vbmeta_img_path, reports_dir, tools, runner, commands_run, log_callback)


def run_unpack_and_analyze_workflow(
    project_state: ProjectState,
    tools: BundledToolConfig,
    runner,
    state_path: str | Path | None = None,
    log_callback=None,
) -> RomAnalyzeWorkflowResult:
    """Unpack ROM, generate reports, refresh Partition Explorer state, and save state."""

    commands_run: list[str] = []
    warnings: list[str] = []

    try:
        unpack_result = unpack_rkfw_rkaf(
            project_state.original_rom_path,
            project_state.work_dir,
            tools,
            runner,
        )
    except RkafWorkflowError as exc:
        raise WorkflowError(str(exc)) from exc

    commands_run.extend(unpack_result.commands_run)
    image_dir = unpack_result.image_dir
    reports_dir = Path(project_state.reports_dir)

    vbmeta_report_path: Path | None = None
    vbmeta_img_path = image_dir / "vbmeta.img"
    if vbmeta_img_path.is_file():
        vbmeta_report_path = _generate_vbmeta_report(
            vbmeta_img_path,
            reports_dir,
            tools,
            runner,
            commands_run,
            log_callback,
        )
    else:
        warnings.append(f"vbmeta.img not found in Image folder: {vbmeta_img_path}")

    lpdump_report_path: Path | None = None
    super_img_path = image_dir / "super.img"
    if super_img_path.is_file():
        try:
            super_result = analyze_super_image(
                super_img_path,
                project_state.work_dir,
                reports_dir,
                tools,
                runner,
                log_callback=log_callback,
            )
        except SuperImageWorkflowError as exc:
            raise WorkflowError(str(exc)) from exc
        commands_run.extend(super_result.commands_run)
        warnings.extend(super_result.warnings)
        lpdump_report_path = super_result.lpdump_report_path
    else:
        warnings.append(f"super.img not found in Image folder: {super_img_path}")

    explorer_result = build_partition_explorer(
        image_dir,
        vbmeta_report_path=vbmeta_report_path if vbmeta_report_path and vbmeta_report_path.exists() else None,
        lpdump_report_path=lpdump_report_path if lpdump_report_path and lpdump_report_path.exists() else None,
        editable_root=project_state.editable_dir,
    )
    warnings.extend(explorer_result.warnings)
    warnings.extend(explorer_result.errors)

    project_state.image_dir = str(image_dir)
    update_partition_explorer_state(project_state, explorer_result)
    if state_path is not None:
        save_project_state(project_state, state_path)

    return RomAnalyzeWorkflowResult(
        image_dir=image_dir,
        reports_dir=reports_dir,
        vbmeta_report_path=vbmeta_report_path,
        lpdump_report_path=lpdump_report_path,
        partition_explorer_result=explorer_result,
        warnings=tuple(warnings),
        commands_run=tuple(commands_run),
    )


def _generate_vbmeta_report(
    vbmeta_img_path: str | Path,
    reports_dir: str | Path,
    tools: BundledToolConfig,
    runner,
    commands_run: list[str],
    log_callback=None,
) -> Path | None:
    vbmeta_img = Path(vbmeta_img_path)
    if not vbmeta_img.is_file():
        return None

    avbtool = _require_tool(tools, "avbtool.py")
    report_dir = Path(reports_dir)
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / "vbmeta_info.txt"
    command = (
        f"python3 {_quote_path(avbtool.path)} info_image "
        f"--image {_quote_path(vbmeta_img)} > {_quote_path(report_path)}"
    )
    _run_command(runner, command, commands_run, log_callback=log_callback)
    return report_path


def _require_tool(tools: BundledToolConfig, name: str) -> BundledToolStatus:
    try:
        tool = tools.by_name(name)
    except KeyError as exc:
        raise WorkflowError(f"Bundled tool is not configured: {name}") from exc
    if not tool.is_ok:
        raise WorkflowError(f"Bundled tool missing: {name} at {tool.path}")
    return tool


def _quote_path(path: str | Path) -> str:
    try:
        return shell_quote(windows_path_to_wsl(path))
    except PathConversionError as exc:
        raise WorkflowError(f"Could not convert path for WSL command: {path}") from exc


def _run_command(runner, command: str, commands_run: list[str], log_callback=None) -> None:
    commands_run.append(command)
    if log_callback is not None:
        log_callback(f"command started: {command}", "info")

    def _on_output(line) -> None:
        if log_callback is not None:
            text = getattr(line, "text", str(line))
            if text:
                log_callback(text, "info")

    try:
        runner.run(command, on_output=_on_output if log_callback is not None else None)
    except TypeError:
        runner.run(command)
    except Exception as exc:
        if log_callback is not None:
            log_callback(f"command failed: {exc}", "error")
        raise

    if log_callback is not None:
        log_callback(f"command finished: {command}", "ok")
