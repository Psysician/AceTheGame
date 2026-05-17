import re
import time
from typing import List, Optional, Tuple

from .exceptions import DeviceNotFoundError
from .models import DeviceInfo, DeviceProperties
from .shell import ADBCommandRunner


class DeviceManager:
    def __init__(self, runner: ADBCommandRunner):
        self._runner = runner

    def list_devices(self) -> List[DeviceInfo]:
        result = self._runner.run_adb(["devices", "-l"])
        devices = []
        for line in result.lines:
            if line.startswith("List of") or not line.strip():
                continue
            parts = line.split()
            if len(parts) < 2:
                continue

            serial = parts[0]
            state = parts[1]

            model = None
            product = None
            transport_id = None
            for part in parts[2:]:
                if part.startswith("model:"):
                    model = part.split(":", 1)[1]
                elif part.startswith("product:"):
                    product = part.split(":", 1)[1]
                elif part.startswith("transport_id:"):
                    transport_id = part.split(":", 1)[1]

            devices.append(DeviceInfo(
                serial=serial,
                state=state,
                model=model,
                product=product,
                transport_id=transport_id,
            ))
        return devices

    def get_device_properties(self) -> DeviceProperties:
        return DeviceProperties(
            model=self.get_model(),
            manufacturer=self.get_property("ro.product.manufacturer"),
            android_version=self.get_android_version(),
            sdk_level=self.get_sdk_level(),
            abi=self.get_abi(),
            serial=self.get_serial(),
            build_fingerprint=self.get_property("ro.build.fingerprint"),
        )

    def get_property(self, prop_name: str) -> str:
        result = self._runner.run_shell(f"getprop {prop_name}")
        return result.output

    def set_property(self, prop_name: str, value: str) -> None:
        self._runner.run_shell(f"setprop {prop_name} {value}")

    def connect(self, host: str, port: int = 5555) -> bool:
        result = self._runner.run_adb(["connect", f"{host}:{port}"])
        return "connected" in result.output.lower()

    def disconnect(self, host: Optional[str] = None) -> None:
        if host:
            self._runner.run_adb(["disconnect", host])
        else:
            self._runner.run_adb(["disconnect"])

    def reboot(self, mode: Optional[str] = None) -> None:
        args = ["reboot"]
        if mode:
            args.append(mode)
        self._runner.run_adb(args)

    def wait_for_device(self, timeout: int = 60) -> bool:
        try:
            self._runner.run_adb(["wait-for-device"], timeout=timeout)
            return True
        except Exception:
            return False

    def is_rooted(self) -> bool:
        try:
            result = self._runner.run_shell("su -c whoami")
            if "root" in result.output.lower():
                return True
        except Exception:
            pass

        try:
            result = self._runner.run_shell("whoami")
            if "root" in result.output.lower():
                return True
        except Exception:
            pass

        try:
            result = self._runner.run_shell("id")
            if "uid=0" in result.output:
                return True
        except Exception:
            pass

        return False

    def get_serial(self) -> str:
        result = self._runner.run_adb(["get-serialno"])
        return result.output

    def get_model(self) -> str:
        return self.get_property("ro.product.model")

    def get_android_version(self) -> str:
        return self.get_property("ro.build.version.release")

    def get_sdk_level(self) -> int:
        val = self.get_property("ro.build.version.sdk")
        try:
            return int(val)
        except (ValueError, TypeError):
            return 0

    def get_abi(self) -> str:
        return self.get_property("ro.product.cpu.abi")

    def get_state(self) -> str:
        result = self._runner.run_adb(["get-state"])
        return result.output

    def get_manufacturer(self) -> str:
        return self.get_property("ro.product.manufacturer")

    def get_build_type(self) -> str:
        return self.get_property("ro.build.type")

    def get_hardware(self) -> str:
        return self.get_property("ro.hardware")

    def get_display_resolution(self) -> Tuple[int, int]:
        result = self._runner.run_shell("wm size")
        match = re.search(r"(\d+)x(\d+)", result.output)
        if match:
            return int(match.group(1)), int(match.group(2))
        return 0, 0

    def get_supported_abis(self) -> List[str]:
        val = self.get_property("ro.product.cpu.abilist")
        if val:
            return [abi.strip() for abi in val.split(",") if abi.strip()]
        return [self.get_abi()] if self.get_abi() else []
