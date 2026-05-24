import inspect
import json
from types import SimpleNamespace

import pytest

from core import editable_extractor
from core.editable_extractor import EditableExtractError, extract_partition_to_editable
from core.path_utils import shell_quote, windows_path_to_wsl


DUMPE2FS_SAMPLE = """
Filesystem volume name:   product_a
Filesystem features:      has_journal ext_attr extent 64bit metadata_csum
Block count:              16
Free blocks:              4
Block size:               4096
"""


class FakeRunner:
    def __init__(self, editable_dir=None, fail_on=None):
        self.commands = []
        self.editable_dir = editable_dir
        self.fail_on = fail_on

    def run(self, command, **kwargs):
        self.commands.append(command)
        if self.fail_on and self.fail_on in command:
            raise RuntimeError("forced failure")
        if command.startswith("command -v "):
            return SimpleNamespace(stdout="/usr/bin/" + command.rsplit(" ", 1)[-1] + "\n", stderr="", exit_code=0)
        if "e2fsck" in command:
            return SimpleNamespace(stdout="clean\n", stderr="", exit_code=0)
        if "dumpe2fs" in command:
            return SimpleNamespace(stdout=DUMPE2FS_SAMPLE, stderr="", exit_code=0)
        if "debugfs" in command and self.editable_dir is not None:
            (self.editable_dir / "app").mkdir(parents=True, exist_ok=True)
            (self.editable_dir / "app" / "Demo.apk").write_bytes(b"apk")
            return SimpleNamespace(stdout="rdump done\n", stderr="", exit_code=0)
        return SimpleNamespace(stdout="", stderr="", exit_code=0)


def test_extract_workflow_success_with_fake_runner(tmp_path):
    source = tmp_path / "work" / "parts" / "product_a.img"
    source.parent.mkdir(parents=True)
    source.write_bytes(b"image")
    editable_root = tmp_path / "editable"
    editable_dir = editable_root / "product_a"
    reports_dir = tmp_path / "work" / "reports"
    runner = FakeRunner(editable_dir)

    result = extract_partition_to_editable(
        "product_a",
        source,
        editable_root,
        tmp_path / "work",
        reports_dir,
        runner,
    )

    assert any(command == "command -v debugfs" for command in runner.commands)
    assert any(command == "command -v e2fsck" for command in runner.commands)
    assert any(command == "command -v dumpe2fs" for command in runner.commands)
    assert any("debugfs" in command and "rdump" in command for command in runner.commands)
    assert result.e2fsck_report_path.read_text(encoding="utf-8") == "clean\n"
    assert "Block count" in result.dumpe2fs_report_path.read_text(encoding="utf-8")
    assert result.extracted_file_count == 1
    manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
    assert manifest["partition_name"] == "product_a"
    assert manifest["file_count"] == 1
    assert manifest["directory_count"] == 1
    assert manifest["note"] == "extracted read-only by debugfs rdump"


def test_source_image_missing_raises(tmp_path):
    with pytest.raises(EditableExtractError, match="Source image"):
        extract_partition_to_editable(
            "product_a",
            tmp_path / "missing.img",
            tmp_path / "editable",
            tmp_path / "work",
            tmp_path / "reports",
            FakeRunner(),
        )


def test_existing_editable_folder_without_overwrite_raises(tmp_path):
    source = tmp_path / "parts" / "product_a.img"
    source.parent.mkdir()
    source.write_bytes(b"image")
    editable_dir = tmp_path / "editable" / "product_a"
    editable_dir.mkdir(parents=True)
    (editable_dir / "old.txt").write_text("old", encoding="utf-8")

    with pytest.raises(EditableExtractError, match="not empty"):
        extract_partition_to_editable(
            "product_a",
            source,
            tmp_path / "editable",
            tmp_path / "work",
            tmp_path / "reports",
            FakeRunner(editable_dir),
        )


def test_overwrite_clears_existing_folder(tmp_path):
    source = tmp_path / "parts" / "product_a.img"
    source.parent.mkdir()
    source.write_bytes(b"image")
    editable_dir = tmp_path / "editable" / "product_a"
    editable_dir.mkdir(parents=True)
    (editable_dir / "old.txt").write_text("old", encoding="utf-8")

    extract_partition_to_editable(
        "product_a",
        source,
        tmp_path / "editable",
        tmp_path / "work",
        tmp_path / "reports",
        FakeRunner(editable_dir),
        overwrite=True,
    )

    assert not (editable_dir / "old.txt").exists()
    assert (editable_dir / "app" / "Demo.apk").is_file()


def test_paths_with_spaces_are_quoted(tmp_path):
    root = tmp_path / "ROM Box"
    source = root / "parts dir" / "product_a.img"
    source.parent.mkdir(parents=True)
    source.write_bytes(b"image")
    editable_root = root / "editable folders"
    runner = FakeRunner(editable_root / "product_a")

    result = extract_partition_to_editable(
        "product_a",
        source,
        editable_root,
        root / "work dir",
        root / "reports dir",
        runner,
    )

    debugfs_command = [command for command in result.commands_run if command.startswith("debugfs")][0]
    assert shell_quote(windows_path_to_wsl(source)) in debugfs_command
    assert shell_quote(f"rdump / {windows_path_to_wsl(editable_root / 'product_a')}") in debugfs_command


def test_unicode_paths_do_not_error(tmp_path):
    source = tmp_path / "Thư mục ROM" / "parts" / "system_a.img"
    source.parent.mkdir(parents=True)
    source.write_bytes(b"image")
    editable_root = tmp_path / "editable"
    runner = FakeRunner(editable_root / "system_a")

    result = extract_partition_to_editable(
        "system_a",
        source,
        editable_root,
        tmp_path / "work",
        tmp_path / "reports",
        runner,
    )

    assert "Thư mục ROM" in result.commands_run[-1]


def test_command_failure_raises_clear_error(tmp_path):
    source = tmp_path / "parts" / "product_a.img"
    source.parent.mkdir()
    source.write_bytes(b"image")

    with pytest.raises(EditableExtractError, match="Command failed"):
        extract_partition_to_editable(
            "product_a",
            source,
            tmp_path / "editable",
            tmp_path / "work",
            tmp_path / "reports",
            FakeRunner(fail_on="dumpe2fs"),
        )


def test_editable_extractor_has_no_direct_process_invocation():
    source = inspect.getsource(editable_extractor)

    assert "subprocess" not in source
    assert "wsl.exe" not in source
    assert "Popen" not in source
    assert "sudo " not in source
    assert "mount -o loop" not in source
