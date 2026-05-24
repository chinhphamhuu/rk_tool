from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem, QWidget

from gui.widgets.status_badge import StatusBadge


class DetectedImageTable(QTableWidget):
    ROWS = [
        ("super.img", "Dynamic partition container", "2.68 GB", "Sẵn sàng", "ok", ("Analyze", "Unpack")),
        ("vbmeta.img", "AVB metadata", "8.0 MB", "Sẵn sàng", "ok", ("Analyze AVB",)),
        ("boot.img", "Boot image", "32.0 MB", "Advanced", "info", ("Advanced",)),
        ("recovery.img", "Recovery image", "48.0 MB", "Advanced", "info", ("Advanced",)),
        ("dtbo.img", "Device tree overlay", "16.0 MB", "Info only", "info", ("Info",)),
        ("uboot.img", "Bootloader", "4.0 MB", "Không sửa", "warning", ("Không sửa",)),
        ("trust.img", "Trust image", "4.0 MB", "Không sửa", "warning", ("Không sửa",)),
        ("parameter.txt", "Text config", "12 KB", "Cảnh báo", "warning", ("Mở xem",)),
    ]

    def __init__(self) -> None:
        super().__init__(len(self.ROWS), 5)
        self.setHorizontalHeaderLabels(("Tên file", "Loại", "Kích thước", "Trạng thái", "Hành động"))
        self.verticalHeader().hide()
        self.setAlternatingRowColors(False)
        self.setShowGrid(False)
        self.setMinimumHeight(360)
        self.horizontalHeader().setStretchLastSection(True)
        for row, (name, kind, size, status, variant, actions) in enumerate(self.ROWS):
            self._set_item(row, 0, f"📄  {name}")
            self._set_item(row, 1, kind)
            self._set_item(row, 2, size)
            self.setCellWidget(row, 3, StatusBadge(f"●  {status}", variant))
            self.setCellWidget(row, 4, self._actions(actions, disabled=variant == "warning" and "Không sửa" in status))
        self.resizeColumnsToContents()

    def _set_item(self, row: int, column: int, text: str) -> None:
        item = QTableWidgetItem(text)
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        self.setItem(row, column, item)

    def _actions(self, labels: tuple[str, ...], disabled: bool = False) -> QWidget:
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        for label in labels:
            button = QPushButton(label)
            button.setEnabled(not disabled)
            layout.addWidget(button)
        layout.addStretch(1)
        return widget
