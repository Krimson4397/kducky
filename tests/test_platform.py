"""Tests for the desktop platform mock."""

import pytest

from ducky.ast import LedState
from ducky.platform import (
    PlatformInterface,
    RestartPayloadSignal,
    StopPayloadSignal,
)
from ducky.platform.desktop import DesktopPlatform


class TestDesktopPlatform:
    """DesktopPlatform mock behavior."""

    def test_platform_is_protocol(self) -> None:
        """DesktopPlatform satisfies PlatformInterface protocol."""
        platform = DesktopPlatform()
        assert isinstance(platform, PlatformInterface)

    def test_type_string_records_output(self) -> None:
        platform = DesktopPlatform()
        platform.type_string("hello")
        assert platform.output == ["hello"]

    def test_type_string_ln_records_output(self) -> None:
        platform = DesktopPlatform()
        platform.type_string_ln("hello")
        assert platform.output == ["hello"]

    def test_type_string_recorded_in_calls(self) -> None:
        platform = DesktopPlatform()
        platform.type_string("hello")
        assert platform.calls[0] == ("type_string", "hello")

    def test_calls_recorded_in_order(self) -> None:
        platform = DesktopPlatform()
        platform.type_string("a")
        platform.delay_ms(100)
        platform.type_string_ln("b")
        assert len(platform.calls) == 3
        assert platform.calls[0] == ("type_string", "a")
        assert platform.calls[1] == ("delay_ms", 100)
        assert platform.calls[2] == ("type_string_ln", "b")

    def test_delay_ms_records_but_does_not_sleep(self) -> None:
        import time

        platform = DesktopPlatform()
        start = time.monotonic()
        platform.delay_ms(1000)
        elapsed = time.monotonic() - start
        assert elapsed < 0.1  # Should be nearly instant, not 1 second
        assert platform.calls[0] == ("delay_ms", 1000)

    def test_random_int_in_range(self) -> None:
        platform = DesktopPlatform()
        for _ in range(100):
            val = platform.random_int(5, 10)
            assert 5 <= val <= 10

    def test_default_delay_default(self) -> None:
        platform = DesktopPlatform()
        assert platform.get_default_delay_ms() == 0

    def test_default_delay_set_get(self) -> None:
        platform = DesktopPlatform()
        platform.set_default_delay_ms(200)
        assert platform.get_default_delay_ms() == 200
        assert ("set_default_delay_ms", 200) in platform.calls
        assert ("get_default_delay_ms",) in platform.calls

    def test_stop_payload_raises(self) -> None:
        platform = DesktopPlatform()
        with pytest.raises(StopPayloadSignal):
            platform.stop_payload()
        assert platform.calls[0] == ("stop_payload",)

    def test_restart_payload_raises(self) -> None:
        platform = DesktopPlatform()
        with pytest.raises(RestartPayloadSignal):
            platform.restart_payload()
        assert platform.calls[0] == ("restart_payload",)

    def test_led_state_records(self) -> None:
        platform = DesktopPlatform()
        platform.set_led(LedState.R)
        assert platform.calls[0] == ("set_led", LedState.R)

    def test_release_all_records(self) -> None:
        platform = DesktopPlatform()
        platform.release_all()
        assert platform.calls[0] == ("release_all",)

    def test_save_restore_lock_state(self) -> None:
        platform = DesktopPlatform()
        platform.save_lock_state()
        platform.restore_lock_state()
        assert platform.calls[0] == ("save_lock_state",)
        assert platform.calls[1] == ("restore_lock_state",)

    def test_attack_mode_records(self) -> None:
        platform = DesktopPlatform()
        platform.set_attack_mode(("HID", "STORAGE"))
        assert platform.calls[0] == ("set_attack_mode", ("HID", "STORAGE"))

    def test_hide_restore_payload_records(self) -> None:
        platform = DesktopPlatform()
        platform.hide_payload()
        platform.restore_payload()
        assert platform.calls[0] == ("hide_payload",)
        assert platform.calls[1] == ("restore_payload",)

    def test_press_key_records(self) -> None:
        platform = DesktopPlatform()
        platform.press_key(("CTRL",), "C")
        assert platform.calls[0] == ("press_key", ("CTRL",), "C")

    def test_hold_key_records(self) -> None:
        platform = DesktopPlatform()
        platform.hold_key("A")
        assert platform.calls[0] == ("hold_key", "A")

    def test_release_key_records(self) -> None:
        platform = DesktopPlatform()
        platform.release_key("A")
        assert platform.calls[0] == ("release_key", "A")

    def test_wait_for_button_press_records(self) -> None:
        platform = DesktopPlatform()
        platform.wait_for_button_press()
        assert platform.calls[0] == ("wait_for_button_press",)

    def test_enable_button_records(self) -> None:
        platform = DesktopPlatform()
        platform.enable_button()
        assert platform.calls[0] == ("enable_button",)

    def test_disable_button_records(self) -> None:
        platform = DesktopPlatform()
        platform.disable_button()
        assert platform.calls[0] == ("disable_button",)

    def test_get_caps_lock_default(self) -> None:
        platform = DesktopPlatform()
        assert platform.get_caps_lock() is False

    def test_get_num_lock_default(self) -> None:
        platform = DesktopPlatform()
        assert platform.get_num_lock() is False

    def test_get_scroll_lock_default(self) -> None:
        platform = DesktopPlatform()
        assert platform.get_scroll_lock() is False

    def test_save_attack_mode_records(self) -> None:
        platform = DesktopPlatform()
        platform.save_attack_mode()
        assert platform.calls[0] == ("save_attack_mode",)

    def test_restore_attack_mode_records(self) -> None:
        platform = DesktopPlatform()
        platform.restore_attack_mode()
        assert platform.calls[0] == ("restore_attack_mode",)

    def test_multiple_output_strings(self) -> None:
        platform = DesktopPlatform()
        platform.type_string("hello")
        platform.type_string_ln("world")
        assert platform.output == ["hello", "world"]

    def test_random_int_records_call(self) -> None:
        platform = DesktopPlatform()
        platform.random_int(1, 6)
        assert platform.calls[0][0] == "random_int"
        assert platform.calls[0][1] == 1
        assert platform.calls[0][2] == 6
