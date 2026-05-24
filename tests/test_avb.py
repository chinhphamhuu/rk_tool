import inspect
from pathlib import Path

import pytest

from core import avb
from core.avb import AvbParseError, classify_avb_risk, load_avb_info_report, parse_avb_info_text


FIXTURES = Path(__file__).parent / "fixtures"


def test_parse_algorithm_none_flags_2_descriptors_none():
    info = parse_avb_info_text(
        """
Algorithm: NONE
Rollback Index: 0
Flags: 2
Descriptors:
    none
"""
    )

    assert info.algorithm == "NONE"
    assert info.rollback_index == 0
    assert info.flags == 2
    assert info.descriptors == ()
    assert info.risk_level == "low"
    assert info.is_disable_verification_likely is True
    assert "verification-disabled" in info.warnings[0]


def test_parse_hash_descriptor_partition_system():
    info = parse_avb_info_text(
        """
Algorithm: SHA256_RSA4096
Flags: 0
Descriptors:
Hash descriptor:
  Image Size: 123456 bytes
  Partition Name: system
  Salt: abcdef
  Digest: 11112222
"""
    )

    assert info.has_hash_descriptor is True
    assert info.has_hashtree_descriptor is False
    assert info.descriptors[0].descriptor_type == "hash"
    assert info.descriptors[0].partition_name == "system"
    assert info.descriptors[0].image_size == 123456
    assert info.descriptors[0].salt == "abcdef"
    assert info.descriptors[0].digest == "11112222"
    assert info.affected_partitions == ("system",)


def test_parse_hashtree_descriptor_partition_product():
    info = parse_avb_info_text(
        """
Algorithm: SHA256_RSA4096
Flags: 0
Descriptors:
Hashtree descriptor:
  Partition Name: product
  Root Digest: 33334444
  Salt: 55556666
"""
    )

    assert info.has_hash_descriptor is False
    assert info.has_hashtree_descriptor is True
    assert info.descriptors[0].descriptor_type == "hashtree"
    assert info.descriptors[0].partition_name == "product"
    assert info.descriptors[0].digest == "33334444"
    assert info.affected_partitions == ("product",)


def test_parse_multiple_descriptors_and_partitions_from_fixture():
    info = load_avb_info_report(FIXTURES / "vbmeta_with_descriptors.txt")

    assert len(info.descriptors) == 3
    assert info.has_hash_descriptor is True
    assert info.has_hashtree_descriptor is True
    assert info.affected_partitions == ("system", "product", "vendor")
    assert info.risk_level == "danger"
    assert "ROM has AVB descriptors" in info.warnings[0]


def test_affected_partitions_are_not_duplicated():
    info = parse_avb_info_text(
        """
Algorithm: SHA256_RSA4096
Flags: 0
Descriptors:
Hash descriptor:
  Partition Name: system
  Digest: aa
Hashtree descriptor:
  Partition Name: system
  Root Digest: bb
Hash descriptor:
  Partition Name: odm
  Digest: cc
"""
    )

    assert info.affected_partitions == ("system", "odm")


def test_flags_parse_as_int_with_hex_value():
    info = parse_avb_info_text(
        """
Algorithm: NONE
Rollback Index: 0
Flags: 0x2
Descriptors:
    none
"""
    )

    assert info.flags == 2
    assert isinstance(info.flags, int)


def test_safe_or_low_risk_when_no_descriptor():
    info = load_avb_info_report(FIXTURES / "vbmeta_algorithm_none.txt")

    assert info.descriptors == ()
    assert info.risk_level == "low"
    assert classify_avb_risk(info) == "low"


def test_warning_or_danger_risk_when_hash_or_hashtree_descriptor_exists():
    info = load_avb_info_report(FIXTURES / "vbmeta_with_descriptors.txt")

    assert info.risk_level == "danger"
    assert classify_avb_risk(info) == "danger"
    assert info.warnings == (
        "ROM has AVB descriptors. Modifying listed partitions may cause bootloop unless AVB is handled correctly.",
    )


def test_empty_text_raises_avb_parse_error():
    with pytest.raises(AvbParseError, match="empty"):
        parse_avb_info_text(" \n\t")


def test_unrecognized_text_raises_avb_parse_error():
    with pytest.raises(AvbParseError, match="does not look"):
        parse_avb_info_text("hello from a non AVB report")


def test_load_avb_info_report_from_fixture():
    info = load_avb_info_report(FIXTURES / "vbmeta_algorithm_none.txt")

    assert info.algorithm == "NONE"
    assert info.flags == 2
    assert info.rollback_index == 0


def test_no_subprocess_wsl_or_tool_invocation_in_core_avb():
    source = inspect.getsource(avb)

    assert "subprocess" not in source
    assert "wsl.exe" not in source
    assert "Popen" not in source
    assert "avbtool" not in source
