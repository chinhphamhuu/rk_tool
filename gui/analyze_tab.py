from __future__ import annotations

from PySide6.QtWidgets import QGridLayout, QVBoxLayout, QWidget

from gui.widgets.info_card import KeyValueCard, MetricCard, page_header
from gui.widgets.log_panel import LogPanel
from gui.widgets.partition_table import PartitionUsageTable
from gui.widgets.warning_box import WarningBox


class AnalyzeTab(QWidget):
    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(36, 30, 36, 24)
        layout.setSpacing(18)

        layout.addWidget(page_header("Phân tích ROM", "Xem thông tin RKFW, vbmeta, super.img và các cảnh báo kỹ thuật."))

        metrics = QGridLayout()
        metrics.setHorizontalSpacing(18)
        metrics.addWidget(MetricCard("RKFW Header", "H223", "Header offset 0x15", "OK", "ok"), 0, 0)
        metrics.addWidget(MetricCard("MD5 Tail", "Match", "32 byte ASCII cuối file", "OK", "ok"), 0, 1)
        metrics.addWidget(MetricCard("vbmeta / AVB", "Descriptors", "Hash descriptor tồn tại", "Cảnh báo", "warning"), 0, 2)
        metrics.addWidget(MetricCard("super.img layout", "Detected", "Dynamic partitions", "OK", "ok"), 0, 3)
        layout.addLayout(metrics)

        grid = QGridLayout()
        grid.setHorizontalSpacing(18)
        grid.setVerticalSpacing(18)
        grid.addWidget(
            KeyValueCard(
                "Thông tin phân tích",
                [
                    ("RKFW header", "H223"),
                    ("Header offset", "0x15"),
                    ("MD5 tail status", "Match"),
                    ("super.img format", "Sparse → Raw converted"),
                    ("Metadata slots", "2"),
                    ("Device size", "3.36 GB"),
                    ("Dynamic partition group", "rockchip_dynamic_partitions"),
                ],
            ),
            0,
            0,
        )
        partition_card = KeyValueCard(
            "Dynamic partition group",
            [
                ("Group name", "rockchip_dynamic_partitions"),
                ("Group size", "3.35 GB"),
                ("Partition count", "5"),
                ("Free space policy", "Preserve original layout"),
            ],
        )
        grid.addWidget(partition_card, 0, 1)
        table_card = KeyValueCard("Partition free space", [])
        table_card.layout.addWidget(PartitionUsageTable())
        grid.addWidget(table_card, 1, 0, 1, 2)
        grid.setColumnStretch(1, 1)
        layout.addLayout(grid)

        warnings = QGridLayout()
        warnings.setHorizontalSpacing(18)
        warnings.addWidget(
            WarningBox(
                "Cảnh báo AVB descriptor",
                "vbmeta có Hash descriptor hoặc Hashtree descriptor. Verify offline không đảm bảo boot sau khi chỉnh sửa.",
                "warning",
            ),
            0,
            0,
        )
        warnings.addWidget(
            WarningBox(
                "Thông tin",
                "Không hard-code lpmake. super.img phải rebuild từ metadata lpdump gốc.",
                "info",
            ),
            0,
            1,
        )
        layout.addLayout(warnings)

        layout.addWidget(
            LogPanel(
                [
                    ("[10:25:18]", "info", "Đọc header RKFW..."),
                    ("[10:25:18]", "ok", "RKFW header: H223 (OK)"),
                    ("[10:25:18]", "ok", "MD5 tail: Match (OK)"),
                    ("[10:25:19]", "warning", "vbmeta: phát hiện descriptor cần cảnh báo."),
                    ("[10:25:19]", "ok", "Phát hiện dynamic partitions (5), Slots=2."),
                ]
            )
        )
