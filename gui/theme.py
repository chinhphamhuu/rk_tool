from __future__ import annotations

from PySide6.QtGui import QFont


def apply_theme(app) -> None:
    app.setFont(QFont("Segoe UI", 10))
    app.setStyleSheet("""
    * {
        font-size: 14px;
        color: #1f2937;
    }
    QMainWindow,
    QWidget#AppRoot {
        background: #f6f8fb;
    }
    QWidget#ContentRoot {
        background: #f8fafc;
    }
    QLabel#PageTitle {
        font-size: 30px;
        font-weight: 800;
        color: #111827;
    }
    QLabel#PageSubtitle {
        font-size: 15px;
        color: #667085;
    }
    QLabel#SectionTitle {
        font-size: 16px;
        font-weight: 700;
        color: #111827;
    }
    QLabel#MutedText {
        color: #667085;
    }
    QLabel#SmallMutedText {
        color: #667085;
        font-size: 12px;
    }
    QLabel#ValueText {
        font-weight: 700;
        color: #111827;
    }
    QLabel#HugeSuccess {
        color: #087443;
        font-size: 30px;
        font-weight: 800;
    }
    QLabel#HeroCheck {
        color: white;
        font-size: 52px;
        font-weight: 800;
    }
    QLabel#StatusBadge_ok,
    QLabel#StatusBadge_success {
        background: #dcfce7;
        color: #079455;
        border-radius: 11px;
        padding: 3px 10px;
        font-weight: 700;
    }
    QLabel#StatusBadge_info {
        background: #dbeafe;
        color: #1d4ed8;
        border-radius: 11px;
        padding: 3px 10px;
        font-weight: 700;
    }
    QLabel#StatusBadge_warning {
        background: #fef3c7;
        color: #b45309;
        border-radius: 11px;
        padding: 3px 10px;
        font-weight: 700;
    }
    QLabel#StatusBadge_error {
        background: #fee2e2;
        color: #b42318;
        border-radius: 11px;
        padding: 3px 10px;
        font-weight: 700;
    }
    QLabel#Pill {
        background: #f2f4f7;
        border: 1px solid #d0d5dd;
        border-radius: 8px;
        padding: 5px 9px;
        color: #344054;
        font-weight: 600;
    }
    QFrame#Card,
    QFrame#LogPanel,
    QFrame#SidebarStatus {
        background: white;
        border: 1px solid #e4e7ec;
        border-radius: 10px;
    }
    QFrame#SuccessHero {
        background: #ecfdf3;
        border: 1px solid #86efac;
        border-radius: 12px;
    }
    QFrame#HeroCheckCircle {
        background: #16a34a;
        border-radius: 42px;
    }
    QFrame#WarningBox_info {
        background: #eff6ff;
        border: 1px solid #bfdbfe;
        border-radius: 10px;
    }
    QFrame#WarningBox_success {
        background: #f0fdf4;
        border: 1px solid #86efac;
        border-radius: 10px;
    }
    QFrame#WarningBox_warning {
        background: #fffbeb;
        border: 1px solid #f59e0b;
        border-radius: 10px;
    }
    QFrame#WarningBox_error {
        background: #fef2f2;
        border: 1px solid #fca5a5;
        border-radius: 10px;
    }
    QLineEdit,
    QTextEdit,
    QPlainTextEdit {
        background: white;
        border: 1px solid #d0d5dd;
        border-radius: 8px;
        padding: 9px 12px;
        selection-background-color: #1a73e8;
    }
    QLineEdit[readOnly="true"] {
        background: #f9fafb;
        color: #475467;
    }
    QPushButton {
        background: white;
        border: 1px solid #d0d5dd;
        border-radius: 8px;
        padding: 9px 14px;
        font-weight: 700;
        color: #344054;
    }
    QPushButton:hover {
        background: #f9fafb;
        border-color: #98a2b3;
    }
    QPushButton#PrimaryButton {
        background: #0b6bff;
        color: white;
        border: 1px solid #0b6bff;
    }
    QPushButton#PrimaryButton:hover {
        background: #075ee8;
    }
    QPushButton#GhostButton {
        background: #f8fafc;
        border: 1px solid #dbe3ef;
        color: #175cd3;
    }
    QPushButton#DangerButton {
        color: #b42318;
        border-color: #fca5a5;
    }
    QTableWidget,
    QTreeWidget {
        background: white;
        border: 1px solid #e4e7ec;
        border-radius: 8px;
        gridline-color: #edf0f5;
        selection-background-color: #e8f1ff;
        selection-color: #0b6bff;
    }
    QHeaderView::section {
        background: #f8fafc;
        color: #475467;
        border: 0;
        border-bottom: 1px solid #e4e7ec;
        padding: 8px;
        font-weight: 700;
    }
    QTableWidget::item,
    QTreeWidget::item {
        padding: 6px;
        border-bottom: 1px solid #f2f4f7;
    }
    QScrollArea {
        border: 0;
        background: transparent;
    }
    QScrollBar:vertical {
        background: transparent;
        width: 10px;
        margin: 2px;
    }
    QScrollBar::handle:vertical {
        background: #cbd5e1;
        border-radius: 5px;
    }
    QScrollBar::add-line:vertical,
    QScrollBar::sub-line:vertical {
        height: 0;
    }
    QListWidget#SidebarList {
        background: transparent;
        border: 0;
        outline: 0;
    }
    QListWidget#SidebarList::item {
        height: 48px;
        margin: 4px 12px;
        padding-left: 16px;
        border-radius: 9px;
        color: #344054;
    }
    QListWidget#SidebarList::item:selected {
        background: #eaf2ff;
        color: #0b6bff;
        border-left: 4px solid #0b6bff;
    }
    QListWidget#SidebarList::item:hover {
        background: #f1f5f9;
    }
    """)
