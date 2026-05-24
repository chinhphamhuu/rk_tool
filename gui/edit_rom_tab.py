from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGridLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from gui.widgets.diff_table import FolderDiffTable
from gui.widgets.info_card import Card, page_header
from gui.widgets.log_panel import LogPanel
from gui.widgets.partition_tree import EditablePartitionTree
from gui.widgets.status_badge import StatusBadge
from gui.widgets.warning_box import WarningBox


class EditRomTab(QWidget):
    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(36, 30, 36, 24)
        layout.setSpacing(18)

        layout.addWidget(page_header("Chỉnh sửa ROM Folder", "Mở thư mục editable, chọn partition và quét thay đổi sau khi chỉnh sửa."))

        actions = QHBoxLayout()
        open_editable = QPushButton("📁  Mở thư mục editable")
        open_editable.setObjectName("GhostButton")
        actions.addWidget(open_editable)
        actions.addWidget(QPushButton("📁  Mở partition folder"))
        scan = QPushButton("🔎  Scan changes")
        scan.setObjectName("PrimaryButton")
        actions.addWidget(scan)
        actions.addStretch(1)
        layout.addLayout(actions)

        grid = QGridLayout()
        grid.setHorizontalSpacing(18)
        tree_card = Card("Cấu trúc ROM (Editable)")
        tree_card.layout.addWidget(EditablePartitionTree())
        grid.addWidget(tree_card, 0, 0)

        content = Card("Nội dung bên trong: system_a")
        content.layout.addWidget(self._content_table())
        grid.addWidget(content, 0, 1)

        side = QVBoxLayout()
        current = Card("Partition hiện tại")
        current.layout.addWidget(QLabel("Đường dẫn"))
        path = QLabel("workspace/projects/rk3318_android11/editable/system_a")
        path.setObjectName("Pill")
        path.setWordWrap(True)
        current.layout.addWidget(path)
        current.layout.addWidget(QLabel("Loại partition"))
        current.layout.addWidget(StatusBadge("system", "info"))
        current.layout.addWidget(QLabel("Trạng thái"))
        current.layout.addWidget(StatusBadge("Cảnh báo đỏ", "error"))
        current.layout.addWidget(
            WarningBox("system_a là partition hệ thống nhạy cảm.", "Vui lòng cẩn thận khi chỉnh sửa nội dung.", "error")
        )
        side.addWidget(current)

        diff = Card("Kết quả scan thay đổi")
        diff.layout.addWidget(FolderDiffTable())
        side.addWidget(diff)
        grid.addLayout(side, 0, 2)
        grid.setColumnStretch(1, 1)
        layout.addLayout(grid)

        layout.addWidget(
            LogPanel(
                [
                    ("[10:32:01]", "info", "Mở thư mục editable tại workspace/projects/rk3318_android11/editable"),
                    ("[10:32:02]", "ok", "Đã trích xuất các thư mục editable."),
                    ("[10:32:03]", "info", "Partition hiện tại: system_a"),
                    ("[10:32:08]", "ok", "Scan changes hoàn tất. Tìm thấy 3 thay đổi."),
                ]
            )
        )

    def _content_table(self) -> QTableWidget:
        rows = [
            ("📁 product", "Thư mục", "-"),
            ("📁 system", "Thư mục", "2024-05-21 10:31"),
            ("📁 vendor", "Thư mục", "2024-05-21 10:31"),
            ("📁 odm", "Thư mục", "2024-05-21 10:31"),
            ("📁 etc", "Thư mục", "2024-05-21 10:31"),
            ("📁 bin", "Thư mục", "2024-05-21 10:31"),
            ("📁 sbin", "Thư mục", "2024-05-21 10:31"),
            ("📁 xbin", "Thư mục", "2024-05-21 10:31"),
            ("📁 lib", "Thư mục", "2024-05-21 10:31"),
            ("📁 lib64", "Thư mục", "2024-05-21 10:31"),
        ]
        table = QTableWidget(len(rows), 3)
        table.setHorizontalHeaderLabels(("Tên", "Loại", "Kích thước / thời gian"))
        table.verticalHeader().hide()
        table.setShowGrid(False)
        table.setMinimumHeight(360)
        for row, data in enumerate(rows):
            for column, text in enumerate(data):
                item = QTableWidgetItem(text)
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                table.setItem(row, column, item)
        return table
