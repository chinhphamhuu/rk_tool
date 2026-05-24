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
        self.title_label = QLabel(title)
        self.title_label.setObjectName("SectionTitle")
        self.message_label = QLabel(message)
        self.message_label.setObjectName("MutedText")
        self.message_label.setWordWrap(True)
        text_layout.addWidget(self.title_label)
        text_layout.addWidget(self.message_label)
        layout.addLayout(text_layout, 1)

    def setText(self, text: str) -> None:
        if "<br>" in text:
            title, message = text.split("<br>", 1)
            self.title_label.setText(title.replace("<b>", "").replace("</b>", ""))
            self.message_label.setText(message)
            return
        self.message_label.setText(text)
