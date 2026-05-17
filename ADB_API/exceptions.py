from typing import List, Optional


class ADBError(Exception):
    pass


class ADBNotFoundError(ADBError):
    def __init__(self, searched_paths: Optional[List[str]] = None):
        paths_info = ""
        if searched_paths:
            paths_info = f" (searched: {', '.join(searched_paths)})"
        super().__init__(f"ADB binary not found in PATH{paths_info}")
        self.searched_paths = searched_paths


class DeviceNotFoundError(ADBError):
    def __init__(self, serial: Optional[str] = None):
        if serial:
            msg = f"Device '{serial}' not found"
        else:
            msg = "No device connected"
        super().__init__(msg)
        self.serial = serial


class MultipleDevicesError(ADBError):
    def __init__(self, devices: Optional[List[str]] = None):
        count = len(devices) if devices else 0
        super().__init__(
            f"Multiple devices connected ({count}), specify a serial with device_serial parameter"
        )
        self.devices = devices or []


class CommandTimeoutError(ADBError):
    def __init__(self, command: str, timeout: int):
        super().__init__(f"Command timed out after {timeout}s: {command}")
        self.command = command
        self.timeout = timeout


class CommandFailedError(ADBError):
    def __init__(self, command: str, return_code: int, stdout: str, stderr: str):
        msg = f"Command failed (exit {return_code}): {command}"
        if stderr.strip():
            msg += f"\nstderr: {stderr.strip()}"
        super().__init__(msg)
        self.command = command
        self.return_code = return_code
        self.stdout = stdout
        self.stderr = stderr


class DeviceOfflineError(ADBError):
    def __init__(self, serial: str):
        super().__init__(f"Device '{serial}' is offline")
        self.serial = serial


class PermissionDeniedError(ADBError):
    def __init__(self, operation: str):
        super().__init__(f"Permission denied: {operation} (may require root)")
        self.operation = operation


class FileTransferError(ADBError):
    def __init__(self, operation: str, local_path: str, remote_path: str, detail: str = ""):
        msg = f"File {operation} failed: {local_path} <-> {remote_path}"
        if detail:
            msg += f" ({detail})"
        super().__init__(msg)
        self.operation = operation
        self.local_path = local_path
        self.remote_path = remote_path


class PackageInstallError(ADBError):
    def __init__(self, package: str, detail: str = ""):
        msg = f"Package install failed: {package}"
        if detail:
            msg += f" ({detail})"
        super().__init__(msg)
        self.package = package
        self.detail = detail


class ShellCommandError(ADBError):
    def __init__(self, command: str, output: str):
        super().__init__(f"Shell command failed: {command}\nOutput: {output}")
        self.command = command
        self.output = output


class DeviceNotRootedError(ADBError):
    def __init__(self):
        super().__init__("Device is not rooted; this operation requires root access")


class ACEOperationError(ADBError):
    def __init__(self, operation: str, detail: str = ""):
        msg = f"ACE operation failed: {operation}"
        if detail:
            msg += f" ({detail})"
        super().__init__(msg)
        self.operation = operation
        self.detail = detail
