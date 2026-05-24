from __future__ import annotations

from PySide6.QtWidgets import QHBoxLayout, QLabel, QMainWindow, QStackedWidget, QVBoxLayout, QWidget

from gui.analyze_tab import AnalyzeTab
from gui.apply_changes_tab import ApplyChangesTab
from gui.edit_rom_tab import EditRomTab
from gui.project_tab import ProjectTab
from gui.rebuild_super_tab import RebuildSuperTab
from gui.repack_verify_tab import RepackVerifyTab
from gui.sidebar import Sidebar
from gui.unpack_tab import UnpackTab


class MainWindow(QMainWindow):
    TAB_LABELS = [
        "Project",
        "Unpack",
        "Analyze",
        "Edit ROM Folder",
        "Apply Changes",
        "Rebuild Super",
        "Repack & Verify",
    ]

    def __init__(self, paths) -> None:
        super().__init__()
        self.paths = paths
        self.setWindowTitle("Rockchip Android ROM Repack GUI")
        self.resize(1450, 1020)

        root = QWidget()
        root.setObjectName("AppRoot")
        self.setCentralWidget(root)
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        shell = QWidget()
        shell_layout = QHBoxLayout(shell)
        shell_layout.setContentsMargins(0, 0, 0, 0)
        shell_layout.setSpacing(0)

        self.sidebar = Sidebar(self.TAB_LABELS)
        self.stack = QStackedWidget()
        self.stack.setObjectName("ContentRoot")
        self.stack.addWidget(ProjectTab(paths))
        self.stack.addWidget(UnpackTab())
        self.stack.addWidget(AnalyzeTab())
        self.stack.addWidget(EditRomTab())
        self.stack.addWidget(ApplyChangesTab())
        self.stack.addWidget(RebuildSuperTab())
        self.stack.addWidget(RepackVerifyTab())

        shell_layout.addWidget(self.sidebar)
        shell_layout.addWidget(self.stack, 1)
        root_layout.addWidget(shell, 1)
        root_layout.addWidget(self._status_bar())

        self.sidebar.current_changed.connect(self.stack.setCurrentIndex)
        self.sidebar.select(0)

    def _status_bar(self) -> QWidget:
        bar = QWidget()
        bar.setStyleSheet("background:white; border-top:1px solid #e4e7ec;")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(24, 8, 24, 8)
        layout.addStretch(1)
        tools = QLabel("●  Công cụ: 5/5 sẵn sàng")
        tools.setStyleSheet("color:#079455; font-weight:700;")
        workspace = QLabel("●  Workspace: Chưa chọn")
        workspace.setStyleSheet("color:#667085; font-weight:600;")
        layout.addWidget(tools)
        layout.addSpacing(28)
        layout.addWidget(workspace)
        return bar
