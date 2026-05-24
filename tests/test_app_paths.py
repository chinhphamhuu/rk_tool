import core.app_paths as app_paths
from core.app_paths import AppPaths


def test_app_paths_detect():
    paths = AppPaths.detect()
    assert paths.app_root.exists()
    assert paths.workspace_dir.name == "workspace"


def test_detect_app_root_python_mode(monkeypatch, tmp_path):
    fake_root = tmp_path / "app"
    fake_module = fake_root / "core" / "app_paths.py"

    monkeypatch.setattr(app_paths.sys, "frozen", False, raising=False)
    monkeypatch.setattr(app_paths, "__file__", str(fake_module))

    paths = AppPaths.detect()

    assert paths.app_root == fake_root.resolve()
    assert paths.tools_dir == fake_root.resolve() / "tools"
    assert paths.workspace_dir == fake_root.resolve() / "workspace"


def test_detect_app_root_frozen_exe(monkeypatch, tmp_path):
    fake_root = tmp_path / "dist"
    fake_exe = fake_root / "RockchipTool.exe"

    monkeypatch.setattr(app_paths.sys, "frozen", True, raising=False)
    monkeypatch.setattr(app_paths.sys, "executable", str(fake_exe))

    paths = AppPaths.detect()

    assert paths.app_root == fake_root.resolve()
    assert paths.workspace_dir == fake_root.resolve() / "workspace"


def test_ensure_workspace_creates_required_directories(tmp_path):
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

    paths.ensure_workspace()

    for directory in (
        paths.workspace_dir,
        paths.projects_dir,
        paths.output_dir,
        paths.logs_dir,
        paths.temp_dir,
    ):
        assert directory.is_dir()
