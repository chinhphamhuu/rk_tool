import inspect
from types import SimpleNamespace

import pytest

from core.app_paths import AppPaths
from core.path_utils import shell_quote, windows_path_to_wsl
from core.rkaf import RkafWorkflowError, unpack_rkfw_rkaf
from core import rkaf
from core.tool_config import load_bundled_tool_config


class FakeRunner:
    def __init__(self, hook=None):
        self.commands = []
        self.hook = hook

    def run(self, command, **kwargs):
        self.commands.append(command)
        if self.hook:
            self.hook(command, len(self.commands))
        return SimpleNamespace(stdout="", stderr="", exit_code=0)


def _paths(tmp_path):
    workspace = tmp_path / "workspace"
    return AppPaths(
        app_root=tmp_path,
        tools_dir=tmp_path / "tools",
        workspace_dir=workspace,
        projects_dir=workspace / "projects",
        output_dir=workspace / "output",
        logs_dir=workspace / "logs",
        temp_dir=workspace / "temp",
    )


def _create_tools(tmp_path):
    paths = _paths(tmp_path)
    (paths.tools_dir / "afptool-rs").mkdir(parents=True)
    (paths.tools_dir / "afptool-rs" / "afptool-rs").write_text("tool", encoding="utf-8")
    return load_bundled_tool_config(paths)


def test_unpack_rkfw_rkaf_builds_both_afptool_commands(tmp_path):
    tools = _create_tools(tmp_path)
    rom = tmp_path / "update.img"
    rom.write_bytes(b"rom")
    work_dir = tmp_path / "project" / "work"

    def hook(command, index):
        if index == 1:
            (work_dir / "outer").mkdir(parents=True, exist_ok=True)
            (work_dir / "outer" / "embedded-update.img").write_bytes(b"rkaf")

    runner = FakeRunner(hook)
    result = unpack_rkfw_rkaf(rom, work_dir, tools, runner)

    assert result.embedded_update_path == work_dir / "outer" / "embedded-update.img"
    assert result.image_dir == work_dir / "update" / "Image"
    assert len(result.commands_run) == 2
    assert " unpack " in result.commands_run[0]
    assert "embedded-update.img" in result.commands_run[1]
    assert result.commands_run == tuple(runner.commands)


def test_unpack_command_quotes_paths_with_spaces(tmp_path):
    spaced_root = tmp_path / "ROM Box"
    spaced_root.mkdir()
    tools = _create_tools(tmp_path)
    rom = spaced_root / "update image.img"
    rom.write_bytes(b"rom")
    work_dir = spaced_root / "project work"

    def hook(command, index):
        if index == 1:
            (work_dir / "outer").mkdir(parents=True, exist_ok=True)
            (work_dir / "outer" / "embedded-update.img").write_bytes(b"rkaf")

    result = unpack_rkfw_rkaf(rom, work_dir, tools, FakeRunner(hook))

    assert shell_quote(windows_path_to_wsl(rom)) in result.commands_run[0]
    assert shell_quote(windows_path_to_wsl(work_dir / "outer")) in result.commands_run[0]


def test_missing_afptool_raises_before_running_command(tmp_path):
    tools = load_bundled_tool_config(_paths(tmp_path))
    rom = tmp_path / "update.img"
    rom.write_bytes(b"rom")
    runner = FakeRunner()

    with pytest.raises(RkafWorkflowError, match="afptool-rs"):
        unpack_rkfw_rkaf(rom, tmp_path / "work", tools, runner)

    assert runner.commands == []


def test_missing_embedded_update_raises_clear_error(tmp_path):
    tools = _create_tools(tmp_path)
    rom = tmp_path / "update.img"
    rom.write_bytes(b"rom")
    work_dir = tmp_path / "work"

    with pytest.raises(RkafWorkflowError, match="embedded RKAF"):
        unpack_rkfw_rkaf(rom, work_dir, tools, FakeRunner())


def test_rkaf_module_has_no_direct_process_invocation():
    source = inspect.getsource(rkaf)

    assert "subprocess" not in source
    assert "wsl.exe" not in source
    assert "Popen" not in source
