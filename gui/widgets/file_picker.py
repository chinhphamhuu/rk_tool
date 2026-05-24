from __future__ import annotations

from PySide6.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget


class FilePicker(QWidget):
    def __init__(self, label: str, placeholder: str, button_text: str = "Chọn file") -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        title = QLabel(label)
        title.setObjectName("SectionTitle")
        row = QHBoxLayout()
        row.setSpacing(12)
        self.input = QLineEdit()
        self.input.setPlaceholderText(placeholder)
        self.button = QPushButton(f"📁  {button_text}")
        row.addWidget(self.input, 1)
        row.addWidget(self.button)
        layout.addWidget(title)
        layout.addLayout(row)
