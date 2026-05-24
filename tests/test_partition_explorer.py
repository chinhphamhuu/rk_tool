import inspect
from pathlib import Path

import pytest

from core import partition_explorer
from core.partition_explorer import (
    PartitionExplorerError,
    build_partition_explorer,
    classify_partition_risk,
)


FIXTURES = Path(__file__).parent / "fixtures"
SPARSE_MAGIC = b"\x3a\xff\x26\xed"


def _write(path, content=b"DATA"):
    path.write_bytes(content)


def _image_by_name(result):
    return {image.name: image for image in result.detected_images}


def _partition_by_name(result):
    return {partition.name: partition for partition in result.dynamic_partitions}


def test_build_explorer_with_known_image_folder(tmp_path):
    image_dir = tmp_path / "Image"
    image_dir.mkdir()
    for name in [
        "super.img",
        "vbmeta.img",
        "boot.img",
        "recovery.img",
        "dtbo.img",
        "uboot.img",
        "trust.img",
        "parameter.txt",
    ]:
        _write(image_dir / name, b"RAWDATA")

    result = build_partition_explorer(image_dir)
    images = _image_by_name(result)

    assert list(images) == [
        "super.img",
        "vbmeta.img",
        "boot.img",
        "recovery.img",
        "dtbo.img",
        "uboot.img",
        "trust.img",
        "parameter.txt",
    ]
    assert images["super.img"].supported_actions == ("analyze", "unpack")
    assert images["vbmeta.img"].supported_actions == ("analyze_avb",)
    assert result.boot_images[0].name == "boot.img"
    assert {image.name for image in result.danger_images} == {"uboot.img", "trust.img"}


def test_super_img_sparse_status_true(tmp_path):
    image_dir = tmp_path / "Image"
    image_dir.mkdir()
    _write(image_dir / "super.img", SPARSE_MAGIC + b"payload")

    result = build_partition_explorer(image_dir)

    assert result.super_images[0].is_sparse is True
    assert result.super_images[0].status == "detected"


def test_super_img_raw_status_false(tmp_path):
    image_dir = tmp_path / "Image"
    image_dir.mkdir()
    _write(image_dir / "super.img", b"RAWDATA")

    result = build_partition_explorer(image_dir)

    assert result.super_images[0].is_sparse is False


def test_vbmeta_report_algorithm_none_has_low_risk(tmp_path):
    image_dir = tmp_path / "Image"
    image_dir.mkdir()
    _write(image_dir / "vbmeta.img", b"vbmeta")

    result = build_partition_explorer(
        image_dir,
        vbmeta_report_path=FIXTURES / "vbmeta_algorithm_none.txt",
    )

    assert result.avb_summary is not None
    assert result.avb_summary.risk_level == "low"
    assert result.avb_summary.affected_partitions == ()


def test_vbmeta_report_with_descriptors_warns_about_avb(tmp_path):
    image_dir = tmp_path / "Image"
    image_dir.mkdir()
    _write(image_dir / "vbmeta.img", b"vbmeta")

    result = build_partition_explorer(
        image_dir,
        vbmeta_report_path=FIXTURES / "vbmeta_with_descriptors.txt",
    )

    assert result.avb_summary is not None
    assert result.avb_summary.risk_level == "danger"
    assert result.avb_summary.affected_partitions == ("system", "product", "vendor")
    assert result.avb_summary.has_hash_descriptor is True
    assert result.avb_summary.has_hashtree_descriptor is True
    assert any("bootloop" in warning for warning in result.warnings)


def test_lpdump_ab_dynamic_partitions(tmp_path):
    image_dir = tmp_path / "Image"
    image_dir.mkdir()

    result = build_partition_explorer(
        image_dir,
        lpdump_report_path=FIXTURES / "lpdump_rk3318_ab.txt",
    )

    assert list(_partition_by_name(result)) == [
        "system_a",
        "product_a",
        "vendor_a",
        "odm_a",
        "system_ext_a",
    ]


def test_lpdump_non_ab_dynamic_partitions(tmp_path):
    image_dir = tmp_path / "Image"
    image_dir.mkdir()

    result = build_partition_explorer(
        image_dir,
        lpdump_report_path=FIXTURES / "lpdump_rk3318_non_ab.txt",
    )

    assert list(_partition_by_name(result)) == [
        "system",
        "product",
        "vendor",
        "odm",
        "system_ext",
    ]


def test_editable_root_sets_dynamic_partition_editable_dir(tmp_path):
    image_dir = tmp_path / "Image"
    editable_root = tmp_path / "editable"
    image_dir.mkdir()

    result = build_partition_explorer(
        image_dir,
        lpdump_report_path=FIXTURES / "lpdump_rk3318_ab.txt",
        editable_root=editable_root,
    )

    assert _partition_by_name(result)["product_a"].editable_dir == editable_root / "product_a"


def test_unknown_partition_gets_node_and_warning_risk(tmp_path):
    image_dir = tmp_path / "Image"
    image_dir.mkdir()
    report = tmp_path / "lpdump_vendor_boot.txt"
    report.write_text(
        """
Metadata size: 4096
Metadata slots: 2
Block size: 4096
Device size: 200000
Group: custom_group
Maximum size: 180000
Partition: vendor_boot
Group: custom_group
Size: 10000
Attributes: readonly
""",
        encoding="utf-8",
    )

    result = build_partition_explorer(image_dir, lpdump_report_path=report)

    assert result.dynamic_partitions[0].name == "vendor_boot"
    assert result.dynamic_partitions[0].risk_level == "warning"


def test_image_dir_missing_raises_partition_explorer_error(tmp_path):
    with pytest.raises(PartitionExplorerError, match="does not exist"):
        build_partition_explorer(tmp_path / "missing" / "Image")


def test_empty_image_folder_returns_result_with_warning(tmp_path):
    image_dir = tmp_path / "Image"
    image_dir.mkdir()

    result = build_partition_explorer(image_dir)

    assert result.detected_images == ()
    assert any("empty" in warning for warning in result.warnings)


def test_invalid_optional_reports_are_collected_as_errors(tmp_path):
    image_dir = tmp_path / "Image"
    image_dir.mkdir()
    bad_avb = tmp_path / "bad_avb.txt"
    bad_lpdump = tmp_path / "bad_lpdump.txt"
    bad_avb.write_text("not an AVB report", encoding="utf-8")
    bad_lpdump.write_text("not an lpdump report", encoding="utf-8")

    result = build_partition_explorer(
        image_dir,
        vbmeta_report_path=bad_avb,
        lpdump_report_path=bad_lpdump,
    )

    assert len(result.errors) == 2
    assert "AVB report" in result.errors[0]
    assert "lpdump report" in result.errors[1]


def test_partition_risk_classification_is_not_absolute_safe():
    assert classify_partition_risk("product_a") == "safe_to_edit_limited"
    assert classify_partition_risk("system") == "warning"
    assert classify_partition_risk("vendor_a") == "danger"
    assert classify_partition_risk("odm") == "danger"
    assert classify_partition_risk("system_ext_a") == "warning"
    assert classify_partition_risk("vendor_boot") == "warning"


def test_no_subprocess_wsl_or_tool_execution_in_partition_explorer():
    source = inspect.getsource(partition_explorer)

    assert "subprocess" not in source
    assert "wsl.exe" not in source
    assert "Popen" not in source
    assert "afptool" not in source
    assert "simg2img" not in source
    assert "lpunpack" not in source
    assert "lpmake" not in source
