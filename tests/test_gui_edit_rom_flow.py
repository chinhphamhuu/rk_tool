import inspect
from pathlib import Path
from types import SimpleNamespace

import pytest

from core.project_state import (
    ProjectDynamicPartition,
    create_project_state,
    load_project_state,
    save_project_state,
    update_lpunpack_state,
)
from gui import edit_rom_tab
from gui.edit_rom_tab import (
    EditRomFlowError,
    extract_editable_partition_backend,
    list_editable_partition_rows,
)


DUMPE2FS_SAMPLE = """
Filesystem volume name:   product_a
Filesystem features:      has_journal ext_attr extent
Block count:              16
Free blocks:              4
Block size:               4096
"""


class FakeRunner:
    def __init__(self, editable_dir=None):
        self.commands = []
        self.editable_dir = editable_dir

    def run(self, command, **kwargs):
        self.commands.append(command)
        if command.startswith("command -v "):
            return SimpleNamespace(stdout="/usr/bin/tool\n", stderr="", exit_code=0)
        if "e2fsck" in command:
            return SimpleNamespace(stdout="clean\n", stderr="", exit_code=0)
        if "dumpe2fs" in command:
            return SimpleNamespace(stdout=DUMPE2FS_SAMPLE, stderr="", exit_code=0)
        if "debugfs" in command and self.editable_dir is not None:
            (self.editable_dir / "etc").mkdir(parents=True, exist_ok=True)
            (self.editable_dir / "etc" / "build.prop").write_text("demo", encoding="utf-8")
        return SimpleNamespace(stdout="", stderr="", exit_code=0)


def _state(tmp_path):
    project_dir = tmp_path / "workspace" / "projects" / "demo"
    work_dir = project_dir / "work"
    state = create_project_state(
        project_name="demo",
        original_rom_path=tmp_path / "update.img",
        project_dir=project_dir,
        image_dir=work_dir / "update" / "Image",
        editable_dir=project_dir / "editable",
        work_dir=work_dir,
        output_dir=project_dir / "output",
        reports_dir=work_dir / "reports",
    )
    state.dynamic_partitions = [
        ProjectDynamicPartition(
            name="product_a",
            group_name="group",
            size_bytes=4096,
            readonly=True,
            source_image_path=None,
            editable_dir=str(Path(state.editable_dir) / "product_a"),
            supported_actions=["extract_tree", "view_info"],
            risk_level="info",
        )
    ]
    state_path = project_dir / "project_state.json"
    state_path.parent.mkdir(parents=True, exist_ok=True)
    save_project_state(state, state_path)
    return state, state_path


def test_no_project_returns_empty_rows_and_extract_raises(tmp_path):
    assert list_editable_partition_rows(None) == []
    with pytest.raises(EditRomFlowError, match="project"):
        extract_editable_partition_backend(None, None, "product_a", runner=FakeRunner())


def test_no_parts_image_reports_missing_source(tmp_path):
    state, state_path = _state(tmp_path)

    rows = list_editable_partition_rows(state)

    assert rows[0].partition_name == "product_a"
    assert rows[0].status == "missing_source"
    with pytest.raises(EditRomFlowError, match="Unpack super"):
        extract_editable_partition_backend(state, state_path, "product_a", runner=FakeRunner())


def test_extract_selected_partition_updates_state(tmp_path):
    state, state_path = _state(tmp_path)
    parts_dir = Path(state.work_dir) / "parts"
    product_img = parts_dir / "product_a.img"
    product_img.parent.mkdir(parents=True)
    product_img.write_bytes(b"image")
    update_lpunpack_state(state, parts_dir, Path(state.work_dir) / "super" / "super.raw.img", [product_img])
    save_project_state(state, state_path)
    editable_dir = Path(state.editable_dir) / "product_a"
    runner = FakeRunner(editable_dir)

    result = extract_editable_partition_backend(
        state,
        state_path,
        "product_a",
        runner=runner,
    )
    loaded = load_project_state(state_path)

    assert result.result.partition_name == "product_a"
    assert loaded.extracted_partitions["product_a"] == str(editable_dir)
    assert loaded.editable_partitions["product_a"] == str(editable_dir)
    assert loaded.dynamic_partitions[0].editable_dir == str(editable_dir)
    assert any("debugfs" in command for command in runner.commands)


def test_edit_rom_tab_source_has_no_direct_process_invocation():
    source = inspect.getsource(edit_rom_tab)

    assert "subprocess" not in source
    assert "wsl.exe" not in source
    assert "Popen" not in source
