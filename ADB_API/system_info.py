import re
from typing import Dict, Optional, Tuple

from .models import BatteryInfo, MemoryInfo
from .shell import ADBCommandRunner


class SystemInfo:
    def __init__(self, runner: ADBCommandRunner):
        self._runner = runner

    def dumpsys(self, service: str, args: Optional[str] = None) -> str:
        cmd = f"dumpsys {service}"
        if args:
            cmd += f" {args}"
        result = self._runner.run_shell(cmd, timeout=30)
        return result.stdout

    def list_services(self) -> list:
        result = self._runner.run_shell("service list")
        services = []
        for line in result.lines:
            match = re.match(r'^\d+\s+(\S+):', line)
            if match:
                services.append(match.group(1))
        return services

    def get_battery_info(self) -> BatteryInfo:
        output = self.dumpsys("battery")
        info = BatteryInfo()

        for line in output.split("\n"):
            line = line.strip()
            if line.startswith("level:"):
                try:
                    info.level = int(line.split(":")[1].strip())
                except ValueError:
                    pass
            elif line.startswith("status:"):
                status_map = {
                    "1": "unknown", "2": "charging", "3": "discharging",
                    "4": "not_charging", "5": "full",
                }
                val = line.split(":")[1].strip()
                info.status = status_map.get(val, val)
            elif line.startswith("health:"):
                health_map = {
                    "1": "unknown", "2": "good", "3": "overheat",
                    "4": "dead", "5": "over_voltage", "6": "unspecified_failure",
                    "7": "cold",
                }
                val = line.split(":")[1].strip()
                info.health = health_map.get(val, val)
            elif line.startswith("temperature:"):
                try:
                    info.temperature = float(line.split(":")[1].strip()) / 10.0
                except ValueError:
                    pass
            elif line.startswith("voltage:"):
                try:
                    info.voltage = float(line.split(":")[1].strip()) / 1000.0
                except ValueError:
                    pass
            elif line.startswith("plugged:"):
                plugged_map = {"0": "unplugged", "1": "ac", "2": "usb", "4": "wireless"}
                val = line.split(":")[1].strip()
                info.plugged = plugged_map.get(val, val)

        return info

    def get_memory_info(self) -> MemoryInfo:
        result = self._runner.run_shell("cat /proc/meminfo")
        info = MemoryInfo()

        for line in result.lines:
            if line.startswith("MemTotal:"):
                info.total_ram = self._parse_meminfo_value(line)
            elif line.startswith("MemFree:"):
                info.free_ram = self._parse_meminfo_value(line)
            elif line.startswith("MemAvailable:"):
                info.available_ram = self._parse_meminfo_value(line)

        info.used_ram = info.total_ram - info.available_ram
        return info

    def get_cpu_info(self) -> str:
        result = self._runner.run_shell("cat /proc/cpuinfo")
        return result.stdout

    def get_cpu_count(self) -> int:
        result = self._runner.run_shell("nproc")
        try:
            return int(result.output)
        except ValueError:
            return 0

    def get_cpu_usage(self) -> str:
        result = self._runner.run_shell("top -n 1 -b")
        return result.stdout

    def get_display_size(self) -> Tuple[int, int]:
        result = self._runner.run_shell("wm size")
        match = re.search(r"(\d+)x(\d+)", result.output)
        if match:
            return int(match.group(1)), int(match.group(2))
        return 0, 0

    def get_display_density(self) -> int:
        result = self._runner.run_shell("wm density")
        match = re.search(r"(\d+)", result.output)
        if match:
            return int(match.group(1))
        return 0

    def set_display_size(self, width: int, height: int) -> None:
        self._runner.run_shell(f"wm size {width}x{height}")

    def reset_display_size(self) -> None:
        self._runner.run_shell("wm size reset")

    def set_display_density(self, density: int) -> None:
        self._runner.run_shell(f"wm density {density}")

    def reset_display_density(self) -> None:
        self._runner.run_shell("wm density reset")

    def screenshot(self, output_path: str, display_id: Optional[int] = None) -> None:
        remote_path = "/data/local/tmp/_screenshot.png"
        cmd = f"screencap -p {remote_path}"
        if display_id is not None:
            cmd += f" -d {display_id}"
        self._runner.run_shell(cmd)
        self._runner.run_adb(["pull", remote_path, output_path])
        self._runner.run_shell(f"rm {remote_path}")

    def screenrecord(
        self,
        output_path: str,
        duration: int = 180,
        size: Optional[str] = None,
        bit_rate: Optional[int] = None,
    ) -> None:
        remote_path = "/data/local/tmp/_screenrecord.mp4"
        cmd = f"screenrecord --time-limit {duration}"
        if size:
            cmd += f" --size {size}"
        if bit_rate:
            cmd += f" --bit-rate {bit_rate}"
        cmd += f" {remote_path}"

        self._runner.run_shell(cmd, timeout=duration + 10)
        self._runner.run_adb(["pull", remote_path, output_path])
        self._runner.run_shell(f"rm {remote_path}")

    def get_uptime(self) -> float:
        result = self._runner.run_shell("cat /proc/uptime")
        parts = result.output.split()
        if parts:
            try:
                return float(parts[0])
            except ValueError:
                pass
        return 0.0

    def get_disk_usage(self, path: str = "/") -> Dict[str, str]:
        result = self._runner.run_shell(f"df -h {path}")
        info = {}
        lines = result.lines
        if len(lines) >= 2:
            header = lines[0].split()
            values = lines[1].split()
            for h, v in zip(header, values):
                info[h.lower()] = v
        return info

    def get_kernel_version(self) -> str:
        result = self._runner.run_shell("uname -r")
        return result.output

    def get_hostname(self) -> str:
        result = self._runner.run_shell("hostname")
        return result.output

    def get_ip_addresses(self) -> Dict[str, str]:
        result = self._runner.run_shell("ip addr show")
        interfaces = {}
        current_iface = None
        for line in result.lines:
            iface_match = re.match(r'^\d+:\s+(\S+):', line)
            if iface_match:
                current_iface = iface_match.group(1)
            elif current_iface:
                ip_match = re.search(r'inet\s+(\d+\.\d+\.\d+\.\d+)', line)
                if ip_match:
                    interfaces[current_iface] = ip_match.group(1)
        return interfaces

    def get_wifi_info(self) -> str:
        return self.dumpsys("wifi")

    def get_connectivity_info(self) -> str:
        return self.dumpsys("connectivity")

    def get_settings(self, namespace: str, key: str) -> str:
        result = self._runner.run_shell(f"settings get {namespace} {key}")
        return result.output

    def put_settings(self, namespace: str, key: str, value: str) -> None:
        self._runner.run_shell(f"settings put {namespace} {key} {value}")

    def get_build_props(self) -> Dict[str, str]:
        result = self._runner.run_shell("getprop")
        props = {}
        for line in result.lines:
            match = re.match(r'\[(.+?)\]:\s*\[(.+?)\]', line)
            if match:
                props[match.group(1)] = match.group(2)
        return props

    def _parse_meminfo_value(self, line: str) -> int:
        match = re.search(r'(\d+)', line)
        if match:
            return int(match.group(1)) * 1024
        return 0
