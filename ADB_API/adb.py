import os
from typing import List, Optional, Union

from .ace_operations import ACEOperations
from .activity import ActivityManager
from .device import DeviceManager
from .file_system import FileSystem
from .file_transfer import FileTransfer
from .input_sim import InputSimulator
from .logcat import LogcatManager
from .models import CommandResult
from .network import NetworkManager
from .package import PackageManager
from .process import ProcessManager
from .release_build import ReleasePipeline
from .shell import ADBCommandRunner
from .system_info import SystemInfo


class ADB:
    def __init__(
        self,
        device_serial: Optional[str] = None,
        adb_path: Optional[str] = None,
        default_timeout: int = 30,
    ):
        self._runner = ADBCommandRunner(
            adb_path=adb_path,
            device_serial=device_serial,
            default_timeout=default_timeout,
        )

        self.device = DeviceManager(self._runner)
        self.packages = PackageManager(self._runner)
        self.files = FileTransfer(self._runner)
        self.process = ProcessManager(self._runner)
        self.activity = ActivityManager(self._runner)
        self.logcat = LogcatManager(self._runner)
        self.network = NetworkManager(self._runner)
        self.system = SystemInfo(self._runner)
        self.fs = FileSystem(self._runner)
        self.input = InputSimulator(self._runner)
        self.ace = ACEOperations(
            runner=self._runner,
            file_transfer=self.files,
            file_system=self.fs,
            process=self.process,
            network=self.network,
            device=self.device,
        )
        self.release = ReleasePipeline(
            project_root=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )

    def run(
        self, args: List[str], timeout: Optional[int] = None
    ) -> CommandResult:
        return self._runner.run_adb(args, timeout=timeout)

    def shell(
        self,
        command: Union[str, List[str]],
        timeout: Optional[int] = None,
        as_root: bool = False,
    ) -> CommandResult:
        return self._runner.run_shell(command, timeout=timeout, as_root=as_root)

    def is_connected(self) -> bool:
        return self._runner.check_connection()

    def select_device(self, serial: str) -> None:
        self._runner.device_serial = serial

    def get_selected_device(self) -> Optional[str]:
        return self._runner.device_serial

    def version(self) -> str:
        result = self._runner.run_adb(["version"])
        return result.output

    def server_version(self) -> str:
        result = self._runner.run_adb(["version"])
        for line in result.lines:
            if "Version" in line:
                return line.strip()
        return result.output

    def start_server(self) -> None:
        self._runner.run_adb(["start-server"])

    def kill_server(self) -> None:
        self._runner.run_adb(["kill-server"])

    def restart_server(self) -> None:
        self.kill_server()
        self.start_server()

    def wait_for_device(self, timeout: int = 60) -> bool:
        return self.device.wait_for_device(timeout=timeout)

    def usb(self) -> None:
        self._runner.run_adb(["usb"])

    def tcpip(self, port: int = 5555) -> None:
        self._runner.run_adb(["tcpip", str(port)])

    def root(self) -> str:
        result = self._runner.run_adb(["root"])
        return result.output

    def unroot(self) -> str:
        result = self._runner.run_adb(["unroot"])
        return result.output

    def remount(self) -> str:
        result = self._runner.run_adb(["remount"])
        return result.output

    def bugreport(self, output_path: str) -> None:
        self._runner.run_adb(["bugreport", output_path], timeout=300)

    def jdwp(self) -> List[int]:
        result = self._runner.run_adb(["jdwp"], timeout=5)
        pids = []
        for line in result.lines:
            try:
                pids.append(int(line.strip()))
            except ValueError:
                pass
        return pids

    def get_state(self) -> str:
        return self.device.get_state()

    def push(self, local_path: str, remote_path: str) -> None:
        self.files.push(local_path, remote_path)

    def pull(self, remote_path: str, local_path: str) -> None:
        self.files.pull(remote_path, local_path)

    def install(self, apk_path: str, **kwargs) -> None:
        self.packages.install(apk_path, **kwargs)

    def uninstall(self, package_name: str, **kwargs) -> None:
        self.packages.uninstall(package_name, **kwargs)

    def __repr__(self) -> str:
        serial = self._runner.device_serial or "auto"
        return f"ADB(device={serial})"
