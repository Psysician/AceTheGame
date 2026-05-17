import re
from typing import Dict, List, Optional, Tuple

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

    def get_device_time(self) -> str:
        result = self._runner.run_shell("date")
        return result.output

    def set_device_time(self, time_str: str) -> None:
        self._runner.run_shell(f"date {time_str}")

    def delete_settings(self, namespace: str, key: str) -> None:
        self._runner.run_shell(f"settings delete {namespace} {key}")

    def list_settings(self, namespace: str) -> Dict[str, str]:
        result = self._runner.run_shell(f"settings list {namespace}")
        settings = {}
        for line in result.lines:
            if "=" in line:
                key, _, val = line.partition("=")
                settings[key.strip()] = val.strip()
        return settings

    def reset_settings(self, namespace: str) -> None:
        self._runner.run_shell(f"settings reset {namespace}")

    def wm_overscan(self, left: int, top: int, right: int, bottom: int) -> None:
        self._runner.run_shell(f"wm overscan {left},{top},{right},{bottom}")

    def wm_reset_overscan(self) -> None:
        self._runner.run_shell("wm overscan reset")

    def wm_scaling(self, mode: str = "auto") -> None:
        self._runner.run_shell(f"wm scaling {mode}")

    def wm_dismiss_keyguard(self) -> None:
        self._runner.run_shell("wm dismiss-keyguard")

    def wm_set_user_rotation(self, mode: str = "free", rotation: Optional[int] = None) -> None:
        cmd = f"wm set-user-rotation {mode}"
        if rotation is not None:
            cmd += f" {rotation}"
        self._runner.run_shell(cmd)

    def wm_fix_to_user_rotation(self, state: str = "default") -> None:
        self._runner.run_shell(f"wm set-fix-to-user-rotation {state}")

    def get_selinux_status(self) -> str:
        result = self._runner.run_shell("getenforce")
        return result.output

    def set_selinux_mode(self, mode: str) -> None:
        self._runner.run_shell(f"setenforce {mode}", as_root=True)

    def get_kernel_cmdline(self) -> str:
        result = self._runner.run_shell("cat /proc/cmdline")
        return result.output

    def service_call(self, service: str, code: int, *args: str) -> str:
        arg_str = " ".join(args)
        result = self._runner.run_shell(f"service call {service} {code} {arg_str}")
        return result.output

    def service_check(self, service: str) -> bool:
        result = self._runner.run_shell(f"service check {service}")
        return "found" in result.output.lower()

    def cmd(self, service: str, *args: str) -> str:
        arg_str = " ".join(args)
        result = self._runner.run_shell(f"cmd {service} {arg_str}")
        return result.output

    def cmd_overlay_enable(self, package: str) -> None:
        self._runner.run_shell(f"cmd overlay enable {package}")

    def cmd_overlay_disable(self, package: str) -> None:
        self._runner.run_shell(f"cmd overlay disable {package}")

    def cmd_overlay_list(self) -> str:
        result = self._runner.run_shell("cmd overlay list")
        return result.output

    def list_displays(self) -> str:
        result = self._runner.run_shell("dumpsys display")
        return result.output

    def atrace_list_categories(self) -> List[str]:
        result = self._runner.run_shell("atrace --list_categories")
        return result.lines

    def atrace_start(self, categories: List[str], buffer_size: int = 2048) -> None:
        cats = " ".join(categories)
        self._runner.run_shell(f"atrace -b {buffer_size} {cats}")

    def atrace_stop(self) -> str:
        result = self._runner.run_shell("atrace --async_stop")
        return result.output
