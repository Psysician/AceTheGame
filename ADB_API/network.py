from typing import List, Optional

from .models import ForwardRule
from .shell import ADBCommandRunner


class NetworkManager:
    def __init__(self, runner: ADBCommandRunner):
        self._runner = runner

    def forward(self, local: str, remote: str, no_rebind: bool = False) -> None:
        args = ["forward"]
        if no_rebind:
            args.append("--no-rebind")
        args.extend([local, remote])
        self._runner.run_adb(args)

    def forward_tcp(self, local_port: int, remote_port: int, no_rebind: bool = False) -> None:
        self.forward(f"tcp:{local_port}", f"tcp:{remote_port}", no_rebind=no_rebind)

    def reverse(self, remote: str, local: str, no_rebind: bool = False) -> None:
        args = ["reverse"]
        if no_rebind:
            args.append("--no-rebind")
        args.extend([remote, local])
        self._runner.run_adb(args)

    def reverse_tcp(self, remote_port: int, local_port: int, no_rebind: bool = False) -> None:
        self.reverse(f"tcp:{remote_port}", f"tcp:{local_port}", no_rebind=no_rebind)

    def list_forwards(self) -> List[ForwardRule]:
        result = self._runner.run_adb(["forward", "--list"])
        rules = []
        for line in result.lines:
            parts = line.split()
            if len(parts) >= 3:
                rules.append(ForwardRule(
                    serial=parts[0],
                    local=parts[1],
                    remote=parts[2],
                ))
        return rules

    def list_reverse(self) -> List[ForwardRule]:
        result = self._runner.run_adb(["reverse", "--list"])
        rules = []
        for line in result.lines:
            parts = line.split()
            if len(parts) >= 3:
                rules.append(ForwardRule(
                    serial=parts[0],
                    local=parts[1],
                    remote=parts[2],
                ))
        return rules

    def remove_forward(self, local: str) -> None:
        self._runner.run_adb(["forward", "--remove", local])

    def remove_forward_tcp(self, local_port: int) -> None:
        self.remove_forward(f"tcp:{local_port}")

    def remove_all_forwards(self) -> None:
        self._runner.run_adb(["forward", "--remove-all"])

    def remove_reverse(self, remote: str) -> None:
        self._runner.run_adb(["reverse", "--remove", remote])

    def remove_reverse_tcp(self, remote_port: int) -> None:
        self.remove_reverse(f"tcp:{remote_port}")

    def remove_all_reverse(self) -> None:
        self._runner.run_adb(["reverse", "--remove-all"])

    def forward_jdwp(self, local_port: int, pid: int) -> None:
        self.forward(f"tcp:{local_port}", f"jdwp:{pid}")

    def forward_localfilesystem(self, local_port: int, socket_name: str) -> None:
        self.forward(f"tcp:{local_port}", f"localfilesystem:{socket_name}")

    def forward_localabstract(self, local_port: int, socket_name: str) -> None:
        self.forward(f"tcp:{local_port}", f"localabstract:{socket_name}")
