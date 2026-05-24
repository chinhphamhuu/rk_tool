import inspect
from pathlib import Path

import pytest

from core import lpmake_builder
from core.lpdump_parser import load_lpdump_report
from core.lpmake_builder import (
    LpMakeBuildError,
    LpMakeImageSource,
    build_lpmake_command,
)


FIXTURES = Path(__file__).parent / "fixtures"


def _sources_for(metadata, base="work/parts"):
    return {partition.name: f"{base}/{partition.name}.img" for partition in metadata.partitions}


def test_build_command_for_ab_fixture():
    metadata = load_lpdump_report(FIXTURES / "lpdump_rk3318_ab.txt")

    command = build_lpmake_command(metadata, _sources_for(metadata), "work/modified/super.img")

    assert command.args[:9] == (
        "lpmake",
        "--metadata-size",
        "65536",
        "--metadata-slots",
        "2",
        "--device-size",
        "3607101440",
        "--block-size",
        "4096",
    )
    assert "--group" in command.args
    assert "rockchip_dynamic_partitions:3602907136" in command.args
    assert "system_a:readonly:1073741824:rockchip_dynamic_partitions" in command.args
    assert "system_a=work/parts/system_a.img" in command.args


def test_build_command_for_non_ab_fixture():
    metadata = load_lpdump_report(FIXTURES / "lpdump_rk3318_non_ab.txt")

    command = build_lpmake_command(metadata, _sources_for(metadata), "work/modified/super.img")

    assert "system:readonly:1073741824:rockchip_dynamic_partitions" in command.args
    assert "product=work/parts/product.img" in command.args


def test_modified_product_image_is_used_when_provided():
    metadata = load_lpdump_report(FIXTURES / "lpdump_rk3318_ab.txt")
    sources = _sources_for(metadata)
    sources["product_a"] = "work/modified/product_a.img"

    command = build_lpmake_command(metadata, sources, "work/modified/super.img")

    assert "product_a=work/modified/product_a.img" in command.args


def test_path_with_spaces_is_quoted_in_preview_string():
    metadata = load_lpdump_report(FIXTURES / "lpdump_rk3318_ab.txt")
    sources = _sources_for(metadata, base="work/ROM Box/parts")

    command = build_lpmake_command(metadata, sources, "work/output/super image.img")

    assert "'system_a=work/ROM Box/parts/system_a.img'" in command.command_string
    assert "'work/output/super image.img'" in command.command_string


def test_unicode_path_is_preserved():
    metadata = load_lpdump_report(FIXTURES / "lpdump_rk3318_non_ab.txt")
    sources = _sources_for(metadata, base="work/Thư mục ROM/parts")

    command = build_lpmake_command(metadata, sources, "work/output/super.img")

    assert "Thư mục ROM" in command.command_string


def test_missing_image_source_raises_error():
    metadata = load_lpdump_report(FIXTURES / "lpdump_rk3318_ab.txt")
    sources = _sources_for(metadata)
    sources.pop("vendor_a")

    with pytest.raises(LpMakeBuildError, match="vendor_a"):
        build_lpmake_command(metadata, sources, "work/modified/super.img")


def test_partition_override_size_valid_passes():
    metadata = load_lpdump_report(FIXTURES / "lpdump_rk3318_ab.txt")
    sources = _sources_for(metadata)
    sources["product_a"] = LpMakeImageSource("work/modified/product_a.img", size_override=700000000)

    command = build_lpmake_command(metadata, sources, "work/modified/super.img")

    assert "product_a:readonly:700000000:rockchip_dynamic_partitions" in command.args


def test_partition_override_exceeding_group_size_raises_error():
    metadata = load_lpdump_report(FIXTURES / "lpdump_rk3318_ab.txt")
    sources = _sources_for(metadata)
    sources["product_a"] = LpMakeImageSource(
        "work/modified/product_a.img",
        size_override=metadata.groups[0].maximum_size,
    )

    with pytest.raises(LpMakeBuildError, match="exceed group"):
        build_lpmake_command(metadata, sources, "work/modified/super.img")


def test_sparse_flag_present_when_sparse_true():
    metadata = load_lpdump_report(FIXTURES / "lpdump_rk3318_non_ab.txt")

    command = build_lpmake_command(metadata, _sources_for(metadata), "work/modified/super.img", sparse=True)

    assert "--sparse" in command.args


def test_sparse_flag_absent_when_sparse_false():
    metadata = load_lpdump_report(FIXTURES / "lpdump_rk3318_non_ab.txt")

    command = build_lpmake_command(metadata, _sources_for(metadata), "work/modified/super.img", sparse=False)

    assert "--sparse" not in command.args


def test_no_subprocess_wsl_or_lpmake_execution():
    source = inspect.getsource(lpmake_builder)

    assert "subprocess" not in source
    assert "wsl.exe" not in source
    assert "Popen" not in source
