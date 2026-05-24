from __future__ import annotations

from PySide6.QtWidgets import QPlainTextEdit


class CommandPreview(QPlainTextEdit):
    def __init__(self, command: str) -> None:
        super().__init__(command)
        self.setReadOnly(True)
        self.setMinimumHeight(150)
        self.setStyleSheet(
            "QPlainTextEdit {"
            "font-family: Consolas, 'Cascadia Mono', monospace;"
            "font-size: 12px;"
            "background: #f8fafc;"
            "}"
        )
