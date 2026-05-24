import pytest

from core.path_utils import (
    PathConversionError,
    WindowsPathToWsl,
    shell_quote,
    windows_path_to_wsl,
)


def test_convert_drive_c_path_to_wsl_path():
    assert windows_path_to_wsl(r"C:\Users\Test\rom.img") == "/mnt/c/Users/Test/rom.img"


def test_convert_drive_d_path_to_wsl_path():
    assert windows_path_to_wsl(r"D:\ROM_BOX\update.img") == "/mnt/d/ROM_BOX/update.img"


def test_convert_drive_e_path_to_wsl_path():
    assert windows_path_to_wsl(r"E:\Thư mục ROM\update.img") == "/mnt/e/Thư mục ROM/update.img"


def test_convert_path_with_spaces():
    assert windows_path_to_wsl(r"D:\ROM Box\update.img") == "/mnt/d/ROM Box/update.img"


def test_convert_unicode_path_without_normalizing_characters():
    assert (
        windows_path_to_wsl(r"D:\ROM tiếng Việt\cập nhật.img")
        == "/mnt/d/ROM tiếng Việt/cập nhật.img"
    )


def test_convert_wsl_unc_path_to_linux_path():
    assert (
        windows_path_to_wsl(r"\\wsl$\Ubuntu-24.04\home\user\project")
        == "/home/user/project"
    )


@pytest.mark.parametrize(
    "path",
    [
        r"\\NAS\share\file.img",
        r"\\192.168.1.10\share\file.img",
    ],
)
def test_unc_network_path_raises_clear_mvp_error(path):
    with pytest.raises(PathConversionError, match="UNC network path chưa hỗ trợ"):
        windows_path_to_wsl(path)


def test_shell_quote_quotes_paths_with_spaces():
    assert shell_quote("/mnt/d/ROM Box/update.img") == "'/mnt/d/ROM Box/update.img'"


def test_shell_quote_escapes_single_quotes():
    assert shell_quote("/mnt/d/O'Brien/update.img") == "'/mnt/d/O'\"'\"'Brien/update.img'"


def test_invalid_relative_path_raises_clear_error():
    with pytest.raises(PathConversionError, match="Unsupported path format"):
        windows_path_to_wsl(r"ROM_BOX\update.img")


def test_invalid_empty_path_raises_clear_error():
    with pytest.raises(PathConversionError, match="must not be empty"):
        windows_path_to_wsl("")


def test_custom_mount_root():
    converter = WindowsPathToWsl(mount_root="/custom")

    assert converter.convert(r"E:\rom.img") == "/custom/e/rom.img"
