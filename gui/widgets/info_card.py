from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QGridLayout, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from gui.widgets.status_badge import StatusBadge


def title_label(text: str) -> QLabel:
    label = QLabel(text)
    label.setObjectName("PageTitle")
    return label


def subtitle_label(text: str) -> QLabel:
    label = QLabel(text)
    label.setObjectName("PageSubtitle")
    return label


def section_label(text: str) -> QLabel:
    label = QLabel(text)
    label.setObjectName("SectionTitle")
    return label


def muted_label(text: str, small: bool = False) -> QLabel:
    label = QLabel(text)
    label.setObjectName("SmallMutedText" if small else "MutedText")
    label.setWordWrap(True)
    return label


class Card(QFrame):
    def __init__(self, title: str | None = None) -> None:
        super().__init__()
        self.setObjectName("Card")
        self.setFrameShape(QFrame.NoFrame)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(18, 16, 18, 16)
        self.layout.setSpacing(12)
        if title:
            self.layout.addWidget(section_label(title))


class MetricCard(Card):
    def __init__(
        self,
        title: str,
        value: str,
        subtitle: str = "",
        badge: str | None = None,
        badge_variant: str = "ok",
    ) -> None:
        super().__init__()
        header = QHBoxLayout()
        header.addWidget(section_label(title))
        header.addStretch(1)
        if badge:
            header.addWidget(StatusBadge(badge, badge_variant))
        self.layout.addLayout(header)

        value_label = QLabel(value)
        value_label.setObjectName("PageTitle")
        value_label.setStyleSheet("font-size: 24px;")
        self.layout.addWidget(value_label)

        if subtitle:
            self.layout.addWidget(muted_label(subtitle))


class KeyValueCard(Card):
    def __init__(self, title: str, rows: list[tuple[str, str]]) -> None:
        super().__init__(title)
        grid = QGridLayout()
        grid.setHorizontalSpacing(24)
        grid.setVerticalSpacing(10)
        for row, (key, value) in enumerate(rows):
            key_label = muted_label(key)
            value_label = QLabel(value)
            value_label.setObjectName("ValueText")
            value_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            grid.addWidget(key_label, row, 0)
            grid.addWidget(value_label, row, 1)
        self.layout.addLayout(grid)


def page_header(title: str, subtitle: str) -> QWidget:
    widget = QWidget()
    layout = QVBoxLayout(widget)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(8)
    layout.addWidget(title_label(title))
    layout.addWidget(subtitle_label(subtitle))
    return widget
