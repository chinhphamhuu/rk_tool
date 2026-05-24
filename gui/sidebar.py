from __future__ import annotations

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QStyle, QVBoxLayout, QWidget

from gui.widgets.info_card import muted_label


class Sidebar(QWidget):
    current_changed = Signal(int)

    def __init__(self, labels: list[str]) -> None:
        super().__init__()
        self.setFixedWidth(320)
        self.setObjectName("Sidebar")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 12, 10, 12)
        layout.setSpacing(12)

        brand = QHBoxLayout()
        logo = QLabel("RK")
        logo.setFixedSize(28, 28)
        logo.setAlignment(Qt.AlignCenter)
        logo.setStyleSheet("background:#0b6bff; color:white; border-radius:7px; font-weight:800;")
        title = QLabel("Rockchip Android ROM Repack GUI")
        title.setStyleSheet("font-size:14px; font-weight:700;")
        title.setWordWrap(True)
        brand.addWidget(logo)
        brand.addWidget(title, 1)
        layout.addLayout(brand)

        self.list = QListWidget()
        self.list.setObjectName("SidebarList")
        self.list.setIconSize(QSize(22, 22))
        for index, label in enumerate(labels):
            item = QListWidgetItem(self._icon(index), label)
            item.setSizeHint(QSize(280, 48))
            self.list.addItem(item)
        self.list.currentRowChanged.connect(self.current_changed.emit)
        layout.addWidget(self.list, 1)

        status = QFrame()
        status.setObjectName("SidebarStatus")
        status_layout = QHBoxLayout(status)
        status_layout.setContentsMargins(18, 14, 18, 14)
        ok = QLabel("✓")
        ok.setFixedSize(36, 36)
        ok.setAlignment(Qt.AlignCenter)
        ok.setStyleSheet("background:#16a34a; color:white; border-radius:18px; font-size:18px; font-weight:800;")
        text = QVBoxLayout()
        ready = QLabel("Sẵn sàng")
        ready.setStyleSheet("font-weight:800;")
        text.addWidget(ready)
        text.addWidget(muted_label("Mọi thứ đã sẵn sàng để bắt đầu.", small=True))
        status_layout.addWidget(ok)
        status_layout.addLayout(text, 1)
        layout.addWidget(status)

        footer = QHBoxLayout()
        version = QLabel("v1.2.0")
        version.setObjectName("MutedText")
        info = QLabel("i")
        info.setFixedSize(18, 18)
        info.setAlignment(Qt.AlignCenter)
        info.setStyleSheet("border:1px solid #98a2b3; border-radius:9px; color:#667085;")
        footer.addWidget(version)
        footer.addStretch(1)
        footer.addWidget(info)
        layout.addLayout(footer)

    def select(self, index: int) -> None:
        self.list.setCurrentRow(index)

    def _icon(self, index: int):
        icons = (
            QStyle.SP_DirIcon,
            QStyle.SP_ArrowDown,
            QStyle.SP_FileDialogDetailedView,
            QStyle.SP_DirOpenIcon,
            QStyle.SP_DialogApplyButton,
            QStyle.SP_FileDialogListView,
            QStyle.SP_DialogYesButton,
        )
        return self.style().standardIcon(icons[index])
