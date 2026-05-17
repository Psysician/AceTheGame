from typing import List, Optional

from .shell import ADBCommandRunner


class DevicePolicyManager:
    def __init__(self, runner: ADBCommandRunner):
        self._runner = runner

    def set_device_owner(self, component: str) -> str:
        result = self._runner.run_shell(f"dpm set-device-owner {component}")
        return result.output

    def set_profile_owner(self, component: str, user_id: Optional[int] = None) -> str:
        cmd = f"dpm set-profile-owner"
        if user_id is not None:
            cmd += f" --user {user_id}"
        cmd += f" {component}"
        result = self._runner.run_shell(cmd)
        return result.output

    def remove_active_admin(self, component: str) -> str:
        result = self._runner.run_shell(f"dpm remove-active-admin {component}")
        return result.output

    def list_owners(self) -> str:
        result = self._runner.run_shell("dumpsys device_policy")
        return result.stdout

    def set_user_restriction(self, restriction: str, enabled: bool) -> None:
        val = "1" if enabled else "0"
        self._runner.run_shell(f"dpm set-user-restriction {restriction} {val}")

    def get_user_restrictions(self) -> str:
        result = self._runner.run_shell("dumpsys user")
        return result.stdout
