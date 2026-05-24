from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QGridLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from core.editable_extractor import EditableExtractError, EditableExtractResult, extract_partition_to_editable
from core.project_state import (
    ProjectState,
    get_partition_editable_dir,
    get_partition_source_image,
    mark_partition_extracted,
    save_project_state,
)
from core.wsl_runner import WslRunner
from gui.widgets.diff_table import FolderDiffTable
from gui.widgets.info_card import Card, KeyValueCard, page_header
from gui.widgets.log_panel import LogPanel
from gui.widgets.partition_tree import EditablePartitionTree
from gui.widgets.status_badge import StatusBadge
from gui.widgets.warning_box import WarningBox


class EditRomFlowError(ValueError):
    """Raised when Edit ROM Folder flow cannot run."""


@dataclass(frozen=True)
class EditablePartitionRow:
    partition_name: str
    source_image_path: Path
    editable_dir: Path
    size_bytes: int
    status: str
    actions: tuple[str, ...]


@dataclass(frozen=True)
class EditableExtractionState:
    result: EditableExtractResult
    state_path: Path


def list_editable_partition_rows(state: ProjectState | None) -> list[EditablePartitionRow]:
    if state is None:
        return []

    partition_names: list[str] = []
    for partition in state.dynamic_partitions:
        if partition.name not in partition_names:
            partition_names.append(partition.name)
    for partition_name in state.extracted_partition_images:
        if partition_name not in partition_names:
            partition_names.append(partition_name)

    rows: list[EditablePartitionRow] = []
    for partition_name in partition_names:
        source_image = get_partition_source_image(state, partition_name)
        editable_dir = get_partition_editable_dir(state, partition_name)
        size_bytes = source_image.stat().st_size if source_image.is_file() else 0
        extracted = partition_name in state.extracted_partitions or partition_name in state.editable_partitions
        if not source_image.is_file():
            status = "missing_source"
        elif extracted and editable_dir.is_dir():
            status = "extracted"
        else:
            status = "ready"
        rows.append(
            EditablePartitionRow(
                partition_name=partition_name,
                source_image_path=source_image,
                editable_dir=editable_dir,
                size_bytes=size_bytes,
                status=status,
                actions=("Extract", "Open folder"),
            )
        )
    return rows


def extract_editable_partition_backend(
    state: ProjectState | None,
    state_path: str | Path | None,
    partition_name: str,
    runner=None,
    overwrite: bool = False,
    log_callback=None,
) -> EditableExtractionState:
    if state is None:
        raise EditRomFlowError("Chua tao hoac mo project.")
    if not partition_name:
        raise EditRomFlowError("Partition name must not be empty.")

    source_image = get_partition_source_image(state, partition_name)
    if not source_image.is_file():
        raise EditRomFlowError("Chua co partition images. Hay chay Unpack super truoc.")

    active_runner = runner or WslRunner()
    saved_path = Path(state_path) if state_path is not None else Path(state.project_dir) / "project_state.json"
    result = extract_partition_to_editable(
        partition_name=partition_name,
        source_image_path=source_image,
        editable_root=state.editable_dir,
        project_work_dir=state.work_dir,
        reports_dir=state.reports_dir,
        runner=active_runner,
        overwrite=overwrite,
        log_callback=log_callback,
    )
    mark_partition_extracted(state, partition_name, result.editable_dir)
    save_project_state(state, saved_path)
    return EditableExtractionState(result=result, state_path=saved_path)


class EditRomTab(QWidget):
    project_state_updated = Signal(object, object)

    def __init__(self, runner_factory=None) -> None:
        super().__init__()
        self.current_project_state: ProjectState | None = None
        self.current_state_path: Path | None = None
        self.runner_factory = runner_factory or WslRunner

        layout = QVBoxLayout(self)
        layout.setContentsMargins(36, 30, 36, 24)
        layout.setSpacing(18)

        layout.addWidget(
            page_header(
                "Chinh sua ROM Folder",
                "Extract partition images vao editable folder de sua bang Windows Explorer.",
            )
        )

        actions = QHBoxLayout()
        self.extract_button = QPushButton("Extract selected")
        self.extract_button.setObjectName("PrimaryButton")
        self.extract_button.clicked.connect(self.extract_selected_partition)
        self.open_partition_button = QPushButton("Open selected folder")
        self.open_partition_button.clicked.connect(self.open_selected_folder)
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.refresh_from_state)
        scan = QPushButton("Scan changes")
        scan.setObjectName("GhostButton")
        scan.clicked.connect(lambda: self.log_panel.add_entry("Scan changes se lam o task sau.", "info"))
        actions.addWidget(self.extract_button)
        actions.addWidget(self.open_partition_button)
        actions.addWidget(self.refresh_button)
        actions.addWidget(scan)
        actions.addStretch(1)
        layout.addLayout(actions)

        self.project_card = KeyValueCard(
            "Project state",
            [("Project", "Chua tao project"), ("Editable root", "-"), ("Parts dir", "-")],
        )
        layout.addWidget(self.project_card)

        grid = QGridLayout()
        grid.setHorizontalSpacing(18)
        tree_card = Card("Editable folders")
        tree_card.layout.addWidget(EditablePartitionTree())
        grid.addWidget(tree_card, 0, 0)

        partition_card = Card("Partitions")
        self.partition_table = QTableWidget(0, 6)
        self.partition_table.setHorizontalHeaderLabels(
            ("Partition", "Source image", "Editable folder", "Size", "Status", "Action")
        )
        self.partition_table.verticalHeader().hide()
        self.partition_table.setShowGrid(False)
        self.partition_table.setMinimumHeight(360)
        self.partition_table.horizontalHeader().setStretchLastSection(True)
        partition_card.layout.addWidget(self.partition_table)
        self.warning_box = WarningBox("Edit ROM Folder", "Chua tao hoac mo project.", "warning")
        partition_card.layout.addWidget(self.warning_box)
        grid.addWidget(partition_card, 0, 1)

        side = QVBoxLayout()
        self.current_card = Card("Partition hien tai")
        self.current_details = QLabel("Source image: -\nEditable folder: -\nStatus: pending")
        self.current_details.setWordWrap(True)
        self.current_details.setObjectName("MutedText")
        self.current_card.layout.addWidget(self.current_details)
        side.addWidget(self.current_card)

        diff = Card("Ket qua scan changes")
        diff.layout.addWidget(FolderDiffTable())
        side.addWidget(diff)
        grid.addLayout(side, 0, 2)
        grid.setColumnStretch(1, 1)
        layout.addLayout(grid)

        self.log_panel = LogPanel(
            [
                ("[ready]", "warning", "Chua tao hoac mo project."),
                ("[ready]", "info", "Extract editable dung debugfs rdump qua WslRunner."),
            ]
        )
        layout.addWidget(self.log_panel)

    def set_project_state(self, state: ProjectState, state_path: str | Path | None = None) -> None:
        self.current_project_state = state
        self.current_state_path = Path(state_path) if state_path is not None else Path(state.project_dir) / "project_state.json"
        self._replace_project_card()
        self.refresh_from_state()
        self.log_panel.add_entry(f"Current project: {state.project_name}", "ok")

    def refresh_from_state(self) -> None:
        rows = list_editable_partition_rows(self.current_project_state)
        self._set_rows(rows)
        if self.current_project_state is None:
            self.warning_box.setText("<b>Edit ROM Folder</b><br>Chua tao hoac mo project.")
        elif not rows:
            self.warning_box.setText("<b>Edit ROM Folder</b><br>Chua co partition images. Hay chay Unpack super truoc.")
        else:
            self.warning_box.setText("<b>Edit ROM Folder</b><br>Editable partition state refreshed.")
        self._update_current_card(rows[0] if rows else None)

    def extract_selected_partition(self) -> None:
        partition_name = self._selected_partition_name()
        if not partition_name:
            self.log_panel.add_entry("Chua chon partition.", "warning")
            return
        self.extract_button.setEnabled(False)
        try:
            result = extract_editable_partition_backend(
                self.current_project_state,
                self.current_state_path,
                partition_name,
                runner=self.runner_factory(),
                log_callback=self._log_backend,
            )
        except Exception as exc:
            self._handle_error(exc)
            return
        finally:
            self.extract_button.setEnabled(True)

        self.log_panel.add_entry(f"Partition extracted: {result.result.partition_name}", "ok")
        self.log_panel.add_entry(f"Manifest: {result.result.manifest_path}", "ok")
        for warning in result.result.warnings:
            self.log_panel.add_entry(warning, "warning")
        self.refresh_from_state()
        self.project_state_updated.emit(self.current_project_state, result.state_path)

    def open_selected_folder(self) -> None:
        partition_name = self._selected_partition_name()
        if self.current_project_state is None:
            self.log_panel.add_entry("Chua tao hoac mo project.", "warning")
            return
        if not partition_name:
            self.log_panel.add_entry("Chua chon partition.", "warning")
            return
        editable_dir = get_partition_editable_dir(self.current_project_state, partition_name)
        self.log_panel.add_entry(f"Editable folder: {editable_dir}", "info")

    def _selected_partition_name(self) -> str | None:
        selected = self.partition_table.selectionModel().selectedRows()
        if not selected:
            return None
        item = self.partition_table.item(selected[0].row(), 0)
        return item.text() if item is not None else None

    def _set_rows(self, rows: list[EditablePartitionRow]) -> None:
        self.partition_table.setRowCount(len(rows))
        for row, data in enumerate(rows):
            self._set_item(row, 0, data.partition_name)
            self._set_item(row, 1, str(data.source_image_path))
            self._set_item(row, 2, str(data.editable_dir))
            self._set_item(row, 3, _format_size(data.size_bytes))
            self.partition_table.setCellWidget(row, 4, StatusBadge(data.status, _status_variant(data.status)))
            self._set_item(row, 5, " / ".join(data.actions))
        self.partition_table.resizeColumnsToContents()

    def _set_item(self, row: int, column: int, text: str) -> None:
        item = QTableWidgetItem(text)
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        self.partition_table.setItem(row, column, item)

    def _replace_project_card(self) -> None:
        state = self.current_project_state
        parent_layout = self.layout()
        index = parent_layout.indexOf(self.project_card)
        parent_layout.removeWidget(self.project_card)
        self.project_card.deleteLater()
        self.project_card = KeyValueCard(
            "Project state",
            [
                ("Project", state.project_name if state else "Chua tao project"),
                ("Editable root", state.editable_dir if state else "-"),
                ("Parts dir", state.parts_dir or str(Path(state.work_dir) / "parts") if state else "-"),
            ],
        )
        parent_layout.insertWidget(index, self.project_card)

    def _update_current_card(self, row: EditablePartitionRow | None) -> None:
        self.current_details.setText(
            "\n".join(
                [
                    f"Source image: {row.source_image_path if row else '-'}",
                    f"Editable folder: {row.editable_dir if row else '-'}",
                    f"Status: {row.status if row else 'pending'}",
                ]
            )
        )

    def _log_backend(self, message: str, variant: str = "info") -> None:
        self.log_panel.add_entry(message, variant)

    def _handle_error(self, exc: Exception) -> None:
        message = str(exc) or exc.__class__.__name__
        if isinstance(exc, (EditRomFlowError, EditableExtractError)):
            self.warning_box.setText(f"<b>Edit ROM Folder</b><br>{message}")
        self.log_panel.add_entry(message, "error")


def _status_variant(status: str) -> str:
    if status in {"done", "extracted", "ready"}:
        return "ok"
    if status in {"failed", "missing_source"}:
        return "error"
    return "info"


def _format_size(size_bytes: int) -> str:
    value = float(size_bytes)
    for unit in ("B", "KB", "MB", "GB"):
        if value < 1024 or unit == "GB":
            return f"{value:.2f} {unit}" if unit != "B" else f"{int(value)} B"
        value /= 1024
    return f"{size_bytes} B"
