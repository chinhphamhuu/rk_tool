from __future__ import annotations

import subprocess
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable


@dataclass(frozen=True)
class WslOutputLine:
    stream: str
    text: str


@dataclass(frozen=True)
class WslCommandResult:
    command: str
    args: tuple[str, ...]
    exit_code: int
    stdout: str
    stderr: str
    output_lines: tuple[WslOutputLine, ...]

    @property
    def ok(self) -> bool:
        return self.exit_code == 0


class WslRunnerError(RuntimeError):
    pass


class WslCommandError(WslRunnerError):
    def __init__(self, result: WslCommandResult) -> None:
        super().__init__(f"WSL command failed with exit code {result.exit_code}: {result.command}")
        self.result = result
        self.exit_code = result.exit_code
        self.stdout = result.stdout
        self.stderr = result.stderr


class WslCommandTimeout(WslRunnerError):
    def __init__(
        self,
        command: str,
        args: tuple[str, ...],
        timeout: float,
        stdout: str,
        stderr: str,
    ) -> None:
        super().__init__(f"WSL command timed out after {timeout} seconds: {command}")
        self.command = command
        self.args = args
        self.timeout = timeout
        self.stdout = stdout
        self.stderr = stderr


LogCallback = Callable[[WslOutputLine], None]
PopenFactory = Callable[..., subprocess.Popen]


class WslRunner:
    def __init__(
        self,
        *,
        wsl_executable: str = "wsl.exe",
        distro: str | None = None,
        popen_factory: PopenFactory | None = None,
    ) -> None:
        self.wsl_executable = wsl_executable
        self.distro = distro
        self._popen_factory = popen_factory or subprocess.Popen

    def build_command(self, command: str) -> list[str]:
        args = [self.wsl_executable]
        if self.distro:
            args.extend(["-d", self.distro])
        args.extend(["bash", "-lc", command])
        return args

    def run(
        self,
        command: str,
        *,
        cwd: Path | str | None = None,
        timeout: float | None = None,
        check: bool = True,
        on_output: LogCallback | None = None,
    ) -> WslCommandResult:
        args = self.build_command(command)
        process = self._popen_factory(
            args,
            cwd=str(cwd) if cwd is not None else None,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )

        stdout_parts: list[str] = []
        stderr_parts: list[str] = []
        output_lines: list[WslOutputLine] = []
        lock = threading.Lock()

        stdout_thread = threading.Thread(
            target=self._read_stream,
            args=(process.stdout, "stdout", stdout_parts, output_lines, lock, on_output),
            daemon=True,
        )
        stderr_thread = threading.Thread(
            target=self._read_stream,
            args=(process.stderr, "stderr", stderr_parts, output_lines, lock, on_output),
            daemon=True,
        )
        stdout_thread.start()
        stderr_thread.start()

        try:
            exit_code = process.wait(timeout=timeout)
        except subprocess.TimeoutExpired as exc:
            process.kill()
            stdout_thread.join(timeout=1)
            stderr_thread.join(timeout=1)
            raise WslCommandTimeout(
                command=command,
                args=tuple(args),
                timeout=timeout if timeout is not None else exc.timeout,
                stdout="".join(stdout_parts),
                stderr="".join(stderr_parts),
            ) from exc

        stdout_thread.join()
        stderr_thread.join()

        result = WslCommandResult(
            command=command,
            args=tuple(args),
            exit_code=exit_code,
            stdout="".join(stdout_parts),
            stderr="".join(stderr_parts),
            output_lines=tuple(output_lines),
        )
        if check and not result.ok:
            raise WslCommandError(result)
        return result

    @staticmethod
    def _read_stream(
        stream: Iterable[str] | None,
        stream_name: str,
        text_parts: list[str],
        output_lines: list[WslOutputLine],
        lock: threading.Lock,
        on_output: LogCallback | None,
    ) -> None:
        if stream is None:
            return
        for raw_line in stream:
            with lock:
                text_parts.append(raw_line)
                line = WslOutputLine(stream=stream_name, text=raw_line.rstrip("\r\n"))
                output_lines.append(line)
            if on_output:
                on_output(line)
