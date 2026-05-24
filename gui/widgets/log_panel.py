from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout


class LogPanel(QFrame):
    def __init__(self, entries: list[tuple[str, str, str]] | None = None) -> None:
        super().__init__()
        self.setObjectName("LogPanel")
        self.setMinimumHeight(150)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(10)

        header = QHBoxLayout()
        title = QLabel("Nhật ký (realtime)")
        title.setObjectName("SectionTitle")
        clear = QPushButton("🗑  Xóa log")
        clear.setObjectName("GhostButton")
        header.addWidget(title)
        header.addStretch(1)
        header.addWidget(clear)
        layout.addLayout(header)

        for timestamp, variant, text in entries or []:
            row = QHBoxLayout()
            row.setSpacing(10)
            time = QLabel(timestamp)
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
            layout.addLayout(row)
        layout.addStretch(1)
