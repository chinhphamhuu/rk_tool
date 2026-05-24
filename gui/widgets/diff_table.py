from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QTableWidget, QTableWidgetItem

from gui.widgets.status_badge import StatusBadge


class DiffTable(QTableWidget):
    ROWS = [
        ("product_a", "+", "/app/DLTivi/DLTivi.apk", "Thấp", "ok"),
        ("system_a", "M", "/build.prop", "Trung bình", "warning"),
        ("system_a", "+", "/priv-app/RemoteFix/RemoteFix.apk", "Thấp", "ok"),
        ("vendor_a", "M", "/vendor/lib/libxyz.so", "Cao", "error"),
    ]

    def __init__(self) -> None:
        super().__init__(len(self.ROWS), 4)
        self.setHorizontalHeaderLabels(("Partition", "Loại thay đổi", "Đường dẫn", "Mức rủi ro"))
        self.verticalHeader().hide()
        self.setShowGrid(False)
        self.setMinimumHeight(260)
        for row, (partition, change, path, risk, variant) in enumerate(self.ROWS):
            self._set_item(row, 0, partition)
            self.setCellWidget(row, 1, StatusBadge(change, variant))
            self._set_item(row, 2, path)
            self.setCellWidget(row, 3, StatusBadge(risk, variant))

    def _set_item(self, row: int, column: int, text: str) -> None:
        item = QTableWidgetItem(text)
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        self.setItem(row, column, item)


class FolderDiffTable(QTableWidget):
    ROWS = [
        ("+", "app/NewTV/NewTV.apk", "File mới", "An toàn", "ok"),
        ("M", "build.prop", "File sửa", "Cảnh báo", "warning"),
        ("-", "old_app/OldApp.apk", "File xóa", "Nguy hiểm", "error"),
    ]

    def __init__(self) -> None:
        super().__init__(len(self.ROWS), 4)
        self.setHorizontalHeaderLabels(("Loại", "Đường dẫn", "Mô tả", "Mức rủi ro"))
        self.verticalHeader().hide()
        self.setShowGrid(False)
        self.setMinimumHeight(190)
        for row, (change, path, desc, risk, variant) in enumerate(self.ROWS):
            self.setCellWidget(row, 0, StatusBadge(change, variant))
            self._set_item(row, 1, path)
            self._set_item(row, 2, desc)
            self.setCellWidget(row, 3, StatusBadge(risk, variant))

    def _set_item(self, row: int, column: int, text: str) -> None:
        item = QTableWidgetItem(text)
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        self.setItem(row, column, item)
