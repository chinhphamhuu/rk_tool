from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout


ICONS = {
    "info": "i",
    "success": "✓",
    "warning": "!",
    "error": "!",
}


class WarningBox(QFrame):
    def __init__(self, title: str, message: str, variant: str = "warning") -> None:
        super().__init__()
        self.setObjectName(f"WarningBox_{variant}")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(12)

        icon = QLabel(ICONS.get(variant, "!"))
        icon.setFixedSize(26, 26)
        icon.setAlignment(Qt.AlignCenter)
        icon.setStyleSheet(
            "border-radius: 13px; font-weight: 800; color: white; "
            + {
                "info": "background:#2563eb;",
                "success": "background:#16a34a;",
                "warning": "background:#f59e0b;",
                "error": "background:#dc2626;",
            }.get(variant, "background:#f59e0b;")
        )
        layout.addWidget(icon)

        text_layout = QVBoxLayout()
        text_layout.setContentsMargins(0, 0, 0, 0)
        title_label = QLabel(title)
        title_label.setObjectName("SectionTitle")
        message_label = QLabel(message)
        message_label.setObjectName("MutedText")
        message_label.setWordWrap(True)
        text_layout.addWidget(title_label)
        text_layout.addWidget(message_label)
        layout.addLayout(text_layout, 1)
