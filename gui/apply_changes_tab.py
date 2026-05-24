from __future__ import annotations

from PySide6.QtWidgets import QGridLayout, QHBoxLayout, QPushButton, QVBoxLayout, QWidget

from gui.widgets.diff_table import DiffTable
from gui.widgets.info_card import Card, KeyValueCard, page_header
from gui.widgets.log_panel import LogPanel
from gui.widgets.verify_checklist import Checklist
from gui.widgets.warning_box import WarningBox


class ApplyChangesTab(QWidget):
    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(36, 30, 36, 24)
        layout.setSpacing(18)

        layout.addWidget(page_header("Áp dụng thay đổi", "Quét diff, resize partition nếu cần, set permission/SELinux và apply vào image."))
        layout.addWidget(
            WarningBox(
                "Editable folder chỉ là staging",
                "Không repack trực tiếp từ folder editable. App copy image gốc sang modified rồi apply diff bằng debugfs.",
                "warning",
            )
        )

        grid = QGridLayout()
        grid.setHorizontalSpacing(18)
        grid.setVerticalSpacing(18)

        left = Card("Danh sách thay đổi")
        left.layout.addWidget(DiffTable())
        left.layout.addWidget(
            KeyValueCard(
                "Resize plan",
                [
                    ("Resize product_a", "+64 MB"),
                    ("Permission mặc định", "file 0644 / folder 0755"),
                    ("Owner", "root:root"),
                    ("SELinux", "u:object_r:system_file:s0"),
                ],
            )
        )
        actions = QHBoxLayout()
        apply = QPushButton("▷  Apply Changes")
        apply.setObjectName("PrimaryButton")
        actions.addWidget(apply)
        actions.addWidget(QPushButton("< >  Xem command mock"))
        actions.addStretch(1)
        left.layout.addLayout(actions)
        grid.addWidget(left, 0, 0)

        checklist = Checklist(
            "Checklist apply",
            [
                ("Copy image gốc sang modified", "Hoàn tất", "ok"),
                ("Tính resize", "Hoàn tất", "ok"),
                ("Resize bằng truncate + resize2fs", "Đang chạy", "info"),
                ("Apply diff bằng debugfs", "Chờ chạy", "warning"),
                ("Set permission", "Chờ chạy", "warning"),
                ("Set SELinux", "Chờ chạy", "warning"),
                ("e2fsck", "Chờ chạy", "warning"),
            ],
        )
        grid.addWidget(checklist, 0, 1)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        layout.addLayout(grid)

        layout.addWidget(
            LogPanel(
                [
                    ("[10:27:41]", "info", "[debugfs] Mở image: work/modified/product_a.img"),
                    ("[10:27:42]", "ok", "[resize2fs] Kích thước hiện tại: 1.50 GB"),
                    ("[10:27:43]", "ok", "[resize2fs] Truncate file... OK"),
                    ("[10:27:43]", "ok", "[resize2fs] Resize filesystem... OK"),
                    ("[10:27:44]", "ok", "[debugfs] Cập nhật super block... OK"),
                ]
            )
        )
