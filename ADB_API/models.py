from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class CommandResult:
    stdout: str
    stderr: str
    return_code: int
    lines: List[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.lines and self.stdout:
            self.lines = [
                line for line in self.stdout.strip().split("\n") if line.strip()
            ]

    @property
    def success(self) -> bool:
        return self.return_code == 0

    @property
    def output(self) -> str:
        return self.stdout.strip()


@dataclass
class DeviceInfo:
    serial: str
    state: str
    model: Optional[str] = None
    product: Optional[str] = None
    transport_id: Optional[str] = None


@dataclass
class PackageInfo:
    package_name: str
    apk_paths: List[str] = field(default_factory=list)
    version_code: Optional[str] = None
    version_name: Optional[str] = None
    installer: Optional[str] = None


@dataclass
class ProcessInfo:
    pid: int
    ppid: int = 0
    name: str = ""
    user: str = ""
    state: Optional[str] = None


@dataclass
class ForwardRule:
    serial: str
    local: str
    remote: str


@dataclass
class DeviceProperties:
    model: str = ""
    manufacturer: str = ""
    android_version: str = ""
    sdk_level: int = 0
    abi: str = ""
    serial: str = ""
    build_fingerprint: str = ""


@dataclass
class FileInfo:
    path: str
    permissions: str = ""
    owner: str = ""
    group: str = ""
    size: int = 0
    date: str = ""
    is_directory: bool = False
    is_symlink: bool = False


@dataclass
class BatteryInfo:
    level: int = 0
    status: str = ""
    health: str = ""
    temperature: float = 0.0
    voltage: float = 0.0
    plugged: str = ""


@dataclass
class MemoryInfo:
    total_ram: int = 0
    free_ram: int = 0
    used_ram: int = 0
    available_ram: int = 0


@dataclass
class LogcatEntry:
    timestamp: str = ""
    pid: int = 0
    tid: int = 0
    priority: str = ""
    tag: str = ""
    message: str = ""


@dataclass
class ACEServerInfo:
    pid: int = 0
    engine_port: int = 0
    status_publisher_port: int = 0
    binary_path: str = ""
