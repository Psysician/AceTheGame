import re
from typing import List, Optional

from .models import FileInfo
from .shell import ADBCommandRunner


class FileSystem:
    def __init__(self, runner: ADBCommandRunner):
        self._runner = runner

    def ls(self, path: str = "/", show_all: bool = True) -> List[FileInfo]:
        flags = "-la" if show_all else "-l"
        result = self._runner.run_shell(f"ls {flags} {path}")
        files = []
        for line in result.lines:
            if line.startswith("total") or not line.strip():
                continue
            info = self._parse_ls_line(line, path)
            if info:
                files.append(info)
        return files

    def exists(self, path: str) -> bool:
        result = self._runner.run_shell(f"[ -e {path} ] && echo EXISTS || echo MISSING")
        return "EXISTS" in result.output

    def is_file(self, path: str) -> bool:
        result = self._runner.run_shell(f"[ -f {path} ] && echo YES || echo NO")
        return "YES" in result.output

    def is_directory(self, path: str) -> bool:
        result = self._runner.run_shell(f"[ -d {path} ] && echo YES || echo NO")
        return "YES" in result.output

    def mkdir(self, path: str, parents: bool = False) -> None:
        flag = "-p " if parents else ""
        self._runner.run_shell(f"mkdir {flag}{path}")

    def rm(self, path: str, recursive: bool = False, force: bool = False) -> None:
        flags = ""
        if recursive:
            flags += "r"
        if force:
            flags += "f"
        if flags:
            flags = f"-{flags} "
        self._runner.run_shell(f"rm {flags}{path}")

    def cp(self, src: str, dst: str, recursive: bool = False) -> None:
        flag = "-r " if recursive else ""
        self._runner.run_shell(f"cp {flag}{src} {dst}")

    def mv(self, src: str, dst: str) -> None:
        self._runner.run_shell(f"mv {src} {dst}")

    def chmod(self, path: str, mode: str) -> None:
        self._runner.run_shell(f"chmod {mode} {path}")

    def chown(self, path: str, owner: str, group: Optional[str] = None) -> None:
        ownership = f"{owner}:{group}" if group else owner
        self._runner.run_shell(f"chown {ownership} {path}")

    def cat(self, path: str) -> str:
        result = self._runner.run_shell(f"cat {path}")
        return result.stdout

    def stat(self, path: str) -> FileInfo:
        result = self._runner.run_shell(f"ls -ld {path}")
        for line in result.lines:
            info = self._parse_ls_line(line, path)
            if info:
                return info
        return FileInfo(path=path)

    def find(
        self, path: str, name: Optional[str] = None, file_type: Optional[str] = None,
        max_depth: Optional[int] = None,
    ) -> List[str]:
        cmd = f"find {path}"
        if max_depth is not None:
            cmd += f" -maxdepth {max_depth}"
        if file_type:
            cmd += f" -type {file_type}"
        if name:
            cmd += f" -name '{name}'"
        result = self._runner.run_shell(cmd)
        return [line for line in result.lines if line.strip()]

    def touch(self, path: str) -> None:
        self._runner.run_shell(f"touch {path}")

    def readlink(self, path: str) -> str:
        result = self._runner.run_shell(f"readlink -f {path}")
        return result.output

    def du(self, path: str, human_readable: bool = True) -> str:
        flag = "-h" if human_readable else ""
        result = self._runner.run_shell(f"du {flag} {path}")
        return result.output

    def head(self, path: str, lines: int = 10) -> str:
        result = self._runner.run_shell(f"head -n {lines} {path}")
        return result.stdout

    def tail(self, path: str, lines: int = 10) -> str:
        result = self._runner.run_shell(f"tail -n {lines} {path}")
        return result.stdout

    def grep(self, pattern: str, path: str, recursive: bool = False) -> List[str]:
        flag = "-r " if recursive else ""
        result = self._runner.run_shell(f"grep {flag}'{pattern}' {path}")
        return result.lines

    def wc(self, path: str) -> dict:
        result = self._runner.run_shell(f"wc {path}")
        parts = result.output.split()
        if len(parts) >= 3:
            return {
                "lines": int(parts[0]),
                "words": int(parts[1]),
                "bytes": int(parts[2]),
            }
        return {"lines": 0, "words": 0, "bytes": 0}

    def _parse_ls_line(self, line: str, base_path: str) -> Optional[FileInfo]:
        pattern = re.compile(
            r'^([drwxlsStT\-]{10})\s+'
            r'(\d+)\s+'
            r'(\S+)\s+'
            r'(\S+)\s+'
            r'(\d+)\s+'
            r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2})\s+'
            r'(.+)$'
        )
        match = pattern.match(line)
        if not match:
            return None

        perms = match.group(1)
        owner = match.group(3)
        group = match.group(4)
        size = int(match.group(5))
        date = match.group(6)
        name = match.group(7)

        is_symlink = perms.startswith("l")
        is_directory = perms.startswith("d")

        if " -> " in name:
            name = name.split(" -> ")[0]

        file_path = name.strip()
        if not file_path.startswith("/"):
            file_path = f"{base_path.rstrip('/')}/{file_path}"

        return FileInfo(
            path=file_path,
            permissions=perms,
            owner=owner,
            group=group,
            size=size,
            date=date,
            is_directory=is_directory,
            is_symlink=is_symlink,
        )
