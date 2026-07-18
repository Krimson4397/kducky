"""Desktop mock platform — records all calls for test verification.

This module provides ``DesktopPlatform``, a full implementation of
``PlatformInterface`` that records every operation to an in-memory call
log.  It is used by the test suite to verify that the interpreter produces
the correct sequence of platform events without requiring any hardware.
"""

from __future__ import annotations

import random as _random

from ducky.ast import LedState
from ducky.platform import RestartPayloadSignal, StopPayloadSignal


class DesktopPlatform:
    """Desktop mock that records all platform operations.

    Every method appends a ``(name, *args)`` tuple to ``self.calls``,
    providing a complete trace of platform interactions for test
    assertions.

    Attributes:
        output: List of strings produced by ``type_string`` /
            ``type_string_ln``.
        calls: List of ``(method_name, *args)`` tuples in call order.
    """

    def __init__(self) -> None:
        self.output: list[str] = []
        self.calls: list[tuple[object, ...]] = []
        self._default_delay_ms: int = 0
        self._caps_lock: bool = False
        self._num_lock: bool = False
        self._scroll_lock: bool = False
        self._lock_state_saved: bool = False
        self._saved_caps: bool = False
        self._saved_num: bool = False
        self._saved_scroll: bool = False
        self._attack_mode_saved: tuple[str, ...] | None = None

    def _record(self, name: str, *args: object) -> None:
        self.calls.append((name, *args))

    # ── Typing ────────────────────────────────────────────────────────

    def type_string(self, text: str) -> None:
        self._record("type_string", text)
        self.output.append(text)

    def type_string_ln(self, text: str) -> None:
        self._record("type_string_ln", text)
        self.output.append(text)

    # ── Key control ───────────────────────────────────────────────────

    def press_key(self, modifiers: tuple[object, ...], key: object | None) -> None:
        self._record("press_key", modifiers, key)

    def hold_key(self, key: object) -> None:
        self._record("hold_key", key)

    def release_key(self, key: object) -> None:
        self._record("release_key", key)

    def release_all(self) -> None:
        self._record("release_all")

    # ── Timing ────────────────────────────────────────────────────────

    def delay_ms(self, ms: int) -> None:
        self._record("delay_ms", ms)
        # Desktop mock does NOT actually sleep — the call is only recorded.

    def get_default_delay_ms(self) -> int:
        self._record("get_default_delay_ms")
        return self._default_delay_ms

    def set_default_delay_ms(self, ms: int) -> None:
        self._record("set_default_delay_ms", ms)
        self._default_delay_ms = ms

    # ── LED ───────────────────────────────────────────────────────────

    def set_led(self, state: LedState) -> None:
        self._record("set_led", state)

    # ── Buttons ───────────────────────────────────────────────────────

    def wait_for_button_press(self) -> None:
        self._record("wait_for_button_press")

    def enable_button(self) -> None:
        self._record("enable_button")

    def disable_button(self) -> None:
        self._record("disable_button")

    # ── Lock keys ─────────────────────────────────────────────────────

    def get_caps_lock(self) -> bool:
        self._record("get_caps_lock")
        return self._caps_lock

    def get_num_lock(self) -> bool:
        self._record("get_num_lock")
        return self._num_lock

    def get_scroll_lock(self) -> bool:
        self._record("get_scroll_lock")
        return self._scroll_lock

    def save_lock_state(self) -> None:
        self._record("save_lock_state")
        self._lock_state_saved = True
        self._saved_caps = self._caps_lock
        self._saved_num = self._num_lock
        self._saved_scroll = self._scroll_lock

    def restore_lock_state(self) -> None:
        self._record("restore_lock_state")
        self._caps_lock = self._saved_caps
        self._num_lock = self._saved_num
        self._scroll_lock = self._saved_scroll

    # ── Attack mode ───────────────────────────────────────────────────

    def set_attack_mode(self, params: tuple[str, ...]) -> None:
        self._record("set_attack_mode", params)

    def save_attack_mode(self) -> None:
        self._record("save_attack_mode")

    # ponytail: restore_attack_mode is a no-op on desktop
    def restore_attack_mode(self) -> None:
        self._record("restore_attack_mode")

    # ── Payload control ───────────────────────────────────────────────

    def restart_payload(self) -> None:
        self._record("restart_payload")
        raise RestartPayloadSignal()

    def stop_payload(self) -> None:
        self._record("stop_payload")
        raise StopPayloadSignal()

    def hide_payload(self) -> None:
        self._record("hide_payload")

    def restore_payload(self) -> None:
        self._record("restore_payload")

    # ── Random ────────────────────────────────────────────────────────

    def random_int(self, min_val: int, max_val: int) -> int:
        self._record("random_int", min_val, max_val)
        return _random.randint(min_val, max_val)
