import multiprocessing
import os
import re
import shutil
import subprocess
import zipfile
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Tuple

ANDROID_ARCH_ABI_ARR = [
    "armeabi-v7a",
    "arm64-v8a",
    "x86",
    "x86_64",
]

ANDROID_PLATFORM_TARGET = "android-23"


@dataclass
class BuildResult:
    success: bool
    component: str
    output_path: str = ""
    build_type: str = ""
    error: str = ""
    artifacts: List[str] = field(default_factory=list)


@dataclass
class ReleaseResult:
    success: bool
    components: Dict[str, BuildResult] = field(default_factory=dict)
    release_dir: str = ""

    @property
    def failed(self) -> List[str]:
        return [name for name, r in self.components.items() if not r.success]


def _run_cmd(
    cmd: List[str],
    cwd: Optional[str] = None,
    timeout: Optional[int] = None,
    env: Optional[dict] = None,
) -> Tuple[bool, str, str]:
    merged_env = None
    if env:
        merged_env = {**os.environ, **env}
    try:
        proc = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=merged_env,
        )
        return proc.returncode == 0, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired:
        return False, "", f"Command timed out after {timeout}s"
    except FileNotFoundError:
        return False, "", f"Command not found: {cmd[0]}"


def _mkdir_clean(path: str):
    if os.path.exists(path):
        shutil.rmtree(path)
    os.makedirs(path, exist_ok=True)


def _find_gradlew(project_dir: str) -> str:
    gradlew = os.path.join(project_dir, "gradlew")
    if os.path.isfile(gradlew):
        os.chmod(gradlew, 0o755)
        return gradlew
    raise FileNotFoundError(f"gradlew not found in {project_dir}")


class APKBuilder:
    def __init__(self, project_root: str):
        if not os.path.isdir(project_root):
            raise FileNotFoundError(f"Project root not found: {project_root}")
        self._root = os.path.abspath(project_root)

    def build_atg_debug(self, output_dir: Optional[str] = None) -> BuildResult:
        return self._build_gradle_apk(
            project_dir=os.path.join(self._root, "ATG"),
            task="assembleDebug",
            build_type="debug",
            component="ATG",
            output_dir=output_dir,
        )

    def build_atg_release(self, output_dir: Optional[str] = None) -> BuildResult:
        return self._build_gradle_apk(
            project_dir=os.path.join(self._root, "ATG"),
            task="assembleRelease",
            build_type="release",
            component="ATG",
            output_dir=output_dir,
        )

    def build_billing_hack_debug(self, output_dir: Optional[str] = None) -> BuildResult:
        return self._build_gradle_apk(
            project_dir=os.path.join(self._root, "billing-hack"),
            task="assembleDebug",
            build_type="debug",
            component="BillingHack",
            output_dir=output_dir,
        )

    def build_billing_hack_release(self, output_dir: Optional[str] = None) -> BuildResult:
        return self._build_gradle_apk(
            project_dir=os.path.join(self._root, "billing-hack"),
            task="assembleRelease",
            build_type="release",
            component="BillingHack",
            output_dir=output_dir,
        )

    def build_modder(self, output_dir: Optional[str] = None) -> BuildResult:
        project_dir = os.path.join(self._root, "Modder")
        component = "Modder"

        try:
            gradlew = _find_gradlew(project_dir)
        except FileNotFoundError as e:
            return BuildResult(success=False, component=component, error=str(e))

        injector_dir = os.path.join(project_dir, "injector")
        gen_smali = os.path.join(injector_dir, "gen_smali.py")
        if os.path.isfile(gen_smali):
            ok, stdout, stderr = _run_cmd(
                ["python3", gen_smali], cwd=injector_dir, timeout=120
            )
            if not ok:
                return BuildResult(
                    success=False, component=component,
                    error=f"gen_smali.py failed: {stderr}",
                )

        ok, stdout, stderr = _run_cmd(
            [gradlew, "clean"], cwd=project_dir, timeout=120
        )
        if not ok:
            return BuildResult(
                success=False, component=component,
                error=f"Gradle clean failed: {stderr}",
            )

        ok, stdout, stderr = _run_cmd(
            [gradlew, "build"], cwd=project_dir, timeout=600
        )
        if not ok:
            return BuildResult(
                success=False, component=component,
                error=f"Gradle build failed: {stderr}",
            )

        zip_path = os.path.join(
            project_dir, "modder", "build", "distributions", "modder.zip"
        )
        if not os.path.isfile(zip_path):
            return BuildResult(
                success=False, component=component,
                error=f"Build output not found: {zip_path}",
            )

        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(output_dir)
            return BuildResult(
                success=True, component=component,
                output_path=output_dir, build_type="distribution",
                artifacts=_list_files_recursive(output_dir),
            )

        return BuildResult(
            success=True, component=component,
            output_path=zip_path, build_type="distribution",
            artifacts=[zip_path],
        )

    def _build_gradle_apk(
        self,
        project_dir: str,
        task: str,
        build_type: str,
        component: str,
        output_dir: Optional[str] = None,
    ) -> BuildResult:
        try:
            gradlew = _find_gradlew(project_dir)
        except FileNotFoundError as e:
            return BuildResult(success=False, component=component, error=str(e))

        ok, stdout, stderr = _run_cmd(
            [gradlew, "clean"], cwd=project_dir, timeout=120
        )

        ok, stdout, stderr = _run_cmd(
            [gradlew, task], cwd=project_dir, timeout=900
        )
        if not ok:
            return BuildResult(
                success=False, component=component,
                error=f"Gradle {task} failed: {stderr}",
            )

        apk_files = _find_apk_outputs(project_dir, build_type)
        if not apk_files:
            return BuildResult(
                success=False, component=component,
                error=f"No APK files found after {task}",
            )

        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            copied = []
            for apk in apk_files:
                dest = os.path.join(output_dir, os.path.basename(apk))
                shutil.copy2(apk, dest)
                copied.append(dest)
            return BuildResult(
                success=True, component=component,
                output_path=output_dir, build_type=build_type,
                artifacts=copied,
            )

        return BuildResult(
            success=True, component=component,
            output_path=os.path.dirname(apk_files[0]) if apk_files else "",
            build_type=build_type,
            artifacts=apk_files,
        )


class ACEBuilder:
    def __init__(self, project_root: str):
        if not os.path.isdir(project_root):
            raise FileNotFoundError(f"Project root not found: {project_root}")
        self._root = os.path.abspath(project_root)
        self._cmake_dir = os.path.join(self._root, "ACE")

    def build_linux(
        self,
        output_dir: Optional[str] = None,
        build_dir: str = "./build",
        cpu_count: Optional[int] = None,
    ) -> BuildResult:
        component = "ACE-linux"
        install_dir = output_dir or os.path.join(self._root, "release", "linux")

        return self._cmake_build(
            install_dir=install_dir,
            build_dir=build_dir,
            component=component,
            extra_args=None,
            toolchain_path=None,
            cpu_count=cpu_count,
        )

    def build_android(
        self,
        toolchain_path: str,
        arch: str,
        output_dir: Optional[str] = None,
        build_dir: str = "./build",
        cpu_count: Optional[int] = None,
    ) -> BuildResult:
        if arch not in ANDROID_ARCH_ABI_ARR:
            return BuildResult(
                success=False, component=f"ACE-android-{arch}",
                error=f"Unsupported arch: {arch}. Supported: {ANDROID_ARCH_ABI_ARR}",
            )

        component = f"ACE-android-{arch}"
        install_dir = output_dir or os.path.join(self._root, "release", "android", arch)

        return self._cmake_build(
            install_dir=install_dir,
            build_dir=build_dir,
            component=component,
            extra_args=[
                f"-DANDROID_ABI={arch}",
                f"-DANDROID_PLATFORM={ANDROID_PLATFORM_TARGET}",
            ],
            toolchain_path=toolchain_path,
            cpu_count=cpu_count,
        )

    def build_android_all_archs(
        self,
        toolchain_path: str,
        output_dir: Optional[str] = None,
        build_dir: str = "./build",
        cpu_count: Optional[int] = None,
    ) -> Dict[str, BuildResult]:
        results = {}
        base_dir = output_dir or os.path.join(self._root, "release", "android")
        for arch in ANDROID_ARCH_ABI_ARR:
            arch_dir = os.path.join(base_dir, arch)
            results[arch] = self.build_android(
                toolchain_path=toolchain_path,
                arch=arch,
                output_dir=arch_dir,
                build_dir=build_dir,
                cpu_count=cpu_count,
            )
        return results

    def _cmake_build(
        self,
        install_dir: str,
        build_dir: str,
        component: str,
        extra_args: Optional[List[str]],
        toolchain_path: Optional[str],
        cpu_count: Optional[int],
    ) -> BuildResult:
        _mkdir_clean(build_dir)
        _mkdir_clean(install_dir)

        install_path = os.path.abspath(install_dir)
        cmake_path = os.path.abspath(self._cmake_dir)

        if cpu_count is None:
            cpu_count = multiprocessing.cpu_count()

        cmake_args = [
            "cmake", cmake_path,
            "-DCMAKE_BUILD_TYPE=Release",
            f"-DCMAKE_INSTALL_PREFIX:PATH={install_path}",
        ]

        if toolchain_path:
            if not os.path.isfile(toolchain_path):
                return BuildResult(
                    success=False, component=component,
                    error=f"Toolchain file not found: {toolchain_path}",
                )
            cmake_args.append(f"-DCMAKE_TOOLCHAIN_FILE={os.path.abspath(toolchain_path)}")

        if extra_args:
            cmake_args.extend(extra_args)

        ok, stdout, stderr = _run_cmd(cmake_args, cwd=build_dir, timeout=120)
        if not ok:
            return BuildResult(
                success=False, component=component,
                error=f"CMake configure failed: {stderr}",
            )

        ok, stdout, stderr = _run_cmd(
            ["make", "all", "install", f"-j{cpu_count}"],
            cwd=build_dir, timeout=600,
        )
        if not ok:
            return BuildResult(
                success=False, component=component,
                error=f"Make failed: {stderr}",
            )

        artifacts = _list_files_recursive(install_dir)
        return BuildResult(
            success=True, component=component,
            output_path=install_dir, build_type="release",
            artifacts=artifacts,
        )


class ReleasePipeline:
    def __init__(self, project_root: str):
        self._root = os.path.abspath(project_root)
        self._apk = APKBuilder(self._root)
        self._ace = ACEBuilder(self._root)

    @property
    def apk(self) -> APKBuilder:
        return self._apk

    @property
    def ace(self) -> ACEBuilder:
        return self._ace

    def build_full_release(
        self,
        android_toolchain_file: str,
        release_dir: Optional[str] = None,
        build_atg: bool = True,
        build_billing: bool = True,
        build_modder: bool = True,
        build_ace_linux: bool = True,
        build_ace_android: bool = True,
        on_progress: Optional[Callable[[str, str], None]] = None,
    ) -> ReleaseResult:
        if release_dir is None:
            release_dir = os.path.join(self._root, "release")
        os.makedirs(release_dir, exist_ok=True)

        result = ReleaseResult(success=True, release_dir=release_dir)

        if build_ace_android:
            self._notify(on_progress, "ACE-android", "building")
            ace_android_dir = os.path.join(release_dir, "ACERelease", "android")
            arch_results = self._ace.build_android_all_archs(
                toolchain_path=android_toolchain_file,
                output_dir=ace_android_dir,
            )
            for arch, br in arch_results.items():
                result.components[f"ACE-android-{arch}"] = br
                if not br.success:
                    result.success = False
            self._notify(on_progress, "ACE-android", "done")

        if build_ace_linux:
            self._notify(on_progress, "ACE-linux", "building")
            ace_linux_dir = os.path.join(release_dir, "ACERelease", "linux")
            br = self._ace.build_linux(output_dir=ace_linux_dir)
            result.components["ACE-linux"] = br
            if not br.success:
                result.success = False
            self._notify(on_progress, "ACE-linux", "done")

        if build_atg:
            self._notify(on_progress, "ATG", "building")
            atg_dir = os.path.join(release_dir, "ATG")
            br = self._apk.build_atg_release(output_dir=atg_dir)
            result.components["ATG"] = br
            if not br.success:
                result.success = False
            self._notify(on_progress, "ATG", "done")

        if build_billing:
            self._notify(on_progress, "BillingHack", "building")
            billing_dir = os.path.join(release_dir, "BillingHack")
            br = self._apk.build_billing_hack_release(output_dir=billing_dir)
            result.components["BillingHack"] = br
            if not br.success:
                result.success = False
            self._notify(on_progress, "BillingHack", "done")

        if build_modder:
            self._notify(on_progress, "Modder", "building")
            modder_dir = os.path.join(release_dir, "ModderRelease")
            br = self._apk.build_modder(output_dir=modder_dir)
            result.components["Modder"] = br
            if not br.success:
                result.success = False
            self._notify(on_progress, "Modder", "done")

        return result

    def build_deploy(
        self,
        android_toolchain_file: str,
        target_pid: int,
        adb_instance=None,
        release_dir: Optional[str] = None,
    ) -> ReleaseResult:
        result = self.build_full_release(
            android_toolchain_file=android_toolchain_file,
            release_dir=release_dir,
            build_atg=True,
            build_billing=False,
            build_modder=False,
            build_ace_linux=False,
            build_ace_android=True,
        )

        if adb_instance and result.success:
            ace_release_dir = os.path.join(result.release_dir, "ACERelease")
            adb_instance.ace.deploy_and_start(ace_release_dir, target_pid)

            for name, br in result.components.items():
                if name == "ATG" and br.success and br.artifacts:
                    for apk in br.artifacts:
                        if apk.endswith(".apk"):
                            adb_instance.install(apk, reinstall=True)

        return result

    def clean_build_artifacts(self):
        dirs_to_clean = [
            os.path.join(self._root, "build"),
            os.path.join(self._root, "release"),
        ]
        for d in dirs_to_clean:
            if os.path.isdir(d):
                shutil.rmtree(d)

        for sub in ["ATG", "Modder", "billing-hack"]:
            build_dir = os.path.join(self._root, sub, "build")
            if os.path.isdir(build_dir):
                shutil.rmtree(build_dir)

            gradle_cache = os.path.join(self._root, sub, ".gradle")
            if os.path.isdir(gradle_cache):
                shutil.rmtree(gradle_cache)

    @staticmethod
    def _notify(
        callback: Optional[Callable[[str, str], None]],
        component: str,
        status: str,
    ):
        if callback:
            callback(component, status)


def _find_apk_outputs(project_dir: str, build_type: str) -> List[str]:
    apk_files = []
    search_dirs = [
        os.path.join(project_dir, "app", "build", "outputs", "apk", build_type),
        os.path.join(project_dir, "app", "build", "outputs", "apk"),
        os.path.join(project_dir, "build", "outputs", "apk", build_type),
        os.path.join(project_dir, "build", "outputs", "apk"),
    ]

    for search_dir in search_dirs:
        if os.path.isdir(search_dir):
            for root, dirs, files in os.walk(search_dir):
                for f in files:
                    if f.endswith(".apk"):
                        apk_files.append(os.path.join(root, f))

    return apk_files


def _list_files_recursive(directory: str) -> List[str]:
    files = []
    if not os.path.isdir(directory):
        return files
    for root, dirs, filenames in os.walk(directory):
        for f in filenames:
            files.append(os.path.join(root, f))
    return files
