import inspect
from pathlib import Path
from types import SimpleNamespace

import pytest

from core.app_paths import AppPaths
from core.project_state import create_project_state, load_project_state, save_project_state
from gui import unpack_tab
from gui.unpack_tab import (
    UnpackFlowError,
    extract_super_partitions_backend,
    refresh_partition_explorer_state,
    run_unpack_analyze_backend,
)


FIXTURES = Path(__file__).parent / "fixtures"
SPARSE_MAGIC = b"\x3a\xff\x26\xed"


class FakeRunner:
    def __init__(self, work_dir=None, reports_dir=None, parts_dir=None):
        self.commands = []
        self.work_dir = work_dir
        self.reports_dir = reports_dir
        self.parts_dir = parts_dir

    def run(self, command, **kwargs):
        self.commands.append(command)
        if self.work_dir is not None and "afptool-rs" in command:
            afp_calls = len([cmd for cmd in self.commands if "afptool-rs" in cmd])
            if afp_calls == 1:
                outer = self.work_dir / "outer"
                outer.mkdir(parents=True, exist_ok=True)
                (outer / "embedded-update.img").write_bytes(b"rkaf")
            else:
                image_dir = self.work_dir / "update" / "Image"
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
        if self.parts_dir is not None and "lpunpack" in command:
            self.parts_dir.mkdir(parents=True, exist_ok=True)
            for name in ("system_a", "product_a", "vendor_a", "odm_a", "system_ext_a"):
                (self.parts_dir / f"{name}.img").write_bytes(name.encode("ascii"))
        return SimpleNamespace(stdout="", stderr="", exit_code=0)


def _paths(tmp_path, *, complete_tools=True):
    workspace = tmp_path / "workspace"
    paths = AppPaths(
        app_root=tmp_path,
        tools_dir=tmp_path / "tools",
        workspace_dir=workspace,
        projects_dir=workspace / "projects",
        output_dir=workspace / "output",
        logs_dir=workspace / "logs",
        temp_dir=workspace / "temp",
    )
    if complete_tools:
        (paths.tools_dir / "afptool-rs").mkdir(parents=True)
        (paths.tools_dir / "afptool-rs" / "afptool-rs").write_text("tool", encoding="utf-8")
        (paths.tools_dir / "lptools").mkdir(parents=True)
        for tool in ("simg2img", "lpdump", "lpunpack", "lpmake"):
            (paths.tools_dir / "lptools" / tool).write_text("tool", encoding="utf-8")
        (paths.tools_dir / "avbtool").mkdir(parents=True)
        (paths.tools_dir / "avbtool" / "avbtool.py").write_text("tool", encoding="utf-8")
    return paths


def _state(tmp_path):
    project_dir = tmp_path / "workspace" / "projects" / "demo"
    work_dir = project_dir / "work"
    image_dir = work_dir / "update" / "Image"
    reports_dir = work_dir / "reports"
    editable_dir = project_dir / "editable"
    for path in (image_dir, reports_dir, editable_dir):
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


def test_unpack_analyze_backend_success_updates_state(tmp_path):
    paths = _paths(tmp_path)
    state, state_path = _state(tmp_path)
    runner = FakeRunner(Path(state.work_dir), Path(state.reports_dir))

    result = run_unpack_analyze_backend(state, state_path, paths, runner=runner)
    loaded = load_project_state(state_path)

    assert result.result.detected_images
    assert [image.name for image in loaded.detected_images] == ["super.img", "vbmeta.img"]
    assert loaded.dynamic_partitions
    assert any("afptool-rs" in command for command in runner.commands)


def test_missing_project_state_raises_warning_error(tmp_path):
    with pytest.raises(UnpackFlowError, match="project"):
        run_unpack_analyze_backend(None, None, _paths(tmp_path), runner=FakeRunner())


def test_missing_tool_raises_clear_error(tmp_path):
    paths = _paths(tmp_path, complete_tools=False)
    state, state_path = _state(tmp_path)
    runner = FakeRunner(Path(state.work_dir), Path(state.reports_dir))

    with pytest.raises(Exception, match="afptool-rs"):
        run_unpack_analyze_backend(state, state_path, paths, runner=runner)

    assert runner.commands == []


def test_lpunpack_super_success_updates_state_source_paths(tmp_path):
    paths = _paths(tmp_path)
    state, state_path = _state(tmp_path)
    image_dir = Path(state.image_dir)
    (image_dir / "super.img").write_bytes(SPARSE_MAGIC + b"payload")
    Path(state.reports_dir, "lpdump_original.txt").write_text(
        (FIXTURES / "lpdump_rk3318_ab.txt").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    refresh_partition_explorer_state(state, state_path)
    parts_dir = Path(state.work_dir) / "parts"
    runner = FakeRunner(parts_dir=parts_dir)

    extract_super_partitions_backend(state, state_path, paths, runner=runner)
    loaded = load_project_state(state_path)

    assert loaded.parts_dir == str(parts_dir)
    assert loaded.extracted_partition_images["product_a"] == str(parts_dir / "product_a.img")
    product = {partition.name: partition for partition in loaded.dynamic_partitions}["product_a"]
    assert product.source_image_path == str(parts_dir / "product_a.img")
    assert any("lpunpack" in command for command in runner.commands)


def test_empty_image_folder_refresh_does_not_crash(tmp_path):
    state, state_path = _state(tmp_path)

    result = refresh_partition_explorer_state(state, state_path)

    assert result.result.detected_images == ()
    assert result.result.warnings


def test_unpack_tab_has_no_direct_process_invocation():
    source = inspect.getsource(unpack_tab)

    assert "subprocess" not in source
    assert "wsl.exe" not in source
    assert "Popen" not in source
