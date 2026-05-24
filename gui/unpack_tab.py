from __future__ import annotations

from PySide6.QtWidgets import QGridLayout, QHBoxLayout, QPushButton, QVBoxLayout, QWidget

from gui.widgets.detected_image_table import DetectedImageTable
from gui.widgets.info_card import Card, page_header
from gui.widgets.log_panel import LogPanel
from gui.widgets.partition_table import DynamicPartitionTable
from gui.widgets.partition_tree import OutputEditableTree
from gui.widgets.step_card import StepCard
from gui.widgets.warning_box import WarningBox


class UnpackTab(QWidget):
    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(36, 30, 36, 24)
        layout.setSpacing(18)

        top = QHBoxLayout()
        top.addWidget(page_header("Giải nén ROM", "Partition Explorer cho update.img, super.img và dynamic partitions."))
        top.addStretch(1)
        top.addWidget(QPushButton("↻  Quét lại ROM"))
        layout.addLayout(top)

        grid = QGridLayout()
        grid.setHorizontalSpacing(18)
        grid.setVerticalSpacing(18)

        steps = StepCard(
            "Quy trình Unpack",
            [
                (1, "Unpack RKFW", "Giải nén Rockchip firmware từ update.img.", "Đã xong", "ok", "Unpack RKFW"),
                (2, "Unpack RKAF", "Giải nén Android firmware package.", "Đã xong", "ok", "Unpack RKAF"),
                (3, "Detect images", "Quét và nhận diện image/partition.", "Đã xong", "ok", "Quét image"),
            ],
        )
        grid.addWidget(steps, 0, 0)

        images = Card("Images / partitions đã phát hiện")
        images.layout.addWidget(DetectedImageTable())
        images.layout.addWidget(
            WarningBox(
                "Partition Explorer",
                "Chọn super.img để phân tích dynamic partitions, hoặc vbmeta.img để analyze AVB. Dữ liệu đang là mock UI.",
                "info",
            )
        )
        grid.addWidget(images, 0, 1)
        grid.setColumnStretch(1, 1)
        layout.addLayout(grid)

        super_panel = QGridLayout()
        dynamic = Card("super.img → Dynamic partitions")
        dynamic.layout.addWidget(DynamicPartitionTable())
        super_panel.addWidget(dynamic, 0, 0)
        tree = Card("Cây thư mục editable sẽ tạo ra")
        tree.layout.addWidget(OutputEditableTree())
        super_panel.addWidget(tree, 0, 1)
        super_panel.setColumnStretch(0, 2)
        super_panel.setColumnStretch(1, 1)
        layout.addLayout(super_panel)

        layout.addWidget(
            LogPanel(
                [
                    ("[10:25:13]", "info", "Bắt đầu giải nén update.img..."),
                    ("[10:25:18]", "ok", "Unpack RKFW hoàn tất."),
                    ("[10:25:24]", "ok", "Unpack RKAF hoàn tất."),
                    ("[10:25:31]", "ok", "Đã phát hiện 8 image/partition trong ROM."),
                    ("[10:28:46]", "ok", "lpunpack: Hoàn tất giải nén dynamic partitions."),
                ]
            )
        )
