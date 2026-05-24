import inspect
from pathlib import Path

import pytest

from core.project_state import create_project_state, load_project_state, save_project_state
from gui import unpack_tab
from gui.unpack_tab import UnpackFlowError, refresh_partition_explorer_state


FIXTURES = Path(__file__).parent / "fixtures"
SPARSE_MAGIC = b"\x3a\xff\x26\xed"


def _make_state(tmp_path):
    project_dir = tmp_path / "workspace" / "projects" / "demo"
    image_dir = project_dir / "work" / "update" / "Image"
    reports_dir = project_dir / "work" / "reports"
    for path in (image_dir, reports_dir, project_dir / "editable"):
        path.mkdir(parents=True, exist_ok=True)
    state = create_project_state(
        project_name="demo",
        original_rom_path=tmp_path / "update.img",
        project_dir=project_dir,
        image_dir=image_dir,
        editable_dir=project_dir / "editable",
        work_dir=project_dir / "work",
        output_dir=project_dir / "output",
        reports_dir=reports_dir,
    )
    state_path = project_dir / "project_state.json"
    save_project_state(state, state_path)
    return state, state_path


def test_refresh_partition_explorer_updates_and_saves_state(tmp_path):
    state, state_path = _make_state(tmp_path)
    image_dir = Path(state.image_dir)
    (image_dir / "super.img").write_bytes(SPARSE_MAGIC + b"payload")
    (image_dir / "vbmeta.img").write_bytes(b"vbmeta")
    Path(state.reports_dir, "lpdump_original.txt").write_text(
        (FIXTURES / "lpdump_rk3318_ab.txt").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    Path(state.reports_dir, "vbmeta_info.txt").write_text(
        (FIXTURES / "vbmeta_with_descriptors.txt").read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    refreshed = refresh_partition_explorer_state(state, state_path)
    loaded = load_project_state(state_path)

    assert refreshed.result.detected_images[0].name == "super.img"
    assert loaded.detected_images[0].name == "super.img"
    assert loaded.detected_images[0].is_sparse is True
    assert [partition.name for partition in loaded.dynamic_partitions] == [
        "system_a",
        "product_a",
        "vendor_a",
        "odm_a",
        "system_ext_a",
    ]
    assert loaded.avb_summary is not None
    assert loaded.avb_summary.affected_partitions == ["system", "product", "vendor"]


def test_refresh_empty_image_folder_does_not_crash(tmp_path):
    state, state_path = _make_state(tmp_path)

    refreshed = refresh_partition_explorer_state(state, state_path)
    loaded = load_project_state(state_path)

    assert refreshed.result.detected_images == ()
    assert loaded.detected_images == []
    assert any("empty" in warning for warning in refreshed.result.warnings)


def test_refresh_without_project_state_raises_warning_error():
    with pytest.raises(UnpackFlowError, match="project"):
        refresh_partition_explorer_state(None)


def test_unpack_tab_source_has_no_direct_process_invocation():
    source = inspect.getsource(unpack_tab)

    assert "subprocess" not in source
    assert "wsl.exe" not in source
    assert "Popen" not in source
    assert "lpmake" not in source
