from __future__ import annotations

from PySide6.QtWidgets import QHBoxLayout, QLabel

from gui.widgets.info_card import Card, muted_label
from gui.widgets.status_badge import StatusBadge


class BundledToolsCard(Card):
    def __init__(self) -> None:
        super().__init__("🛠  Bundled tools")
        chips = QHBoxLayout()
        chips.setSpacing(8)
        for tool in ("afptool-rs", "avbtool.py", "lpunpack", "lpmake", "lpdump"):
            chip = QLabel(tool)
            chip.setObjectName("Pill")
            chips.addWidget(chip)
        chips.addStretch(1)
        self.layout.addLayout(chips)

        status = QHBoxLayout()
        status.addWidget(muted_label("✓  Tất cả công cụ hiển thị read-only từ thư mục tools/."))
        status.addStretch(1)
        status.addWidget(StatusBadge("OK", "ok"))
        self.layout.addLayout(status)
