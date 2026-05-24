import inspect
from types import SimpleNamespace

import pytest

from core import super_image
from core.app_paths import AppPaths
from core.path_utils import shell_quote, windows_path_to_wsl
from core.super_image import SuperImageWorkflowError, extract_dynamic_partitions
from core.tool_config import load_bundled_tool_config


SPARSE_MAGIC = b"\x3a\xff\x26\xed"


class FakeRunner:
    def __init__(self, parts_dir=None):
        self.commands = []
        self.parts_dir = parts_dir

    def run(self, command, **kwargs):
        self.commands.append(command)
        if "lpunpack" in command and self.parts_dir is not None:
            self.parts_dir.mkdir(parents=True, exist_ok=True)
            (self.parts_dir / "system_a.img").write_bytes(b"system")
            (self.parts_dir / "product_a.img").write_bytes(b"product")
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


def _create_tools(tmp_path, *, include_simg2img=True, include_lpunpack=True):
    paths = _paths(tmp_path)
    (paths.tools_dir / "lptools").mkdir(parents=True)
    if include_simg2img:
        (paths.tools_dir / "lptools" / "simg2img").write_text("tool", encoding="utf-8")
    if include_lpunpack:
        (paths.tools_dir / "lptools" / "lpunpack").write_text("tool", encoding="utf-8")
    return load_bundled_tool_config(paths)


def test_sparse_super_runs_simg2img_before_lpunpack(tmp_path):
    tools = _create_tools(tmp_path)
    super_img = tmp_path / "Image" / "super.img"
    super_img.parent.mkdir()
    super_img.write_bytes(SPARSE_MAGIC + b"payload")
    parts_dir = tmp_path / "work" / "parts"

    result = extract_dynamic_partitions(
        super_img,
        tmp_path / "work",
        parts_dir,
        tools,
        FakeRunner(parts_dir),
    )

    assert result.is_sparse is True
    assert len(result.commands_run) == 2
    assert "simg2img" in result.commands_run[0]
    assert "lpunpack" in result.commands_run[1]
    assert [path.name for path in result.extracted_images] == ["product_a.img", "system_a.img"]


def test_raw_super_skips_simg2img_and_runs_lpunpack(tmp_path):
    tools = _create_tools(tmp_path)
    super_img = tmp_path / "Image" / "super.img"
    super_img.parent.mkdir()
    super_img.write_bytes(b"RAWIMAGE")
    parts_dir = tmp_path / "work" / "parts"

    result = extract_dynamic_partitions(
        super_img,
        tmp_path / "work",
        parts_dir,
        tools,
        FakeRunner(parts_dir),
    )

    assert result.is_sparse is False
    assert len(result.commands_run) == 1
    assert "lptools/simg2img" not in result.commands_run[0]
    assert "lpunpack" in result.commands_run[0]


def test_expected_partition_warning_when_missing(tmp_path):
    tools = _create_tools(tmp_path)
    super_img = tmp_path / "super.img"
    super_img.write_bytes(b"RAWIMAGE")
    parts_dir = tmp_path / "parts"

    result = extract_dynamic_partitions(
        super_img,
        tmp_path / "work",
        parts_dir,
        tools,
        FakeRunner(parts_dir),
        expected_partitions=("system_a", "vendor_a"),
    )

    assert any("vendor_a" in warning for warning in result.warnings)


def test_missing_super_img_raises(tmp_path):
    tools = _create_tools(tmp_path)

    with pytest.raises(SuperImageWorkflowError, match="super.img"):
        extract_dynamic_partitions(
            tmp_path / "missing.img",
            tmp_path / "work",
            tmp_path / "parts",
            tools,
            FakeRunner(),
        )


def test_missing_lpunpack_raises(tmp_path):
    tools = _create_tools(tmp_path, include_lpunpack=False)
    super_img = tmp_path / "super.img"
    super_img.write_bytes(b"RAWIMAGE")

    with pytest.raises(SuperImageWorkflowError, match="lpunpack"):
        extract_dynamic_partitions(super_img, tmp_path / "work", tmp_path / "parts", tools, FakeRunner())


def test_missing_simg2img_when_sparse_raises(tmp_path):
    tools = _create_tools(tmp_path, include_simg2img=False)
    super_img = tmp_path / "super.img"
    super_img.write_bytes(SPARSE_MAGIC + b"payload")

    with pytest.raises(SuperImageWorkflowError, match="simg2img"):
        extract_dynamic_partitions(super_img, tmp_path / "work", tmp_path / "parts", tools, FakeRunner())


def test_lpunpack_command_quotes_paths_with_spaces(tmp_path):
    tools = _create_tools(tmp_path)
    root = tmp_path / "ROM Box"
    super_img = root / "Image Files" / "super.img"
    super_img.parent.mkdir(parents=True)
    super_img.write_bytes(b"RAWIMAGE")
    parts_dir = root / "parts dir"

    result = extract_dynamic_partitions(
        super_img,
        root / "work dir",
        parts_dir,
        tools,
        FakeRunner(parts_dir),
    )

    assert shell_quote(windows_path_to_wsl(super_img)) in result.commands_run[0]
    assert shell_quote(windows_path_to_wsl(parts_dir)) in result.commands_run[0]


def test_super_image_lpunpack_has_no_direct_process_invocation():
    source = inspect.getsource(super_image)

    assert "subprocess" not in source
    assert "wsl.exe" not in source
    assert "Popen" not in source
