from __future__ import annotations

from PySide6.QtWidgets import QGridLayout, QHBoxLayout, QPushButton, QVBoxLayout, QWidget

from gui.widgets.command_preview import CommandPreview
from gui.widgets.info_card import Card, KeyValueCard, page_header
from gui.widgets.log_panel import LogPanel
from gui.widgets.partition_table import SourcePartitionTable
from gui.widgets.verify_checklist import Checklist


class RebuildSuperTab(QWidget):
    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(36, 30, 36, 24)
        layout.setSpacing(18)

        layout.addWidget(page_header("Rebuild super.img", "Tạo lại super.img từ lpdump gốc và các partition đã chỉnh sửa."))

        grid = QGridLayout()
        grid.setHorizontalSpacing(18)
        sources = Card("Nguồn partition sẽ dùng")
        sources.layout.addWidget(SourcePartitionTable())
        grid.addWidget(sources, 0, 0)
        grid.addWidget(
            KeyValueCard(
                "Metadata từ lpdump gốc",
                [
                    ("metadata-size", "65,536 (64 KiB)"),
                    ("metadata-slots", "2"),
                    ("device-size", "3,607,101,440"),
                    ("group name", "rockchip_dynamic_partitions"),
                    ("group size", "3,602,907,136"),
                    ("block size", "4,096"),
                    ("alignment", "1,048,576"),
                ],
            ),
            0,
            1,
        )
        layout.addLayout(grid)

        command = Card("Preview lpmake command")
        command.layout.addWidget(
            CommandPreview(
                "lpmake --metadata-size 65536 --metadata-slots 2 --device super:3607101440 \\\n"
                "  --group rockchip_dynamic_partitions:3602907136 \\\n"
                "  --partition system_a:readonly:1503238553:rockchip_dynamic_partitions --image system_a=modified/system_a.img \\\n"
                "  --partition product_a:readonly:658505728:rockchip_dynamic_partitions --image product_a=modified/product_a.img \\\n"
                "  --partition vendor_a:readonly:188743680:rockchip_dynamic_partitions --image vendor_a=parts/vendor_a.img \\\n"
                "  --partition odm_a:readonly:629145:rockchip_dynamic_partitions --image odm_a=parts/odm_a.img \\\n"
                "  --partition system_ext_a:readonly:138412032:rockchip_dynamic_partitions --image system_ext_a=parts/system_ext_a.img \\\n"
                "  --sparse --output workspace/output/super.img"
            )
        )
        buttons = QHBoxLayout()
        buttons.addWidget(QPushButton("📄  Build lpmake command"))
        rebuild = QPushButton("🔨  Rebuild super.img")
        rebuild.setObjectName("PrimaryButton")
        buttons.addWidget(rebuild)
        buttons.addWidget(QPushButton("🛡  Verify super mới"))
        buttons.addStretch(1)
        command.layout.addLayout(buttons)
        layout.addWidget(command)

        layout.addWidget(
            Checklist(
                "Checklist rebuild",
                [
                    ("Parse lpdump", "Hoàn tất", "ok"),
                    ("Build lpmake command", "Hoàn tất", "ok"),
                    ("Run lpmake", "Mock", "info"),
                    ("Verify super mới", "Chờ chạy", "warning"),
                ],
            )
        )

        layout.addWidget(
            LogPanel(
                [
                    ("[10:32:10]", "info", "Đang tạo lpmake command từ cấu hình current workspace..."),
                    ("[10:32:10]", "ok", "Đã tạo command thành công."),
                    ("[10:33:42]", "ok", "Rebuild super.img hoàn tất: output/super.img."),
                    ("[10:34:02]", "ok", "Tất cả kiểm tra quick đều OK."),
                ]
            )
        )
