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
        self.current_project_state = None
        self.current_project_state_path = None
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

        self.project_tab = ProjectTab(paths)
        self.unpack_tab = UnpackTab(paths)
        self.project_tab.project_created.connect(self._set_project_state)
        self.project_tab.project_loaded.connect(self._set_project_state)
        self.unpack_tab.project_state_updated.connect(self._set_project_state)

        self.stack.addWidget(self.project_tab)
        self.stack.addWidget(self.unpack_tab)
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
        self.tools_label = QLabel("●  Công cụ: bundled/read-only")
        self.tools_label.setStyleSheet("color:#079455; font-weight:700;")
        self.workspace_label = QLabel("●  Project: Chưa tạo")
        self.workspace_label.setStyleSheet("color:#667085; font-weight:600;")
        layout.addWidget(self.tools_label)
        layout.addSpacing(28)
        layout.addWidget(self.workspace_label)
        return bar

    def _set_project_state(self, state, state_path) -> None:
        self.current_project_state = state
        self.current_project_state_path = state_path
        self.unpack_tab.set_project_state(state, state_path)
        self.workspace_label.setText(f"●  Project: {state.project_name}")
