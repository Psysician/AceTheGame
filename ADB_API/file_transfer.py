import os
from typing import Callable, Optional

from .exceptions import FileTransferError
from .shell import ADBCommandRunner


class FileTransfer:
    def __init__(self, runner: ADBCommandRunner):
        self._runner = runner

    def push(self, local_path: str, remote_path: str, sync: bool = False) -> None:
        if not os.path.exists(local_path):
            raise FileTransferError("push", local_path, remote_path, "local file not found")

        args = ["push"]
        if sync:
            args.append("--sync")
        args.extend([local_path, remote_path])

        result = self._runner.run_adb(args, timeout=300)
        if not result.success and "error" in result.stderr.lower():
            raise FileTransferError("push", local_path, remote_path, result.stderr.strip())

    def pull(self, remote_path: str, local_path: str) -> None:
        local_dir = os.path.dirname(local_path)
        if local_dir and not os.path.exists(local_dir):
            os.makedirs(local_dir, exist_ok=True)

        result = self._runner.run_adb(["pull", remote_path, local_path], timeout=300)
        if not result.success and "error" in result.stderr.lower():
            raise FileTransferError("pull", local_path, remote_path, result.stderr.strip())

    def push_dir(self, local_dir: str, remote_dir: str) -> None:
        if not os.path.isdir(local_dir):
            raise FileTransferError("push", local_dir, remote_dir, "local directory not found")

        result = self._runner.run_adb(["push", local_dir, remote_dir], timeout=600)
        if not result.success and "error" in result.stderr.lower():
            raise FileTransferError("push", local_dir, remote_dir, result.stderr.strip())

    def pull_dir(self, remote_dir: str, local_dir: str) -> None:
        if not os.path.exists(local_dir):
            os.makedirs(local_dir, exist_ok=True)

        result = self._runner.run_adb(["pull", remote_dir, local_dir], timeout=600)
        if not result.success and "error" in result.stderr.lower():
            raise FileTransferError("pull", local_dir, remote_dir, result.stderr.strip())

    def sync(self, partition: Optional[str] = None) -> None:
        args = ["sync"]
        if partition:
            args.append(partition)
        self._runner.run_adb(args, timeout=600)

    def push_multiple(self, file_pairs: list) -> None:
        for local_path, remote_path in file_pairs:
            self.push(local_path, remote_path)

    def pull_multiple(self, file_pairs: list) -> None:
        for remote_path, local_path in file_pairs:
            self.pull(remote_path, local_path)
