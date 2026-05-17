import re
from typing import List, Optional

from .models import ProcessInfo
from .shell import ADBCommandRunner


class ProcessManager:
    def __init__(self, runner: ADBCommandRunner):
        self._runner = runner

    def list_processes(self) -> List[ProcessInfo]:
        result = self._runner.run_shell("ps -A -o PID,PPID,USER,NAME")
        processes = []

        for line in result.lines:
            if line.strip().startswith("PID") or line.strip().startswith("USER"):
                continue
            info = self._parse_ps_line(line)
            if info:
                processes.append(info)

        if not processes:
            result = self._runner.run_shell("ps")
            for line in result.lines:
                if line.strip().startswith("USER") or line.strip().startswith("PID"):
                    continue
                info = self._parse_ps_fallback(line)
                if info:
                    processes.append(info)

        return processes

    def get_process_by_pid(self, pid: int) -> Optional[ProcessInfo]:
        result = self._runner.run_shell(f"ps -p {pid} -o PID,PPID,USER,NAME")
        for line in result.lines:
            if line.strip().startswith("PID") or line.strip().startswith("USER"):
                continue
            info = self._parse_ps_line(line)
            if info:
                return info

        result = self._runner.run_shell(f"cat /proc/{pid}/comm")
        if result.success and result.output:
            return ProcessInfo(pid=pid, name=result.output.strip())

        return None

    def get_processes_by_name(self, name: str) -> List[ProcessInfo]:
        all_procs = self.list_processes()
        return [p for p in all_procs if name.lower() in p.name.lower()]

    def kill_process(self, pid: int, signal: int = 9) -> None:
        self._runner.run_shell(f"kill -{signal} {pid}")

    def kill_by_name(self, name: str) -> None:
        self._runner.run_shell(f"pkill {name}")

    def is_process_running(self, pid: int) -> bool:
        result = self._runner.run_shell(f"kill -0 {pid} 2>/dev/null && echo RUNNING || echo DEAD")
        return "RUNNING" in result.output

    def get_process_cmdline(self, pid: int) -> str:
        result = self._runner.run_shell(f"cat /proc/{pid}/cmdline")
        return result.output.replace("\x00", " ").strip()

    def get_process_status(self, pid: int) -> dict:
        result = self._runner.run_shell(f"cat /proc/{pid}/status")
        status = {}
        for line in result.lines:
            if ":" in line:
                key, _, val = line.partition(":")
                status[key.strip()] = val.strip()
        return status

    def get_process_maps(self, pid: int) -> List[str]:
        result = self._runner.run_shell(f"cat /proc/{pid}/maps")
        return result.lines

    def get_uid_for_package(self, package_name: str) -> Optional[int]:
        result = self._runner.run_shell(f"dumpsys package {package_name}")
        for line in result.lines:
            if "userId=" in line:
                match = re.search(r'userId=(\d+)', line)
                if match:
                    return int(match.group(1))
        return None

    def get_top_activity(self) -> Optional[str]:
        result = self._runner.run_shell("dumpsys activity top")
        for line in result.lines:
            if "ACTIVITY" in line:
                parts = line.strip().split()
                for part in parts:
                    if "/" in part and "." in part:
                        return part
        return None

    def _parse_ps_line(self, line: str) -> Optional[ProcessInfo]:
        parts = line.split()
        if len(parts) < 4:
            return None
        try:
            pid = int(parts[0])
            ppid = int(parts[1])
            user = parts[2]
            name = " ".join(parts[3:])
            return ProcessInfo(pid=pid, ppid=ppid, user=user, name=name)
        except (ValueError, IndexError):
            return None

    def _parse_ps_fallback(self, line: str) -> Optional[ProcessInfo]:
        parts = line.split()
        if len(parts) < 9:
            return None
        try:
            user = parts[0]
            pid = int(parts[1])
            ppid = int(parts[2])
            name = parts[-1]
            return ProcessInfo(pid=pid, ppid=ppid, user=user, name=name)
        except (ValueError, IndexError):
            return None
