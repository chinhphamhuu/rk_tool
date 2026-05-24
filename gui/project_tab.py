from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QUrl, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from core.app_paths import AppPaths
from core.project_state import ProjectState, create_project_state, load_project_state, save_project_state
from core.tool_config import BundledToolConfig, load_bundled_tool_config
from gui.widgets.bundled_tools_card import BundledToolsCard
from gui.widgets.file_picker import FilePicker
from gui.widgets.info_card import Card, page_header, section_label
from gui.widgets.log_panel import LogPanel
from gui.widgets.workspace_card import WorkspaceCard


PROJECT_STATE_FILENAME = "project_state.json"
PROJECT_SUBDIRS = (
    "work",
    "work/update",
    "work/update/Image",
    "work/reports",
    "work/parts",
    "work/modified",
    "editable",
    "output",
    "logs",
)
INVALID_PROJECT_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


class ProjectCreationError(ValueError):
    """Raised when the Project tab cannot create a project."""


@dataclass(frozen=True)
class CreatedProject:
    state: ProjectState
    state_path: Path
    tool_config: BundledToolConfig


def project_state_path(project_dir: str | Path) -> Path:
    return Path(project_dir) / PROJECT_STATE_FILENAME


def create_project_from_inputs(
    paths: AppPaths,
    rom_path: str | Path,
    project_name: str,
    selected_apk_path: str | Path | None = None,
) -> CreatedProject:
    paths.ensure_workspace()
    rom = Path(rom_path)
    name = _validate_project_name(project_name)
    if not rom.is_file():
        raise ProjectCreationError(f"ROM gốc không tồn tại: {rom}")

    apk_path = Path(selected_apk_path) if selected_apk_path else None
    if apk_path is not None and not apk_path.is_file():
        raise ProjectCreationError(f"APK tùy chọn không tồn tại: {apk_path}")

    project_dir = paths.projects_dir / name
    if project_dir.exists():
        raise ProjectCreationError(f"Project đã tồn tại, hãy chọn tên khác: {project_dir}")

    for relative_dir in PROJECT_SUBDIRS:
        (project_dir / relative_dir).mkdir(parents=True, exist_ok=False)

    state = create_project_state(
        project_name=name,
        original_rom_path=rom,
        project_dir=project_dir,
        image_dir=project_dir / "work" / "update" / "Image",
        editable_dir=project_dir / "editable",
        work_dir=project_dir / "work",
        output_dir=project_dir / "output",
        reports_dir=project_dir / "work" / "reports",
        selected_apk_path=apk_path,
    )
    state_path = project_state_path(project_dir)
    save_project_state(state, state_path)

    return CreatedProject(
        state=state,
        state_path=state_path,
        tool_config=load_bundled_tool_config(paths),
    )


def _validate_project_name(project_name: str) -> str:
    name = project_name.strip()
    if not name:
        raise ProjectCreationError("Tên project không được rỗng.")
    if INVALID_PROJECT_CHARS.search(name):
        raise ProjectCreationError("Tên project chứa ký tự không hợp lệ.")
    return name


class ProjectTab(QWidget):
    project_created = Signal(object, object)
    project_loaded = Signal(object, object)

    def __init__(self, paths: AppPaths) -> None:
        super().__init__()
        self.paths = paths
        self.tool_config = load_bundled_tool_config(paths)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(36, 30, 36, 24)
        layout.setSpacing(18)

        layout.addWidget(page_header("Tạo project ROM", "Tạo project mới từ ROM gốc update.img."))

        form = Card()
        self.rom_picker = FilePicker("ROM gốc update.img", "Chọn file update.img từ ROM gốc...")
        self.rom_picker.button.clicked.connect(self._pick_rom)
        form.layout.addWidget(self.rom_picker)

        self.project_name = QLineEdit()
        self.project_name.setPlaceholderText("Ví dụ: rk3318_android11")
        self.project_name.textChanged.connect(self._update_workspace_preview)
        name_card = QWidget()
        name_layout = QVBoxLayout(name_card)
        name_layout.setContentsMargins(0, 0, 0, 0)
        name_layout.setSpacing(8)
        name_layout.addWidget(section_label("Tên project"))
        name_layout.addWidget(self.project_name)
        form.layout.addWidget(name_card)

        self.apk_picker = FilePicker("APK cần thêm (tùy chọn)", "Chọn file APK (không bắt buộc)...")
        self.apk_picker.button.clicked.connect(self._pick_apk)
        form.layout.addWidget(self.apk_picker)

        cards = QGridLayout()
        cards.setHorizontalSpacing(24)
        self.workspace_card = WorkspaceCard(str(self.paths.projects_dir / "<project_name>"))
        cards.addWidget(self.workspace_card, 0, 0)
        cards.addWidget(BundledToolsCard(self.tool_config), 0, 1)
        form.layout.addLayout(cards)

        actions = QHBoxLayout()
        create = QPushButton("⊕  Tạo project")
        create.setObjectName("PrimaryButton")
        create.clicked.connect(self._create_project)
        open_workspace = QPushButton("Mở workspace")
        open_workspace.clicked.connect(lambda: self._open_folder(self.paths.projects_dir))
        load_state = QPushButton("Mở project_state.json")
        load_state.clicked.connect(self._load_project_state)
        actions.addWidget(create)
        actions.addWidget(open_workspace)
        actions.addWidget(load_state)
        actions.addStretch(1)
        form.layout.addLayout(actions)
        layout.addWidget(form)

        self.log_panel = LogPanel(
            [
                ("[ready]", "info", "Sẵn sàng tạo project mới."),
                ("[ready]", "ok" if self.tool_config.all_ok else "warning", self._tool_status_message()),
                ("[ready]", "info", "Workspace được tạo tự động dưới APP_ROOT/workspace."),
            ]
        )
        layout.addWidget(self.log_panel)
        layout.addStretch(1)

    def _pick_rom(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Chọn ROM gốc", str(self.paths.app_root), "Rockchip ROM (*.img);;All files (*)")
        if path:
            self.rom_picker.input.setText(path)

    def _pick_apk(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Chọn APK", str(self.paths.app_root), "Android APK (*.apk);;All files (*)")
        if path:
            self.apk_picker.input.setText(path)

    def _create_project(self) -> None:
        try:
            created = create_project_from_inputs(
                paths=self.paths,
                rom_path=self.rom_picker.input.text(),
                project_name=self.project_name.text(),
                selected_apk_path=self.apk_picker.input.text().strip() or None,
            )
        except ProjectCreationError as exc:
            self.log_panel.add_entry(str(exc), "error")
            return

        self.log_panel.add_entry("Project created", "ok")
        self.log_panel.add_entry(f"Project state saved: {created.state_path}", "ok")
        self.log_panel.add_entry(f"Workspace path: {created.state.project_dir}", "info")
        self.log_panel.add_entry(self._tool_status_message(), "ok" if created.tool_config.all_ok else "warning")
        self.project_created.emit(created.state, created.state_path)

    def _load_project_state(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Mở project_state.json",
            str(self.paths.projects_dir),
            "Project state (project_state.json);;JSON (*.json);;All files (*)",
        )
        if not path:
            return
        try:
            state = load_project_state(path)
        except Exception as exc:
            self.log_panel.add_entry(f"Không thể load project_state.json: {exc}", "error")
            return
        self.log_panel.add_entry(f"Loaded project: {state.project_name}", "ok")
        self.project_loaded.emit(state, Path(path))

    def _update_workspace_preview(self) -> None:
        name = self.project_name.text().strip() or "<project_name>"
        self.workspace_card.path_input.setText(str(self.paths.projects_dir / name))

    def _open_folder(self, path: Path) -> None:
        path.mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))

    def _tool_status_message(self) -> str:
        if self.tool_config.all_ok:
            return "Tools status OK: bundled tools are read-only."
        missing = ", ".join(tool.name for tool in self.tool_config.missing_tools)
        return f"Tools status MISSING: {missing}"
