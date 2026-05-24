from __future__ import annotations

from PySide6.QtWidgets import QLineEdit

from gui.widgets.info_card import Card, muted_label


class WorkspaceCard(Card):
    def __init__(self, workspace_path: str) -> None:
        super().__init__("📁  Workspace tự động")
        self.path_input = QLineEdit(workspace_path)
        self.path_input.setReadOnly(True)
        self.layout.addWidget(self.path_input)
        self.layout.addWidget(muted_label("Thư mục workspace sẽ được tự động tạo theo APP_ROOT.", small=True))
