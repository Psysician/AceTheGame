from typing import Dict, List, Optional

from .shell import ADBCommandRunner


class ActivityManager:
    def __init__(self, runner: ADBCommandRunner):
        self._runner = runner

    def start_activity(
        self,
        component: str,
        action: Optional[str] = None,
        data: Optional[str] = None,
        mime_type: Optional[str] = None,
        category: Optional[str] = None,
        extras: Optional[Dict[str, str]] = None,
        flags: Optional[List[str]] = None,
        wait: bool = False,
    ) -> str:
        cmd = "am start"
        if wait:
            cmd += " -W"
        if action:
            cmd += f" -a {action}"
        if data:
            cmd += f" -d {data}"
        if mime_type:
            cmd += f" -t {mime_type}"
        if category:
            cmd += f" -c {category}"
        if extras:
            for key, value in extras.items():
                cmd += f" --es {key} {value}"
        if flags:
            for flag in flags:
                cmd += f" {flag}"
        cmd += f" -n {component}"

        result = self._runner.run_shell(cmd)
        return result.output

    def start_service(
        self,
        component: str,
        action: Optional[str] = None,
        extras: Optional[Dict[str, str]] = None,
    ) -> str:
        cmd = "am startservice"
        if action:
            cmd += f" -a {action}"
        if extras:
            for key, value in extras.items():
                cmd += f" --es {key} {value}"
        cmd += f" -n {component}"

        result = self._runner.run_shell(cmd)
        return result.output

    def stop_service(self, component: str) -> str:
        result = self._runner.run_shell(f"am stopservice -n {component}")
        return result.output

    def send_broadcast(
        self,
        action: str,
        component: Optional[str] = None,
        extras: Optional[Dict[str, str]] = None,
        extra_ints: Optional[Dict[str, int]] = None,
        extra_bools: Optional[Dict[str, bool]] = None,
    ) -> str:
        cmd = f"am broadcast -a {action}"
        if component:
            cmd += f" -n {component}"
        if extras:
            for key, value in extras.items():
                cmd += f" --es {key} '{value}'"
        if extra_ints:
            for key, value in extra_ints.items():
                cmd += f" --ei {key} {value}"
        if extra_bools:
            for key, value in extra_bools.items():
                cmd += f" --ez {key} {str(value).lower()}"

        result = self._runner.run_shell(cmd)
        return result.output

    def force_stop(self, package_name: str) -> None:
        self._runner.run_shell(f"am force-stop {package_name}")

    def kill(self, package_name: str) -> None:
        self._runner.run_shell(f"am kill {package_name}")

    def kill_all(self) -> None:
        self._runner.run_shell("am kill-all")

    def send_intent(self, intent_args: List[str]) -> str:
        args_str = " ".join(intent_args)
        result = self._runner.run_shell(f"am start {args_str}")
        return result.output

    def get_current_activity(self) -> Optional[str]:
        result = self._runner.run_shell("dumpsys activity activities")
        for line in result.lines:
            if "mResumedActivity" in line or "mFocusedActivity" in line:
                parts = line.strip().split()
                for part in parts:
                    if "/" in part and "." in part:
                        return part.rstrip("}")
        return None

    def get_current_package(self) -> Optional[str]:
        activity = self.get_current_activity()
        if activity and "/" in activity:
            return activity.split("/")[0]
        return None

    def start_instrumentation(
        self,
        component: str,
        args: Optional[Dict[str, str]] = None,
        raw: bool = False,
        wait: bool = True,
    ) -> str:
        cmd = "am instrument"
        if raw:
            cmd += " -r"
        if wait:
            cmd += " -w"
        if args:
            for key, value in args.items():
                cmd += f" -e {key} {value}"
        cmd += f" {component}"

        result = self._runner.run_shell(cmd, timeout=300)
        return result.output

    def set_debug_app(self, package_name: str, wait: bool = False) -> None:
        cmd = f"am set-debug-app"
        if wait:
            cmd += " -w"
        cmd += f" {package_name}"
        self._runner.run_shell(cmd)

    def clear_debug_app(self) -> None:
        self._runner.run_shell("am clear-debug-app")

    def monitor(self) -> str:
        result = self._runner.run_shell("am monitor", timeout=5)
        return result.output

    def profile_start(self, process: str, output_file: str) -> None:
        self._runner.run_shell(f"am profile start {process} {output_file}")

    def profile_stop(self, process: str) -> None:
        self._runner.run_shell(f"am profile stop {process}")

    def dumpheap(self, process: str, output_file: str) -> None:
        self._runner.run_shell(f"am dumpheap {process} {output_file}")

    def send_trimming(self, level: str = "COMPLETE") -> None:
        self._runner.run_shell(f"am send-trim-memory {level}")

    def restart(self) -> None:
        self._runner.run_shell("am restart")

    def hang(self, allow_restart: bool = False) -> None:
        cmd = "am hang"
        if allow_restart:
            cmd += " --allow-restart"
        self._runner.run_shell(cmd)

    def idle_maintenance(self) -> None:
        self._runner.run_shell("am idle-maintenance")

    def screen_compat(self, package_name: str, enabled: bool) -> None:
        state = "on" if enabled else "off"
        self._runner.run_shell(f"am screen-compat {state} {package_name}")

    def switch_user(self, user_id: int) -> None:
        self._runner.run_shell(f"am switch-user {user_id}")

    def start_user(self, user_id: int) -> None:
        self._runner.run_shell(f"am start-user {user_id}")

    def stop_user(self, user_id: int, wait: bool = False, force: bool = False) -> None:
        cmd = "am stop-user"
        if wait:
            cmd += " -w"
        if force:
            cmd += " -f"
        cmd += f" {user_id}"
        self._runner.run_shell(cmd)

    def get_current_user(self) -> str:
        result = self._runner.run_shell("am get-current-user")
        return result.output

    def get_config(self) -> str:
        result = self._runner.run_shell("am get-config")
        return result.output

    def set_inactive(self, package_name: str, inactive: bool) -> None:
        val = "true" if inactive else "false"
        self._runner.run_shell(f"am set-inactive {package_name} {val}")

    def get_inactive(self, package_name: str) -> str:
        result = self._runner.run_shell(f"am get-inactive {package_name}")
        return result.output

    def make_uid_idle(self, package_name: str) -> None:
        self._runner.run_shell(f"am make-uid-idle {package_name}")

    def to_uri(self, intent_args: str) -> str:
        result = self._runner.run_shell(f"am to-uri {intent_args}")
        return result.output

    def to_intent_uri(self, intent_args: str) -> str:
        result = self._runner.run_shell(f"am to-intent-uri {intent_args}")
        return result.output

    def to_app_uri(self, intent_args: str) -> str:
        result = self._runner.run_shell(f"am to-app-uri {intent_args}")
        return result.output

    def stack_list(self) -> str:
        result = self._runner.run_shell("am stack list")
        return result.output

    def stack_info(self, stack_id: int) -> str:
        result = self._runner.run_shell(f"am stack info {stack_id}")
        return result.output

    def suppress_resize_config_changes(self, suppress: bool) -> None:
        val = "true" if suppress else "false"
        self._runner.run_shell(f"am suppress-resize-config-changes {val}")

    def start_activity_as_user(self, component: str, user_id: int, wait: bool = False) -> str:
        cmd = "am start"
        if wait:
            cmd += " -W"
        cmd += f" --user {user_id} -n {component}"
        result = self._runner.run_shell(cmd)
        return result.output
