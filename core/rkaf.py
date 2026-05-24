"""RKFW/RKAF unpack workflow foundation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from core.path_utils import PathConversionError, shell_quote, windows_path_to_wsl
from core.tool_config import BundledToolConfig, BundledToolStatus


class RkafWorkflowError(ValueError):
    """Raised when RKFW/RKAF unpack workflow cannot continue."""


@dataclass(frozen=True)
class RkafUnpackResult:
    outer_dir: Path
    update_dir: Path
    image_dir: Path
    embedded_update_path: Path
    commands_run: tuple[str, ...]
    logs: tuple[str, ...]


def unpack_rkfw_rkaf(
    original_rom_path: str | Path,
    project_work_dir: str | Path,
    tools: BundledToolConfig,
    runner,
) -> RkafUnpackResult:
    """Unpack RKFW then RKAF using the provided WSL runner interface."""

    original_rom = Path(original_rom_path)
    work_dir = Path(project_work_dir)
    if not original_rom.is_file():
        raise RkafWorkflowError(f"Original ROM does not exist: {original_rom}")

    afptool = _require_tool(tools, "afptool-rs")
    outer_dir = work_dir / "outer"
    update_dir = work_dir / "update"
    image_dir = update_dir / "Image"
    outer_dir.mkdir(parents=True, exist_ok=True)
    update_dir.mkdir(parents=True, exist_ok=True)

    commands_run: list[str] = []
    logs: list[str] = []

    command = f"{_quote_path(afptool.path)} unpack {_quote_path(original_rom)} {_quote_path(outer_dir)}"
    _run_command(runner, command, commands_run, logs)

    embedded_update = _find_embedded_update(outer_dir)
    if embedded_update is None:
        available = ", ".join(path.name for path in sorted(outer_dir.iterdir())) or "<empty>"
        raise RkafWorkflowError(
            f"Could not find embedded RKAF update image in {outer_dir}. Available files: {available}"
        )

    command = f"{_quote_path(afptool.path)} unpack {_quote_path(embedded_update)} {_quote_path(update_dir)}"
    _run_command(runner, command, commands_run, logs)
    image_dir.mkdir(parents=True, exist_ok=True)

    return RkafUnpackResult(
        outer_dir=outer_dir,
        update_dir=update_dir,
        image_dir=image_dir,
        embedded_update_path=embedded_update,
        commands_run=tuple(commands_run),
        logs=tuple(logs),
    )


def _require_tool(tools: BundledToolConfig, name: str) -> BundledToolStatus:
    try:
        tool = tools.by_name(name)
    except KeyError as exc:
        raise RkafWorkflowError(f"Bundled tool is not configured: {name}") from exc
    if not tool.is_ok:
        raise RkafWorkflowError(f"Bundled tool missing: {name} at {tool.path}")
    return tool


def _quote_path(path: str | Path) -> str:
    try:
        return shell_quote(windows_path_to_wsl(path))
    except PathConversionError as exc:
        raise RkafWorkflowError(f"Could not convert path for WSL command: {path}") from exc


def _run_command(runner, command: str, commands_run: list[str], logs: list[str]) -> None:
    commands_run.append(command)
    result = runner.run(command)
    stdout = getattr(result, "stdout", "")
    stderr = getattr(result, "stderr", "")
    if stdout:
        logs.append(stdout)
    if stderr:
        logs.append(stderr)


def _find_embedded_update(outer_dir: Path) -> Path | None:
    candidates = (
        outer_dir / "embedded-update.img",
        outer_dir / "update.img",
    )
    for candidate in candidates:
        if candidate.is_file():
            return candidate

    update_like_files = sorted(
        path
        for path in outer_dir.rglob("*.img")
        if path.is_file() and "update" in path.name.lower()
    )
    return update_like_files[0] if update_like_files else None
