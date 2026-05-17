import os
from typing import List, Optional

from .exceptions import PackageInstallError
from .models import PackageInfo
from .shell import ADBCommandRunner


class PackageManager:
    def __init__(self, runner: ADBCommandRunner):
        self._runner = runner

    def list_packages(
        self, filter_str: Optional[str] = None, show_only: str = "all"
    ) -> List[str]:
        cmd = "pm list packages"

        if show_only == "system":
            cmd += " -s"
        elif show_only == "third-party":
            cmd += " -3"
        elif show_only == "enabled":
            cmd += " -e"
        elif show_only == "disabled":
            cmd += " -d"

        if filter_str:
            cmd += f" {filter_str}"

        result = self._runner.run_shell(cmd)
        packages = []
        for line in result.lines:
            pkg = line.replace("package:", "").strip()
            if pkg:
                packages.append(pkg)
        return sorted(packages)

    def get_package_info(self, package_name: str) -> PackageInfo:
        info = PackageInfo(package_name=package_name)
        info.apk_paths = self.get_apk_paths(package_name)

        result = self._runner.run_shell(f"dumpsys package {package_name}")
        for line in result.lines:
            line = line.strip()
            if line.startswith("versionCode="):
                parts = line.split()
                for part in parts:
                    if part.startswith("versionCode="):
                        info.version_code = part.split("=", 1)[1]
                    elif part.startswith("versionName="):
                        info.version_name = part.split("=", 1)[1]
            elif line.startswith("installerPackageName="):
                info.installer = line.split("=", 1)[1]

        return info

    def get_apk_paths(self, package_name: str) -> List[str]:
        result = self._runner.run_shell(f"pm path {package_name}")
        paths = []
        for line in result.lines:
            path = line.replace("package:", "").strip()
            if path:
                paths.append(path)
        return paths

    def package_exists(self, package_name: str) -> bool:
        packages = self.list_packages(filter_str=package_name)
        return package_name in packages

    def install(
        self,
        apk_path: str,
        reinstall: bool = False,
        allow_downgrade: bool = False,
        grant_permissions: bool = False,
        allow_test: bool = False,
    ) -> None:
        if not os.path.isfile(apk_path):
            raise PackageInstallError(apk_path, "APK file not found")

        args = ["install"]
        if reinstall:
            args.append("-r")
        if allow_downgrade:
            args.append("-d")
        if grant_permissions:
            args.append("-g")
        if allow_test:
            args.append("-t")
        args.append(apk_path)

        result = self._runner.run_adb(args, timeout=120)
        if "failure" in result.output.lower() or "error" in result.stderr.lower():
            detail = result.output if result.output else result.stderr
            raise PackageInstallError(apk_path, detail.strip())

    def install_multiple(self, apk_dir: str) -> None:
        if not os.path.isdir(apk_dir):
            raise PackageInstallError(apk_dir, "APK directory not found")

        apk_files = [
            os.path.join(apk_dir, f)
            for f in os.listdir(apk_dir)
            if f.endswith(".apk")
        ]

        if not apk_files:
            raise PackageInstallError(apk_dir, "no .apk files found in directory")

        args = ["install-multiple"] + apk_files
        result = self._runner.run_adb(args, timeout=120)
        if "failure" in result.output.lower() or "error" in result.stderr.lower():
            detail = result.output if result.output else result.stderr
            raise PackageInstallError(apk_dir, detail.strip())

    def uninstall(self, package_name: str, keep_data: bool = False) -> None:
        args = ["uninstall"]
        if keep_data:
            args.append("-k")
        args.append(package_name)
        self._runner.run_adb(args)

    def clear_data(self, package_name: str) -> None:
        self._runner.run_shell(f"pm clear {package_name}")

    def enable(self, package_name: str) -> None:
        self._runner.run_shell(f"pm enable {package_name}")

    def disable(self, package_name: str) -> None:
        self._runner.run_shell(f"pm disable-user {package_name}")

    def force_stop(self, package_name: str) -> None:
        self._runner.run_shell(f"am force-stop {package_name}")

    def grant_permission(self, package_name: str, permission: str) -> None:
        self._runner.run_shell(f"pm grant {package_name} {permission}")

    def revoke_permission(self, package_name: str, permission: str) -> None:
        self._runner.run_shell(f"pm revoke {package_name} {permission}")

    def list_permissions(self, package_name: str) -> List[str]:
        result = self._runner.run_shell(f"dumpsys package {package_name}")
        permissions = []
        in_permissions = False
        for line in result.lines:
            stripped = line.strip()
            if "granted=true" in stripped or "android.permission." in stripped:
                for part in stripped.split():
                    if part.startswith("android.permission."):
                        perm = part.rstrip(":,")
                        if perm not in permissions:
                            permissions.append(perm)
        return permissions

    def list_requested_permissions(self, package_name: str) -> List[str]:
        result = self._runner.run_shell(f"dumpsys package {package_name}")
        permissions = []
        in_section = False
        for line in result.lines:
            stripped = line.strip()
            if "requested permissions:" in stripped.lower():
                in_section = True
                continue
            elif in_section:
                if stripped.startswith("android.permission.") or stripped.startswith("com."):
                    permissions.append(stripped)
                elif stripped and not stripped.startswith(" "):
                    in_section = False
        return permissions

    def download_apk(self, package_name: str, output_dir: str) -> List[str]:
        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)

        apk_paths = self.get_apk_paths(package_name)
        downloaded = []
        for remote_path in apk_paths:
            filename = os.path.basename(remote_path)
            local_path = os.path.join(output_dir, filename)
            self._runner.run_adb(["pull", remote_path, local_path], timeout=120)
            downloaded.append(local_path)
        return downloaded

    def get_install_location(self) -> str:
        result = self._runner.run_shell("pm get-install-location")
        return result.output

    def set_install_location(self, location: int) -> None:
        self._runner.run_shell(f"pm set-install-location {location}")

    def list_features(self) -> List[str]:
        result = self._runner.run_shell("pm list features")
        features = []
        for line in result.lines:
            feat = line.replace("feature:", "").strip()
            if feat:
                features.append(feat)
        return features

    def list_libraries(self) -> List[str]:
        result = self._runner.run_shell("pm list libraries")
        libs = []
        for line in result.lines:
            lib = line.replace("library:", "").strip()
            if lib:
                libs.append(lib)
        return libs
