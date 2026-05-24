import inspect

import pytest

from core import ext4_image
from core.ext4_image import (
    Ext4ImageError,
    build_debugfs_rdump_command,
    build_dumpe2fs_command,
    build_e2fsck_readonly_command,
    parse_dumpe2fs_header,
)
from core.path_utils import shell_quote, windows_path_to_wsl


DUMPE2FS_SAMPLE = """
Filesystem volume name:   product_a
Filesystem features:      has_journal ext_attr resize_inode dir_index filetype extent 64bit flex_bg sparse_super large_file huge_file dir_nlink extra_isize metadata_csum
Block count:              157184
Free blocks:              49712
Block size:               4096
"""


def test_build_debugfs_rdump_command_quotes_paths_with_spaces(tmp_path):
    image = tmp_path / "ROM Box" / "parts" / "product_a.img"
    output = tmp_path / "ROM Box" / "editable folders" / "product_a"

    command = build_debugfs_rdump_command(image, output)

    assert command.startswith("debugfs -R ")
    assert shell_quote(f"rdump / {windows_path_to_wsl(output)}") in command
    assert shell_quote(windows_path_to_wsl(image)) in command


def test_build_readonly_inspection_commands(tmp_path):
    image = tmp_path / "system_a.img"

    assert build_e2fsck_readonly_command(image) == f"e2fsck -fn {shell_quote(windows_path_to_wsl(image))}"
    assert build_dumpe2fs_command(image) == f"dumpe2fs -h {shell_quote(windows_path_to_wsl(image))}"


def test_build_command_preserves_unicode_path(tmp_path):
    image = tmp_path / "Thư mục ROM" / "system_a.img"
    output = tmp_path / "editable" / "system_a"

    command = build_debugfs_rdump_command(image, output)

    assert "Thư mục ROM" in command


def test_parse_dumpe2fs_header_sample(tmp_path):
    image = tmp_path / "product_a.img"
    image.write_bytes(b"image")

    info = parse_dumpe2fs_header(DUMPE2FS_SAMPLE, image_path=image)

    assert info.image_path == image
    assert info.exists is True
    assert info.size_bytes == 5
    assert info.filesystem_type == "ext4"
    assert info.volume_name == "product_a"
    assert info.block_count == 157184
    assert info.free_blocks == 49712
    assert info.used_blocks == 107472
    assert info.block_size == 4096
    assert "extent" in info.filesystem_features


def test_parse_empty_or_invalid_header_raises():
    with pytest.raises(Ext4ImageError, match="empty"):
        parse_dumpe2fs_header("")

    with pytest.raises(Ext4ImageError, match="recognizable"):
        parse_dumpe2fs_header("not a dumpe2fs report")


def test_ext4_image_has_no_direct_process_invocation():
    source = inspect.getsource(ext4_image)

    assert "subprocess" not in source
    assert "wsl.exe" not in source
    assert "Popen" not in source
    assert "sudo " not in source
    assert "mount -o loop" not in source
