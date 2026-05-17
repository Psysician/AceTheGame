from typing import List, Optional

from .shell import ADBCommandRunner


class BackupManager:
    def __init__(self, runner: ADBCommandRunner):
        self._runner = runner

    def backup_now(self, package: str) -> str:
        result = self._runner.run_shell(f"bmgr backupnow {package}")
        return result.output

    def restore(self, token: str) -> str:
        result = self._runner.run_shell(f"bmgr restore {token}")
        return result.output

    def list_transports(self) -> List[str]:
        result = self._runner.run_shell("bmgr list transports")
        return result.lines

    def list_sets(self) -> List[str]:
        result = self._runner.run_shell("bmgr list sets")
        return result.lines

    def transport(self, transport_name: str) -> str:
        result = self._runner.run_shell(f"bmgr transport {transport_name}")
        return result.output

    def enable(self, enabled: bool) -> None:
        val = "true" if enabled else "false"
        self._runner.run_shell(f"bmgr enabled {val}")

    def is_enabled(self) -> bool:
        result = self._runner.run_shell("bmgr enabled")
        return "enabled" in result.output.lower()

    def run_backup(self) -> str:
        result = self._runner.run_shell("bmgr run")
        return result.output

    def wipe(self, transport: str, package: str) -> str:
        result = self._runner.run_shell(f"bmgr wipe {transport} {package}")
        return result.output

    def full_backup(self, package: str) -> str:
        result = self._runner.run_shell(f"bmgr fullbackup {package}")
        return result.output
