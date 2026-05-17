import re
from typing import Iterator, List, Optional

from .models import LogcatEntry
from .shell import ADBCommandRunner


class LogcatManager:
    def __init__(self, runner: ADBCommandRunner):
        self._runner = runner

    def dump(
        self,
        tags: Optional[List[str]] = None,
        priority: Optional[str] = None,
        format: str = "threadtime",
        max_count: Optional[int] = None,
        since: Optional[str] = None,
        buffer: Optional[str] = None,
    ) -> List[LogcatEntry]:
        args = self._build_logcat_args(
            tags=tags, priority=priority, format=format,
            max_count=max_count, since=since, buffer=buffer, dump=True,
        )
        result = self._runner.run_adb(args, timeout=30)
        return self._parse_entries(result.lines)

    def dump_raw(
        self,
        tags: Optional[List[str]] = None,
        priority: Optional[str] = None,
        max_count: Optional[int] = None,
        buffer: Optional[str] = None,
    ) -> List[str]:
        args = self._build_logcat_args(
            tags=tags, priority=priority, max_count=max_count,
            buffer=buffer, dump=True,
        )
        result = self._runner.run_adb(args, timeout=30)
        return result.lines

    def clear(self) -> None:
        self._runner.run_adb(["logcat", "-c"])

    def stream(
        self,
        tags: Optional[List[str]] = None,
        priority: Optional[str] = None,
        format: str = "threadtime",
        buffer: Optional[str] = None,
    ) -> Iterator[LogcatEntry]:
        args = self._build_logcat_args(
            tags=tags, priority=priority, format=format, buffer=buffer,
        )
        shell_cmd = " ".join(args)
        for line in self._runner.run_shell_stream(shell_cmd.replace("logcat", "logcat", 1)):
            entry = self._parse_entry(line)
            if entry:
                yield entry

    def stream_raw(
        self,
        tags: Optional[List[str]] = None,
        priority: Optional[str] = None,
        buffer: Optional[str] = None,
    ) -> Iterator[str]:
        args = self._build_logcat_args(tags=tags, priority=priority, buffer=buffer)
        for line in self._runner.run_shell_stream("logcat " + " ".join(args[1:])):
            yield line

    def dump_crash(self) -> List[LogcatEntry]:
        return self.dump(buffer="crash")

    def save_to_file(
        self,
        filepath: str,
        tags: Optional[List[str]] = None,
        priority: Optional[str] = None,
        buffer: Optional[str] = None,
    ) -> None:
        entries = self.dump_raw(tags=tags, priority=priority, buffer=buffer)
        with open(filepath, "w") as f:
            f.write("\n".join(entries))

    def dump_ace_logs(self) -> List[LogcatEntry]:
        return self.dump(tags=["ACE"])

    def dump_atg_logs(self) -> List[LogcatEntry]:
        return self.dump(tags=["ATG"])

    def dump_ace_atg_logs(self) -> List[LogcatEntry]:
        return self.dump(tags=["ACE", "ATG"])

    def get_log_buffers(self) -> List[str]:
        result = self._runner.run_adb(["logcat", "-g"])
        buffers = []
        for line in result.lines:
            if line.strip():
                buffers.append(line.strip())
        return buffers

    def get_log_size(self, buffer: str = "main") -> str:
        result = self._runner.run_adb(["logcat", "-g", "-b", buffer])
        return result.output

    def _build_logcat_args(
        self,
        tags: Optional[List[str]] = None,
        priority: Optional[str] = None,
        format: Optional[str] = None,
        max_count: Optional[int] = None,
        since: Optional[str] = None,
        buffer: Optional[str] = None,
        dump: bool = False,
    ) -> List[str]:
        args = ["logcat"]

        if dump:
            args.append("-d")
        if format:
            args.extend(["-v", format])
        if buffer:
            args.extend(["-b", buffer])
        if max_count:
            args.extend(["-m", str(max_count)])
        if since:
            args.extend(["-T", since])

        if tags:
            if priority:
                for tag in tags:
                    args.append(f"{tag}:{priority}")
                args.append("*:S")
            else:
                args.extend(["-s"] + tags)
        elif priority:
            args.append(f"*:{priority}")

        return args

    def _parse_entries(self, lines: List[str]) -> List[LogcatEntry]:
        entries = []
        for line in lines:
            entry = self._parse_entry(line)
            if entry:
                entries.append(entry)
        return entries

    def _parse_entry(self, line: str) -> Optional[LogcatEntry]:
        pattern = re.compile(
            r'^(\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\.\d{3})\s+'
            r'(\d+)\s+(\d+)\s+'
            r'([VDIWEFS])\s+'
            r'(\S+?)\s*:\s+'
            r'(.*)$'
        )
        match = pattern.match(line)
        if match:
            return LogcatEntry(
                timestamp=match.group(1),
                pid=int(match.group(2)),
                tid=int(match.group(3)),
                priority=match.group(4),
                tag=match.group(5),
                message=match.group(6),
            )

        brief_pattern = re.compile(
            r'^([VDIWEFS])/(\S+?)\s*\(\s*(\d+)\):\s+(.*)$'
        )
        match = brief_pattern.match(line)
        if match:
            return LogcatEntry(
                priority=match.group(1),
                tag=match.group(2),
                pid=int(match.group(3)),
                message=match.group(4),
            )

        return None
