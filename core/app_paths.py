from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path


def _detect_app_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class AppPaths:
    app_root: Path
    tools_dir: Path
    workspace_dir: Path
    projects_dir: Path
    output_dir: Path
    logs_dir: Path
    temp_dir: Path

    @classmethod
    def detect(cls) -> "AppPaths":
        app_root = _detect_app_root()
        workspace = app_root / "workspace"
        return cls(
            app_root=app_root,
            tools_dir=app_root / "tools",
            workspace_dir=workspace,
            projects_dir=workspace / "projects",
            output_dir=workspace / "output",
            logs_dir=workspace / "logs",
            temp_dir=workspace / "temp",
        )

    def ensure_workspace(self) -> None:
        for path in (self.workspace_dir, self.projects_dir, self.output_dir, self.logs_dir, self.temp_dir):
            path.mkdir(parents=True, exist_ok=True)
