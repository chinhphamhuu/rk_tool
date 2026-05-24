"""Path conversion helpers for WSL command construction."""

from __future__ import annotations

import re
import shlex
from dataclasses import dataclass
from pathlib import Path


class PathConversionError(ValueError):
    """Raised when a path cannot be converted safely."""


_DRIVE_PATH_RE = re.compile(r"^(?P<drive>[A-Za-z]):[\\/](?P<tail>.*)$")
_WSL_UNC_RE = re.compile(
    r"^[\\/]{2}(?P<prefix>wsl\$|wsl\.localhost)[\\/](?P<distro>[^\\/]+)(?P<tail>(?:[\\/].*)?)$",
    re.IGNORECASE,
)
_UNC_PATH_RE = re.compile(r"^[\\/]{2}[^\\/]+[\\/].+")


@dataclass(frozen=True)
class WindowsPathToWsl:
    """Convert supported Windows path forms to Linux paths visible from WSL."""

    mount_root: str = "/mnt"

    def convert(self, path: str | Path) -> str:
        value = _coerce_path(path)
        drive_match = _DRIVE_PATH_RE.match(value)
        if drive_match:
            return self._convert_drive_path(drive_match)

        wsl_unc_match = _WSL_UNC_RE.match(value)
        if wsl_unc_match:
            return self._convert_wsl_unc_path(wsl_unc_match)

        if _UNC_PATH_RE.match(value):
            raise PathConversionError(
                "UNC network path chưa hỗ trợ trong MVP, hãy copy file vào workspace local."
            )

        raise PathConversionError(
            "Unsupported path format. Expected an absolute Windows drive path "
            "like C:\\path\\file.img or a WSL UNC path like \\\\wsl$\\Ubuntu\\home\\user."
        )

    def _convert_drive_path(self, match: re.Match[str]) -> str:
        drive = match.group("drive").lower()
        tail = match.group("tail").replace("\\", "/")
        mount_root = self.mount_root.rstrip("/")
        if not mount_root.startswith("/"):
            raise PathConversionError("mount_root must be an absolute WSL path.")
        return f"{mount_root}/{drive}/{tail}" if tail else f"{mount_root}/{drive}"

    @staticmethod
    def _convert_wsl_unc_path(match: re.Match[str]) -> str:
        tail = match.group("tail")
        if not tail:
            return "/"
        return tail.replace("\\", "/")


def windows_path_to_wsl(path: str | Path) -> str:
    """Convert a Windows path to the equivalent WSL-visible path."""

    return WindowsPathToWsl().convert(path)


def shell_quote(path: str | Path) -> str:
    """Quote a path for safe use inside a POSIX shell command."""

    return shlex.quote(_coerce_path(path))


def _coerce_path(path: str | Path) -> str:
    if isinstance(path, Path):
        value = str(path)
    elif isinstance(path, str):
        value = path
    else:
        raise PathConversionError(f"Path must be str or pathlib.Path, got {type(path).__name__}.")

    if not value:
        raise PathConversionError("Path must not be empty.")

    if value.strip() != value:
        raise PathConversionError("Path must not have leading or trailing whitespace.")

    return value
