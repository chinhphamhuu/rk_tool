import inspect
from types import SimpleNamespace

import pytest

from core import super_image
from core.app_paths import AppPaths
from core.path_utils import shell_quote, windows_path_to_wsl
from core.super_image import SuperImageWorkflowError, analyze_super_image
from core.tool_config import load_bundled_tool_config


FIXTURES = __import__("pathlib").Path(__file__).parent / "fixtures"
SPARSE_MAGIC = b"\x3a\xff\x26\xed"


class FakeRunner:
    def __init__(self, report_path=None):
        self.commands = []
        self.report_path = report_path

    def run(self, command, **kwargs):
        self.commands.append(command)
        if "lpdump" in command and self.report_path is not None:
            self.report_path.parent.mkdir(parents=True, exist_ok=True)
            self.report_path.write_text(
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


def _create_tools(tmp_path, *, include_simg2img=True, include_lpdump=True):
    paths = _paths(tmp_path)
    (paths.tools_dir / "lptools").mkdir(parents=True)
    if include_simg2img:
        (paths.tools_dir / "lptools" / "simg2img").write_text("tool", encoding="utf-8")
    if include_lpdump:
        (paths.tools_dir / "lptools" / "lpdump").write_text("tool", encoding="utf-8")
    return load_bundled_tool_config(paths)


def test_sparse_super_runs_simg2img_then_lpdump(tmp_path):
    tools = _create_tools(tmp_path)
    super_img = tmp_path / "Image" / "super.img"
    super_img.parent.mkdir()
    super_img.write_bytes(SPARSE_MAGIC + b"payload")
    report_path = tmp_path / "work" / "reports" / "lpdump_original.txt"

    result = analyze_super_image(
        super_img,
        tmp_path / "work",
        report_path.parent,
        tools,
        FakeRunner(report_path),
    )

    assert result.is_sparse is True
    assert result.raw_super_img_path == tmp_path / "work" / "super" / "super.raw.img"
    assert result.lpdump_report_path == report_path
    assert len(result.commands_run) == 2
    assert "simg2img" in result.commands_run[0]
    assert "lpdump" in result.commands_run[1]
    assert result.metadata_summary is not None


def test_raw_super_skips_simg2img_and_runs_lpdump(tmp_path):
    tools = _create_tools(tmp_path)
    super_img = tmp_path / "Image" / "super.img"
    super_img.parent.mkdir()
    super_img.write_bytes(b"RAWIMAGE")
    report_path = tmp_path / "work" / "reports" / "lpdump_original.txt"

    result = analyze_super_image(
        super_img,
        tmp_path / "work",
        report_path.parent,
        tools,
        FakeRunner(report_path),
    )

    assert result.is_sparse is False
    assert result.raw_super_img_path == super_img
    assert len(result.commands_run) == 1
    assert "lptools/simg2img" not in result.commands_run[0]
    assert "lpdump" in result.commands_run[0]


def test_lpdump_command_quotes_paths_with_spaces(tmp_path):
    tools = _create_tools(tmp_path)
    root = tmp_path / "ROM Box"
    super_img = root / "Image Files" / "super.img"
    super_img.parent.mkdir(parents=True)
    super_img.write_bytes(b"RAWIMAGE")
    report_path = root / "work reports" / "lpdump_original.txt"

    result = analyze_super_image(
        super_img,
        root / "work dir",
        report_path.parent,
        tools,
        FakeRunner(report_path),
    )

    assert shell_quote(windows_path_to_wsl(super_img)) in result.commands_run[0]
    assert shell_quote(windows_path_to_wsl(report_path)) in result.commands_run[0]


def test_missing_super_img_raises(tmp_path):
    tools = _create_tools(tmp_path)

    with pytest.raises(SuperImageWorkflowError, match="super.img"):
        analyze_super_image(
            tmp_path / "missing.img",
            tmp_path / "work",
            tmp_path / "work" / "reports",
            tools,
            FakeRunner(),
        )


def test_missing_lpdump_raises(tmp_path):
    tools = _create_tools(tmp_path, include_lpdump=False)
    super_img = tmp_path / "super.img"
    super_img.write_bytes(b"RAWIMAGE")

    with pytest.raises(SuperImageWorkflowError, match="lpdump"):
        analyze_super_image(super_img, tmp_path / "work", tmp_path / "reports", tools, FakeRunner())


def test_missing_simg2img_for_sparse_super_raises(tmp_path):
    tools = _create_tools(tmp_path, include_simg2img=False)
    super_img = tmp_path / "super.img"
    super_img.write_bytes(SPARSE_MAGIC + b"payload")

    with pytest.raises(SuperImageWorkflowError, match="simg2img"):
        analyze_super_image(super_img, tmp_path / "work", tmp_path / "reports", tools, FakeRunner())


def test_super_image_module_has_no_direct_process_invocation():
    source = inspect.getsource(super_image)

    assert "subprocess" not in source
    assert "wsl.exe" not in source
    assert "Popen" not in source
