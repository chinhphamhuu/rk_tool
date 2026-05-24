from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QUrl, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QGridLayout, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from core.partition_explorer import PartitionExplorerResult, build_partition_explorer
from core.project_state import ProjectState, save_project_state, update_partition_explorer_state
from gui.widgets.detected_image_table import DetectedImageRow, DetectedImageTable
from gui.widgets.info_card import Card, KeyValueCard, page_header
from gui.widgets.log_panel import LogPanel
from gui.widgets.partition_table import DynamicPartitionRow, DynamicPartitionTable
from gui.widgets.partition_tree import OutputEditableTree
from gui.widgets.step_card import StepCard
from gui.widgets.warning_box import WarningBox


class UnpackFlowError(ValueError):
    """Raised when Unpack tab refresh cannot run."""


@dataclass(frozen=True)
class RefreshedExplorerState:
    result: PartitionExplorerResult
    state_path: Path | None


def refresh_partition_explorer_state(
    state: ProjectState | None,
    state_path: str | Path | None = None,
) -> RefreshedExplorerState:
    if state is None:
        raise UnpackFlowError("Chưa tạo project. Hãy tạo project ở tab Project trước.")

    reports_dir = Path(state.reports_dir)
    vbmeta_report = reports_dir / "vbmeta_info.txt"
    lpdump_report = reports_dir / "lpdump_original.txt"

    result = build_partition_explorer(
        image_dir=state.image_dir,
        vbmeta_report_path=vbmeta_report if vbmeta_report.exists() else None,
        lpdump_report_path=lpdump_report if lpdump_report.exists() else None,
        editable_root=state.editable_dir,
    )
    update_partition_explorer_state(state, result)

    saved_path = Path(state_path) if state_path is not None else Path(state.project_dir) / "project_state.json"
    save_project_state(state, saved_path)
    return RefreshedExplorerState(result=result, state_path=saved_path)


class UnpackTab(QWidget):
    project_state_updated = Signal(object, object)

    def __init__(self) -> None:
        super().__init__()
        self.current_project_state: ProjectState | None = None
        self.current_state_path: Path | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(36, 30, 36, 24)
        layout.setSpacing(18)

        top = QHBoxLayout()
        top.addWidget(page_header("Giải nén ROM", "Partition Explorer đọc dữ liệu từ project_state và report sẵn có."))
        top.addStretch(1)
        refresh = QPushButton("↻  Refresh detected images")
        refresh.clicked.connect(self.refresh_from_state)
        open_image = QPushButton("Open Image folder")
        open_image.clicked.connect(self._open_image_folder)
        open_reports = QPushButton("Open reports folder")
        open_reports.clicked.connect(self._open_reports_folder)
        top.addWidget(refresh)
        top.addWidget(open_image)
        top.addWidget(open_reports)
        layout.addLayout(top)

        self.project_card = KeyValueCard(
            "Project state",
            [("Project", "Chưa tạo project"), ("Image dir", "-"), ("Reports dir", "-")],
        )
        layout.addWidget(self.project_card)

        grid = QGridLayout()
        grid.setHorizontalSpacing(18)
        grid.setVerticalSpacing(18)
        steps = StepCard(
            "Quy trình Unpack",
            [
                (1, "Unpack RKFW", "Task sau sẽ chạy tool thật qua WslRunner.", "Chưa chạy", "info", "Disabled"),
                (2, "Unpack RKAF", "Task sau sẽ tạo Image/ thật.", "Chưa chạy", "info", "Disabled"),
                (3, "Detect images", "Refresh đọc Image/ hiện có bằng Python thuần.", "Sẵn sàng", "ok", "Refresh"),
            ],
        )
        grid.addWidget(steps, 0, 0)

        images = Card("Images / partitions đã phát hiện")
        self.image_table = DetectedImageTable(rows=[])
        images.layout.addWidget(self.image_table)
        self.warning_box = WarningBox(
            "Partition Explorer",
            "Chưa tạo project. Hãy tạo project ở tab Project trước.",
            "warning",
        )
        images.layout.addWidget(self.warning_box)
        grid.addWidget(images, 0, 1)
        grid.setColumnStretch(1, 1)
        layout.addLayout(grid)

        super_panel = QGridLayout()
        dynamic = Card("super.img → Dynamic partitions")
        self.partition_table = DynamicPartitionTable(rows=[])
        dynamic.layout.addWidget(self.partition_table)
        super_panel.addWidget(dynamic, 0, 0)

        self.avb_card = Card("vbmeta / AVB summary")
        self.avb_lines = QLabel("Chưa có report vbmeta_info.txt.")
        self.avb_lines.setWordWrap(True)
        self.avb_lines.setObjectName("MutedText")
        self.avb_card.layout.addWidget(self.avb_lines)
        super_panel.addWidget(self.avb_card, 0, 1)

        tree = Card("Cây thư mục editable sẽ tạo ra")
        tree.layout.addWidget(OutputEditableTree())
        super_panel.addWidget(tree, 0, 2)
        super_panel.setColumnStretch(0, 2)
        super_panel.setColumnStretch(1, 1)
        super_panel.setColumnStretch(2, 1)
        layout.addLayout(super_panel)

        self.log_panel = LogPanel(
            [
                ("[ready]", "warning", "Chưa tạo project. Hãy tạo project ở tab Project trước."),
                ("[ready]", "info", "Refresh chỉ đọc Image/ và report text sẵn có, chưa chạy tool thật."),
            ]
        )
        layout.addWidget(self.log_panel)

    def set_project_state(self, state: ProjectState, state_path: str | Path | None = None) -> None:
        self.current_project_state = state
        self.current_state_path = Path(state_path) if state_path is not None else Path(state.project_dir) / "project_state.json"
        self._replace_project_card()
        self.log_panel.add_entry(f"Current project: {state.project_name}", "ok")

    def refresh_from_state(self) -> None:
        try:
            refreshed = refresh_partition_explorer_state(self.current_project_state, self.current_state_path)
        except Exception as exc:
            self.warning_box.setText(f"<b>Partition Explorer</b><br>{exc}")
            self.log_panel.add_entry(str(exc), "error")
            return

        result = refreshed.result
        self.image_table.set_rows(_image_rows(result))
        self.partition_table.set_rows(_partition_rows(result))
        self._update_avb_summary(result)
        self._update_warning(result)
        self.log_panel.add_entry("Partition explorer state updated", "ok")
        if refreshed.state_path is not None:
            self.log_panel.add_entry(f"Project state saved: {refreshed.state_path}", "ok")
        for warning in result.warnings:
            self.log_panel.add_entry(warning, "warning")
        for error in result.errors:
            self.log_panel.add_entry(error, "error")
        self.project_state_updated.emit(self.current_project_state, refreshed.state_path)

    def _replace_project_card(self) -> None:
        state = self.current_project_state
        parent_layout = self.layout()
        index = parent_layout.indexOf(self.project_card)
        parent_layout.removeWidget(self.project_card)
        self.project_card.deleteLater()
        self.project_card = KeyValueCard(
            "Project state",
            [
                ("Project", state.project_name if state else "Chưa tạo project"),
                ("Image dir", state.image_dir if state else "-"),
                ("Reports dir", state.reports_dir if state else "-"),
            ],
        )
        parent_layout.insertWidget(index, self.project_card)

    def _update_avb_summary(self, result: PartitionExplorerResult) -> None:
        summary = result.avb_summary
        if summary is None:
            self.avb_lines.setText("Chưa có report vbmeta_info.txt.")
            return
        self.avb_lines.setText(
            "\n".join(
                [
                    f"Algorithm: {summary.algorithm}",
                    f"Flags: {summary.flags}",
                    f"Risk: {summary.risk_level}",
                    "Affected: " + (", ".join(summary.affected_partitions) or "-"),
                    "Warnings: " + (" | ".join(summary.warnings) or "-"),
                ]
            )
        )

    def _update_warning(self, result: PartitionExplorerResult) -> None:
        if not result.detected_images:
            message = "Chưa có file trong Image/. Task unpack thật sẽ tạo dữ liệu sau."
        elif result.errors:
            message = result.errors[0]
        elif result.warnings:
            message = result.warnings[0]
        else:
            message = "Đã refresh dữ liệu Partition Explorer từ core state."
        self.warning_box.setText(f"<b>Partition Explorer</b><br>{message}")

    def _open_image_folder(self) -> None:
        if self.current_project_state is None:
            self.log_panel.add_entry("Chưa tạo project. Hãy tạo project ở tab Project trước.", "warning")
            return
        path = Path(self.current_project_state.image_dir)
        path.mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))

    def _open_reports_folder(self) -> None:
        if self.current_project_state is None:
            self.log_panel.add_entry("Chưa tạo project. Hãy tạo project ở tab Project trước.", "warning")
            return
        path = Path(self.current_project_state.reports_dir)
        path.mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))


def _image_rows(result: PartitionExplorerResult) -> list[DetectedImageRow]:
    return [
        (
            image.name,
            image.image_type,
            _format_size(image.size_bytes),
            image.risk_level,
            image.status,
            image.supported_actions,
            "; ".join(image.notes),
        )
        for image in result.detected_images
    ]


def _partition_rows(result: PartitionExplorerResult) -> list[DynamicPartitionRow]:
    return [
        (
            partition.name,
            partition.group_name,
            _format_size(partition.size_bytes),
            "yes" if partition.readonly else "no",
            str(partition.editable_dir) if partition.editable_dir else "-",
            partition.risk_level,
            partition.supported_actions,
        )
        for partition in result.dynamic_partitions
    ]


def _format_size(size_bytes: int) -> str:
    value = float(size_bytes)
    for unit in ("B", "KB", "MB", "GB"):
        if value < 1024 or unit == "GB":
            return f"{value:.2f} {unit}" if unit != "B" else f"{int(value)} B"
        value /= 1024
    return f"{size_bytes} B"
