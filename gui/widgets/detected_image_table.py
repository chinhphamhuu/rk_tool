from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem, QWidget

from gui.widgets.status_badge import StatusBadge


DetectedImageRow = tuple[str, str, str, str, str, tuple[str, ...], str]


class DetectedImageTable(QTableWidget):
    DEFAULT_ROWS: list[DetectedImageRow] = [
        ("super.img", "dynamic_super", "2.68 GB", "safe", "mock", ("Analyze", "Unpack"), "Mock data"),
        ("vbmeta.img", "avb_vbmeta", "8.0 MB", "warning", "mock", ("Analyze AVB",), "Mock data"),
        ("boot.img", "boot_image", "32.0 MB", "warning", "mock", ("Advanced",), "Mock data"),
        ("recovery.img", "recovery_image", "48.0 MB", "warning", "mock", ("Advanced",), "Mock data"),
        ("dtbo.img", "dtbo_image", "16.0 MB", "info", "mock", ("Info",), "Mock data"),
        ("uboot.img", "bootloader_danger", "4.0 MB", "danger", "mock", ("Info",), "Không sửa trong MVP"),
        ("trust.img", "bootloader_danger", "4.0 MB", "danger", "mock", ("Info",), "Không sửa trong MVP"),
        ("parameter.txt", "rockchip_parameter", "12 KB", "warning", "mock", ("View",), "Cảnh báo"),
    ]

    def __init__(self, rows: list[DetectedImageRow] | None = None) -> None:
        super().__init__(0, 7)
        self.setHorizontalHeaderLabels(
            ("Tên file", "Loại", "Kích thước", "Risk", "Trạng thái", "Ghi chú", "Hành động")
        )
        self.verticalHeader().hide()
        self.setAlternatingRowColors(False)
        self.setShowGrid(False)
        self.setMinimumHeight(360)
        self.horizontalHeader().setStretchLastSection(True)
        self.set_rows(rows if rows is not None else self.DEFAULT_ROWS)

    def set_rows(self, rows: list[DetectedImageRow]) -> None:
        self.setRowCount(len(rows))
        for row, (name, kind, size, risk, status, actions, notes) in enumerate(rows):
            self._set_item(row, 0, f"📄  {name}")
            self._set_item(row, 1, kind)
            self._set_item(row, 2, size)
            self.setCellWidget(row, 3, StatusBadge(f"●  {risk}", _badge_variant(risk)))
            self._set_item(row, 4, status)
            self._set_item(row, 5, notes)
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
        layout.addStretch(1)
        return widget


def _badge_variant(value: str) -> str:
    normalized = value.lower()
    if normalized in {"safe", "safe_to_edit_limited", "low", "ok"}:
        return "ok"
    if normalized in {"danger", "error"}:
        return "error"
    if normalized == "info":
        return "info"
    return "warning"
