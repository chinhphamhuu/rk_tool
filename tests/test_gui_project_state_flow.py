import inspect
from pathlib import Path

import pytest

from core.app_paths import AppPaths
from core.project_state import load_project_state
from gui import project_tab
from gui.project_tab import ProjectCreationError, create_project_from_inputs


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


def _create_required_tools(paths):
    (paths.tools_dir / "afptool-rs").mkdir(parents=True)
    (paths.tools_dir / "lptools").mkdir(parents=True)
    (paths.tools_dir / "lptools" / "lpunpack").write_text("tool", encoding="utf-8")
    (paths.tools_dir / "lptools" / "lpmake").write_text("tool", encoding="utf-8")
    (paths.tools_dir / "lptools" / "lpdump").write_text("tool", encoding="utf-8")
    (paths.tools_dir / "avbtool").mkdir(parents=True)
    (paths.tools_dir / "avbtool" / "avbtool.py").write_text("tool", encoding="utf-8")


def test_project_tab_helper_creates_project_state_and_dirs(tmp_path):
    paths = _paths(tmp_path)
    _create_required_tools(paths)
    rom = tmp_path / "update.img"
    rom.write_bytes(b"rom")
    apk = tmp_path / "app.apk"
    apk.write_bytes(b"apk")

    created = create_project_from_inputs(paths, rom, "rk3318_android11", apk)
    state = load_project_state(created.state_path)
    project_dir = paths.projects_dir / "rk3318_android11"

    assert created.state_path == project_dir / "project_state.json"
    assert state.project_name == "rk3318_android11"
    assert state.original_rom_path == str(rom)
    assert state.selected_apk_path == str(apk)
    assert state.project_dir == str(project_dir)
    assert state.image_dir == str(project_dir / "work" / "update" / "Image")
    assert state.reports_dir == str(project_dir / "work" / "reports")
    for relative in (
        "work",
        "work/update",
        "work/update/Image",
        "work/reports",
        "work/parts",
        "work/modified",
        "editable",
        "output",
        "logs",
    ):
        assert (project_dir / relative).is_dir()


def test_project_tab_helper_preserves_unicode_project_name(tmp_path):
    paths = _paths(tmp_path)
    rom = tmp_path / "ROM gốc.img"
    rom.write_bytes(b"rom")

    created = create_project_from_inputs(paths, rom, "Dự án ROM")
    state = load_project_state(created.state_path)

    assert state.project_name == "Dự án ROM"
    assert "Dự án ROM" in created.state_path.read_text(encoding="utf-8")


def test_project_tab_helper_rejects_existing_project(tmp_path):
    paths = _paths(tmp_path)
    rom = tmp_path / "update.img"
    rom.write_bytes(b"rom")

    create_project_from_inputs(paths, rom, "demo")

    with pytest.raises(ProjectCreationError, match="Project đã tồn tại"):
        create_project_from_inputs(paths, rom, "demo")


def test_project_tab_helper_validates_rom_and_project_name(tmp_path):
    paths = _paths(tmp_path)

    with pytest.raises(ProjectCreationError, match="Tên project"):
        create_project_from_inputs(paths, tmp_path / "missing.img", " ")

    with pytest.raises(ProjectCreationError, match="ROM gốc"):
        create_project_from_inputs(paths, tmp_path / "missing.img", "demo")


def test_project_tab_source_has_no_subprocess_or_tool_invocation():
    source = inspect.getsource(project_tab)

    assert "subprocess" not in source
    assert "wsl.exe" not in source
    assert "Popen" not in source
    assert "afptool" not in source
    assert "lpdump" not in source
