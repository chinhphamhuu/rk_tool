from __future__ import annotations

from PySide6.QtWidgets import QGridLayout, QHBoxLayout, QLineEdit, QPushButton, QVBoxLayout, QWidget

from gui.widgets.bundled_tools_card import BundledToolsCard
from gui.widgets.file_picker import FilePicker
from gui.widgets.info_card import Card, page_header
from gui.widgets.log_panel import LogPanel
from gui.widgets.workspace_card import WorkspaceCard


class ProjectTab(QWidget):
    def __init__(self, paths) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(36, 30, 36, 24)
        layout.setSpacing(18)

        layout.addWidget(page_header("Tạo project ROM", "Tạo project mới từ ROM gốc update.img."))

        form = Card()
        form.layout.addWidget(FilePicker("ROM gốc update.img", "Chọn file update.img từ ROM gốc..."))

        project_name = QLineEdit()
        project_name.setPlaceholderText("Ví dụ: rk3318_android11")
        name_card = QWidget()
        name_layout = QVBoxLayout(name_card)
        name_layout.setContentsMargins(0, 0, 0, 0)
        name_layout.setSpacing(8)
        from gui.widgets.info_card import section_label

        name_layout.addWidget(section_label("Tên project"))
        name_layout.addWidget(project_name)
        form.layout.addWidget(name_card)

        form.layout.addWidget(FilePicker("APK cần thêm (tùy chọn)", "Chọn file APK (không bắt buộc)..."))

        cards = QGridLayout()
        cards.setHorizontalSpacing(24)
        cards.addWidget(WorkspaceCard(str(paths.projects_dir / "rk3318_android11")), 0, 0)
        cards.addWidget(BundledToolsCard(), 0, 1)
        form.layout.addLayout(cards)

        actions = QHBoxLayout()
        create = QPushButton("⊕  Tạo project")
        create.setObjectName("PrimaryButton")
        actions.addWidget(create)
        actions.addWidget(QPushButton("📁  Mở thư mục workspace"))
        actions.addStretch(1)
        form.layout.addLayout(actions)
        layout.addWidget(form)

        layout.addWidget(
            LogPanel(
                [
                    ("[10:25:13]", "info", "Sẵn sàng tạo project mới."),
                    ("[10:25:13]", "ok", "Các công cụ đã được kiểm tra: OK"),
                    ("[10:25:13]", "info", "Chọn file update.img để bắt đầu."),
                    ("[10:25:13]", "info", "Workspace sẽ được tạo tự động sau khi tạo project."),
                ]
            )
        )
        layout.addStretch(1)
