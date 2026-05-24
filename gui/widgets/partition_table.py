from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem, QWidget

from gui.widgets.status_badge import StatusBadge


DynamicPartitionRow = tuple[str, str, str, str, str, str, tuple[str, ...]]


class DynamicPartitionTable(QTableWidget):
    DEFAULT_ROWS: list[DynamicPartitionRow] = [
        ("system_a", "mock_group", "1.40 GB", "yes", "editable/system_a", "warning", ("View", "Extract tree")),
        ("product_a", "mock_group", "628 MB", "yes", "editable/product_a", "safe_to_edit_limited", ("View", "Extract tree")),
        ("vendor_a", "mock_group", "180 MB", "yes", "editable/vendor_a", "danger", ("View", "Extract tree")),
        ("odm_a", "mock_group", "0.6 MB", "yes", "editable/odm_a", "danger", ("View", "Extract tree")),
        ("system_ext_a", "mock_group", "132 MB", "yes", "editable/system_ext_a", "warning", ("View", "Extract tree")),
    ]

    def __init__(self, rows: list[DynamicPartitionRow] | None = None) -> None:
        super().__init__(0, 7)
        self.setHorizontalHeaderLabels(
            ("Tên partition", "Group", "Kích thước", "Readonly", "Editable", "Risk", "Hành động")
        )
        self.verticalHeader().hide()
        self.setShowGrid(False)
        self.setMinimumHeight(300)
        self.horizontalHeader().setStretchLastSection(True)
        self.set_rows(rows if rows is not None else self.DEFAULT_ROWS)

    def set_rows(self, rows: list[DynamicPartitionRow]) -> None:
        self.setRowCount(len(rows))
        for row, (name, group, size, readonly, editable, risk, actions) in enumerate(rows):
            self._set_item(row, 0, f"📁  {name}")
            self._set_item(row, 1, group)
            self._set_item(row, 2, size)
            self._set_item(row, 3, readonly)
            self._set_item(row, 4, editable)
            self.setCellWidget(row, 5, StatusBadge(f"●  {risk}", _badge_variant(risk)))
            self.setCellWidget(row, 6, self._actions(actions))
        self.resizeColumnsToContents()

    def _set_item(self, row: int, column: int, text: str) -> None:
        item = QTableWidgetItem(text)
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        self.setItem(row, column, item)

    def _actions(self, labels: tuple[str, ...]) -> QWidget:
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        for label in labels:
            button = QPushButton(label)
            button.setEnabled(False)
            button.setToolTip("Chức năng chạy tool thật sẽ làm ở task sau.")
            layout.addWidget(button)
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


def _badge_variant(value: str) -> str:
    normalized = value.lower()
    if normalized in {"safe", "safe_to_edit_limited", "low", "ok"}:
        return "ok"
    if normalized in {"danger", "error"}:
        return "error"
    if normalized == "info":
        return "info"
    return "warning"
