import inspect
from types import SimpleNamespace

import pytest

from core import workflow
from core.app_paths import AppPaths
from core.path_utils import shell_quote, windows_path_to_wsl
from core.project_state import create_project_state, load_project_state, save_project_state
from core.tool_config import load_bundled_tool_config
from core.workflow import WorkflowError, generate_vbmeta_report, run_unpack_and_analyze_workflow


FIXTURES = __import__("pathlib").Path(__file__).parent / "fixtures"
SPARSE_MAGIC = b"\x3a\xff\x26\xed"


class FakeRunner:
    def __init__(self, project_work_dir=None, reports_dir=None):
        self.commands = []
        self.project_work_dir = project_work_dir
        self.reports_dir = reports_dir

    def run(self, command, **kwargs):
        self.commands.append(command)
        if self.project_work_dir is not None and "afptool-rs" in command:
            if len([cmd for cmd in self.commands if "afptool-rs" in cmd]) == 1:
                outer = self.project_work_dir / "outer"
                outer.mkdir(parents=True, exist_ok=True)
                (outer / "embedded-update.img").write_bytes(b"rkaf")
            else:
                image_dir = self.project_work_dir / "update" / "Image"
                image_dir.mkdir(parents=True, exist_ok=True)
                (image_dir / "super.img").write_bytes(SPARSE_MAGIC + b"payload")
                (image_dir / "vbmeta.img").write_bytes(b"vbmeta")
        if self.reports_dir is not None and "avbtool.py" in command:
            self.reports_dir.mkdir(parents=True, exist_ok=True)
            (self.reports_dir / "vbmeta_info.txt").write_text(
                (FIXTURES / "vbmeta_algorithm_none.txt").read_text(encoding="utf-8"),
                encoding="utf-8",
            )
        if self.reports_dir is not None and "lpdump" in command:
            self.reports_dir.mkdir(parents=True, exist_ok=True)
            (self.reports_dir / "lpdump_original.txt").write_text(
                (FIXTURES / "lpdump_rk3318_ab.txt").read_text(encoding="utf-8"),
                encoding="utf-8",
            )
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


def _create_tools(tmp_path, *, include_avbtool=True):
    paths = _paths(tmp_path)
    (paths.tools_dir / "afptool-rs").mkdir(parents=True)
    (paths.tools_dir / "afptool-rs" / "afptool-rs").write_text("tool", encoding="utf-8")
    (paths.tools_dir / "lptools").mkdir(parents=True)
    (paths.tools_dir / "lptools" / "simg2img").write_text("tool", encoding="utf-8")
    (paths.tools_dir / "lptools" / "lpdump").write_text("tool", encoding="utf-8")
    if include_avbtool:
        (paths.tools_dir / "avbtool").mkdir(parents=True)
        (paths.tools_dir / "avbtool" / "avbtool.py").write_text("tool", encoding="utf-8")
    return load_bundled_tool_config(paths)


def _make_state(tmp_path):
    project_dir = tmp_path / "workspace" / "projects" / "demo"
    work_dir = project_dir / "work"
    reports_dir = work_dir / "reports"
    image_dir = work_dir / "update" / "Image"
    editable_dir = project_dir / "editable"
    for path in (reports_dir, image_dir, editable_dir):
        path.mkdir(parents=True, exist_ok=True)
    rom = tmp_path / "ROM Box" / "update.img"
    rom.parent.mkdir()
    rom.write_bytes(b"rom")
    state = create_project_state(
        project_name="demo",
        original_rom_path=rom,
        project_dir=project_dir,
        image_dir=image_dir,
        editable_dir=editable_dir,
        work_dir=work_dir,
        output_dir=project_dir / "output",
        reports_dir=reports_dir,
    )
    state_path = project_dir / "project_state.json"
    save_project_state(state, state_path)
    return state, state_path


def test_generate_vbmeta_report_builds_avbtool_command(tmp_path):
    tools = _create_tools(tmp_path)
    vbmeta = tmp_path / "Image Folder" / "vbmeta.img"
    vbmeta.parent.mkdir()
    vbmeta.write_bytes(b"vbmeta")
    reports_dir = tmp_path / "work reports"
    runner = FakeRunner(reports_dir=reports_dir)

    report_path = generate_vbmeta_report(vbmeta, reports_dir, tools, runner)

    assert report_path == reports_dir / "vbmeta_info.txt"
    assert len(runner.commands) == 1
    assert "python3" in runner.commands[0]
    assert "avbtool.py" in runner.commands[0]
    assert shell_quote(windows_path_to_wsl(vbmeta)) in runner.commands[0]
    assert shell_quote(windows_path_to_wsl(report_path)) in runner.commands[0]


def test_generate_vbmeta_report_returns_none_when_missing(tmp_path):
    tools = _create_tools(tmp_path)
    runner = FakeRunner()

    assert generate_vbmeta_report(tmp_path / "missing.img", tmp_path / "reports", tools, runner) is None
    assert runner.commands == []


def test_run_unpack_and_analyze_workflow_updates_project_state(tmp_path):
    state, state_path = _make_state(tmp_path)
    tools = _create_tools(tmp_path)
    runner = FakeRunner(project_work_dir=__import__("pathlib").Path(state.work_dir), reports_dir=__import__("pathlib").Path(state.reports_dir))

    result = run_unpack_and_analyze_workflow(state, tools, runner, state_path)
    loaded = load_project_state(state_path)

    assert result.partition_explorer_result.detected_images
    assert result.vbmeta_report_path == __import__("pathlib").Path(state.reports_dir) / "vbmeta_info.txt"
    assert result.lpdump_report_path == __import__("pathlib").Path(state.reports_dir) / "lpdump_original.txt"
    assert [image.name for image in loaded.detected_images] == ["super.img", "vbmeta.img"]
    assert [partition.name for partition in loaded.dynamic_partitions] == [
        "system_a",
        "product_a",
        "vendor_a",
        "odm_a",
        "system_ext_a",
    ]
    assert any("afptool-rs" in command for command in result.commands_run)
    assert any("avbtool.py" in command for command in result.commands_run)
    assert any("simg2img" in command for command in result.commands_run)
    assert any("lpdump" in command for command in result.commands_run)


def test_missing_tool_raises_workflow_error(tmp_path):
    state, state_path = _make_state(tmp_path)
    tools = _create_tools(tmp_path, include_avbtool=False)
    runner = FakeRunner(project_work_dir=__import__("pathlib").Path(state.work_dir), reports_dir=__import__("pathlib").Path(state.reports_dir))

    with pytest.raises(WorkflowError, match="avbtool.py"):
        run_unpack_and_analyze_workflow(state, tools, runner, state_path)


def test_workflow_module_has_no_direct_process_invocation():
    source = inspect.getsource(workflow)

    assert "subprocess" not in source
    assert "wsl.exe" not in source
    assert "Popen" not in source
