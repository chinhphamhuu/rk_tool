import inspect
from pathlib import Path

import pytest

from core import project_state
from core.partition_explorer import build_partition_explorer
from core.project_state import (
    ProjectStateError,
    create_project_state,
    get_partition_source_image,
    load_project_state,
    mark_partition_extracted,
    mark_partition_modified,
    save_project_state,
    update_partition_explorer_state,
)


FIXTURES = Path(__file__).parent / "fixtures"
SPARSE_MAGIC = b"\x3a\xff\x26\xed"


def _make_state(tmp_path):
    project_dir = tmp_path / "projects" / "Dự án ROM"
    project_dir.mkdir(parents=True)
    return create_project_state(
        project_name="Dự án ROM",
        original_rom_path=tmp_path / "ROM gốc" / "update.img",
        project_dir=project_dir,
        image_dir=project_dir / "work" / "update" / "Image",
        editable_dir=project_dir / "editable",
        work_dir=project_dir / "work",
        output_dir=project_dir / "output",
        reports_dir=project_dir / "reports",
    )


def test_create_save_load_project_state(tmp_path):
    state = _make_state(tmp_path)
    state_file = tmp_path / "state.json"

    save_project_state(state, state_file)
    loaded = load_project_state(state_file)

    assert loaded.project_name == state.project_name
    assert loaded.project_dir == state.project_dir
    assert loaded.schema_version == 1


def test_unicode_path_and_project_name_are_preserved(tmp_path):
    state = _make_state(tmp_path)
    state_file = tmp_path / "trạng thái.json"

    save_project_state(state, state_file)
    raw_json = state_file.read_text(encoding="utf-8")
    loaded = load_project_state(state_file)

    assert "Dự án ROM" in raw_json
    assert "ROM gốc" in raw_json
    assert loaded.project_name == "Dự án ROM"
    assert "ROM gốc" in loaded.original_rom_path


def test_update_partition_explorer_state_saves_detected_dynamic_and_avb(tmp_path):
    state = _make_state(tmp_path)
    image_dir = Path(state.image_dir)
    image_dir.mkdir(parents=True)
    (image_dir / "super.img").write_bytes(SPARSE_MAGIC + b"payload")
    (image_dir / "vbmeta.img").write_bytes(b"vbmeta")

    explorer = build_partition_explorer(
        image_dir,
        vbmeta_report_path=FIXTURES / "vbmeta_with_descriptors.txt",
        lpdump_report_path=FIXTURES / "lpdump_rk3318_ab.txt",
        editable_root=Path(state.editable_dir),
    )

    update_partition_explorer_state(state, explorer)

    assert [image.name for image in state.detected_images] == ["super.img", "vbmeta.img"]
    assert state.detected_images[0].is_sparse is True
    assert [partition.name for partition in state.dynamic_partitions] == [
        "system_a",
        "product_a",
        "vendor_a",
        "odm_a",
        "system_ext_a",
    ]
    assert state.avb_summary is not None
    assert state.avb_summary.affected_partitions == ["system", "product", "vendor"]


def test_mark_partition_extracted(tmp_path):
    state = _make_state(tmp_path)
    image_dir = Path(state.image_dir)
    image_dir.mkdir(parents=True)
    explorer = build_partition_explorer(
        image_dir,
        lpdump_report_path=FIXTURES / "lpdump_rk3318_ab.txt",
        editable_root=Path(state.editable_dir),
    )
    update_partition_explorer_state(state, explorer)

    editable_dir = Path(state.editable_dir) / "product_a"
    mark_partition_extracted(state, "product_a", editable_dir)

    assert state.extracted_partitions["product_a"] == str(editable_dir)
    product = {partition.name: partition for partition in state.dynamic_partitions}["product_a"]
    assert product.extracted is True
    assert product.editable_dir == str(editable_dir)


def test_mark_partition_modified(tmp_path):
    state = _make_state(tmp_path)

    mark_partition_modified(state, "product_a")
    mark_partition_modified(state, "product_a")

    assert state.modified_partitions == ["product_a"]


def test_get_partition_source_image_prefers_modified_when_marked(tmp_path):
    state = _make_state(tmp_path)

    assert get_partition_source_image(state, "product_a") == Path(state.project_dir) / "parts" / "product_a.img"

    mark_partition_modified(state, "product_a")

    assert get_partition_source_image(state, "product_a") == Path(state.project_dir) / "modified" / "product_a.img"


def test_missing_state_file_raises_clear_error(tmp_path):
    with pytest.raises(ProjectStateError, match="does not exist"):
        load_project_state(tmp_path / "missing.json")


def test_invalid_json_raises_clear_error(tmp_path):
    state_file = tmp_path / "state.json"
    state_file.write_text("{ not json", encoding="utf-8")

    with pytest.raises(ProjectStateError, match="invalid JSON"):
        load_project_state(state_file)


def test_no_subprocess_wsl_or_tool_calls_in_project_state():
    source = inspect.getsource(project_state)

    assert "subprocess" not in source
    assert "wsl.exe" not in source
    assert "Popen" not in source
    assert "afptool" not in source
