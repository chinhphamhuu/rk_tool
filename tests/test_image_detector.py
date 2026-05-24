import inspect

import pytest

from core import image_detector
from core.image_detector import ImageDetectorError, detect_images, scan_image_dir


def _write_file(path, size=3):
    path.write_bytes(b"X" * size)


def _by_name(detected):
    return {image.name: image for image in detected}


def test_detect_super_img(tmp_path):
    image_dir = tmp_path / "Image"
    image_dir.mkdir()
    _write_file(image_dir / "super.img", size=128)

    detected = _by_name(scan_image_dir(image_dir))

    assert detected["super.img"].type == "dynamic_super"
    assert detected["super.img"].size_bytes == 128
    assert detected["super.img"].risk_level == "safe"
    assert detected["super.img"].supported_actions == ("analyze", "unpack")


def test_detect_vbmeta_img(tmp_path):
    image_dir = tmp_path / "Image"
    image_dir.mkdir()
    _write_file(image_dir / "vbmeta.img")

    detected = _by_name(scan_image_dir(image_dir))

    assert detected["vbmeta.img"].type == "avb_vbmeta"
    assert detected["vbmeta.img"].risk_level == "warning"
    assert detected["vbmeta.img"].supported_actions == ("analyze_avb",)


def test_detect_boot_and_recovery_images(tmp_path):
    image_dir = tmp_path / "Image"
    image_dir.mkdir()
    _write_file(image_dir / "boot.img")
    _write_file(image_dir / "recovery.img")

    detected = _by_name(scan_image_dir(image_dir))

    assert detected["boot.img"].type == "boot_image"
    assert detected["boot.img"].risk_level == "warning"
    assert detected["boot.img"].supported_actions == ("analyze_only",)
    assert detected["recovery.img"].type == "recovery_image"
    assert detected["recovery.img"].risk_level == "warning"
    assert detected["recovery.img"].supported_actions == ("analyze_only",)


def test_detect_dtbo_img(tmp_path):
    image_dir = tmp_path / "Image"
    image_dir.mkdir()
    _write_file(image_dir / "dtbo.img")

    detected = _by_name(scan_image_dir(image_dir))

    assert detected["dtbo.img"].type == "dtbo_image"
    assert detected["dtbo.img"].risk_level == "info"
    assert detected["dtbo.img"].supported_actions == ("info_only",)


def test_detect_uboot_and_trust_as_danger_info_only(tmp_path):
    image_dir = tmp_path / "Image"
    image_dir.mkdir()
    _write_file(image_dir / "uboot.img")
    _write_file(image_dir / "trust.img")

    detected = _by_name(scan_image_dir(image_dir))

    assert detected["uboot.img"].type == "bootloader_danger"
    assert detected["uboot.img"].risk_level == "danger"
    assert detected["uboot.img"].supported_actions == ("info_only",)
    assert detected["trust.img"].type == "bootloader_danger"
    assert detected["trust.img"].risk_level == "danger"
    assert detected["trust.img"].supported_actions == ("info_only",)


def test_detect_misc_img(tmp_path):
    image_dir = tmp_path / "Image"
    image_dir.mkdir()
    _write_file(image_dir / "misc.img")

    detected = _by_name(scan_image_dir(image_dir))

    assert detected["misc.img"].type == "misc_image"
    assert detected["misc.img"].risk_level == "info"
    assert detected["misc.img"].supported_actions == ("info_only",)


def test_detect_parameter_txt(tmp_path):
    image_dir = tmp_path / "Image"
    image_dir.mkdir()
    _write_file(image_dir / "parameter.txt")

    detected = _by_name(scan_image_dir(image_dir))

    assert detected["parameter.txt"].type == "rockchip_parameter"
    assert detected["parameter.txt"].risk_level == "warning"
    assert detected["parameter.txt"].supported_actions == ("view_with_warning",)


def test_detect_unknown_img_and_ignore_unrelated_files(tmp_path):
    image_dir = tmp_path / "Image"
    image_dir.mkdir()
    _write_file(image_dir / "vendor_boot.img")
    _write_file(image_dir / "readme.txt")

    detected = scan_image_dir(image_dir)

    assert [image.name for image in detected] == ["vendor_boot.img"]
    assert detected[0].type == "unknown_image"
    assert detected[0].risk_level == "warning"
    assert detected[0].supported_actions == ("info_only",)


def test_empty_image_folder_returns_empty_list(tmp_path):
    image_dir = tmp_path / "Image"
    image_dir.mkdir()

    assert scan_image_dir(image_dir) == []


def test_detect_images_alias(tmp_path):
    image_dir = tmp_path / "Image"
    image_dir.mkdir()
    _write_file(image_dir / "super.img")

    assert detect_images(image_dir) == scan_image_dir(image_dir)


def test_missing_image_dir_raises_clear_error(tmp_path):
    with pytest.raises(ImageDetectorError, match="does not exist"):
        scan_image_dir(tmp_path / "missing" / "Image")


def test_no_wsl_subprocess_or_tool_calls():
    source = inspect.getsource(image_detector)

    assert "subprocess" not in source
    assert "wsl.exe" not in source
    assert "afptool" not in source
