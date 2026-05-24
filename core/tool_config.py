from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from core.app_paths import AppPaths


TOOL_OK = "OK"
TOOL_MISSING = "MISSING"


@dataclass(frozen=True)
class BundledToolSpec:
    name: str
    relative_path: Path
    expected_kind: str


@dataclass(frozen=True)
class BundledToolStatus:
    name: str
    path: Path
    expected_kind: str
    status: str

    @property
    def is_ok(self) -> bool:
        return self.status == TOOL_OK

    @property
    def is_missing(self) -> bool:
        return self.status == TOOL_MISSING


@dataclass(frozen=True)
class BundledToolConfig:
    tools_dir: Path
    tools: tuple[BundledToolStatus, ...]

    @property
    def all_ok(self) -> bool:
        return all(tool.is_ok for tool in self.tools)

    @property
    def missing_tools(self) -> tuple[BundledToolStatus, ...]:
        return tuple(tool for tool in self.tools if tool.is_missing)

    def by_name(self, name: str) -> BundledToolStatus:
        for tool in self.tools:
            if tool.name == name:
                return tool
        raise KeyError(f"Unknown bundled tool: {name}")


REQUIRED_BUNDLED_TOOLS: tuple[BundledToolSpec, ...] = (
    BundledToolSpec("afptool-rs", Path("afptool-rs") / "afptool-rs", "file"),
    BundledToolSpec("simg2img", Path("lptools") / "simg2img", "file"),
    BundledToolSpec("lpunpack", Path("lptools") / "lpunpack", "file"),
    BundledToolSpec("lpmake", Path("lptools") / "lpmake", "file"),
    BundledToolSpec("lpdump", Path("lptools") / "lpdump", "file"),
    BundledToolSpec("avbtool.py", Path("avbtool") / "avbtool.py", "file"),
)


def load_bundled_tool_config(paths: AppPaths) -> BundledToolConfig:
    tools = tuple(_check_tool(paths.tools_dir, spec) for spec in REQUIRED_BUNDLED_TOOLS)
    return BundledToolConfig(tools_dir=paths.tools_dir, tools=tools)


def _check_tool(tools_dir: Path, spec: BundledToolSpec) -> BundledToolStatus:
    path = tools_dir / spec.relative_path
    exists = path.is_dir() if spec.expected_kind == "dir" else path.is_file()
    return BundledToolStatus(
        name=spec.name,
        path=path,
        expected_kind=spec.expected_kind,
        status=TOOL_OK if exists else TOOL_MISSING,
    )
