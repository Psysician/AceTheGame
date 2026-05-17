# ADB_API -- Python ADB Interface Reference

Complete Python wrapper around the Android Debug Bridge (ADB) CLI. Provides typed methods for every `adb` and `adb shell` command, organized into sub-modules by functionality.

---

## Table of Contents

- [Quick Start](#quick-start)
- [Installation](#installation)
- [ADB Class (Main Facade)](#adb-class-main-facade)
- [Sub-modules Reference](#sub-modules-reference)
  - [shell -- ADBCommandRunner](#shell----adbcommandrunner)
  - [device -- DeviceManager](#device----devicemanager)
  - [package -- PackageManager](#package----packagemanager)
  - [process -- ProcessManager](#process----processmanager)
  - [activity -- ActivityManager](#activity----activitymanager)
  - [logcat -- LogcatManager](#logcat----logcatmanager)
  - [network -- NetworkManager](#network----networkmanager)
  - [system_info -- SystemInfo](#system_info----systeminfo)
  - [file_system -- FileSystem](#file_system----filesystem)
  - [file_transfer -- FileTransfer](#file_transfer----filetransfer)
  - [input_sim -- InputSimulator](#input_sim----inputsimulator)
  - [content_provider -- ContentProvider](#content_provider----contentprovider)
  - [app_ops -- AppOpsManager](#app_ops----appopsmanager)
  - [backup_manager -- BackupManager](#backup_manager----backupmanager)
  - [device_policy -- DevicePolicyManager](#device_policy----devicepolicymanager)
  - [ace_operations -- ACEOperations](#ace_operations----aceoperations)
- [Release Build](#release-build)
  - [APKBuilder](#apkbuilder)
  - [ACEBuilder](#acebuilder)
  - [ReleasePipeline](#releasepipeline)
- [Data Models](#data-models)
- [Exceptions](#exceptions)
- [ADB Command Mapping](#adb-command-mapping)
- [Keycode Constants](#keycode-constants)

---

## Quick Start

```python
from ADB_API import ADB

adb = ADB()

# List connected devices
devices = adb.device.list_devices()
for d in devices:
    print(f"{d.serial} - {d.model} ({d.state})")

# Select a specific device
adb.select_device("emulator-5554")

# Install an APK
adb.install("/path/to/app.apk", reinstall=True, grant_permissions=True)

# Run a shell command
result = adb.shell("ls /sdcard/")
print(result.output)

# Push and pull files
adb.push("local_file.txt", "/sdcard/file.txt")
adb.pull("/sdcard/file.txt", "downloaded.txt")

# Get device info
props = adb.device.get_device_properties()
print(f"Model: {props.model}, Android: {props.android_version}")

# Take a screenshot
adb.system.screenshot("screen.png")

# Interact with the device
adb.input.tap(500, 800)
adb.input.text("Hello")
adb.input.press_home()

# Read logcat
entries = adb.logcat.dump(priority="E", max_count=50)
for entry in entries:
    print(f"[{entry.tag}] {entry.message}")

# ACE game hacking operations (requires root)
status = adb.ace.verify_device_ready()
adb.ace.deploy_and_start("/path/to/release", target_pid=12345)
```

---

## Installation

No external dependencies. Copy the `ADB_API/` folder into your project or add its parent directory to `sys.path`. Requires the `adb` binary in your `PATH` or set via `ANDROID_HOME` / `ANDROID_SDK_ROOT`.

```python
from ADB_API import ADB
adb = ADB()
```

Constructor parameters:

| Parameter | Type | Default | Description |
|---|---|---|---|
| `device_serial` | `Optional[str]` | `None` | Target device serial. If `None`, auto-selects when only one device is connected. |
| `adb_path` | `Optional[str]` | `None` | Path to the `adb` binary. Auto-detected if not set. |
| `default_timeout` | `int` | `30` | Default command timeout in seconds. |

---

## ADB Class (Main Facade)

Accessed as the top-level `ADB` object. Provides convenience wrappers and exposes all sub-modules as attributes.

### Attributes (Sub-modules)

| Attribute | Type | Description |
|---|---|---|
| `device` | `DeviceManager` | Device discovery, properties, connection |
| `packages` | `PackageManager` | APK install/uninstall, package listing |
| `files` | `FileTransfer` | Push/pull files and directories |
| `process` | `ProcessManager` | Process listing, killing |
| `activity` | `ActivityManager` | Activities, services, broadcasts, intents |
| `logcat` | `LogcatManager` | Log reading and streaming |
| `network` | `NetworkManager` | Port forwarding and reverse |
| `system` | `SystemInfo` | Battery, memory, display, settings, screenshots |
| `fs` | `FileSystem` | On-device filesystem operations |
| `input` | `InputSimulator` | Tap, swipe, key events, text input |
| `ace` | `ACEOperations` | ACE engine deployment and control |
| `release` | `ReleasePipeline` | Build APKs and native binaries |
| `content` | `ContentProvider` | Android content provider CRUD |
| `appops` | `AppOpsManager` | App operations permissions |
| `backup_mgr` | `BackupManager` | Backup manager (bmgr) |
| `dpm` | `DevicePolicyManager` | Device policy management |

### Top-level Methods

```python
run(args: List[str], timeout: Optional[int] = None) -> CommandResult
```
Run a raw ADB command. Maps to: `adb <args>`

```python
shell(command: Union[str, List[str]], timeout: Optional[int] = None, as_root: bool = False) -> CommandResult
```
Run a shell command on the device. Maps to: `adb shell <command>` (or `adb shell su -c <command>` when `as_root=True`)

```python
is_connected() -> bool
```
Check if a device is reachable. Maps to: `adb shell echo test`

```python
select_device(serial: str) -> None
```
Set the target device serial for all subsequent commands.

```python
get_selected_device() -> Optional[str]
```
Return the currently selected device serial.

```python
version() -> str
```
Get ADB version string. Maps to: `adb version`

```python
server_version() -> str
```
Get ADB server version line. Maps to: `adb version` (parses the "Version" line)

```python
start_server() -> None
```
Start the ADB server. Maps to: `adb start-server`

```python
kill_server() -> None
```
Kill the ADB server. Maps to: `adb kill-server`

```python
restart_server() -> None
```
Kill and restart the ADB server.

```python
wait_for_device(timeout: int = 60) -> bool
```
Block until a device is connected. Maps to: `adb wait-for-device`

```python
usb() -> None
```
Restart ADB in USB mode. Maps to: `adb usb`

```python
tcpip(port: int = 5555) -> None
```
Restart ADB in TCP/IP mode. Maps to: `adb tcpip <port>`

```python
root() -> str
```
Restart adbd with root permissions. Maps to: `adb root`

```python
unroot() -> str
```
Restart adbd without root. Maps to: `adb unroot`

```python
remount() -> str
```
Remount /system as read-write. Maps to: `adb remount`

```python
bugreport(output_path: str) -> None
```
Generate a bugreport. Maps to: `adb bugreport <output_path>`

```python
jdwp() -> List[int]
```
List PIDs of processes hosting a JDWP transport. Maps to: `adb jdwp`

```python
get_state() -> str
```
Get device state (device/offline/bootloader). Maps to: `adb get-state`

```python
push(local_path: str, remote_path: str) -> None
```
Push a file to the device. Maps to: `adb push <local> <remote>`

```python
pull(remote_path: str, local_path: str) -> None
```
Pull a file from the device. Maps to: `adb pull <remote> <local>`

```python
install(apk_path: str, **kwargs) -> None
```
Install an APK. Maps to: `adb install [flags] <apk>`. See `PackageManager.install` for kwargs.

```python
uninstall(package_name: str, **kwargs) -> None
```
Uninstall a package. Maps to: `adb uninstall [flags] <package>`. See `PackageManager.uninstall` for kwargs.

```python
pair(host: str, port: int, pairing_code: str) -> bool
```
Pair with a device over WiFi (Android 11+). Maps to: `adb pair <host>:<port> <code>`

```python
reconnect(mode: Optional[str] = None) -> None
```
Kick connection and reconnect. Maps to: `adb reconnect [mode]`

```python
sideload(filepath: str) -> str
```
Sideload an OTA package in recovery. Maps to: `adb sideload <file>`

```python
disable_verity() -> str
```
Disable dm-verity. Maps to: `adb disable-verity`

```python
enable_verity() -> str
```
Enable dm-verity. Maps to: `adb enable-verity`

```python
exec_out(command: str) -> bytes
```
Run a command with raw binary output. Maps to: `adb exec-out <command>`

```python
emu(command: str) -> str
```
Send an emulator console command. Maps to: `adb emu <command>`

```python
backup(output_file: str, packages: Optional[List[str]] = None, apk: bool = False, shared: bool = False, system: bool = True, all_packages: bool = False) -> None
```
Perform a full device backup. Maps to: `adb backup -f <file> [flags] [packages]`

```python
restore(backup_file: str) -> None
```
Restore from a backup file. Maps to: `adb restore <file>`

```python
get_devpath() -> str
```
Get the device path. Maps to: `adb get-devpath`

```python
install_multi_package(apk_paths: List[str], **kwargs) -> None
```
Install multiple packages atomically. Maps to: `adb install-multi-package [flags] <apks>`. Kwargs: `reinstall`, `allow_downgrade`, `grant_permissions`.

---

## Sub-modules Reference

### shell -- ADBCommandRunner

Low-level command runner. Not typically used directly; used internally by all sub-modules.

Access: `adb._runner` (internal)

```python
ADBCommandRunner(adb_path: Optional[str] = None, device_serial: Optional[str] = None, default_timeout: int = 30)
```

| Method | Signature | Description | ADB Command |
|---|---|---|---|
| `run_adb` | `(args: List[str], timeout: Optional[int] = None, check: bool = False) -> CommandResult` | Execute an ADB command | `adb <args>` |
| `run_shell` | `(command: Union[str, List[str]], timeout: Optional[int] = None, as_root: bool = False) -> CommandResult` | Execute a shell command on device | `adb shell <cmd>` |
| `run_shell_stream` | `(command: Union[str, List[str]], as_root: bool = False) -> Iterator[str]` | Stream shell command output line-by-line | `adb shell <cmd>` (streaming) |
| `check_connection` | `() -> bool` | Verify device connectivity | `adb shell echo test` |

Properties:
- `device_serial` -- get/set the target device serial

---

### device -- DeviceManager

Access: `adb.device`

| Method | Signature | Description | ADB Command |
|---|---|---|---|
| `list_devices` | `() -> List[DeviceInfo]` | List all connected devices | `adb devices -l` |
| `get_device_properties` | `() -> DeviceProperties` | Get aggregated device properties | Multiple `getprop` calls |
| `get_property` | `(prop_name: str) -> str` | Get a single system property | `adb shell getprop <prop>` |
| `set_property` | `(prop_name: str, value: str) -> None` | Set a system property | `adb shell setprop <prop> <val>` |
| `connect` | `(host: str, port: int = 5555) -> bool` | Connect to a device over TCP/IP | `adb connect <host>:<port>` |
| `disconnect` | `(host: Optional[str] = None) -> None` | Disconnect a TCP/IP device | `adb disconnect [host]` |
| `reboot` | `(mode: Optional[str] = None) -> None` | Reboot the device | `adb reboot [mode]` |
| `wait_for_device` | `(timeout: int = 60) -> bool` | Wait until a device is online | `adb wait-for-device` |
| `is_rooted` | `() -> bool` | Check if device has root access | `adb shell su -c whoami` / `id` |
| `get_serial` | `() -> str` | Get device serial number | `adb get-serialno` |
| `get_model` | `() -> str` | Get device model name | `getprop ro.product.model` |
| `get_android_version` | `() -> str` | Get Android version string | `getprop ro.build.version.release` |
| `get_sdk_level` | `() -> int` | Get SDK API level | `getprop ro.build.version.sdk` |
| `get_abi` | `() -> str` | Get primary CPU ABI | `getprop ro.product.cpu.abi` |
| `get_state` | `() -> str` | Get device state | `adb get-state` |
| `get_manufacturer` | `() -> str` | Get device manufacturer | `getprop ro.product.manufacturer` |
| `get_build_type` | `() -> str` | Get build type (userdebug/user/eng) | `getprop ro.build.type` |
| `get_hardware` | `() -> str` | Get hardware name | `getprop ro.hardware` |
| `get_display_resolution` | `() -> Tuple[int, int]` | Get screen resolution (width, height) | `adb shell wm size` |
| `get_supported_abis` | `() -> List[str]` | Get all supported ABIs | `getprop ro.product.cpu.abilist` |
| `pair` | `(host: str, port: int, pairing_code: str) -> bool` | Pair with device over WiFi | `adb pair <host>:<port> <code>` |
| `reconnect` | `(mode: Optional[str] = None) -> None` | Reconnect to device | `adb reconnect [mode]` |
| `get_devpath` | `() -> str` | Get device path | `adb get-devpath` |
| `wait_for_recovery` | `(timeout: int = 60) -> bool` | Wait for device in recovery mode | `adb wait-for-recovery` |
| `wait_for_sideload` | `(timeout: int = 60) -> bool` | Wait for device in sideload mode | `adb wait-for-sideload` |
| `wait_for_bootloader` | `(timeout: int = 60) -> bool` | Wait for device in bootloader | `adb wait-for-bootloader` |
| `wait_for_disconnect` | `(timeout: int = 60) -> bool` | Wait for device to disconnect | `adb wait-for-disconnect` |
| `get_bootloader_version` | `() -> str` | Get bootloader version | `getprop ro.boot.bootloader` |
| `get_secure_status` | `() -> bool` | Check if ro.secure is 1 | `getprop ro.secure` |
| `get_boot_fingerprint` | `() -> str` | Get boot image fingerprint | `getprop ro.bootimage.build.fingerprint` |
| `get_usb_mode` | `() -> str` | Get current USB config | `getprop persist.sys.usb.config` |
| `set_usb_mode` | `(config: str) -> None` | Set USB config (mtp, ptp, etc.) | `setprop persist.sys.usb.config <val>` |
| `mdns_check` | `() -> str` | Check mDNS status | `adb mdns check` |
| `mdns_services` | `() -> List[str]` | List discovered mDNS services | `adb mdns services` |

---

### package -- PackageManager

Access: `adb.packages`

| Method | Signature | Description | ADB Command |
|---|---|---|---|
| `list_packages` | `(filter_str: Optional[str] = None, show_only: str = "all") -> List[str]` | List installed packages. `show_only`: `"all"`, `"system"`, `"third-party"`, `"enabled"`, `"disabled"` | `pm list packages [-s\|-3\|-e\|-d] [filter]` |
| `get_package_info` | `(package_name: str) -> PackageInfo` | Get version and installer info for a package | `dumpsys package <pkg>` |
| `get_apk_paths` | `(package_name: str) -> List[str]` | Get APK file paths on device | `pm path <pkg>` |
| `package_exists` | `(package_name: str) -> bool` | Check if a package is installed | `pm list packages <pkg>` |
| `install` | `(apk_path: str, reinstall: bool = False, allow_downgrade: bool = False, grant_permissions: bool = False, allow_test: bool = False) -> None` | Install an APK | `adb install [-r] [-d] [-g] [-t] <apk>` |
| `install_multiple` | `(apk_dir: str) -> None` | Install split APKs from a directory | `adb install-multiple <apks>` |
| `uninstall` | `(package_name: str, keep_data: bool = False) -> None` | Uninstall a package | `adb uninstall [-k] <pkg>` |
| `clear_data` | `(package_name: str) -> None` | Clear all app data | `pm clear <pkg>` |
| `enable` | `(package_name: str) -> None` | Enable a package | `pm enable <pkg>` |
| `disable` | `(package_name: str) -> None` | Disable a package for the current user | `pm disable-user <pkg>` |
| `force_stop` | `(package_name: str) -> None` | Force stop a package | `am force-stop <pkg>` |
| `grant_permission` | `(package_name: str, permission: str) -> None` | Grant a runtime permission | `pm grant <pkg> <perm>` |
| `revoke_permission` | `(package_name: str, permission: str) -> None` | Revoke a runtime permission | `pm revoke <pkg> <perm>` |
| `list_permissions` | `(package_name: str) -> List[str]` | List granted permissions | `dumpsys package <pkg>` |
| `list_requested_permissions` | `(package_name: str) -> List[str]` | List permissions declared in manifest | `dumpsys package <pkg>` |
| `download_apk` | `(package_name: str, output_dir: str) -> List[str]` | Pull APK files to local directory | `pm path` + `adb pull` |
| `get_install_location` | `() -> str` | Get default install location | `pm get-install-location` |
| `set_install_location` | `(location: int) -> None` | Set default install location (0=auto, 1=internal, 2=external) | `pm set-install-location <loc>` |
| `list_features` | `() -> List[str]` | List device hardware features | `pm list features` |
| `list_libraries` | `() -> List[str]` | List shared libraries | `pm list libraries` |
| `list_permission_groups` | `() -> List[str]` | List permission groups | `pm list permission-groups` |
| `list_permissions_detailed` | `(group: Optional[str] = None, dangerous_only: bool = False) -> List[str]` | List permissions, optionally filtered | `pm list permissions [-d] [group]` |
| `list_instrumentation` | `(target_package: Optional[str] = None) -> List[str]` | List instrumentation components | `pm list instrumentation [pkg]` |
| `list_users` | `() -> List[str]` | List all user accounts | `pm list users` |
| `dump` | `(package_name: str) -> str` | Dump full package information | `pm dump <pkg>` |
| `hide` | `(package_name: str) -> None` | Hide a package | `pm hide <pkg>` |
| `unhide` | `(package_name: str) -> None` | Unhide a package | `pm unhide <pkg>` |
| `suspend` | `(package_name: str) -> None` | Suspend a package | `pm suspend <pkg>` |
| `unsuspend` | `(package_name: str) -> None` | Unsuspend a package | `pm unsuspend <pkg>` |
| `reset_permissions` | `() -> None` | Reset all runtime permissions | `pm reset-permissions` |
| `set_permission_enforced` | `(permission: str, enforced: bool) -> None` | Set permission enforcement | `pm set-permission-enforced <perm> <bool>` |
| `trim_caches` | `(free_space: str) -> None` | Trim package caches to reach free space target | `pm trim-caches <space>` |
| `create_user` | `(user_name: str) -> str` | Create a new user account | `pm create-user <name>` |
| `remove_user` | `(user_id: int) -> None` | Remove a user account | `pm remove-user <id>` |
| `get_max_users` | `() -> int` | Get maximum supported users | `pm get-max-users` |
| `compile_package` | `(package_name: str, mode: str = "speed", force: bool = False, reset: bool = False) -> None` | Compile a package with dex2oat | `cmd package compile -m <mode> [-f] [--reset] <pkg>` |
| `compile_all` | `(mode: str = "speed") -> None` | Compile all packages | `cmd package compile -m <mode> -a` |
| `force_dex_opt` | `(package_name: str) -> None` | Force dex optimization | `cmd package force-dex-opt <pkg>` |
| `bg_dexopt_job` | `() -> None` | Trigger background dex optimization job | `cmd package bg-dexopt-job` |
| `move_package` | `(package_name: str, volume: str = "internal") -> None` | Move package to a storage volume | `pm move-package <pkg> <vol>` |
| `move_primary_storage` | `(volume: str = "internal") -> None` | Move primary storage | `pm move-primary-storage <vol>` |
| `set_app_links` | `(package_name: str, state: str = "verified") -> None` | Set app link verification state | `pm set-app-links --package <pkg> <state>` |
| `get_app_links` | `(package_name: str) -> str` | Get app link verification info | `pm get-app-links <pkg>` |
| `default_state` | `(package_name: str) -> None` | Reset package to default state | `pm default-state <pkg>` |
| `install_streaming` | `(apk_path: str) -> None` | Install APK via streaming | `pm install -S <size>` |

---

### process -- ProcessManager

Access: `adb.process`

| Method | Signature | Description | ADB Command |
|---|---|---|---|
| `list_processes` | `() -> List[ProcessInfo]` | List all running processes | `ps -A -o PID,PPID,USER,NAME` |
| `get_process_by_pid` | `(pid: int) -> Optional[ProcessInfo]` | Get process info by PID | `ps -p <pid>` / `/proc/<pid>/comm` |
| `get_processes_by_name` | `(name: str) -> List[ProcessInfo]` | Find processes by name substring | `ps -A` (filtered) |
| `kill_process` | `(pid: int, signal: int = 9) -> None` | Kill a process by PID | `kill -<signal> <pid>` |
| `kill_by_name` | `(name: str) -> None` | Kill processes by name | `pkill <name>` |
| `is_process_running` | `(pid: int) -> bool` | Check if a process is alive | `kill -0 <pid>` |
| `get_process_cmdline` | `(pid: int) -> str` | Get full command line of a process | `cat /proc/<pid>/cmdline` |
| `get_process_status` | `(pid: int) -> dict` | Get /proc status fields as a dict | `cat /proc/<pid>/status` |
| `get_process_maps` | `(pid: int) -> List[str]` | Get memory maps of a process | `cat /proc/<pid>/maps` |
| `get_uid_for_package` | `(package_name: str) -> Optional[int]` | Get UID assigned to a package | `dumpsys package <pkg>` |
| `get_top_activity` | `() -> Optional[str]` | Get the currently focused activity | `dumpsys activity top` |

---

### activity -- ActivityManager

Access: `adb.activity`

| Method | Signature | Description | ADB Command |
|---|---|---|---|
| `start_activity` | `(component: str, action: Optional[str] = None, data: Optional[str] = None, mime_type: Optional[str] = None, category: Optional[str] = None, extras: Optional[Dict[str, str]] = None, flags: Optional[List[str]] = None, wait: bool = False) -> str` | Start an activity | `am start [-W] [-a action] [-d data] [-t type] [-c cat] [--es k v] -n <component>` |
| `start_service` | `(component: str, action: Optional[str] = None, extras: Optional[Dict[str, str]] = None) -> str` | Start a service | `am startservice [-a action] [--es k v] -n <component>` |
| `stop_service` | `(component: str) -> str` | Stop a service | `am stopservice -n <component>` |
| `send_broadcast` | `(action: str, component: Optional[str] = None, extras: Optional[Dict[str, str]] = None, extra_ints: Optional[Dict[str, int]] = None, extra_bools: Optional[Dict[str, bool]] = None) -> str` | Send a broadcast intent | `am broadcast -a <action> [-n comp] [--es/--ei/--ez ...]` |
| `force_stop` | `(package_name: str) -> None` | Force stop an application | `am force-stop <pkg>` |
| `kill` | `(package_name: str) -> None` | Kill an application's processes | `am kill <pkg>` |
| `kill_all` | `() -> None` | Kill all background processes | `am kill-all` |
| `send_intent` | `(intent_args: List[str]) -> str` | Send a raw intent | `am start <args>` |
| `get_current_activity` | `() -> Optional[str]` | Get the currently resumed activity | `dumpsys activity activities` |
| `get_current_package` | `() -> Optional[str]` | Get the foreground package name | Parses `get_current_activity()` |
| `start_instrumentation` | `(component: str, args: Optional[Dict[str, str]] = None, raw: bool = False, wait: bool = True) -> str` | Run instrumentation tests | `am instrument [-r] [-w] [-e k v] <component>` |
| `set_debug_app` | `(package_name: str, wait: bool = False) -> None` | Set app for debugging | `am set-debug-app [-w] <pkg>` |
| `clear_debug_app` | `() -> None` | Clear debug app | `am clear-debug-app` |
| `monitor` | `() -> str` | Start activity monitor | `am monitor` |
| `profile_start` | `(process: str, output_file: str) -> None` | Start method profiling | `am profile start <proc> <file>` |
| `profile_stop` | `(process: str) -> None` | Stop method profiling | `am profile stop <proc>` |
| `dumpheap` | `(process: str, output_file: str) -> None` | Dump heap of a process | `am dumpheap <proc> <file>` |
| `send_trimming` | `(level: str = "COMPLETE") -> None` | Send memory trim level | `am send-trim-memory <level>` |
| `restart` | `() -> None` | Restart the activity manager | `am restart` |
| `hang` | `(allow_restart: bool = False) -> None` | Hang the system (testing) | `am hang [--allow-restart]` |
| `idle_maintenance` | `() -> None` | Run idle maintenance | `am idle-maintenance` |
| `screen_compat` | `(package_name: str, enabled: bool) -> None` | Toggle screen compatibility mode | `am screen-compat on\|off <pkg>` |
| `switch_user` | `(user_id: int) -> None` | Switch to a user | `am switch-user <id>` |
| `start_user` | `(user_id: int) -> None` | Start a user | `am start-user <id>` |
| `stop_user` | `(user_id: int, wait: bool = False, force: bool = False) -> None` | Stop a user | `am stop-user [-w] [-f] <id>` |
| `get_current_user` | `() -> str` | Get current user ID | `am get-current-user` |
| `get_config` | `() -> str` | Get device configuration | `am get-config` |
| `set_inactive` | `(package_name: str, inactive: bool) -> None` | Set app standby bucket | `am set-inactive <pkg> true\|false` |
| `get_inactive` | `(package_name: str) -> str` | Get app standby state | `am get-inactive <pkg>` |
| `make_uid_idle` | `(package_name: str) -> None` | Make UID idle | `am make-uid-idle <pkg>` |
| `to_uri` | `(intent_args: str) -> str` | Convert intent to URI | `am to-uri <args>` |
| `to_intent_uri` | `(intent_args: str) -> str` | Convert to intent URI | `am to-intent-uri <args>` |
| `to_app_uri` | `(intent_args: str) -> str` | Convert to app URI | `am to-app-uri <args>` |
| `stack_list` | `() -> str` | List activity stacks | `am stack list` |
| `stack_info` | `(stack_id: int) -> str` | Get stack info | `am stack info <id>` |
| `suppress_resize_config_changes` | `(suppress: bool) -> None` | Suppress resize config changes | `am suppress-resize-config-changes true\|false` |
| `start_activity_as_user` | `(component: str, user_id: int, wait: bool = False) -> str` | Start activity as a specific user | `am start [-W] --user <id> -n <comp>` |

---

### logcat -- LogcatManager

Access: `adb.logcat`

| Method | Signature | Description | ADB Command |
|---|---|---|---|
| `dump` | `(tags: Optional[List[str]] = None, priority: Optional[str] = None, format: str = "threadtime", max_count: Optional[int] = None, since: Optional[str] = None, buffer: Optional[str] = None) -> List[LogcatEntry]` | Dump logcat and parse into entries | `logcat -d [-v fmt] [-b buf] [-m count] [-T since] [tag:pri]` |
| `dump_raw` | `(tags: Optional[List[str]] = None, priority: Optional[str] = None, max_count: Optional[int] = None, buffer: Optional[str] = None) -> List[str]` | Dump logcat as raw lines | `logcat -d [filters]` |
| `clear` | `() -> None` | Clear the log buffer | `logcat -c` |
| `stream` | `(tags: Optional[List[str]] = None, priority: Optional[str] = None, format: str = "threadtime", buffer: Optional[str] = None) -> Iterator[LogcatEntry]` | Stream logcat entries in real time | `logcat [filters]` (streaming) |
| `stream_raw` | `(tags: Optional[List[str]] = None, priority: Optional[str] = None, buffer: Optional[str] = None) -> Iterator[str]` | Stream raw logcat lines | `logcat [filters]` (streaming) |
| `dump_crash` | `() -> List[LogcatEntry]` | Dump crash log buffer | `logcat -d -b crash` |
| `save_to_file` | `(filepath: str, tags: Optional[List[str]] = None, priority: Optional[str] = None, buffer: Optional[str] = None) -> None` | Save logcat output to a local file | `logcat -d` + write to file |
| `dump_ace_logs` | `() -> List[LogcatEntry]` | Dump logs for the ACE tag | `logcat -d -s ACE` |
| `dump_atg_logs` | `() -> List[LogcatEntry]` | Dump logs for the ATG tag | `logcat -d -s ATG` |
| `dump_ace_atg_logs` | `() -> List[LogcatEntry]` | Dump ACE and ATG logs | `logcat -d -s ACE ATG` |
| `get_log_buffers` | `() -> List[str]` | List available log buffers | `logcat -g` |
| `get_log_size` | `(buffer: str = "main") -> str` | Get buffer size info | `logcat -g -b <buffer>` |

Priority levels: `V` (Verbose), `D` (Debug), `I` (Info), `W` (Warn), `E` (Error), `F` (Fatal), `S` (Silent)

---

### network -- NetworkManager

Access: `adb.network`

| Method | Signature | Description | ADB Command |
|---|---|---|---|
| `forward` | `(local: str, remote: str, no_rebind: bool = False) -> None` | Set up port forwarding | `adb forward [--no-rebind] <local> <remote>` |
| `forward_tcp` | `(local_port: int, remote_port: int, no_rebind: bool = False) -> None` | Forward TCP port | `adb forward tcp:<local> tcp:<remote>` |
| `reverse` | `(remote: str, local: str, no_rebind: bool = False) -> None` | Set up reverse port forwarding | `adb reverse [--no-rebind] <remote> <local>` |
| `reverse_tcp` | `(remote_port: int, local_port: int, no_rebind: bool = False) -> None` | Reverse forward TCP port | `adb reverse tcp:<remote> tcp:<local>` |
| `list_forwards` | `() -> List[ForwardRule]` | List all forward rules | `adb forward --list` |
| `list_reverse` | `() -> List[ForwardRule]` | List all reverse rules | `adb reverse --list` |
| `remove_forward` | `(local: str) -> None` | Remove a forward rule | `adb forward --remove <local>` |
| `remove_forward_tcp` | `(local_port: int) -> None` | Remove TCP forward rule | `adb forward --remove tcp:<port>` |
| `remove_all_forwards` | `() -> None` | Remove all forward rules | `adb forward --remove-all` |
| `remove_reverse` | `(remote: str) -> None` | Remove a reverse rule | `adb reverse --remove <remote>` |
| `remove_reverse_tcp` | `(remote_port: int) -> None` | Remove TCP reverse rule | `adb reverse --remove tcp:<port>` |
| `remove_all_reverse` | `() -> None` | Remove all reverse rules | `adb reverse --remove-all` |
| `forward_jdwp` | `(local_port: int, pid: int) -> None` | Forward to JDWP transport | `adb forward tcp:<port> jdwp:<pid>` |
| `forward_localfilesystem` | `(local_port: int, socket_name: str) -> None` | Forward to a filesystem socket | `adb forward tcp:<port> localfilesystem:<name>` |
| `forward_localabstract` | `(local_port: int, socket_name: str) -> None` | Forward to an abstract socket | `adb forward tcp:<port> localabstract:<name>` |
| `forward_localreserved` | `(local_port: int, socket_name: str) -> None` | Forward to a reserved socket | `adb forward tcp:<port> localreserved:<name>` |
| `forward_vsock` | `(local_port: int, cid: int, remote_port: int) -> None` | Forward to a vsock | `adb forward tcp:<port> vsock:<cid>:<port>` |

---

### system_info -- SystemInfo

Access: `adb.system`

| Method | Signature | Description | ADB Command |
|---|---|---|---|
| `dumpsys` | `(service: str, args: Optional[str] = None) -> str` | Dump system service info | `dumpsys <service> [args]` |
| `list_services` | `() -> list` | List all registered services | `service list` |
| `get_battery_info` | `() -> BatteryInfo` | Get battery level, status, health, temp | `dumpsys battery` |
| `get_memory_info` | `() -> MemoryInfo` | Get RAM usage stats | `cat /proc/meminfo` |
| `get_cpu_info` | `() -> str` | Get CPU info | `cat /proc/cpuinfo` |
| `get_cpu_count` | `() -> int` | Get number of CPU cores | `nproc` |
| `get_cpu_usage` | `() -> str` | Get current CPU usage | `top -n 1 -b` |
| `get_display_size` | `() -> Tuple[int, int]` | Get display resolution | `wm size` |
| `get_display_density` | `() -> int` | Get display density (DPI) | `wm density` |
| `set_display_size` | `(width: int, height: int) -> None` | Override display size | `wm size <W>x<H>` |
| `reset_display_size` | `() -> None` | Reset display to default size | `wm size reset` |
| `set_display_density` | `(density: int) -> None` | Override display density | `wm density <dpi>` |
| `reset_display_density` | `() -> None` | Reset display density | `wm density reset` |
| `screenshot` | `(output_path: str, display_id: Optional[int] = None) -> None` | Take a screenshot | `screencap -p` + `adb pull` |
| `screenrecord` | `(output_path: str, duration: int = 180, size: Optional[str] = None, bit_rate: Optional[int] = None) -> None` | Record the screen | `screenrecord [--size] [--bit-rate] [--time-limit]` + `adb pull` |
| `get_uptime` | `() -> float` | Get device uptime in seconds | `cat /proc/uptime` |
| `get_disk_usage` | `(path: str = "/") -> Dict[str, str]` | Get disk usage for a path | `df -h <path>` |
| `get_kernel_version` | `() -> str` | Get kernel version string | `uname -r` |
| `get_hostname` | `() -> str` | Get device hostname | `hostname` |
| `get_ip_addresses` | `() -> Dict[str, str]` | Get IP addresses per interface | `ip addr show` |
| `get_wifi_info` | `() -> str` | Get WiFi service dump | `dumpsys wifi` |
| `get_connectivity_info` | `() -> str` | Get connectivity service dump | `dumpsys connectivity` |
| `get_settings` | `(namespace: str, key: str) -> str` | Get a system setting | `settings get <ns> <key>` |
| `put_settings` | `(namespace: str, key: str, value: str) -> None` | Set a system setting | `settings put <ns> <key> <val>` |
| `delete_settings` | `(namespace: str, key: str) -> None` | Delete a system setting | `settings delete <ns> <key>` |
| `list_settings` | `(namespace: str) -> Dict[str, str]` | List all settings in a namespace | `settings list <ns>` |
| `reset_settings` | `(namespace: str) -> None` | Reset a settings namespace | `settings reset <ns>` |
| `get_build_props` | `() -> Dict[str, str]` | Get all build properties | `getprop` |
| `get_device_time` | `() -> str` | Get device clock time | `date` |
| `set_device_time` | `(time_str: str) -> None` | Set device clock time | `date <time>` |
| `wm_overscan` | `(left: int, top: int, right: int, bottom: int) -> None` | Set display overscan | `wm overscan <l>,<t>,<r>,<b>` |
| `wm_reset_overscan` | `() -> None` | Reset display overscan | `wm overscan reset` |
| `wm_scaling` | `(mode: str = "auto") -> None` | Set display scaling mode | `wm scaling <mode>` |
| `wm_dismiss_keyguard` | `() -> None` | Dismiss the keyguard/lockscreen | `wm dismiss-keyguard` |
| `wm_set_user_rotation` | `(mode: str = "free", rotation: Optional[int] = None) -> None` | Set user rotation mode | `wm set-user-rotation <mode> [rotation]` |
| `wm_fix_to_user_rotation` | `(state: str = "default") -> None` | Fix to user rotation | `wm set-fix-to-user-rotation <state>` |
| `get_selinux_status` | `() -> str` | Get SELinux enforcement mode | `getenforce` |
| `set_selinux_mode` | `(mode: str) -> None` | Set SELinux mode (requires root) | `setenforce <mode>` |
| `get_kernel_cmdline` | `() -> str` | Get kernel command line | `cat /proc/cmdline` |
| `service_call` | `(service: str, code: int, *args: str) -> str` | Make a raw binder service call | `service call <svc> <code> [args]` |
| `service_check` | `(service: str) -> bool` | Check if a service is running | `service check <svc>` |
| `cmd` | `(service: str, *args: str) -> str` | Run a cmd shell command | `cmd <service> [args]` |
| `cmd_overlay_enable` | `(package: str) -> None` | Enable a runtime resource overlay | `cmd overlay enable <pkg>` |
| `cmd_overlay_disable` | `(package: str) -> None` | Disable a runtime resource overlay | `cmd overlay disable <pkg>` |
| `cmd_overlay_list` | `() -> str` | List runtime resource overlays | `cmd overlay list` |
| `list_displays` | `() -> str` | Get display information | `dumpsys display` |
| `atrace_list_categories` | `() -> List[str]` | List available atrace categories | `atrace --list_categories` |
| `atrace_start` | `(categories: List[str], buffer_size: int = 2048) -> None` | Start system tracing | `atrace -b <size> <categories>` |
| `atrace_stop` | `() -> str` | Stop system tracing | `atrace --async_stop` |

Settings namespaces: `system`, `secure`, `global`

---

### file_system -- FileSystem

Access: `adb.fs`

| Method | Signature | Description | ADB Command |
|---|---|---|---|
| `ls` | `(path: str = "/", show_all: bool = True) -> List[FileInfo]` | List directory contents | `ls -la <path>` |
| `exists` | `(path: str) -> bool` | Check if a path exists | `[ -e <path> ]` |
| `is_file` | `(path: str) -> bool` | Check if path is a regular file | `[ -f <path> ]` |
| `is_directory` | `(path: str) -> bool` | Check if path is a directory | `[ -d <path> ]` |
| `mkdir` | `(path: str, parents: bool = False) -> None` | Create a directory | `mkdir [-p] <path>` |
| `rm` | `(path: str, recursive: bool = False, force: bool = False) -> None` | Remove a file or directory | `rm [-rf] <path>` |
| `cp` | `(src: str, dst: str, recursive: bool = False) -> None` | Copy files | `cp [-r] <src> <dst>` |
| `mv` | `(src: str, dst: str) -> None` | Move or rename files | `mv <src> <dst>` |
| `chmod` | `(path: str, mode: str) -> None` | Change file permissions | `chmod <mode> <path>` |
| `chown` | `(path: str, owner: str, group: Optional[str] = None) -> None` | Change file ownership | `chown <owner>[:<group>] <path>` |
| `cat` | `(path: str) -> str` | Read file contents | `cat <path>` |
| `stat` | `(path: str) -> FileInfo` | Get file info (permissions, size, dates) | `ls -ld <path>` |
| `find` | `(path: str, name: Optional[str] = None, file_type: Optional[str] = None, max_depth: Optional[int] = None) -> List[str]` | Find files | `find <path> [-maxdepth n] [-type t] [-name 'pattern']` |
| `touch` | `(path: str) -> None` | Create empty file or update timestamp | `touch <path>` |
| `readlink` | `(path: str) -> str` | Resolve symlink target | `readlink -f <path>` |
| `du` | `(path: str, human_readable: bool = True) -> str` | Get disk usage of a path | `du [-h] <path>` |
| `head` | `(path: str, lines: int = 10) -> str` | Read first N lines of a file | `head -n <N> <path>` |
| `tail` | `(path: str, lines: int = 10) -> str` | Read last N lines of a file | `tail -n <N> <path>` |
| `grep` | `(pattern: str, path: str, recursive: bool = False) -> List[str]` | Search for pattern in files | `grep [-r] '<pattern>' <path>` |
| `wc` | `(path: str) -> dict` | Count lines, words, bytes | `wc <path>` |

---

### file_transfer -- FileTransfer

Access: `adb.files`

| Method | Signature | Description | ADB Command |
|---|---|---|---|
| `push` | `(local_path: str, remote_path: str, sync: bool = False, compress: Optional[str] = None, no_compress: bool = False) -> None` | Push file to device | `adb push [--sync] [-z algo\|-Z] <local> <remote>` |
| `pull` | `(remote_path: str, local_path: str, preserve_attrs: bool = False, compress: Optional[str] = None, no_compress: bool = False) -> None` | Pull file from device | `adb pull [-a] [-z algo\|-Z] <remote> <local>` |
| `push_dir` | `(local_dir: str, remote_dir: str) -> None` | Push entire directory | `adb push <local_dir> <remote_dir>` |
| `pull_dir` | `(remote_dir: str, local_dir: str) -> None` | Pull entire directory | `adb pull <remote_dir> <local_dir>` |
| `sync` | `(partition: Optional[str] = None, list_only: bool = False, compress: Optional[str] = None, no_compress: bool = False) -> None` | Sync local to device | `adb sync [-l] [-z algo\|-Z] [partition]` |
| `push_multiple` | `(file_pairs: list) -> None` | Push multiple files. Each pair: `(local, remote)` | Multiple `adb push` calls |
| `pull_multiple` | `(file_pairs: list) -> None` | Pull multiple files. Each pair: `(remote, local)` | Multiple `adb pull` calls |

---

### input_sim -- InputSimulator

Access: `adb.input`

| Method | Signature | Description | ADB Command |
|---|---|---|---|
| `tap` | `(x: int, y: int) -> None` | Tap at coordinates | `input tap <x> <y>` |
| `double_tap` | `(x: int, y: int, interval_ms: int = 100) -> None` | Double tap at coordinates | Two `input tap` calls |
| `long_press` | `(x: int, y: int, duration_ms: int = 1000) -> None` | Long press at coordinates | `input swipe <x> <y> <x> <y> <duration>` |
| `swipe` | `(x1: int, y1: int, x2: int, y2: int, duration_ms: int = 300) -> None` | Swipe from point to point | `input swipe <x1> <y1> <x2> <y2> <duration>` |
| `swipe_up` | `(x: int = 540, start_y: int = 1500, end_y: int = 500, duration_ms: int = 300) -> None` | Swipe upward | `input swipe` |
| `swipe_down` | `(x: int = 540, start_y: int = 500, end_y: int = 1500, duration_ms: int = 300) -> None` | Swipe downward | `input swipe` |
| `swipe_left` | `(y: int = 960, start_x: int = 900, end_x: int = 100, duration_ms: int = 300) -> None` | Swipe left | `input swipe` |
| `swipe_right` | `(y: int = 960, start_x: int = 100, end_x: int = 900, duration_ms: int = 300) -> None` | Swipe right | `input swipe` |
| `pinch_in` | `(cx: int, cy: int, distance: int = 200, duration_ms: int = 300) -> None` | Pinch in gesture | `input swipe` |
| `pinch_out` | `(cx: int, cy: int, distance: int = 200, duration_ms: int = 300) -> None` | Pinch out gesture | `input swipe` |
| `key_event` | `(keycode: Union[int, str]) -> None` | Send a key event | `input keyevent <code>` |
| `key_events` | `(keycodes: list) -> None` | Send multiple key events in sequence | Multiple `input keyevent` calls |
| `text` | `(text: str) -> None` | Type text (special chars escaped) | `input text '<text>'` |
| `press_home` | `() -> None` | Press Home button | `input keyevent 3` |
| `press_back` | `() -> None` | Press Back button | `input keyevent 4` |
| `press_power` | `() -> None` | Press Power button | `input keyevent 26` |
| `press_volume_up` | `() -> None` | Press Volume Up | `input keyevent 24` |
| `press_volume_down` | `() -> None` | Press Volume Down | `input keyevent 25` |
| `press_enter` | `() -> None` | Press Enter | `input keyevent 66` |
| `press_delete` | `() -> None` | Press Delete/Backspace | `input keyevent 67` |
| `press_tab` | `() -> None` | Press Tab | `input keyevent 61` |
| `press_menu` | `() -> None` | Press Menu | `input keyevent 82` |
| `press_app_switch` | `() -> None` | Press App Switch (Recent Apps) | `input keyevent 187` |
| `press_search` | `() -> None` | Press Search | `input keyevent 84` |
| `press_camera` | `() -> None` | Press Camera | `input keyevent 27` |
| `open_notifications` | `() -> None` | Open notification shade | `cmd statusbar expand-notifications` |
| `close_notifications` | `() -> None` | Close notification shade | `cmd statusbar collapse` |
| `open_quick_settings` | `() -> None` | Open quick settings panel | `cmd statusbar expand-settings` |
| `toggle_wifi` | `() -> None` | Enable WiFi | `svc wifi enable` |
| `set_wifi` | `(enabled: bool) -> None` | Enable or disable WiFi | `svc wifi enable\|disable` |
| `set_mobile_data` | `(enabled: bool) -> None` | Enable or disable mobile data | `svc data enable\|disable` |
| `set_airplane_mode` | `(enabled: bool) -> None` | Enable or disable airplane mode | `settings put global airplane_mode_on` + broadcast |
| `wake_up` | `() -> None` | Wake up the device | `input keyevent 224` |
| `sleep` | `() -> None` | Put device to sleep | `input keyevent 223` |
| `unlock_screen` | `() -> None` | Unlock screen (menu + swipe up) | `input keyevent 82` + swipe |
| `media_play_pause` | `() -> None` | Toggle media playback | `input keyevent 85` |
| `media_next` | `() -> None` | Skip to next track | `input keyevent 87` |
| `media_previous` | `() -> None` | Go to previous track | `input keyevent 88` |
| `set_brightness` | `(value: int) -> None` | Set screen brightness (0-255) | `settings put system screen_brightness <val>` |
| `set_screen_timeout` | `(ms: int) -> None` | Set screen off timeout | `settings put system screen_off_timeout <ms>` |
| `rotate_screen` | `(rotation: int = 0) -> None` | Set screen rotation (0=0, 1=90, 2=180, 3=270) | `settings put system user_rotation <val>` |
| `auto_rotate` | `(enabled: bool = True) -> None` | Enable or disable auto-rotate | `settings put system accelerometer_rotation 0\|1` |
| `long_press_key` | `(keycode: Union[int, str]) -> None` | Long press a key | `input keyevent --longpress <code>` |
| `drag_and_drop` | `(x1: int, y1: int, x2: int, y2: int, duration_ms: int = 1000) -> None` | Drag from one point to another | `input draganddrop <x1> <y1> <x2> <y2> <dur>` |
| `roll` | `(dx: int, dy: int) -> None` | Simulate trackball roll | `input roll <dx> <dy>` |
| `motion_event` | `(action: str, x: int, y: int) -> None` | Send a raw motion event | `input motionevent <action> <x> <y>` |
| `key_combination` | `(*keycodes: Union[int, str]) -> None` | Send a key combination (multiple keys at once) | `input keycombination <codes>` |
| `press` | `() -> None` | Send generic press event | `input press` |

---

### content_provider -- ContentProvider

Access: `adb.content`

| Method | Signature | Description | ADB Command |
|---|---|---|---|
| `query` | `(uri: str, projection: Optional[List[str]] = None, where: Optional[str] = None, sort: Optional[str] = None) -> str` | Query a content provider | `content query --uri <uri> [--projection cols] [--where cond] [--sort order]` |
| `insert` | `(uri: str, bindings: Dict[str, str]) -> str` | Insert a row into a content provider | `content insert --uri <uri> --bind key:s:val ...` |
| `update` | `(uri: str, bindings: Dict[str, str], where: Optional[str] = None) -> str` | Update rows in a content provider | `content update --uri <uri> --bind key:s:val [--where cond]` |
| `delete` | `(uri: str, where: Optional[str] = None) -> str` | Delete rows from a content provider | `content delete --uri <uri> [--where cond]` |
| `call` | `(uri: str, method: str, arg: Optional[str] = None) -> str` | Call a content provider method | `content call --uri <uri> --method <m> [--arg val]` |
| `read` | `(uri: str) -> str` | Read content from a URI | `content read --uri <uri>` |

---

### app_ops -- AppOpsManager

Access: `adb.appops`

| Method | Signature | Description | ADB Command |
|---|---|---|---|
| `set_op` | `(package: str, op: str, mode: str) -> None` | Set an app operation mode | `appops set <pkg> <op> <mode>` |
| `get_op` | `(package: str, op: str) -> str` | Get an app operation mode | `appops get <pkg> <op>` |
| `get_ops` | `(package: str) -> str` | Get all app operations for a package | `appops get <pkg>` |
| `reset` | `(package: Optional[str] = None) -> None` | Reset app operations | `appops reset [pkg]` |
| `allow` | `(package: str, op: str) -> None` | Allow an app operation | `appops set <pkg> <op> allow` |
| `deny` | `(package: str, op: str) -> None` | Deny an app operation | `appops set <pkg> <op> deny` |
| `ignore` | `(package: str, op: str) -> None` | Set app operation to ignore | `appops set <pkg> <op> ignore` |
| `default` | `(package: str, op: str) -> None` | Reset app operation to default | `appops set <pkg> <op> default` |
| `query` | `(op: str) -> str` | Query packages using an operation | `appops query-op <op>` |

---

### backup_manager -- BackupManager

Access: `adb.backup_mgr`

| Method | Signature | Description | ADB Command |
|---|---|---|---|
| `backup_now` | `(package: str) -> str` | Trigger immediate backup for a package | `bmgr backupnow <pkg>` |
| `restore` | `(token: str) -> str` | Restore from a backup token | `bmgr restore <token>` |
| `list_transports` | `() -> List[str]` | List available backup transports | `bmgr list transports` |
| `list_sets` | `() -> List[str]` | List available restore sets | `bmgr list sets` |
| `transport` | `(transport_name: str) -> str` | Select a backup transport | `bmgr transport <name>` |
| `enable` | `(enabled: bool) -> None` | Enable or disable backup | `bmgr enabled true\|false` |
| `is_enabled` | `() -> bool` | Check if backup is enabled | `bmgr enabled` |
| `run_backup` | `() -> str` | Run a scheduled backup pass | `bmgr run` |
| `wipe` | `(transport: str, package: str) -> str` | Wipe backup data for a package | `bmgr wipe <transport> <pkg>` |
| `full_backup` | `(package: str) -> str` | Perform a full backup of a package | `bmgr fullbackup <pkg>` |

---

### device_policy -- DevicePolicyManager

Access: `adb.dpm`

| Method | Signature | Description | ADB Command |
|---|---|---|---|
| `set_device_owner` | `(component: str) -> str` | Set the device owner admin | `dpm set-device-owner <comp>` |
| `set_profile_owner` | `(component: str, user_id: Optional[int] = None) -> str` | Set a profile owner admin | `dpm set-profile-owner [--user id] <comp>` |
| `remove_active_admin` | `(component: str) -> str` | Remove an active device admin | `dpm remove-active-admin <comp>` |
| `list_owners` | `() -> str` | List device and profile owners | `dumpsys device_policy` |
| `set_user_restriction` | `(restriction: str, enabled: bool) -> None` | Set a user restriction | `dpm set-user-restriction <restriction> 0\|1` |
| `get_user_restrictions` | `() -> str` | Get current user restrictions | `dumpsys user` |

---

### ace_operations -- ACEOperations

Access: `adb.ace`

See the [ACE-Specific Operations](#ace-specific-operations) section below for full documentation.

---

## Release Build

### APKBuilder

Builds the Android APK components of the AceTheGame project using Gradle.

```python
from ADB_API import APKBuilder
builder = APKBuilder(project_root="/path/to/AceTheGame")
```

| Method | Signature | Description |
|---|---|---|
| `build_atg_debug` | `(output_dir: Optional[str] = None) -> BuildResult` | Build ATG in debug mode |
| `build_atg_release` | `(output_dir: Optional[str] = None) -> BuildResult` | Build ATG in release mode |
| `build_billing_hack_debug` | `(output_dir: Optional[str] = None) -> BuildResult` | Build BillingHack in debug mode |
| `build_billing_hack_release` | `(output_dir: Optional[str] = None) -> BuildResult` | Build BillingHack in release mode |
| `build_modder` | `(output_dir: Optional[str] = None) -> BuildResult` | Build Modder distribution (runs gen_smali.py first) |

### ACEBuilder

Builds the ACE native engine using CMake for Linux and Android targets.

```python
from ADB_API import ACEBuilder
builder = ACEBuilder(project_root="/path/to/AceTheGame")
```

| Method | Signature | Description |
|---|---|---|
| `build_linux` | `(output_dir: Optional[str] = None, build_dir: str = "./build", cpu_count: Optional[int] = None) -> BuildResult` | Build ACE for Linux x86_64 |
| `build_android` | `(toolchain_path: str, arch: str, output_dir: Optional[str] = None, build_dir: str = "./build", cpu_count: Optional[int] = None) -> BuildResult` | Build ACE for a specific Android ABI |
| `build_android_all_archs` | `(toolchain_path: str, output_dir: Optional[str] = None, build_dir: str = "./build", cpu_count: Optional[int] = None) -> Dict[str, BuildResult]` | Build ACE for all Android ABIs |

Supported Android ABIs: `armeabi-v7a`, `arm64-v8a`, `x86`, `x86_64`

### ReleasePipeline

Orchestrates building all components for a full release.

Access: `adb.release` or standalone:

```python
from ADB_API import ReleasePipeline
pipeline = ReleasePipeline(project_root="/path/to/AceTheGame")
```

| Property/Method | Signature | Description |
|---|---|---|
| `apk` | `-> APKBuilder` | Access the APK builder instance |
| `ace` | `-> ACEBuilder` | Access the ACE builder instance |
| `build_full_release` | `(android_toolchain_file: str, release_dir: Optional[str] = None, build_atg: bool = True, build_billing: bool = True, build_modder: bool = True, build_ace_linux: bool = True, build_ace_android: bool = True, on_progress: Optional[Callable[[str, str], None]] = None) -> ReleaseResult` | Build all components |
| `build_deploy` | `(android_toolchain_file: str, target_pid: int, adb_instance=None, release_dir: Optional[str] = None) -> ReleaseResult` | Build ACE + ATG, then deploy to device and attach to process |
| `clean_build_artifacts` | `() -> None` | Remove all build and release directories |

Full release example:

```python
from ADB_API import ADB

adb = ADB()
result = adb.release.build_full_release(
    android_toolchain_file="/path/to/android.toolchain.cmake",
    release_dir="./release_output",
    on_progress=lambda comp, status: print(f"{comp}: {status}"),
)
print(f"Success: {result.success}")
for name, br in result.components.items():
    print(f"  {name}: {'OK' if br.success else br.error}")
```

Build and deploy to a running device:

```python
result = adb.release.build_deploy(
    android_toolchain_file="/path/to/android.toolchain.cmake",
    target_pid=12345,
    adb_instance=adb,
)
```

---

## Data Models

All models are Python `dataclasses` defined in `models.py`.

### CommandResult

Result of every ADB command execution.

```python
@dataclass
class CommandResult:
    stdout: str                       # Raw stdout
    stderr: str                       # Raw stderr
    return_code: int                  # Process exit code
    lines: List[str]                  # stdout split into non-empty lines (auto-populated)

    @property
    def success(self) -> bool         # True if return_code == 0

    @property
    def output(self) -> str           # stdout.strip()
```

### DeviceInfo

Represents a connected device from `adb devices -l`.

```python
@dataclass
class DeviceInfo:
    serial: str                       # Device serial number
    state: str                        # "device", "offline", "unauthorized", etc.
    model: Optional[str]              # Device model name
    product: Optional[str]            # Product name
    transport_id: Optional[str]       # Transport ID
```

### PackageInfo

Package metadata from `dumpsys package`.

```python
@dataclass
class PackageInfo:
    package_name: str                 # Package identifier
    apk_paths: List[str]             # APK file paths on device
    version_code: Optional[str]       # versionCode
    version_name: Optional[str]       # versionName
    installer: Optional[str]          # Installer package name
```

### ProcessInfo

Process information from `ps`.

```python
@dataclass
class ProcessInfo:
    pid: int                          # Process ID
    ppid: int = 0                     # Parent process ID
    name: str = ""                    # Process name
    user: str = ""                    # User running the process
    state: Optional[str] = None       # Process state
```

### ForwardRule

Port forwarding rule.

```python
@dataclass
class ForwardRule:
    serial: str                       # Device serial
    local: str                        # Local endpoint (e.g. "tcp:8080")
    remote: str                       # Remote endpoint (e.g. "tcp:80")
```

### DeviceProperties

Aggregated device properties.

```python
@dataclass
class DeviceProperties:
    model: str = ""                   # ro.product.model
    manufacturer: str = ""            # ro.product.manufacturer
    android_version: str = ""         # ro.build.version.release
    sdk_level: int = 0                # ro.build.version.sdk
    abi: str = ""                     # ro.product.cpu.abi
    serial: str = ""                  # Device serial
    build_fingerprint: str = ""       # ro.build.fingerprint
```

### FileInfo

File metadata from `ls -l`.

```python
@dataclass
class FileInfo:
    path: str                         # Full file path
    permissions: str = ""             # Permission string (e.g. "-rwxr-xr-x")
    owner: str = ""                   # File owner
    group: str = ""                   # File group
    size: int = 0                     # File size in bytes
    date: str = ""                    # Last modified date
    is_directory: bool = False        # True if directory
    is_symlink: bool = False          # True if symbolic link
```

### BatteryInfo

Battery status from `dumpsys battery`.

```python
@dataclass
class BatteryInfo:
    level: int = 0                    # Battery percentage (0-100)
    status: str = ""                  # "charging", "discharging", "full", etc.
    health: str = ""                  # "good", "overheat", "dead", etc.
    temperature: float = 0.0          # Temperature in Celsius
    voltage: float = 0.0             # Voltage in volts
    plugged: str = ""                 # "ac", "usb", "wireless", "unplugged"
```

### MemoryInfo

RAM usage from `/proc/meminfo`.

```python
@dataclass
class MemoryInfo:
    total_ram: int = 0                # Total RAM in bytes
    free_ram: int = 0                 # Free RAM in bytes
    used_ram: int = 0                 # Used RAM in bytes (total - available)
    available_ram: int = 0            # Available RAM in bytes
```

### LogcatEntry

A single parsed logcat line.

```python
@dataclass
class LogcatEntry:
    timestamp: str = ""               # Timestamp string
    pid: int = 0                      # Process ID
    tid: int = 0                      # Thread ID
    priority: str = ""                # V/D/I/W/E/F/S
    tag: str = ""                     # Log tag
    message: str = ""                 # Log message
```

### ACEServerInfo

Information about a running ACE server instance.

```python
@dataclass
class ACEServerInfo:
    pid: int = 0                      # ACE server process ID
    engine_port: int = 0              # Engine communication port
    status_publisher_port: int = 0    # Status publisher port
    binary_path: str = ""             # Path to ACE binary on device
```

### BuildResult

Result of a single build operation.

```python
@dataclass
class BuildResult:
    success: bool                     # Whether the build succeeded
    component: str                    # Component name (e.g. "ATG", "ACE-linux")
    output_path: str = ""             # Output directory or file path
    build_type: str = ""              # "debug", "release", "distribution"
    error: str = ""                   # Error message if failed
    artifacts: List[str]              # List of produced file paths
```

### ReleaseResult

Result of a full release pipeline run.

```python
@dataclass
class ReleaseResult:
    success: bool                     # True if all components built successfully
    components: Dict[str, BuildResult]  # Per-component results
    release_dir: str = ""             # Release output directory

    @property
    def failed(self) -> List[str]     # Names of failed components
```

---

## Exceptions

All exceptions inherit from `ADBError`. Import them from `ADB_API` or `ADB_API.exceptions`.

| Exception | Raised When | Attributes |
|---|---|---|
| `ADBError` | Base class for all ADB errors | -- |
| `ADBNotFoundError` | `adb` binary not found in PATH or common locations | `searched_paths: Optional[List[str]]` |
| `DeviceNotFoundError` | No device connected or specified serial not found | `serial: Optional[str]` |
| `MultipleDevicesError` | Multiple devices connected and no serial specified | `devices: List[str]` |
| `CommandTimeoutError` | Command exceeded timeout | `command: str`, `timeout: int` |
| `CommandFailedError` | Command exited with non-zero code (when `check=True`) | `command: str`, `return_code: int`, `stdout: str`, `stderr: str` |
| `DeviceOfflineError` | Device is connected but offline | `serial: str` |
| `PermissionDeniedError` | Operation requires higher privileges | `operation: str` |
| `FileTransferError` | Push or pull operation failed | `operation: str`, `local_path: str`, `remote_path: str` |
| `PackageInstallError` | APK installation failed | `package: str`, `detail: str` |
| `ShellCommandError` | Shell command produced an error | `command: str`, `output: str` |
| `DeviceNotRootedError` | Operation requires root but device is not rooted | -- |
| `ACEOperationError` | ACE-specific operation failed | `operation: str`, `detail: str` |

Exception hierarchy:

```
ADBError
  +-- ADBNotFoundError
  +-- DeviceNotFoundError
  +-- MultipleDevicesError
  +-- CommandTimeoutError
  +-- CommandFailedError
  +-- DeviceOfflineError
  +-- PermissionDeniedError
  +-- FileTransferError
  +-- PackageInstallError
  +-- ShellCommandError
  +-- DeviceNotRootedError
  +-- ACEOperationError
```

---

## ADB Command Mapping

Comprehensive mapping of `adb` CLI commands to their Python method equivalents.

### Server and Connection

| ADB Command | Python Method |
|---|---|
| `adb version` | `adb.version()` |
| `adb start-server` | `adb.start_server()` |
| `adb kill-server` | `adb.kill_server()` |
| `adb devices -l` | `adb.device.list_devices()` |
| `adb connect <host>:<port>` | `adb.device.connect(host, port)` |
| `adb disconnect [host]` | `adb.device.disconnect(host)` |
| `adb pair <host>:<port> <code>` | `adb.pair(host, port, pairing_code)` |
| `adb reconnect [mode]` | `adb.reconnect(mode)` |
| `adb wait-for-device` | `adb.wait_for_device(timeout)` |
| `adb wait-for-recovery` | `adb.device.wait_for_recovery(timeout)` |
| `adb wait-for-sideload` | `adb.device.wait_for_sideload(timeout)` |
| `adb wait-for-bootloader` | `adb.device.wait_for_bootloader(timeout)` |
| `adb wait-for-disconnect` | `adb.device.wait_for_disconnect(timeout)` |
| `adb usb` | `adb.usb()` |
| `adb tcpip <port>` | `adb.tcpip(port)` |
| `adb mdns check` | `adb.device.mdns_check()` |
| `adb mdns services` | `adb.device.mdns_services()` |

### Device Info

| ADB Command | Python Method |
|---|---|
| `adb get-state` | `adb.get_state()` |
| `adb get-serialno` | `adb.device.get_serial()` |
| `adb get-devpath` | `adb.get_devpath()` |
| `adb shell getprop <prop>` | `adb.device.get_property(prop)` |
| `adb shell setprop <prop> <val>` | `adb.device.set_property(prop, val)` |
| `adb shell getprop` | `adb.system.get_build_props()` |
| `adb shell wm size` | `adb.device.get_display_resolution()` / `adb.system.get_display_size()` |
| `adb shell wm density` | `adb.system.get_display_density()` |
| `adb shell dumpsys battery` | `adb.system.get_battery_info()` |
| `adb shell cat /proc/meminfo` | `adb.system.get_memory_info()` |
| `adb shell cat /proc/cpuinfo` | `adb.system.get_cpu_info()` |
| `adb shell nproc` | `adb.system.get_cpu_count()` |
| `adb shell uname -r` | `adb.system.get_kernel_version()` |
| `adb shell hostname` | `adb.system.get_hostname()` |
| `adb shell ip addr show` | `adb.system.get_ip_addresses()` |
| `adb shell service list` | `adb.system.list_services()` |
| `adb shell dumpsys <service>` | `adb.system.dumpsys(service)` |
| `adb shell getenforce` | `adb.system.get_selinux_status()` |
| `adb shell setenforce <mode>` | `adb.system.set_selinux_mode(mode)` |

### Privileged Operations

| ADB Command | Python Method |
|---|---|
| `adb root` | `adb.root()` |
| `adb unroot` | `adb.unroot()` |
| `adb remount` | `adb.remount()` |
| `adb reboot [mode]` | `adb.device.reboot(mode)` |
| `adb disable-verity` | `adb.disable_verity()` |
| `adb enable-verity` | `adb.enable_verity()` |
| `adb sideload <file>` | `adb.sideload(filepath)` |

### Shell Execution

| ADB Command | Python Method |
|---|---|
| `adb shell <command>` | `adb.shell(command)` |
| `adb shell su -c <command>` | `adb.shell(command, as_root=True)` |
| `adb exec-out <command>` | `adb.exec_out(command)` |
| `adb emu <command>` | `adb.emu(command)` |
| `adb jdwp` | `adb.jdwp()` |
| `adb bugreport <path>` | `adb.bugreport(output_path)` |

### File Transfer

| ADB Command | Python Method |
|---|---|
| `adb push <local> <remote>` | `adb.push(local, remote)` / `adb.files.push(local, remote)` |
| `adb pull <remote> <local>` | `adb.pull(remote, local)` / `adb.files.pull(remote, local)` |
| `adb push --sync <local> <remote>` | `adb.files.push(local, remote, sync=True)` |
| `adb pull -a <remote> <local>` | `adb.files.pull(remote, local, preserve_attrs=True)` |
| `adb sync [partition]` | `adb.files.sync(partition)` |

### Package Management

| ADB Command | Python Method |
|---|---|
| `adb install [-r] [-d] [-g] [-t] <apk>` | `adb.install(apk)` / `adb.packages.install(apk, ...)` |
| `adb uninstall [-k] <pkg>` | `adb.uninstall(pkg)` / `adb.packages.uninstall(pkg, ...)` |
| `adb install-multiple <apks>` | `adb.packages.install_multiple(apk_dir)` |
| `adb install-multi-package <apks>` | `adb.install_multi_package(apk_paths)` |
| `pm list packages [-s\|-3\|-e\|-d]` | `adb.packages.list_packages(show_only=...)` |
| `pm path <pkg>` | `adb.packages.get_apk_paths(pkg)` |
| `pm clear <pkg>` | `adb.packages.clear_data(pkg)` |
| `pm enable <pkg>` | `adb.packages.enable(pkg)` |
| `pm disable-user <pkg>` | `adb.packages.disable(pkg)` |
| `pm grant <pkg> <perm>` | `adb.packages.grant_permission(pkg, perm)` |
| `pm revoke <pkg> <perm>` | `adb.packages.revoke_permission(pkg, perm)` |
| `pm list features` | `adb.packages.list_features()` |
| `pm list libraries` | `adb.packages.list_libraries()` |
| `pm list users` | `adb.packages.list_users()` |
| `pm dump <pkg>` | `adb.packages.dump(pkg)` |
| `pm hide <pkg>` | `adb.packages.hide(pkg)` |
| `pm unhide <pkg>` | `adb.packages.unhide(pkg)` |
| `pm suspend <pkg>` | `adb.packages.suspend(pkg)` |
| `pm unsuspend <pkg>` | `adb.packages.unsuspend(pkg)` |
| `pm create-user <name>` | `adb.packages.create_user(name)` |
| `pm remove-user <id>` | `adb.packages.remove_user(id)` |
| `pm get-max-users` | `adb.packages.get_max_users()` |
| `pm get-install-location` | `adb.packages.get_install_location()` |
| `pm set-install-location <loc>` | `adb.packages.set_install_location(loc)` |
| `pm move-package <pkg> <vol>` | `adb.packages.move_package(pkg, vol)` |
| `pm trim-caches <space>` | `adb.packages.trim_caches(space)` |
| `pm reset-permissions` | `adb.packages.reset_permissions()` |
| `cmd package compile -m <mode> <pkg>` | `adb.packages.compile_package(pkg, mode)` |
| `cmd package compile -m <mode> -a` | `adb.packages.compile_all(mode)` |
| `cmd package force-dex-opt <pkg>` | `adb.packages.force_dex_opt(pkg)` |
| `cmd package bg-dexopt-job` | `adb.packages.bg_dexopt_job()` |

### Activity Manager

| ADB Command | Python Method |
|---|---|
| `am start [-W] -n <comp>` | `adb.activity.start_activity(comp, wait=True)` |
| `am startservice -n <comp>` | `adb.activity.start_service(comp)` |
| `am stopservice -n <comp>` | `adb.activity.stop_service(comp)` |
| `am broadcast -a <action>` | `adb.activity.send_broadcast(action)` |
| `am force-stop <pkg>` | `adb.activity.force_stop(pkg)` |
| `am kill <pkg>` | `adb.activity.kill(pkg)` |
| `am kill-all` | `adb.activity.kill_all()` |
| `am instrument -w <comp>` | `adb.activity.start_instrumentation(comp)` |
| `am set-debug-app <pkg>` | `adb.activity.set_debug_app(pkg)` |
| `am clear-debug-app` | `adb.activity.clear_debug_app()` |
| `am profile start <proc> <file>` | `adb.activity.profile_start(proc, file)` |
| `am profile stop <proc>` | `adb.activity.profile_stop(proc)` |
| `am dumpheap <proc> <file>` | `adb.activity.dumpheap(proc, file)` |
| `am switch-user <id>` | `adb.activity.switch_user(id)` |
| `am get-current-user` | `adb.activity.get_current_user()` |
| `am restart` | `adb.activity.restart()` |

### Port Forwarding

| ADB Command | Python Method |
|---|---|
| `adb forward tcp:<l> tcp:<r>` | `adb.network.forward_tcp(l, r)` |
| `adb forward --list` | `adb.network.list_forwards()` |
| `adb forward --remove tcp:<port>` | `adb.network.remove_forward_tcp(port)` |
| `adb forward --remove-all` | `adb.network.remove_all_forwards()` |
| `adb reverse tcp:<r> tcp:<l>` | `adb.network.reverse_tcp(r, l)` |
| `adb reverse --list` | `adb.network.list_reverse()` |
| `adb reverse --remove tcp:<port>` | `adb.network.remove_reverse_tcp(port)` |
| `adb reverse --remove-all` | `adb.network.remove_all_reverse()` |
| `adb forward tcp:<p> jdwp:<pid>` | `adb.network.forward_jdwp(p, pid)` |
| `adb forward tcp:<p> localabstract:<s>` | `adb.network.forward_localabstract(p, s)` |

### Input Simulation

| ADB Command | Python Method |
|---|---|
| `input tap <x> <y>` | `adb.input.tap(x, y)` |
| `input swipe <x1> <y1> <x2> <y2> <dur>` | `adb.input.swipe(x1, y1, x2, y2, dur)` |
| `input text '<text>'` | `adb.input.text(text)` |
| `input keyevent <code>` | `adb.input.key_event(code)` |
| `input keyevent 3` (HOME) | `adb.input.press_home()` |
| `input keyevent 4` (BACK) | `adb.input.press_back()` |
| `input keyevent 26` (POWER) | `adb.input.press_power()` |
| `input keyevent --longpress <code>` | `adb.input.long_press_key(code)` |
| `input draganddrop <x1> <y1> <x2> <y2>` | `adb.input.drag_and_drop(x1, y1, x2, y2)` |
| `input keycombination <codes>` | `adb.input.key_combination(*codes)` |

### Logcat

| ADB Command | Python Method |
|---|---|
| `logcat -d` | `adb.logcat.dump()` |
| `logcat -c` | `adb.logcat.clear()` |
| `logcat -d -b crash` | `adb.logcat.dump_crash()` |
| `logcat -d -s ACE` | `adb.logcat.dump_ace_logs()` |
| `logcat -g` | `adb.logcat.get_log_buffers()` |
| `logcat` (streaming) | `adb.logcat.stream()` |

### Settings

| ADB Command | Python Method |
|---|---|
| `settings get <ns> <key>` | `adb.system.get_settings(ns, key)` |
| `settings put <ns> <key> <val>` | `adb.system.put_settings(ns, key, val)` |
| `settings delete <ns> <key>` | `adb.system.delete_settings(ns, key)` |
| `settings list <ns>` | `adb.system.list_settings(ns)` |
| `settings reset <ns>` | `adb.system.reset_settings(ns)` |

### Content Provider

| ADB Command | Python Method |
|---|---|
| `content query --uri <uri>` | `adb.content.query(uri)` |
| `content insert --uri <uri> --bind ...` | `adb.content.insert(uri, bindings)` |
| `content update --uri <uri> --bind ...` | `adb.content.update(uri, bindings)` |
| `content delete --uri <uri>` | `adb.content.delete(uri)` |
| `content call --uri <uri> --method <m>` | `adb.content.call(uri, method)` |
| `content read --uri <uri>` | `adb.content.read(uri)` |

### App Operations

| ADB Command | Python Method |
|---|---|
| `appops set <pkg> <op> <mode>` | `adb.appops.set_op(pkg, op, mode)` |
| `appops get <pkg> <op>` | `adb.appops.get_op(pkg, op)` |
| `appops get <pkg>` | `adb.appops.get_ops(pkg)` |
| `appops reset [pkg]` | `adb.appops.reset(pkg)` |
| `appops query-op <op>` | `adb.appops.query(op)` |

### Backup Manager (bmgr)

| ADB Command | Python Method |
|---|---|
| `bmgr backupnow <pkg>` | `adb.backup_mgr.backup_now(pkg)` |
| `bmgr restore <token>` | `adb.backup_mgr.restore(token)` |
| `bmgr list transports` | `adb.backup_mgr.list_transports()` |
| `bmgr list sets` | `adb.backup_mgr.list_sets()` |
| `bmgr transport <name>` | `adb.backup_mgr.transport(name)` |
| `bmgr enabled true\|false` | `adb.backup_mgr.enable(True\|False)` |
| `bmgr run` | `adb.backup_mgr.run_backup()` |
| `bmgr wipe <transport> <pkg>` | `adb.backup_mgr.wipe(transport, pkg)` |
| `bmgr fullbackup <pkg>` | `adb.backup_mgr.full_backup(pkg)` |

### Device Policy Manager (dpm)

| ADB Command | Python Method |
|---|---|
| `dpm set-device-owner <comp>` | `adb.dpm.set_device_owner(comp)` |
| `dpm set-profile-owner <comp>` | `adb.dpm.set_profile_owner(comp)` |
| `dpm remove-active-admin <comp>` | `adb.dpm.remove_active_admin(comp)` |
| `dpm set-user-restriction <r> 0\|1` | `adb.dpm.set_user_restriction(r, True\|False)` |

### Backup/Restore (adb level)

| ADB Command | Python Method |
|---|---|
| `adb backup -f <file> [flags] [pkgs]` | `adb.backup(output_file, ...)` |
| `adb restore <file>` | `adb.restore(backup_file)` |

### Screenshot/Recording

| ADB Command | Python Method |
|---|---|
| `screencap -p <path>` + `adb pull` | `adb.system.screenshot(output_path)` |
| `screenrecord <path>` + `adb pull` | `adb.system.screenrecord(output_path, ...)` |

### Display Management (wm)

| ADB Command | Python Method |
|---|---|
| `wm size <W>x<H>` | `adb.system.set_display_size(w, h)` |
| `wm size reset` | `adb.system.reset_display_size()` |
| `wm density <dpi>` | `adb.system.set_display_density(dpi)` |
| `wm density reset` | `adb.system.reset_display_density()` |
| `wm overscan <l>,<t>,<r>,<b>` | `adb.system.wm_overscan(l, t, r, b)` |
| `wm overscan reset` | `adb.system.wm_reset_overscan()` |
| `wm dismiss-keyguard` | `adb.system.wm_dismiss_keyguard()` |

### System Tracing (atrace)

| ADB Command | Python Method |
|---|---|
| `atrace --list_categories` | `adb.system.atrace_list_categories()` |
| `atrace -b <size> <categories>` | `adb.system.atrace_start(categories, buffer_size)` |
| `atrace --async_stop` | `adb.system.atrace_stop()` |

---

## ACE-Specific Operations

The `adb.ace` sub-module provides methods for deploying and controlling the ACE memory hacking engine on Android devices. All operations require a rooted device.

### Constants

| Constant | Value | Description |
|---|---|---|
| `DEFAULT_INSTALL_PATH` | `/data/local/tmp` | Default binary install location |
| `DEFAULT_ENGINE_PORT` | `56666` | Default ACE engine TCP port |
| `DEFAULT_STATUS_PORT` | `56667` | Default status publisher TCP port |
| `ACE_BINARY_NAME` | `ACE` | ACE engine binary name |
| `CLIENT_BINARY_NAME` | `attach_client` | Client binary name |

### Methods

| Method | Signature | Description |
|---|---|---|
| `push_ace_binary` | `(local_binary_path: str, remote_path: Optional[str] = None) -> str` | Push ACE binary to device and set executable permissions. Returns remote path. |
| `push_ace_for_arch` | `(release_dir: str, arch: Optional[str] = None) -> str` | Push ACE binary for the device's architecture from a release directory. Auto-detects arch if not specified. |
| `set_ace_permissions` | `(remote_path: str) -> None` | Set executable permissions on a remote binary. |
| `start_ace_server` | `(pid: int, port: int = 56666, status_port: int = 56667, binary_path: Optional[str] = None) -> ACEServerInfo` | Start ACE engine attached to a target process. Returns server info. |
| `stop_ace_server` | `(port: int = 56666) -> None` | Stop all running ACE engine processes (SIGTERM). |
| `is_ace_running` | `() -> bool` | Check if an ACE engine process is running. |
| `get_ace_pid` | `() -> Optional[int]` | Get the PID of the running ACE engine. |
| `forward_ace_ports` | `(engine_port: int = 56666, status_port: int = 56667) -> None` | Set up TCP port forwarding for ACE communication. |
| `remove_ace_forwards` | `(engine_port: int = 56666, status_port: int = 56667) -> None` | Remove ACE port forwarding rules. |
| `list_target_processes` | `() -> List[ProcessInfo]` | List non-system processes suitable as ACE targets. |
| `check_root` | `() -> bool` | Check if the device has root access. |
| `verify_device_ready` | `() -> Dict[str, bool]` | Comprehensive readiness check. Returns dict with keys: `adb_connected`, `rooted`, `ace_binary_present`, `client_binary_present`, `ace_running`. |
| `deploy_and_start` | `(local_binary_path: str, target_pid: int, arch: Optional[str] = None, engine_port: int = 56666, status_port: int = 56667) -> ACEServerInfo` | Full deployment: push binary, forward ports, start server. Accepts a file or release directory. |
| `push_client_binary` | `(local_path: str, remote_path: Optional[str] = None) -> str` | Push the attach_client binary to device. Returns remote path. |
| `push_client_for_arch` | `(release_dir: str, arch: Optional[str] = None) -> str` | Push attach_client for the device's architecture. |
| `run_client_command` | `(command: str, port: int = 56666) -> str` | Run a command through the attach_client. Requires root. |
| `get_ace_version` | `() -> str` | Get the version of the ACE binary on device. |
| `set_aslr` | `(enabled: bool) -> None` | Enable or disable ASLR. Requires root. Writes to `/proc/sys/kernel/randomize_va_space`. |
| `get_aslr_status` | `() -> bool` | Check if ASLR is enabled. |
| `deploy_full` | `(release_dir: str, arch: Optional[str] = None) -> Dict[str, str]` | Deploy both ACE and attach_client binaries. Returns dict with keys: `ace`, `client`, `arch`. |

### Supported Architecture Mapping

| Device ABI | Mapped ABI |
|---|---|
| `arm64-v8a` / `aarch64` | `arm64-v8a` |
| `armeabi-v7a` / `armv7l` | `armeabi-v7a` |
| `x86_64` | `x86_64` |
| `x86` / `i686` | `x86` |

### Typical ACE Workflow

```python
from ADB_API import ADB

adb = ADB(device_serial="emulator-5554")

# 1. Verify the device is ready
status = adb.ace.verify_device_ready()
if not status["rooted"]:
    adb.root()

# 2. List target processes
targets = adb.ace.list_target_processes()
for t in targets:
    print(f"PID {t.pid}: {t.name}")

# 3. Deploy and attach to a game process
game_procs = adb.process.get_processes_by_name("com.example.game")
if game_procs:
    info = adb.ace.deploy_and_start(
        local_binary_path="/path/to/release",
        target_pid=game_procs[0].pid,
    )
    print(f"ACE running on port {info.engine_port}")

# 4. Send commands through the client
output = adb.ace.run_client_command("scan 100")

# 5. View ACE logs
logs = adb.logcat.dump_ace_logs()
for entry in logs:
    print(f"[{entry.priority}] {entry.message}")

# 6. Clean up
adb.ace.stop_ace_server()
adb.ace.remove_ace_forwards()
```

---

## Keycode Constants

Defined in `input_sim.py` and used with `adb.input.key_event()`:

| Constant | Value | Description |
|---|---|---|
| `KEYCODE_HOME` | 3 | Home button |
| `KEYCODE_BACK` | 4 | Back button |
| `KEYCODE_CALL` | 5 | Dial/call |
| `KEYCODE_ENDCALL` | 6 | End call |
| `KEYCODE_VOLUME_UP` | 24 | Volume up |
| `KEYCODE_VOLUME_DOWN` | 25 | Volume down |
| `KEYCODE_POWER` | 26 | Power button |
| `KEYCODE_CAMERA` | 27 | Camera button |
| `KEYCODE_MENU` | 82 | Menu button |
| `KEYCODE_ENTER` | 66 | Enter/return |
| `KEYCODE_DEL` | 67 | Delete/backspace |
| `KEYCODE_TAB` | 61 | Tab |
| `KEYCODE_SPACE` | 62 | Space |
| `KEYCODE_DPAD_UP` | 19 | D-pad up |
| `KEYCODE_DPAD_DOWN` | 20 | D-pad down |
| `KEYCODE_DPAD_LEFT` | 21 | D-pad left |
| `KEYCODE_DPAD_RIGHT` | 22 | D-pad right |
| `KEYCODE_DPAD_CENTER` | 23 | D-pad center/select |
| `KEYCODE_APP_SWITCH` | 187 | Recent apps |
| `KEYCODE_SEARCH` | 84 | Search |
| `KEYCODE_NOTIFICATION` | 83 | Notification |
| `KEYCODE_SETTINGS` | 176 | Settings |
| `KEYCODE_MEDIA_PLAY_PAUSE` | 85 | Play/pause media |
| `KEYCODE_MEDIA_STOP` | 86 | Stop media |
| `KEYCODE_MEDIA_NEXT` | 87 | Next track |
| `KEYCODE_MEDIA_PREVIOUS` | 88 | Previous track |
| `KEYCODE_MEDIA_REWIND` | 89 | Rewind media |
| `KEYCODE_MEDIA_FAST_FORWARD` | 90 | Fast forward media |
| `KEYCODE_MUTE` | 91 | Mute |
| `KEYCODE_BRIGHTNESS_UP` | 221 | Increase brightness |
| `KEYCODE_BRIGHTNESS_DOWN` | 220 | Decrease brightness |
| `KEYCODE_WAKEUP` | 224 | Wake up device |
| `KEYCODE_SLEEP` | 223 | Put device to sleep |
