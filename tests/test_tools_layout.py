from pathlib import Path

from core.app_paths import AppPaths
from core.tool_config import REQUIRED_BUNDLED_TOOLS, TOOL_MISSING, TOOL_OK, load_bundled_tool_config


RUNTIME_FILES = (
    Path("core/app_paths.py"),
    Path("core/tool_config.py"),
    Path("core/rkaf.py"),
    Path("core/super_image.py"),
    Path("core/workflow.py"),
)


def make_paths(tmp_path):
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


def touch_tool(root, relative_path):
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("#!/usr/bin/env sh\n", encoding="utf-8")
    return path


def test_required_bundled_tool_specs_use_standard_layout():
    specs = {spec.name: spec.relative_path.as_posix() for spec in REQUIRED_BUNDLED_TOOLS}

    assert specs == {
        "afptool-rs": "afptool-rs/afptool-rs",
        "simg2img": "lptools/simg2img",
        "lpunpack": "lptools/lpunpack",
        "lpmake": "lptools/lpmake",
        "lpdump": "lptools/lpdump",
        "avbtool.py": "avbtool/avbtool.py",
    }


def test_tool_config_detects_all_standard_tools(tmp_path):
    paths = make_paths(tmp_path)
    for spec in REQUIRED_BUNDLED_TOOLS:
        touch_tool(paths.tools_dir, spec.relative_path)

    config = load_bundled_tool_config(paths)

    assert config.all_ok
    assert {tool.name: tool.status for tool in config.tools} == {
        spec.name: TOOL_OK for spec in REQUIRED_BUNDLED_TOOLS
    }


def test_tool_config_handles_empty_tools_folder(tmp_path):
    paths = make_paths(tmp_path)
    paths.tools_dir.mkdir(parents=True)

    config = load_bundled_tool_config(paths)

    assert not config.all_ok
    assert {tool.name: tool.status for tool in config.tools} == {
        spec.name: TOOL_MISSING for spec in REQUIRED_BUNDLED_TOOLS
    }


def test_runtime_code_does_not_hard_code_local_tool_source_or_app_root():
    forbidden = (
        "G:\\codex",
        "G:/codex",
        "/mnt/g/codex/tools",
        "/mnt/g/codex/rockchip_tool_updated_structure",
    )

    for runtime_file in RUNTIME_FILES:
        text = runtime_file.read_text(encoding="utf-8")
        for marker in forbidden:
            assert marker not in text, f"{runtime_file} contains hard-coded path {marker}"


def test_tool_scripts_exist():
    assert Path("scripts/normalize_existing_tools.sh").is_file()
    assert Path("scripts/check_tools.sh").is_file()

    normalize_text = Path("scripts/normalize_existing_tools.sh").read_text(encoding="utf-8")
    assert 'SOURCE_TOOLS="${1:-../tools}"' in normalize_text
    assert 'command -v "${tool_name}"' in normalize_text
    assert "APP_ROOT" in normalize_text
