"""super.img analyze workflow foundation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from core.lpdump_parser import LpDumpParseError, SuperMetadata, load_lpdump_report
from core.path_utils import PathConversionError, shell_quote, windows_path_to_wsl
from core.sparse_image import SparseImageError, is_android_sparse_image
from core.tool_config import BundledToolConfig, BundledToolStatus


class SuperImageWorkflowError(ValueError):
    """Raised when super.img analyze workflow cannot continue."""


@dataclass(frozen=True)
class SuperAnalyzeResult:
    super_img_path: Path
    raw_super_img_path: Path
    lpdump_report_path: Path
    is_sparse: bool
    commands_run: tuple[str, ...]
    metadata_summary: SuperMetadata | None = None
    warnings: tuple[str, ...] = ()


def analyze_super_image(
    super_img_path: str | Path,
    project_work_dir: str | Path,
    reports_dir: str | Path,
    tools: BundledToolConfig,
    runner,
) -> SuperAnalyzeResult:
    """Analyze super.img and write an lpdump text report via the provided runner."""

    super_img = Path(super_img_path)
    work_dir = Path(project_work_dir)
    report_dir = Path(reports_dir)
    if not super_img.is_file():
        raise SuperImageWorkflowError(f"super.img does not exist: {super_img}")

    lpdump = _require_tool(tools, "lpdump")
    try:
        is_sparse = is_android_sparse_image(super_img)
    except SparseImageError as exc:
        raise SuperImageWorkflowError(f"Could not inspect super.img format: {super_img}") from exc

    super_work_dir = work_dir / "super"
    super_work_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)
    lpdump_report_path = report_dir / "lpdump_original.txt"

    commands_run: list[str] = []
    warnings: list[str] = []
    raw_super_img_path = super_img

    if is_sparse:
        simg2img = _require_tool(tools, "simg2img")
        raw_super_img_path = super_work_dir / "super.raw.img"
        command = f"{_quote_path(simg2img.path)} {_quote_path(super_img)} {_quote_path(raw_super_img_path)}"
        _run_command(runner, command, commands_run)

    command = f"{_quote_path(lpdump.path)} {_quote_path(raw_super_img_path)} > {_quote_path(lpdump_report_path)}"
    _run_command(runner, command, commands_run)

    metadata_summary: SuperMetadata | None = None
    if lpdump_report_path.exists():
        try:
            metadata_summary = load_lpdump_report(lpdump_report_path)
        except LpDumpParseError as exc:
            warnings.append(f"lpdump report was generated but could not be parsed: {exc}")
    else:
        warnings.append(f"lpdump report was not found after analyze command: {lpdump_report_path}")

    return SuperAnalyzeResult(
        super_img_path=super_img,
        raw_super_img_path=raw_super_img_path,
        lpdump_report_path=lpdump_report_path,
        is_sparse=is_sparse,
        commands_run=tuple(commands_run),
        metadata_summary=metadata_summary,
        warnings=tuple(warnings),
    )


def _require_tool(tools: BundledToolConfig, name: str) -> BundledToolStatus:
    try:
        tool = tools.by_name(name)
    except KeyError as exc:
        raise SuperImageWorkflowError(f"Bundled tool is not configured: {name}") from exc
    if not tool.is_ok:
        raise SuperImageWorkflowError(f"Bundled tool missing: {name} at {tool.path}")
    return tool


def _quote_path(path: str | Path) -> str:
    try:
        return shell_quote(windows_path_to_wsl(path))
    except PathConversionError as exc:
        raise SuperImageWorkflowError(f"Could not convert path for WSL command: {path}") from exc


def _run_command(runner, command: str, commands_run: list[str]) -> None:
    commands_run.append(command)
    runner.run(command)
