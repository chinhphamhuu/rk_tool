from core.app_paths import AppPaths
from core.tool_config import TOOL_MISSING, TOOL_OK, load_bundled_tool_config


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


def create_required_tools(tools_dir):
    (tools_dir / "afptool-rs").mkdir(parents=True)
    (tools_dir / "afptool-rs" / "afptool-rs").write_text("", encoding="utf-8")
    (tools_dir / "lptools").mkdir(parents=True)
    (tools_dir / "lptools" / "simg2img").write_text("", encoding="utf-8")
    (tools_dir / "lptools" / "lpunpack").write_text("", encoding="utf-8")
    (tools_dir / "lptools" / "lpmake").write_text("", encoding="utf-8")
    (tools_dir / "lptools" / "lpdump").write_text("", encoding="utf-8")
    (tools_dir / "avbtool").mkdir(parents=True)
    (tools_dir / "avbtool" / "avbtool.py").write_text("# avbtool placeholder\n", encoding="utf-8")


def test_load_bundled_tool_config_all_ok(tmp_path):
    paths = make_paths(tmp_path)
    create_required_tools(paths.tools_dir)

    config = load_bundled_tool_config(paths)

    assert config.tools_dir == paths.tools_dir
    assert config.all_ok
    assert config.missing_tools == ()
    assert [tool.name for tool in config.tools] == [
        "afptool-rs",
        "simg2img",
        "lpunpack",
        "lpmake",
        "lpdump",
        "avbtool.py",
    ]
    assert all(tool.status == TOOL_OK for tool in config.tools)
    assert config.by_name("afptool-rs").path == paths.tools_dir / "afptool-rs" / "afptool-rs"
    assert config.by_name("simg2img").path == paths.tools_dir / "lptools" / "simg2img"
    assert config.by_name("avbtool.py").path == paths.tools_dir / "avbtool" / "avbtool.py"


def test_load_bundled_tool_config_reports_missing_tools(tmp_path):
    paths = make_paths(tmp_path)
    (paths.tools_dir / "afptool-rs").mkdir(parents=True)
    (paths.tools_dir / "afptool-rs" / "afptool-rs").write_text("", encoding="utf-8")
    (paths.tools_dir / "lptools").mkdir(parents=True)
    (paths.tools_dir / "lptools" / "lpunpack").write_text("", encoding="utf-8")

    config = load_bundled_tool_config(paths)

    assert not config.all_ok
    missing = {tool.name: tool for tool in config.missing_tools}
    assert set(missing) == {"simg2img", "lpmake", "lpdump", "avbtool.py"}
    assert missing["simg2img"].path == paths.tools_dir / "lptools" / "simg2img"
    assert missing["lpmake"].status == TOOL_MISSING
    assert missing["lpdump"].path == paths.tools_dir / "lptools" / "lpdump"
    assert missing["avbtool.py"].path == paths.tools_dir / "avbtool" / "avbtool.py"


def test_afptool_rs_must_be_binary_file(tmp_path):
    paths = make_paths(tmp_path)
    (paths.tools_dir / "afptool-rs" / "afptool-rs").mkdir(parents=True)

    config = load_bundled_tool_config(paths)

    afptool = config.by_name("afptool-rs")
    assert afptool.status == TOOL_MISSING
    assert afptool.expected_kind == "file"
