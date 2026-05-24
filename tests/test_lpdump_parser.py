import inspect
from pathlib import Path

import pytest

from core import lpdump_parser
from core.lpdump_parser import LpDumpParseError, load_lpdump_report, parse_lpdump_text


FIXTURES = Path(__file__).parent / "fixtures"


def _partition_by_name(metadata):
    return {partition.name: partition for partition in metadata.partitions}


def test_parse_ab_metadata_fixture():
    metadata = load_lpdump_report(FIXTURES / "lpdump_rk3318_ab.txt")

    assert metadata.metadata_size == 65536
    assert metadata.metadata_slots == 2
    assert metadata.block_size == 4096
    assert metadata.device_size == 3607101440
    assert metadata.alignment == 1048576
    assert [partition.name for partition in metadata.partitions] == [
        "system_a",
        "product_a",
        "vendor_a",
        "odm_a",
        "system_ext_a",
    ]


def test_parse_non_ab_metadata_fixture():
    metadata = load_lpdump_report(FIXTURES / "lpdump_rk3318_non_ab.txt")

    assert [partition.name for partition in metadata.partitions] == [
        "system",
        "product",
        "vendor",
        "odm",
        "system_ext",
    ]


def test_parse_group_maximum_size():
    metadata = load_lpdump_report(FIXTURES / "lpdump_rk3318_ab.txt")

    assert metadata.groups[0].name == "rockchip_dynamic_partitions"
    assert metadata.groups[0].maximum_size == 3602907136
    assert metadata.groups[0].flags == "none"


def test_parse_partition_sizes_and_attributes():
    metadata = load_lpdump_report(FIXTURES / "lpdump_rk3318_ab.txt")
    partitions = _partition_by_name(metadata)

    assert partitions["product_a"].size == 628748288
    assert partitions["product_a"].group_name == "rockchip_dynamic_partitions"
    assert partitions["product_a"].readonly is True
    assert partitions["product_a"].attributes == ("readonly",)
    assert partitions["product_a"].extent_count == 1


def test_partition_names_are_preserved():
    metadata = load_lpdump_report(FIXTURES / "lpdump_rk3318_non_ab.txt")

    assert "system_ext" in _partition_by_name(metadata)


def test_unknown_partition_is_parsed():
    report = """
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
"""

    metadata = parse_lpdump_text(report)

    assert metadata.partitions[0].name == "vendor_boot"
    assert metadata.partitions[0].size == 10000


def test_empty_text_raises_error():
    with pytest.raises(LpDumpParseError, match="empty"):
        parse_lpdump_text(" \n\t")


def test_missing_required_field_raises_error():
    report = """
Metadata size: 4096
Metadata slots: 2
Block size: 4096
Group: group_a
Maximum size: 1000
Partition: system
Group: group_a
Size: 100
"""

    with pytest.raises(LpDumpParseError, match="device size"):
        parse_lpdump_text(report)


def test_no_subprocess_wsl_or_lpdump_calls():
    source = inspect.getsource(lpdump_parser)

    assert "subprocess" not in source
    assert "wsl.exe" not in source
    assert "Popen" not in source
