import os
import shutil
import subprocess
from typing import Iterator, List, Optional, Union

from .exceptions import (
    ADBNotFoundError,
    CommandFailedError,
    CommandTimeoutError,
    DeviceNotFoundError,
    DeviceOfflineError,
    MultipleDevicesError,
)
from .models import CommandResult


class ADBCommandRunner:
    def __init__(
        self,
        adb_path: Optional[str] = None,
        device_serial: Optional[str] = None,
        default_timeout: int = 30,
    ):
        self._adb_path = adb_path or self._find_adb()
        self._device_serial = device_serial
        self._default_timeout = default_timeout

    @staticmethod
    def _find_adb() -> str:
        adb = shutil.which("adb")
        if adb:
            return adb

        common_paths = []
        android_home = os.environ.get("ANDROID_HOME") or os.environ.get("ANDROID_SDK_ROOT")
        if android_home:
            common_paths.append(os.path.join(android_home, "platform-tools", "adb"))

        home = os.path.expanduser("~")
        common_paths.extend([
            os.path.join(home, "Android", "Sdk", "platform-tools", "adb"),
            os.path.join(home, "Library", "Android", "sdk", "platform-tools", "adb"),
            os.path.join(home, "AppData", "Local", "Android", "Sdk", "platform-tools", "adb.exe"),
        ])

        for path in common_paths:
            if os.path.isfile(path) and os.access(path, os.X_OK):
                return path

        raise ADBNotFoundError(searched_paths=common_paths)

    @property
    def device_serial(self) -> Optional[str]:
        return self._device_serial

    @device_serial.setter
    def device_serial(self, serial: Optional[str]):
        self._device_serial = serial

    def _build_command(self, args: List[str]) -> List[str]:
        cmd = [self._adb_path]
        if self._device_serial:
            cmd.extend(["-s", self._device_serial])
        cmd.extend(args)
        return cmd

    def run_adb(
        self, args: List[str], timeout: Optional[int] = None, check: bool = False
    ) -> CommandResult:
        cmd = self._build_command(args)
        effective_timeout = timeout if timeout is not None else self._default_timeout
        cmd_str = " ".join(cmd)

        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=effective_timeout,
            )
        except subprocess.TimeoutExpired:
            raise CommandTimeoutError(cmd_str, effective_timeout)
        except FileNotFoundError:
            raise ADBNotFoundError()

        result = CommandResult(
            stdout=proc.stdout,
            stderr=proc.stderr,
            return_code=proc.returncode,
        )

        self._check_adb_errors(result, cmd_str)

        if check and not result.success:
            raise CommandFailedError(cmd_str, proc.returncode, proc.stdout, proc.stderr)

        return result

    def run_shell(
        self,
        command: Union[str, List[str]],
        timeout: Optional[int] = None,
        as_root: bool = False,
    ) -> CommandResult:
        if isinstance(command, list):
            cmd_str = " ".join(command)
        else:
            cmd_str = command

        if as_root:
            shell_args = ["shell", "su", "-c", cmd_str]
        else:
            shell_args = ["shell", cmd_str]

        return self.run_adb(shell_args, timeout=timeout)

    def run_shell_stream(
        self,
        command: Union[str, List[str]],
        as_root: bool = False,
    ) -> Iterator[str]:
        if isinstance(command, list):
            cmd_str = " ".join(command)
        else:
            cmd_str = command

        if as_root:
            args = ["shell", "su", "-c", cmd_str]
        else:
            args = ["shell", cmd_str]

        full_cmd = self._build_command(args)

        proc = subprocess.Popen(
            full_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        try:
            for line in proc.stdout:
                yield line.rstrip("\n\r")
        finally:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()

    def check_connection(self) -> bool:
        try:
            result = self.run_adb(["shell", "echo", "test"], timeout=10)
            return result.success and "test" in result.stdout
        except (ADBNotFoundError, CommandTimeoutError):
            return False

    def _check_adb_errors(self, result: CommandResult, cmd_str: str):
        stderr = result.stderr.strip()
        if not stderr:
            return

        if "device not found" in stderr or "no devices/emulators found" in stderr:
            raise DeviceNotFoundError(self._device_serial)

        if "more than one device" in stderr or "multiple devices" in stderr.lower():
            raise MultipleDevicesError()

        if "device offline" in stderr:
            raise DeviceOfflineError(self._device_serial or "unknown")
