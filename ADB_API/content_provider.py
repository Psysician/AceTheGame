from typing import Dict, List, Optional

from .shell import ADBCommandRunner


class ContentProvider:
    def __init__(self, runner: ADBCommandRunner):
        self._runner = runner

    def query(
        self,
        uri: str,
        projection: Optional[List[str]] = None,
        where: Optional[str] = None,
        sort: Optional[str] = None,
    ) -> str:
        cmd = f"content query --uri {uri}"
        if projection:
            cmd += f" --projection {':'.join(projection)}"
        if where:
            cmd += f" --where \"{where}\""
        if sort:
            cmd += f" --sort \"{sort}\""
        result = self._runner.run_shell(cmd)
        return result.stdout

    def insert(self, uri: str, bindings: Dict[str, str]) -> str:
        cmd = f"content insert --uri {uri}"
        for key, value in bindings.items():
            cmd += f" --bind {key}:s:{value}"
        result = self._runner.run_shell(cmd)
        return result.output

    def update(
        self, uri: str, bindings: Dict[str, str], where: Optional[str] = None
    ) -> str:
        cmd = f"content update --uri {uri}"
        for key, value in bindings.items():
            cmd += f" --bind {key}:s:{value}"
        if where:
            cmd += f" --where \"{where}\""
        result = self._runner.run_shell(cmd)
        return result.output

    def delete(self, uri: str, where: Optional[str] = None) -> str:
        cmd = f"content delete --uri {uri}"
        if where:
            cmd += f" --where \"{where}\""
        result = self._runner.run_shell(cmd)
        return result.output

    def call(self, uri: str, method: str, arg: Optional[str] = None) -> str:
        cmd = f"content call --uri {uri} --method {method}"
        if arg:
            cmd += f" --arg {arg}"
        result = self._runner.run_shell(cmd)
        return result.output

    def read(self, uri: str) -> str:
        result = self._runner.run_shell(f"content read --uri {uri}")
        return result.stdout
