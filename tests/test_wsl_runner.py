from __future__ import annotations

import io
import subprocess

import pytest

from core.wsl_runner import WslCommandError, WslCommandTimeout, WslRunner


class FakeProcess:
    def __init__(self, stdout: str = "", stderr: str = "", returncode: int = 0, timeout: bool = False) -> None:
        self.stdout = io.StringIO(stdout)
        self.stderr = io.StringIO(stderr)
        self.returncode = returncode
        self.timeout = timeout
        self.killed = False

    def wait(self, timeout=None):
        if self.timeout:
            raise subprocess.TimeoutExpired(cmd=["wsl.exe"], timeout=timeout)
        return self.returncode

    def kill(self):
        self.killed = True


class FakePopenFactory:
    def __init__(self, process: FakeProcess) -> None:
        self.process = process
        self.calls = []

    def __call__(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        return self.process


def test_build_command_uses_wsl_bash_lc_without_distro_by_default():
    runner = WslRunner()

    assert runner.build_command("echo hello") == ["wsl.exe", "bash", "-lc", "echo hello"]


def test_build_command_supports_optional_distro_without_hard_coding_ubuntu():
    runner = WslRunner(distro="Debian")

    assert runner.build_command("pwd") == ["wsl.exe", "-d", "Debian", "bash", "-lc", "pwd"]


def test_run_success_streams_and_captures_stdout_and_stderr():
    process = FakeProcess(stdout="one\nthree\n", stderr="two\n", returncode=0)
    popen = FakePopenFactory(process)
    streamed = []
    runner = WslRunner(popen_factory=popen)

    result = runner.run("printf demo", on_output=streamed.append)

    assert result.ok
    assert result.exit_code == 0
    assert result.stdout == "one\nthree\n"
    assert result.stderr == "two\n"
    assert {line.stream for line in streamed} == {"stdout", "stderr"}
    assert {line.text for line in streamed} == {"one", "two", "three"}
    assert popen.calls[0][0][0] == ["wsl.exe", "bash", "-lc", "printf demo"]
    assert popen.calls[0][1]["stdout"] == subprocess.PIPE
    assert popen.calls[0][1]["stderr"] == subprocess.PIPE
    assert popen.calls[0][1]["text"] is True


def test_run_failure_raises_with_exit_code_and_captured_stderr():
    process = FakeProcess(stdout="before fail\n", stderr="bad thing\n", returncode=7)
    runner = WslRunner(popen_factory=FakePopenFactory(process))

    with pytest.raises(WslCommandError) as exc_info:
        runner.run("exit 7")

    error = exc_info.value
    assert error.exit_code == 7
    assert error.stdout == "before fail\n"
    assert error.stderr == "bad thing\n"
    assert error.result.args == ("wsl.exe", "bash", "-lc", "exit 7")


def test_run_failure_can_return_result_when_check_false():
    process = FakeProcess(stderr="warning\n", returncode=3)
    runner = WslRunner(popen_factory=FakePopenFactory(process))

    result = runner.run("exit 3", check=False)

    assert not result.ok
    assert result.exit_code == 3
    assert result.stderr == "warning\n"


def test_run_timeout_kills_process_and_preserves_partial_output():
    process = FakeProcess(stdout="partial\n", stderr="still here\n", timeout=True)
    runner = WslRunner(popen_factory=FakePopenFactory(process))

    with pytest.raises(WslCommandTimeout) as exc_info:
        runner.run("sleep 99", timeout=0.25)

    error = exc_info.value
    assert process.killed
    assert error.command == "sleep 99"
    assert error.args == ("wsl.exe", "bash", "-lc", "sleep 99")
    assert error.timeout == 0.25
    assert error.stdout == "partial\n"
    assert error.stderr == "still here\n"
