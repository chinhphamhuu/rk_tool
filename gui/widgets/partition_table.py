from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QTableWidget, QTableWidgetItem, QWidget

from gui.widgets.status_badge import StatusBadge


class DynamicPartitionTable(QTableWidget):
    ROWS = [
        ("system_a.img", "ext4", "1.40 GB", "Sẵn sàng"),
        ("product_a.img", "ext4", "628 MB", "Sẵn sàng"),
        ("vendor_a.img", "ext4", "180 MB", "Sẵn sàng"),
        ("odm_a.img", "ext4", "0.6 MB", "Sẵn sàng"),
        ("system_ext_a.img", "ext4", "132 MB", "Sẵn sàng"),
    ]

    def __init__(self) -> None:
        super().__init__(len(self.ROWS), 5)
        self.setHorizontalHeaderLabels(("Tên partition", "Loại", "Kích thước", "Trạng thái", "Hành động"))
        self.verticalHeader().hide()
        self.setShowGrid(False)
        self.setMinimumHeight(300)
        self.horizontalHeader().setStretchLastSection(True)
        for row, (name, kind, size, status) in enumerate(self.ROWS):
            self._set_item(row, 0, f"📁  {name}")
            self._set_item(row, 1, kind)
            self._set_item(row, 2, size)
            self.setCellWidget(row, 3, StatusBadge(f"●  {status}", "ok"))
            self.setCellWidget(row, 4, self._actions())

    def _set_item(self, row: int, column: int, text: str) -> None:
        item = QTableWidgetItem(text)
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        self.setItem(row, column, item)

    def _actions(self) -> QWidget:
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        layout.addWidget(QPushButton("Analyze"))
        layout.addWidget(QPushButton("📁 Extract tree"))
        return widget


class PartitionUsageTable(QTableWidget):
    ROWS = [
        ("system_a", "1.62 GB", "436.62 MB (26.29%)", "██████░░"),
        ("product_a", "512.00 MB", "198.34 MB (38.74%)", "█████░░░"),
        ("vendor_a", "896.00 MB", "256.41 MB (28.62%)", "████░░░░"),
        ("odm_a", "256.00 MB", "88.72 MB (34.66%)", "█████░░░"),
        ("system_ext_a", "256.00 MB", "76.11 MB (29.73%)", "████░░░░"),
    ]

    def __init__(self) -> None:
        super().__init__(len(self.ROWS), 4)
        self.setHorizontalHeaderLabels(("Partition", "Size", "Free space", "Used"))
        self.verticalHeader().hide()
        self.setShowGrid(False)
        self.setMinimumHeight(250)
        for row, data in enumerate(self.ROWS):
            for column, text in enumerate(data):
                item = QTableWidgetItem(text)
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                if column == 3:
                    item.setForeground(QColor("#16a34a"))
                self.setItem(row, column, item)


class SourcePartitionTable(QTableWidget):
    ROWS = [
        ("system_a", "modified/system_a.img", "Đã chỉnh sửa", "ok"),
        ("product_a", "modified/product_a.img", "Đã chỉnh sửa", "ok"),
        ("vendor_a", "parts/vendor_a.img", "Từ lpdump gốc", "info"),
        ("odm_a", "parts/odm_a.img", "Từ lpdump gốc", "info"),
        ("system_ext_a", "parts/system_ext_a.img", "Từ lpdump gốc", "info"),
    ]

    def __init__(self) -> None:
        super().__init__(len(self.ROWS), 3)
        self.setHorizontalHeaderLabels(("Partition", "Nguồn image", "Trạng thái"))
        self.verticalHeader().hide()
        self.setShowGrid(False)
        self.setMinimumHeight(260)
        for row, (partition, source, status, variant) in enumerate(self.ROWS):
            self._set_item(row, 0, f"📁  {partition}")
            self._set_item(row, 1, source)
            self.setCellWidget(row, 2, StatusBadge(status, variant))

    def _set_item(self, row: int, column: int, text: str) -> None:
        item = QTableWidgetItem(text)
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        self.setItem(row, column, item)
