from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from gui.widgets.info_card import Card, muted_label
from gui.widgets.status_badge import StatusBadge


class StepRow(QWidget):
    def __init__(
        self,
        number: int,
        title: str,
        subtitle: str,
        status: str = "Chờ chạy",
        variant: str = "info",
        button: str | None = None,
    ) -> None:
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        marker = QLabel(str(number))
        marker.setFixedSize(28, 28)
        marker.setAlignment(Qt.AlignCenter)
        marker.setStyleSheet(
            "border-radius:14px; font-weight:800; "
            + ("background:#16a34a; color:white;" if variant == "ok" else "background:#e8f1ff; color:#0b6bff;")
        )
        text = QVBoxLayout()
        text.setSpacing(3)
        title_label = QLabel(title)
        title_label.setObjectName("SectionTitle")
        title_label.setStyleSheet("font-size: 14px;")
        text.addWidget(title_label)
        text.addWidget(muted_label(subtitle, small=True))

        layout.addWidget(marker)
        layout.addLayout(text, 1)
        layout.addWidget(StatusBadge(status, "ok" if variant == "ok" else variant))
        if button:
            layout.addWidget(QPushButton(button))


class StepCard(Card):
    def __init__(self, title: str, steps: list[tuple[int, str, str, str, str, str | None]]) -> None:
        super().__init__(title)
        for step in steps:
            self.layout.addWidget(StepRow(*step))
