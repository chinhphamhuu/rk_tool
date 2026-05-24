from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel


class StatusBadge(QLabel):
    def __init__(self, text: str, variant: str = "info") -> None:
        super().__init__(text)
        self.setObjectName(f"StatusBadge_{variant}")
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumHeight(24)
