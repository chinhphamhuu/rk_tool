from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from gui.widgets.info_card import Card, muted_label
from gui.widgets.status_badge import StatusBadge


class Checklist(Card):
    def __init__(self, title: str, rows: list[tuple[str, str, str]]) -> None:
        super().__init__(title)
        for index, (text, status, variant) in enumerate(rows, start=1):
            row = QHBoxLayout()
            marker = QLabel(str(index))
            marker.setFixedSize(26, 26)
            marker.setAlignment(Qt.AlignCenter)
            marker.setStyleSheet(
                "border-radius:13px; font-weight:800; "
                + {
                    "ok": "background:#dcfce7; color:#079455;",
                    "info": "background:#dbeafe; color:#1d4ed8;",
                    "warning": "background:#fef3c7; color:#b45309;",
                }.get(variant, "background:#e5e7eb; color:#667085;")
            )
            label = QLabel(text)
            label.setWordWrap(True)
            row.addWidget(marker)
            row.addWidget(label, 1)
            row.addWidget(StatusBadge(status, variant))
            self.layout.addLayout(row)


class SimpleChecklist(QWidget):
    def __init__(self, rows: list[tuple[str, str, str]]) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        for text, status, variant in rows:
            row = QHBoxLayout()
            row.addWidget(QLabel("✓" if variant == "ok" else "•"))
            row.addWidget(muted_label(text), 1)
            row.addWidget(StatusBadge(status, variant))
            layout.addLayout(row)
