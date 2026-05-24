from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QUrl, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QGridLayout, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from core.app_paths import AppPaths
from core.lpdump_parser import LpDumpParseError, load_lpdump_report
from core.partition_explorer import PartitionExplorerResult, build_partition_explorer
from core.project_state import (
    ProjectState,
    save_project_state,
    update_lpunpack_state,
    update_partition_explorer_state,
)
from core.super_image import SuperImageWorkflowError, extract_dynamic_partitions
from core.tool_config import load_bundled_tool_config
from core.workflow import WorkflowError, run_unpack_and_analyze_workflow
from core.wsl_runner import WslCommandError, WslCommandTimeout, WslRunner
from gui.widgets.detected_image_table import DetectedImageRow, DetectedImageTable
from gui.widgets.info_card import Card, KeyValueCard, page_header
from gui.widgets.log_panel import LogPanel
from gui.widgets.partition_table import DynamicPartitionRow, DynamicPartitionTable
from gui.widgets.partition_tree import OutputEditableTree
from gui.widgets.step_card import StepCard
from gui.widgets.warning_box import WarningBox


class UnpackFlowError(ValueError):
    """Raised when Unpack tab backend flow cannot run."""


@dataclass(frozen=True)
class RefreshedExplorerState:
    result: PartitionExplorerResult
    state_path: Path | None


@dataclass(frozen=True)
class BackendExplorerState:
    result: PartitionExplorerResult
    state_path: Path
    commands_run: tuple[str, ...]
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class SuperPartitionExtractedState:
    result: object
    explorer_result: PartitionExplorerResult
    state_path: Path


def refresh_partition_explorer_state(
    state: ProjectState | None,
    state_path: str | Path | None = None,
) -> RefreshedExplorerState:
    if state is None:
        raise UnpackFlowError("Chua tao hoac mo project.")

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


def run_unpack_analyze_backend(
    state: ProjectState | None,
    state_path: str | Path | None,
    paths: AppPaths,
    runner=None,
    log_callback=None,
) -> BackendExplorerState:
    if state is None:
        raise UnpackFlowError("Chua tao hoac mo project.")

    tools = load_bundled_tool_config(paths)
    active_runner = runner or WslRunner()
    saved_path = Path(state_path) if state_path is not None else Path(state.project_dir) / "project_state.json"
    result = run_unpack_and_analyze_workflow(
        project_state=state,
        tools=tools,
        runner=active_runner,
        state_path=saved_path,
        log_callback=log_callback,
    )
    return BackendExplorerState(
        result=result.partition_explorer_result,
        state_path=saved_path,
        commands_run=result.commands_run,
        warnings=result.warnings,
    )


def extract_super_partitions_backend(
    state: ProjectState | None,
    state_path: str | Path | None,
    paths: AppPaths,
    runner=None,
    log_callback=None,
) -> SuperPartitionExtractedState:
    if state is None:
        raise UnpackFlowError("Chua tao hoac mo project.")

    super_img = Path(state.image_dir) / "super.img"
    if not super_img.is_file():
        raise UnpackFlowError(f"super.img not found: {super_img}")

    tools = load_bundled_tool_config(paths)
    active_runner = runner or WslRunner()
    saved_path = Path(state_path) if state_path is not None else Path(state.project_dir) / "project_state.json"
    parts_dir = Path(state.parts_dir) if state.parts_dir else Path(state.work_dir) / "parts"
    extract_result = extract_dynamic_partitions(
        super_img_path=super_img,
        project_work_dir=state.work_dir,
        parts_dir=parts_dir,
        tools=tools,
        runner=active_runner,
        expected_partitions=_expected_partitions_from_state_or_report(state),
        log_callback=log_callback,
    )
    refreshed = refresh_partition_explorer_state(state, saved_path)
    update_lpunpack_state(
        state,
        parts_dir=extract_result.parts_dir,
        raw_super_img_path=extract_result.raw_super_img_path,
        extracted_images=extract_result.extracted_images,
    )
    save_project_state(state, saved_path)
    return SuperPartitionExtractedState(
        result=extract_result,
        explorer_result=refreshed.result,
        state_path=saved_path,
    )


class UnpackTab(QWidget):
    project_state_updated = Signal(object, object)

    def __init__(self, paths: AppPaths | None = None, runner_factory=None) -> None:
        super().__init__()
        self.paths = paths
        self.runner_factory = runner_factory or WslRunner
        self.current_project_state: ProjectState | None = None
        self.current_state_path: Path | None = None
        self.workflow_status = "Idle"

        layout = QVBoxLayout(self)
        layout.setContentsMargins(36, 30, 36, 24)
        layout.setSpacing(18)

        top = QHBoxLayout()
        top.addWidget(page_header("Giai nen ROM", "Partition Explorer doc project_state va report hien co."))
        top.addStretch(1)
        self.run_unpack_button = QPushButton("Run unpack & analyze")
        self.run_unpack_button.setObjectName("PrimaryButton")
        self.run_unpack_button.clicked.connect(self.run_unpack_analyze)
        self.extract_super_button = QPushButton("Extract partitions")
        self.extract_super_button.clicked.connect(self.extract_super_partitions)
        self.refresh_button = QPushButton("Refresh detected images")
        self.refresh_button.clicked.connect(self.refresh_from_state)
        open_image = QPushButton("Open Image folder")
        open_image.clicked.connect(self._open_image_folder)
        open_reports = QPushButton("Open reports folder")
        open_reports.clicked.connect(self._open_reports_folder)
        top.addWidget(self.run_unpack_button)
        top.addWidget(self.extract_super_button)
        top.addWidget(self.refresh_button)
        top.addWidget(open_image)
        top.addWidget(open_reports)
        layout.addLayout(top)

        self.status_label = QLabel("Status: Idle")
        self.status_label.setObjectName("MutedText")
        layout.addWidget(self.status_label)

        self.project_card = KeyValueCard(
            "Project state",
            [("Project", "Chua tao project"), ("Image dir", "-"), ("Reports dir", "-")],
        )
        layout.addWidget(self.project_card)

        grid = QGridLayout()
        grid.setHorizontalSpacing(18)
        grid.setVerticalSpacing(18)
        steps = StepCard(
            "Unpack workflow",
            [
                (1, "Unpack RKFW", "Runs through WslRunner backend workflow.", "pending", "info", "Run"),
                (2, "Unpack RKAF", "Creates work/update/Image when tools are available.", "pending", "info", "Run"),
                (3, "Detect images", "Refresh reads Image/ and report text.", "ready", "ok", "Refresh"),
            ],
        )
        grid.addWidget(steps, 0, 0)

        images = Card("Detected images")
        self.image_table = DetectedImageTable(rows=[])
        images.layout.addWidget(self.image_table)
        self.warning_box = WarningBox(
            "Partition Explorer",
            "Chua tao hoac mo project.",
            "warning",
        )
        images.layout.addWidget(self.warning_box)
        grid.addWidget(images, 0, 1)
        grid.setColumnStretch(1, 1)
        layout.addLayout(grid)

        super_panel = QGridLayout()
        dynamic = Card("super.img -> Dynamic partitions")
        self.partition_table = DynamicPartitionTable(rows=[])
        dynamic.layout.addWidget(self.partition_table)
        super_panel.addWidget(dynamic, 0, 0)

        self.avb_card = Card("vbmeta / AVB summary")
        self.avb_lines = QLabel("AVB descriptors: unknown\nAffected partitions: -")
        self.avb_lines.setWordWrap(True)
        self.avb_lines.setObjectName("MutedText")
        self.avb_card.layout.addWidget(self.avb_lines)
        super_panel.addWidget(self.avb_card, 0, 1)

        tree = Card("Editable tree target")
        tree.layout.addWidget(OutputEditableTree())
        super_panel.addWidget(tree, 0, 2)
        super_panel.setColumnStretch(0, 2)
        super_panel.setColumnStretch(1, 1)
        super_panel.setColumnStretch(2, 1)
        layout.addLayout(super_panel)

        self.log_panel = LogPanel(
            [
                ("[ready]", "warning", "Chua tao hoac mo project."),
                ("[ready]", "info", "Backend commands run through WslRunner only."),
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
            self._handle_backend_error(exc)
            return

        self._apply_explorer_result(refreshed.result)
        self.log_panel.add_entry("Partition explorer state updated", "ok")
        if refreshed.state_path is not None:
            self.log_panel.add_entry(f"Project state saved: {refreshed.state_path}", "ok")
        self.project_state_updated.emit(self.current_project_state, refreshed.state_path)

    def run_unpack_analyze(self) -> None:
        if self.paths is None:
            self.log_panel.add_entry("App paths are not configured.", "error")
            return
        self._set_status("Running")
        try:
            result = run_unpack_analyze_backend(
                self.current_project_state,
                self.current_state_path,
                self.paths,
                runner=self.runner_factory(),
                log_callback=self._log_backend,
            )
        except Exception as exc:
            self._handle_backend_error(exc)
            self._set_status("Failed")
            return

        self._apply_explorer_result(result.result)
        for warning in result.warnings:
            self._log_warning(warning)
        self.log_panel.add_entry("Unpack/analyze completed", "ok")
        self.log_panel.add_entry(f"Project state saved: {result.state_path}", "ok")
        self.project_state_updated.emit(self.current_project_state, result.state_path)
        self._set_status("Done")

    def extract_super_partitions(self) -> None:
        if self.paths is None:
            self.log_panel.add_entry("App paths are not configured.", "error")
            return
        self._set_status("Running")
        try:
            result = extract_super_partitions_backend(
                self.current_project_state,
                self.current_state_path,
                self.paths,
                runner=self.runner_factory(),
                log_callback=self._log_backend,
            )
        except Exception as exc:
            self._handle_backend_error(exc)
            self._set_status("Failed")
            return

        self._apply_explorer_result(result.explorer_result)
        self.log_panel.add_entry(f"Dynamic partitions extracted: {len(result.result.extracted_images)}", "ok")
        for warning in result.result.warnings:
            self._log_warning(warning)
        self.log_panel.add_entry(f"Project state saved: {result.state_path}", "ok")
        self.project_state_updated.emit(self.current_project_state, result.state_path)
        self._set_status("Done")

    def _apply_explorer_result(self, result: PartitionExplorerResult) -> None:
        self.image_table.set_rows(_image_rows(result))
        self.partition_table.set_rows(_partition_rows(result))
        self._update_avb_summary(result)
        self._update_warning(result)
        for warning in result.warnings:
            self._log_warning(warning)
        for error in result.errors:
            self.log_panel.add_entry(error, "error")

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
                ("Image dir", state.image_dir if state else "-"),
                ("Reports dir", state.reports_dir if state else "-"),
            ],
        )
        parent_layout.insertWidget(index, self.project_card)

    def _update_avb_summary(self, result: PartitionExplorerResult) -> None:
        summary = result.avb_summary
        if summary is None:
            self.avb_lines.setText("AVB descriptors: unknown\nAffected partitions: -")
            return
        descriptor_state = (
            "detected"
            if summary.has_hash_descriptor or summary.has_hashtree_descriptor
            else "none"
        )
        self.avb_lines.setText(
            "\n".join(
                [
                    f"Algorithm: {summary.algorithm}",
                    f"Flags: {summary.flags}",
                    f"AVB descriptors: {descriptor_state}",
                    "Affected partitions: " + (", ".join(summary.affected_partitions) or "-"),
                ]
            )
        )

    def _update_warning(self, result: PartitionExplorerResult) -> None:
        if not result.detected_images:
            message = "Image folder is empty. Run unpack/analyze after tools are available."
        elif result.errors:
            message = result.errors[0]
        elif result.warnings:
            message = _technical_warning(result.warnings[0])
        else:
            message = "Partition Explorer state refreshed."
        self.warning_box.setText(f"<b>Partition Explorer</b><br>{message}")

    def _set_status(self, status: str) -> None:
        self.workflow_status = status
        self.status_label.setText(f"Status: {status}")
        running = status == "Running"
        self.run_unpack_button.setEnabled(not running)
        self.extract_super_button.setEnabled(not running)
        self.refresh_button.setEnabled(not running)

    def _log_backend(self, message: str, variant: str = "info") -> None:
        self.log_panel.add_entry(message, variant)

    def _log_warning(self, message: str) -> None:
        self.log_panel.add_entry(_technical_warning(message), "warning")

    def _handle_backend_error(self, exc: Exception) -> None:
        message = _friendly_backend_error(exc)
        self.warning_box.setText(f"<b>Backend workflow</b><br>{message}")
        self.log_panel.add_entry(message, "error")

    def _open_image_folder(self) -> None:
        if self.current_project_state is None:
            self.log_panel.add_entry("Chua tao hoac mo project.", "warning")
            return
        path = Path(self.current_project_state.image_dir)
        path.mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))

    def _open_reports_folder(self) -> None:
        if self.current_project_state is None:
            self.log_panel.add_entry("Chua tao hoac mo project.", "warning")
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
            _image_technical_status(image.status),
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
            _partition_status(partition.source_image_path),
            partition.supported_actions,
        )
        for partition in result.dynamic_partitions
    ]


def _expected_partitions_from_state_or_report(state: ProjectState) -> list[str]:
    report_path = Path(state.reports_dir) / "lpdump_original.txt"
    if report_path.exists():
        try:
            return [partition.name for partition in load_lpdump_report(report_path).partitions]
        except LpDumpParseError:
            return [partition.name for partition in state.dynamic_partitions]
    return [partition.name for partition in state.dynamic_partitions]


def _image_technical_status(status: str) -> str:
    return "failed" if status == "error" else "ready"


def _partition_status(source_image_path: Path | None) -> str:
    if source_image_path is not None and Path(source_image_path).is_file():
        return "extracted"
    return "pending"


def _technical_warning(message: str) -> str:
    lowered = message.lower()
    if "avb" in lowered or "descriptor" in lowered:
        return "AVB descriptors: detected"
    return message


def _friendly_backend_error(exc: Exception) -> str:
    if isinstance(exc, WslCommandError):
        detail = exc.stderr.strip() or exc.stdout.strip() or "command failed"
        return f"command failed: exit code {exc.exit_code}; {detail}"
    if isinstance(exc, WslCommandTimeout):
        return f"command failed: timeout after {exc.timeout} seconds"
    message = str(exc)
    if "Bundled tool missing:" in message:
        return "Missing tool: " + message.split("Bundled tool missing:", 1)[1].strip()
    if isinstance(exc, (WorkflowError, SuperImageWorkflowError, UnpackFlowError)):
        return message
    return message or exc.__class__.__name__


def _format_size(size_bytes: int) -> str:
    value = float(size_bytes)
    for unit in ("B", "KB", "MB", "GB"):
        if value < 1024 or unit == "GB":
            return f"{value:.2f} {unit}" if unit != "B" else f"{int(value)} B"
        value /= 1024
    return f"{size_bytes} B"
