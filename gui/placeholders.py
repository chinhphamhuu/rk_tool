from __future__ import annotations

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class PlaceholderTab(QWidget):
    def __init__(self, title: str, subtitle: str) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(36, 30, 36, 30)
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 26px; font-weight: 800;")
        subtitle_label = QLabel(subtitle)
        subtitle_label.setStyleSheet("font-size: 14px; color: #475467;")
        layout.addWidget(title_label)
        layout.addWidget(subtitle_label)
        layout.addStretch(1)
