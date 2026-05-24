from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout


class LogPanel(QFrame):
    def __init__(self, entries: list[tuple[str, str, str]] | None = None) -> None:
        super().__init__()
        self.setObjectName("LogPanel")
        self.setMinimumHeight(150)
        self._entry_layouts: list[QHBoxLayout] = []

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(18, 14, 18, 14)
        self.layout.setSpacing(10)

        header = QHBoxLayout()
        title = QLabel("Nhật ký (realtime)")
        title.setObjectName("SectionTitle")
        clear = QPushButton("Xóa log")
        clear.setObjectName("GhostButton")
        clear.clicked.connect(self.clear_entries)
        header.addWidget(title)
        header.addStretch(1)
        header.addWidget(clear)
        self.layout.addLayout(header)

        self._stretch = None
        for timestamp, variant, text in entries or []:
            self.add_entry(text, variant=variant, timestamp=timestamp)
        self._add_stretch()

    def add_entry(self, text: str, variant: str = "info", timestamp: str | None = None) -> None:
        self._remove_stretch()

        row = QHBoxLayout()
        row.setSpacing(10)
        time = QLabel(timestamp or datetime.now().strftime("[%H:%M:%S]"))
        time.setObjectName("MutedText")
        icon = QLabel({"ok": "✓", "info": "i", "warning": "!", "error": "!"}.get(variant, "i"))
        icon.setFixedSize(18, 18)
        icon.setAlignment(Qt.AlignCenter)
        icon.setStyleSheet(
            "border-radius: 9px; font-size: 11px; font-weight: 800; "
            + {
                "ok": "background:#dcfce7; color:#079455;",
                "info": "background:#dbeafe; color:#1d4ed8;",
                "warning": "background:#fef3c7; color:#b45309;",
                "error": "background:#fee2e2; color:#b42318;",
            }.get(variant, "background:#dbeafe; color:#1d4ed8;")
        )
        message = QLabel(text)
        message.setWordWrap(True)
        row.addWidget(time)
        row.addWidget(icon)
        row.addWidget(message, 1)
        self.layout.addLayout(row)
        self._entry_layouts.append(row)
        self._add_stretch()

    def clear_entries(self) -> None:
        self._remove_stretch()
        while self.layout.count() > 1:
            item = self.layout.takeAt(1)
            if item.layout():
                self._clear_layout(item.layout())
            elif item.widget():
                item.widget().deleteLater()
        self._entry_layouts.clear()
        self._add_stretch()

    def _add_stretch(self) -> None:
        self._stretch = self.layout.addStretch(1)

    def _remove_stretch(self) -> None:
        if self._stretch is not None:
            self.layout.removeItem(self._stretch)
            self._stretch = None

    def _clear_layout(self, layout: QHBoxLayout | QVBoxLayout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())
