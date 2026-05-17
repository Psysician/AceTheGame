import os
from typing import Dict, List, Optional

from .device import DeviceManager
from .exceptions import ACEOperationError, DeviceNotRootedError
from .file_system import FileSystem
from .file_transfer import FileTransfer
from .models import ACEServerInfo, ProcessInfo
from .network import NetworkManager
from .process import ProcessManager
from .shell import ADBCommandRunner

ANDROID_ARCH_ABI_MAP = {
    "arm64-v8a": "arm64-v8a",
    "aarch64": "arm64-v8a",
    "armeabi-v7a": "armeabi-v7a",
    "armv7l": "armeabi-v7a",
    "x86_64": "x86_64",
    "x86": "x86",
    "i686": "x86",
}


class ACEOperations:
    DEFAULT_INSTALL_PATH = "/data/local/tmp"
    DEFAULT_ENGINE_PORT = 56666
    DEFAULT_STATUS_PORT = 56667
    ACE_BINARY_NAME = "ACE"
    CLIENT_BINARY_NAME = "attach_client"

    def __init__(
        self,
        runner: ADBCommandRunner,
        file_transfer: FileTransfer,
        file_system: FileSystem,
        process: ProcessManager,
        network: NetworkManager,
        device: DeviceManager,
    ):
        self._runner = runner
        self._file_transfer = file_transfer
        self._fs = file_system
        self._process = process
        self._network = network
        self._device = device

    def push_ace_binary(
        self, local_binary_path: str, remote_path: Optional[str] = None
    ) -> str:
        if not os.path.isfile(local_binary_path):
            raise ACEOperationError("push_ace_binary", f"binary not found: {local_binary_path}")

        if remote_path is None:
            binary_name = os.path.basename(local_binary_path)
            remote_path = f"{self.DEFAULT_INSTALL_PATH}/{binary_name}"

        self._file_transfer.push(local_binary_path, remote_path)
        self.set_ace_permissions(remote_path)
        return remote_path

    def push_ace_for_arch(
        self, release_dir: str, arch: Optional[str] = None
    ) -> str:
        if arch is None:
            arch = self._detect_device_arch()

        binary_path = os.path.join(release_dir, "android", arch, "bin", self.ACE_BINARY_NAME)
        if not os.path.isfile(binary_path):
            raise ACEOperationError(
                "push_ace_for_arch",
                f"binary not found for arch '{arch}': {binary_path}"
            )

        return self.push_ace_binary(binary_path)

    def set_ace_permissions(self, remote_path: str) -> None:
        self._fs.chmod(remote_path, "+x")

    def start_ace_server(
        self,
        pid: int,
        port: int = DEFAULT_ENGINE_PORT,
        status_port: int = DEFAULT_STATUS_PORT,
        binary_path: Optional[str] = None,
    ) -> ACEServerInfo:
        if binary_path is None:
            binary_path = f"{self.DEFAULT_INSTALL_PATH}/{self.ACE_BINARY_NAME}"

        if not self._fs.exists(binary_path):
            raise ACEOperationError("start_ace_server", f"ACE binary not found at {binary_path}")

        if not self._process.is_process_running(pid):
            raise ACEOperationError("start_ace_server", f"target process {pid} is not running")

        cmd = (
            f"{binary_path} attach-pid {pid} "
            f"--port {port} "
            f"--status_publisher_port {status_port}"
        )
        self._runner.run_shell(f"nohup {cmd} > /dev/null 2>&1 &", as_root=True)

        ace_pid = self._find_ace_process_pid()

        return ACEServerInfo(
            pid=ace_pid or 0,
            engine_port=port,
            status_publisher_port=status_port,
            binary_path=binary_path,
        )

    def stop_ace_server(self, port: int = DEFAULT_ENGINE_PORT) -> None:
        ace_procs = self._process.get_processes_by_name(self.ACE_BINARY_NAME)
        for proc in ace_procs:
            self._process.kill_process(proc.pid, signal=15)

    def is_ace_running(self) -> bool:
        procs = self._process.get_processes_by_name(self.ACE_BINARY_NAME)
        return len(procs) > 0

    def get_ace_pid(self) -> Optional[int]:
        return self._find_ace_process_pid()

    def forward_ace_ports(
        self,
        engine_port: int = DEFAULT_ENGINE_PORT,
        status_port: int = DEFAULT_STATUS_PORT,
    ) -> None:
        self._network.forward_tcp(engine_port, engine_port)
        self._network.forward_tcp(status_port, status_port)

    def remove_ace_forwards(
        self,
        engine_port: int = DEFAULT_ENGINE_PORT,
        status_port: int = DEFAULT_STATUS_PORT,
    ) -> None:
        try:
            self._network.remove_forward_tcp(engine_port)
        except Exception:
            pass
        try:
            self._network.remove_forward_tcp(status_port)
        except Exception:
            pass

    def list_target_processes(self) -> List[ProcessInfo]:
        all_procs = self._process.list_processes()
        system_prefixes = [
            "/system/", "/vendor/", "zygote", "servicemanager",
            "surfaceflinger", "logd", "lmkd", "healthd",
            "vold", "netd", "installd", "adbd",
        ]
        targets = []
        for proc in all_procs:
            is_system = any(proc.name.startswith(prefix) for prefix in system_prefixes)
            if not is_system and proc.name and proc.pid > 1:
                targets.append(proc)
        return targets

    def check_root(self) -> bool:
        return self._device.is_rooted()

    def verify_device_ready(self) -> Dict[str, bool]:
        status = {
            "adb_connected": False,
            "rooted": False,
            "ace_binary_present": False,
            "client_binary_present": False,
            "ace_running": False,
        }

        status["adb_connected"] = self._runner.check_connection()
        if not status["adb_connected"]:
            return status

        status["rooted"] = self._device.is_rooted()

        ace_path = f"{self.DEFAULT_INSTALL_PATH}/{self.ACE_BINARY_NAME}"
        status["ace_binary_present"] = self._fs.exists(ace_path)

        client_path = f"{self.DEFAULT_INSTALL_PATH}/{self.CLIENT_BINARY_NAME}"
        status["client_binary_present"] = self._fs.exists(client_path)

        status["ace_running"] = self.is_ace_running()

        return status

    def deploy_and_start(
        self,
        local_binary_path: str,
        target_pid: int,
        arch: Optional[str] = None,
        engine_port: int = DEFAULT_ENGINE_PORT,
        status_port: int = DEFAULT_STATUS_PORT,
    ) -> ACEServerInfo:
        if not self._runner.check_connection():
            raise ACEOperationError("deploy_and_start", "no device connected")

        if os.path.isdir(local_binary_path):
            remote_path = self.push_ace_for_arch(local_binary_path, arch)
        else:
            remote_path = self.push_ace_binary(local_binary_path)

        self.forward_ace_ports(engine_port, status_port)

        return self.start_ace_server(
            pid=target_pid,
            port=engine_port,
            status_port=status_port,
            binary_path=remote_path,
        )

    def push_client_binary(
        self, local_path: str, remote_path: Optional[str] = None
    ) -> str:
        if not os.path.isfile(local_path):
            raise ACEOperationError("push_client_binary", f"binary not found: {local_path}")

        if remote_path is None:
            remote_path = f"{self.DEFAULT_INSTALL_PATH}/{self.CLIENT_BINARY_NAME}"

        self._file_transfer.push(local_path, remote_path)
        self._fs.chmod(remote_path, "+x")
        return remote_path

    def push_client_for_arch(
        self, release_dir: str, arch: Optional[str] = None
    ) -> str:
        if arch is None:
            arch = self._detect_device_arch()

        binary_path = os.path.join(
            release_dir, "android", arch, "bin", self.CLIENT_BINARY_NAME
        )
        if not os.path.isfile(binary_path):
            raise ACEOperationError(
                "push_client_for_arch",
                f"client binary not found for arch '{arch}': {binary_path}"
            )

        return self.push_client_binary(binary_path)

    def run_client_command(
        self, command: str, port: int = DEFAULT_ENGINE_PORT
    ) -> str:
        client_path = f"{self.DEFAULT_INSTALL_PATH}/{self.CLIENT_BINARY_NAME}"
        result = self._runner.run_shell(
            f"{client_path} {port} '{command}'", as_root=True
        )
        return result.output

    def get_ace_version(self) -> str:
        ace_path = f"{self.DEFAULT_INSTALL_PATH}/{self.ACE_BINARY_NAME}"
        result = self._runner.run_shell(f"{ace_path} --version", as_root=True)
        return result.output

    def set_aslr(self, enabled: bool) -> None:
        value = "2" if enabled else "0"
        self._runner.run_shell(
            f"echo {value} > /proc/sys/kernel/randomize_va_space",
            as_root=True,
        )

    def get_aslr_status(self) -> bool:
        result = self._runner.run_shell("cat /proc/sys/kernel/randomize_va_space")
        return result.output.strip() != "0"

    def deploy_full(
        self,
        release_dir: str,
        arch: Optional[str] = None,
    ) -> Dict[str, str]:
        if arch is None:
            arch = self._detect_device_arch()

        results = {}
        results["ace"] = self.push_ace_for_arch(release_dir, arch)
        results["client"] = self.push_client_for_arch(release_dir, arch)
        results["arch"] = arch

        return results

    def _detect_device_arch(self) -> str:
        device_abi = self._device.get_abi()

        mapped = ANDROID_ARCH_ABI_MAP.get(device_abi)
        if mapped:
            return mapped

        for key, value in ANDROID_ARCH_ABI_MAP.items():
            if key in device_abi:
                return value

        raise ACEOperationError(
            "detect_arch",
            f"unsupported device ABI: {device_abi}"
        )

    def _find_ace_process_pid(self) -> Optional[int]:
        procs = self._process.get_processes_by_name(self.ACE_BINARY_NAME)
        if procs:
            return procs[0].pid
        return None
