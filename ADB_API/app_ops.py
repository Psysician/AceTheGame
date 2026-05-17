from typing import Dict, List, Optional

from .shell import ADBCommandRunner


class AppOpsManager:
    def __init__(self, runner: ADBCommandRunner):
        self._runner = runner

    def set_op(self, package: str, op: str, mode: str) -> None:
        self._runner.run_shell(f"appops set {package} {op} {mode}")

    def get_op(self, package: str, op: str) -> str:
        result = self._runner.run_shell(f"appops get {package} {op}")
        return result.output

    def get_ops(self, package: str) -> str:
        result = self._runner.run_shell(f"appops get {package}")
        return result.stdout

    def reset(self, package: Optional[str] = None) -> None:
        cmd = "appops reset"
        if package:
            cmd += f" {package}"
        self._runner.run_shell(cmd)

    def allow(self, package: str, op: str) -> None:
        self.set_op(package, op, "allow")

    def deny(self, package: str, op: str) -> None:
        self.set_op(package, op, "deny")

    def ignore(self, package: str, op: str) -> None:
        self.set_op(package, op, "ignore")

    def default(self, package: str, op: str) -> None:
        self.set_op(package, op, "default")

    def query(self, op: str) -> str:
        result = self._runner.run_shell(f"appops query-op {op}")
        return result.stdout
