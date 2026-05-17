from typing import Optional, Union

from .shell import ADBCommandRunner


KEYCODE_HOME = 3
KEYCODE_BACK = 4
KEYCODE_CALL = 5
KEYCODE_ENDCALL = 6
KEYCODE_VOLUME_UP = 24
KEYCODE_VOLUME_DOWN = 25
KEYCODE_POWER = 26
KEYCODE_CAMERA = 27
KEYCODE_MENU = 82
KEYCODE_ENTER = 66
KEYCODE_DEL = 67
KEYCODE_TAB = 61
KEYCODE_SPACE = 62
KEYCODE_DPAD_UP = 19
KEYCODE_DPAD_DOWN = 20
KEYCODE_DPAD_LEFT = 21
KEYCODE_DPAD_RIGHT = 22
KEYCODE_DPAD_CENTER = 23
KEYCODE_APP_SWITCH = 187
KEYCODE_SEARCH = 84
KEYCODE_NOTIFICATION = 83
KEYCODE_SETTINGS = 176
KEYCODE_MEDIA_PLAY_PAUSE = 85
KEYCODE_MEDIA_STOP = 86
KEYCODE_MEDIA_NEXT = 87
KEYCODE_MEDIA_PREVIOUS = 88
KEYCODE_MEDIA_REWIND = 89
KEYCODE_MEDIA_FAST_FORWARD = 90
KEYCODE_MUTE = 91
KEYCODE_BRIGHTNESS_UP = 221
KEYCODE_BRIGHTNESS_DOWN = 220
KEYCODE_WAKEUP = 224
KEYCODE_SLEEP = 223


class InputSimulator:
    def __init__(self, runner: ADBCommandRunner):
        self._runner = runner

    def tap(self, x: int, y: int) -> None:
        self._runner.run_shell(f"input tap {x} {y}")

    def double_tap(self, x: int, y: int, interval_ms: int = 100) -> None:
        self._runner.run_shell(
            f"input tap {x} {y} && sleep {interval_ms / 1000.0} && input tap {x} {y}"
        )

    def long_press(self, x: int, y: int, duration_ms: int = 1000) -> None:
        self._runner.run_shell(f"input swipe {x} {y} {x} {y} {duration_ms}")

    def swipe(
        self, x1: int, y1: int, x2: int, y2: int, duration_ms: int = 300
    ) -> None:
        self._runner.run_shell(f"input swipe {x1} {y1} {x2} {y2} {duration_ms}")

    def swipe_up(self, x: int = 540, start_y: int = 1500, end_y: int = 500, duration_ms: int = 300) -> None:
        self.swipe(x, start_y, x, end_y, duration_ms)

    def swipe_down(self, x: int = 540, start_y: int = 500, end_y: int = 1500, duration_ms: int = 300) -> None:
        self.swipe(x, start_y, x, end_y, duration_ms)

    def swipe_left(self, y: int = 960, start_x: int = 900, end_x: int = 100, duration_ms: int = 300) -> None:
        self.swipe(start_x, y, end_x, y, duration_ms)

    def swipe_right(self, y: int = 960, start_x: int = 100, end_x: int = 900, duration_ms: int = 300) -> None:
        self.swipe(start_x, y, end_x, y, duration_ms)

    def pinch_in(self, cx: int, cy: int, distance: int = 200, duration_ms: int = 300) -> None:
        self.swipe(cx - distance, cy, cx, cy, duration_ms)

    def pinch_out(self, cx: int, cy: int, distance: int = 200, duration_ms: int = 300) -> None:
        self.swipe(cx, cy, cx - distance, cy, duration_ms)

    def key_event(self, keycode: Union[int, str]) -> None:
        self._runner.run_shell(f"input keyevent {keycode}")

    def key_events(self, keycodes: list) -> None:
        for keycode in keycodes:
            self.key_event(keycode)

    def text(self, text: str) -> None:
        escaped = text.replace(" ", "%s")
        escaped = escaped.replace("'", "\\'")
        escaped = escaped.replace('"', '\\"')
        escaped = escaped.replace("&", "\\&")
        escaped = escaped.replace("<", "\\<")
        escaped = escaped.replace(">", "\\>")
        escaped = escaped.replace("|", "\\|")
        escaped = escaped.replace(";", "\\;")
        escaped = escaped.replace("(", "\\(")
        escaped = escaped.replace(")", "\\)")
        self._runner.run_shell(f"input text '{escaped}'")

    def press_home(self) -> None:
        self.key_event(KEYCODE_HOME)

    def press_back(self) -> None:
        self.key_event(KEYCODE_BACK)

    def press_power(self) -> None:
        self.key_event(KEYCODE_POWER)

    def press_volume_up(self) -> None:
        self.key_event(KEYCODE_VOLUME_UP)

    def press_volume_down(self) -> None:
        self.key_event(KEYCODE_VOLUME_DOWN)

    def press_enter(self) -> None:
        self.key_event(KEYCODE_ENTER)

    def press_delete(self) -> None:
        self.key_event(KEYCODE_DEL)

    def press_tab(self) -> None:
        self.key_event(KEYCODE_TAB)

    def press_menu(self) -> None:
        self.key_event(KEYCODE_MENU)

    def press_app_switch(self) -> None:
        self.key_event(KEYCODE_APP_SWITCH)

    def press_search(self) -> None:
        self.key_event(KEYCODE_SEARCH)

    def press_camera(self) -> None:
        self.key_event(KEYCODE_CAMERA)

    def open_notifications(self) -> None:
        self._runner.run_shell("cmd statusbar expand-notifications")

    def close_notifications(self) -> None:
        self._runner.run_shell("cmd statusbar collapse")

    def open_quick_settings(self) -> None:
        self._runner.run_shell("cmd statusbar expand-settings")

    def toggle_wifi(self) -> None:
        self._runner.run_shell("svc wifi enable")

    def set_wifi(self, enabled: bool) -> None:
        state = "enable" if enabled else "disable"
        self._runner.run_shell(f"svc wifi {state}")

    def set_mobile_data(self, enabled: bool) -> None:
        state = "enable" if enabled else "disable"
        self._runner.run_shell(f"svc data {state}")

    def set_airplane_mode(self, enabled: bool) -> None:
        val = "1" if enabled else "0"
        self._runner.run_shell(f"settings put global airplane_mode_on {val}")
        self._runner.run_shell(
            f"am broadcast -a android.intent.action.AIRPLANE_MODE --ez state {str(enabled).lower()}"
        )

    def wake_up(self) -> None:
        self.key_event(KEYCODE_WAKEUP)

    def sleep(self) -> None:
        self.key_event(KEYCODE_SLEEP)

    def unlock_screen(self) -> None:
        self.key_event(KEYCODE_MENU)
        self.swipe_up()

    def media_play_pause(self) -> None:
        self.key_event(KEYCODE_MEDIA_PLAY_PAUSE)

    def media_next(self) -> None:
        self.key_event(KEYCODE_MEDIA_NEXT)

    def media_previous(self) -> None:
        self.key_event(KEYCODE_MEDIA_PREVIOUS)

    def set_brightness(self, value: int) -> None:
        value = max(0, min(255, value))
        self._runner.run_shell(f"settings put system screen_brightness {value}")

    def set_screen_timeout(self, ms: int) -> None:
        self._runner.run_shell(f"settings put system screen_off_timeout {ms}")

    def rotate_screen(self, rotation: int = 0) -> None:
        self._runner.run_shell("settings put system accelerometer_rotation 0")
        self._runner.run_shell(f"settings put system user_rotation {rotation}")

    def auto_rotate(self, enabled: bool = True) -> None:
        val = "1" if enabled else "0"
        self._runner.run_shell(f"settings put system accelerometer_rotation {val}")

    def long_press_key(self, keycode: Union[int, str]) -> None:
        self._runner.run_shell(f"input keyevent --longpress {keycode}")

    def drag_and_drop(
        self, x1: int, y1: int, x2: int, y2: int, duration_ms: int = 1000
    ) -> None:
        self._runner.run_shell(f"input draganddrop {x1} {y1} {x2} {y2} {duration_ms}")

    def roll(self, dx: int, dy: int) -> None:
        self._runner.run_shell(f"input roll {dx} {dy}")

    def motion_event(self, action: str, x: int, y: int) -> None:
        self._runner.run_shell(f"input motionevent {action} {x} {y}")

    def key_combination(self, *keycodes: Union[int, str]) -> None:
        codes = " ".join(str(k) for k in keycodes)
        self._runner.run_shell(f"input keycombination {codes}")

    def press(self) -> None:
        self._runner.run_shell("input press")
