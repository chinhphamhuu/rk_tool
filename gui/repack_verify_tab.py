from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QGridLayout, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from gui.widgets.info_card import Card, KeyValueCard, page_header
from gui.widgets.log_panel import LogPanel
from gui.widgets.verify_checklist import Checklist
from gui.widgets.warning_box import WarningBox


class RepackVerifyTab(QWidget):
    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(36, 30, 36, 24)
        layout.setSpacing(18)

        layout.addWidget(page_header("Repack & Verify", "Đóng gói ROM final và tự động verify offline sau khi repack."))
        layout.addWidget(self._success_hero())

        grid = QGridLayout()
        grid.setHorizontalSpacing(18)
        grid.addWidget(
            Checklist(
                "Quy trình Repack & Verify",
                [
                    ("Pack RKAF", "Hoàn tất", "ok"),
                    ("Pack RKFW", "Hoàn tất", "ok"),
                    ("Restore RKFW header offset 0x15", "Hoàn tất", "ok"),
                    ("Recalculate MD5 tail", "Hoàn tất", "ok"),
                    ("Verify RKFW header", "Hoàn tất", "ok"),
                    ("Verify MD5 tail", "Hoàn tất", "ok"),
                    ("Unpack thử RKFW final", "Hoàn tất", "ok"),
                    ("Unpack thử RKAF final", "Hoàn tất", "ok"),
                    ("Verify super.img final", "Hoàn tất", "ok"),
                    ("Check file/APK đã thêm", "Hoàn tất", "ok"),
                    ("Write SHA256", "Hoàn tất", "ok"),
                ],
            ),
            0,
            0,
        )
        final = KeyValueCard(
            "Thông tin ROM final",
            [
                ("Tên file", "rk3318_android11_final.img"),
                ("SHA256", "2f6e8b9c9f1b0a5a2d7c2d4f9cbe3e2b3a5f7d6c8b9a1e4f2dbc5b7a8e9d1f2"),
                ("Kích thước", "1.68 GB (1,803,889,664 bytes)"),
                ("Output folder", "APP_ROOT/workspace/output/"),
            ],
        )
        final.layout.addWidget(
            WarningBox(
                "Chỉ verify offline, chưa flash thật",
                "Verify offline PASS chỉ kiểm tra tính toàn vẹn file sau đóng gói.",
                "warning",
            )
        )
        grid.addWidget(final, 0, 1)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        layout.addLayout(grid)

        actions = QHBoxLayout()
        repack = QPushButton("▷  Repack final")
        repack.setObjectName("PrimaryButton")
        actions.addWidget(QPushButton("📁  Mở thư mục output"))
        actions.addWidget(QPushButton("📄  Xuất báo cáo"))
        actions.addWidget(repack)
        actions.addStretch(1)
        layout.addLayout(actions)

        layout.addWidget(
            LogPanel(
                [
                    ("[10:32:18]", "ok", "Header match (rkxml): OK"),
                    ("[10:32:18]", "ok", "MD5 match: OK"),
                    ("[10:32:19]", "ok", "Unpack RKFW/RKAF: thành công"),
                    ("[10:32:19]", "ok", "Unpack super.img: thành công"),
                    ("[10:32:20]", "ok", "APK tồn tại sau rebuild: OK"),
                    ("[10:32:20]", "ok", "Verify offline PASS."),
                ]
            )
        )

    def _success_hero(self) -> QFrame:
        hero = QFrame()
        hero.setObjectName("SuccessHero")
        layout = QHBoxLayout(hero)
        layout.setContentsMargins(42, 26, 42, 26)
        layout.setSpacing(28)
        circle = QFrame()
        circle.setObjectName("HeroCheckCircle")
        circle.setFixedSize(84, 84)
        circle_layout = QHBoxLayout(circle)
        check = QLabel("✓")
        check.setObjectName("HeroCheck")
        check.setAlignment(Qt.AlignCenter)
        circle_layout.addWidget(check)
        layout.addWidget(circle)

        text = QVBoxLayout()
        text.addWidget(QLabel("Verify offline PASS"))
        text.itemAt(0).widget().setObjectName("HugeSuccess")
        text.addWidget(QLabel("ROM final sẵn sàng để thử flash bằng RKDevTool."))
        layout.addLayout(text, 1)
        return hero
