"""CircuitPython Pico platform backend — flat PlatformInterface implementation.

This module implements ``PlatformInterface`` for the Raspberry Pi Pico 2 W
(RP2350) running CircuitPython 10.x.  All imports from CircuitPython /
``adafruit_hid`` are guarded behind a ``try/except ImportError`` so the
file can be imported on desktop Python without raising (the class will
raise ``ImportError`` only when instantiated without hardware).
"""

import random as _random

from ducky.ast import LedState
from ducky.layouts import load as _load_layout
from ducky.platform import RestartPayloadSignal, StopPayloadSignal
from ducky.tokens import ActionKey, ModifierKey

_HAS_HW: bool
try:
    import os as _os
    import time as _time

    import board
    import digitalio
    import microcontroller  # noqa: F401  — used for reset / chip info
    import storage
    import usb_hid
    from adafruit_hid.keyboard import Keyboard
    from adafruit_hid.keycode import Keycode as _KC  # noqa: N814

    # ── Keycode alias compatibility ──────────────────────────────────────
    # CircuitPython's Keycode uses descriptive names (KEYPAD_NUMLOCK,
    # KEYPAD_FORWARD_SLASH, KEYPAD_ZERO, etc.) that differ from the
    # numeric-style names (NUM_LOCK, KEYPAD_DIVIDE, KEYPAD_0, etc.)
    # used in the _ACTION_KEY_MAP.  Add missing names as aliases.
    # Only adds if not already present, so future firmware updates that
    # add the canonical name are not overridden.
    _KC_ALIASES: dict[str, str] = {
        "NUM_LOCK": "KEYPAD_NUMLOCK",
        "KEYPAD_DIVIDE": "KEYPAD_FORWARD_SLASH",
        "KEYPAD_MULTIPLY": "KEYPAD_ASTERISK",
        "KEYPAD_0": "KEYPAD_ZERO",
        "KEYPAD_1": "KEYPAD_ONE",
        "KEYPAD_2": "KEYPAD_TWO",
        "KEYPAD_3": "KEYPAD_THREE",
        "KEYPAD_4": "KEYPAD_FOUR",
        "KEYPAD_5": "KEYPAD_FIVE",
        "KEYPAD_6": "KEYPAD_SIX",
        "KEYPAD_7": "KEYPAD_SEVEN",
        "KEYPAD_8": "KEYPAD_EIGHT",
        "KEYPAD_9": "KEYPAD_NINE",
        "KEYPAD_COMMA": "KEYPAD_PERIOD",
        "KEYPAD_00": "KEYPAD_ZERO",
        "KEYPAD_000": "KEYPAD_ZERO",
        "INTERNATIONAL_5": "BACKSLASH",
        "COMPOSE": "APPLICATION",
        "PROPS": "APPLICATION",
        "UNDO": "Z",
        "PASTE": "V",
    }
    for _alias, _target in _KC_ALIASES.items():
        if not hasattr(_KC, _alias):
            setattr(_KC, _alias, getattr(_KC, _target))
    del _KC_ALIASES, _alias, _target

    _HAS_HW = True
except Exception:
    _HAS_HW = False

# ── Keycode maps ──────────────────────────────────────────────────────
# Defined inside the guard so the dicts are only populated when the
# CircuitPython libraries are available.

if _HAS_HW:
    # Diagnostic: show all available Keycode attributes
    print("[backends] Keycode attributes:", sorted(
        x for x in dir(_KC) if x.isupper()
    ))

    _ACTION_KEY_MAP: dict[ActionKey, int] = {
        # Navigation
        ActionKey.UP: _KC.UP_ARROW,
        ActionKey.UPARROW: _KC.UP_ARROW,
        ActionKey.DOWN: _KC.DOWN_ARROW,
        ActionKey.DOWNARROW: _KC.DOWN_ARROW,
        ActionKey.LEFT: _KC.LEFT_ARROW,
        ActionKey.LEFTARROW: _KC.LEFT_ARROW,
        ActionKey.RIGHT: _KC.RIGHT_ARROW,
        ActionKey.RIGHTARROW: _KC.RIGHT_ARROW,
        ActionKey.PAGEUP: _KC.PAGE_UP,
        ActionKey.PAGEDOWN: _KC.PAGE_DOWN,
        ActionKey.HOME: _KC.HOME,
        ActionKey.END: _KC.END,
        ActionKey.INSERT: _KC.INSERT,
        ActionKey.DELETE: _KC.DELETE,
        ActionKey.DEL: _KC.DELETE,
        # Editing / control
        ActionKey.ENTER: _KC.ENTER,
        ActionKey.RETURN: _KC.RETURN,
        ActionKey.SPACE: _KC.SPACE,
        ActionKey.TAB: _KC.TAB,
        ActionKey.BACKSPACE: _KC.BACKSPACE,
        ActionKey.ESCAPE: _KC.ESCAPE,
        ActionKey.ESC: _KC.ESCAPE,
        ActionKey.PRINTSCREEN: _KC.PRINT_SCREEN,
        ActionKey.SCROLLLOCK: _KC.SCROLL_LOCK,
        ActionKey.PAUSE: _KC.PAUSE,
        # ponytail: BREAK shares the PAUSE HID usage
        ActionKey.BREAK: _KC.PAUSE,
        ActionKey.MENU: _KC.APPLICATION,
        ActionKey.APP: _KC.APPLICATION,
        ActionKey.CAPSLOCK: _KC.CAPS_LOCK,
        ActionKey.NUMLOCK: _KC.NUM_LOCK,
        ActionKey.POWER: _KC.POWER,
        # Function keys
        ActionKey.F1: _KC.F1,
        ActionKey.F2: _KC.F2,
        ActionKey.F3: _KC.F3,
        ActionKey.F4: _KC.F4,
        ActionKey.F5: _KC.F5,
        ActionKey.F6: _KC.F6,
        ActionKey.F7: _KC.F7,
        ActionKey.F8: _KC.F8,
        ActionKey.F9: _KC.F9,
        ActionKey.F10: _KC.F10,
        ActionKey.F11: _KC.F11,
        ActionKey.F12: _KC.F12,
        # Numpad
        ActionKey.KP_SLASH: _KC.KEYPAD_DIVIDE,
        ActionKey.KP_ASTERISK: _KC.KEYPAD_MULTIPLY,
        ActionKey.KP_MINUS: _KC.KEYPAD_MINUS,
        ActionKey.KP_PLUS: _KC.KEYPAD_PLUS,
        ActionKey.KP_ENTER: _KC.KEYPAD_ENTER,
        ActionKey.KP_0: _KC.KEYPAD_0,
        ActionKey.KP_1: _KC.KEYPAD_1,
        ActionKey.KP_2: _KC.KEYPAD_2,
        ActionKey.KP_3: _KC.KEYPAD_3,
        ActionKey.KP_4: _KC.KEYPAD_4,
        ActionKey.KP_5: _KC.KEYPAD_5,
        ActionKey.KP_6: _KC.KEYPAD_6,
        ActionKey.KP_7: _KC.KEYPAD_7,
        ActionKey.KP_8: _KC.KEYPAD_8,
        ActionKey.KP_9: _KC.KEYPAD_9,
        ActionKey.KP_DOT: _KC.KEYPAD_PERIOD,
        ActionKey.KP_EQUAL: _KC.KEYPAD_EQUALS,
        ActionKey.KP_COMMA: _KC.KEYPAD_COMMA,
        # ponytail: KEYPAD_00 / KEYPAD_000 — aliased to KEYPAD_ZERO via _KC_ALIASES
        ActionKey.KP_00: _KC.KEYPAD_00,
        ActionKey.KP_000: _KC.KEYPAD_000,
        # Extended keys
        # ponytail: ISO 102nd key — aliased via INTERNATIONAL_5 → BACKSLASH
        ActionKey.KEY_102ND: _KC.INTERNATIONAL_5,
        # ponytail: COMPOSE, PROPS, UNDO, PASTE — aliased via _KC_ALIASES
        ActionKey.COMPOSE: _KC.COMPOSE,
        ActionKey.KPEQUAL: _KC.KEYPAD_EQUALS,
        ActionKey.PROPS: _KC.PROPS,
        ActionKey.UNDO: _KC.UNDO,
        ActionKey.PASTE: _KC.PASTE,
    }

    _MODIFIER_KEY_MAP: dict[ModifierKey, int] = {
        ModifierKey.CONTROL: _KC.LEFT_CONTROL,
        ModifierKey.CTRL: _KC.LEFT_CONTROL,
        ModifierKey.SHIFT: _KC.LEFT_SHIFT,
        ModifierKey.ALT: _KC.LEFT_ALT,
        ModifierKey.GUI: _KC.LEFT_GUI,
        ModifierKey.WINDOWS: _KC.LEFT_GUI,
        ModifierKey.COMMAND: _KC.LEFT_GUI,
        ModifierKey.OPTION: _KC.LEFT_ALT,
    }

    # Seeded RNG for random_int — uses urandom entropy on Pico
    _SEED = int.from_bytes(_os.urandom(8), "big")
    try:
        _RNG = _random.Random(_SEED)
    except AttributeError:
        # CircuitPython: random module has no Random() class
        _random.seed(_SEED)

        class _PicoRNG:  # noqa: N801
            """Minimal RNG for CircuitPython (wraps module-level random)."""
            def randint(self, a: int, b: int) -> int:
                return _random.randint(a, b)

        _RNG = _PicoRNG()

else:
    _ACTION_KEY_MAP = {}
    _MODIFIER_KEY_MAP = {}
    _RNG = _random.Random()

# Digit key names for single-char keycode resolution
_DIGIT_NAMES = ["ZERO", "ONE", "TWO", "THREE", "FOUR",
                "FIVE", "SIX", "SEVEN", "EIGHT", "NINE"]

# ── Configuration constants ───────────────────────────────────────────

# ponytail: configurable GPIO pin for the trigger button
_PICO_BUTTON_PIN: str = "GP15"

# Bit positions in Keyboard.led_state (USB HID LED o/p report)
_LED_NUM: int = 0x01
_LED_CAPS: int = 0x02
_LED_SCROLL: int = 0x04

# ── Payload file path (on the Pico's internal filesystem) ─────────────
_PAYLOAD_PATH: str = "/payload.dd"
_HIDDEN_PREFIX: str = "._"


class PicoPlatform:
    """Platform backend for Raspberry Pi Pico 2 W (CircuitPython).

    Implements all 25 methods of the flat ``PlatformInterface`` protocol.
    Raises ``ImportError`` at construction time if the required
    CircuitPython modules are not available (i.e. when running on desktop
    Python for testing).
    """

    def __init__(self) -> None:
        if not _HAS_HW:
            msg = (
                "PicoPlatform requires CircuitPython hardware modules "
                "(board, digitalio, adafruit_hid, etc.). "
                "Cannot instantiate on desktop Python."
            )
            raise ImportError(msg)

        # ── HID keyboard ──────────────────────────────────────────
        self._hid_keyboard = Keyboard(usb_hid.devices)
        try:
            self._current_layout = _load_layout("US")
        except ValueError:
            self._current_layout = None
        self._current_layout_code: str = "US"

        # ── Onboard LED ───────────────────────────────────────────
        self._led = digitalio.DigitalInOut(board.LED)
        self._led.direction = digitalio.Direction.OUTPUT

        # ── Button ────────────────────────────────────────────────
        self._button = digitalio.DigitalInOut(
            getattr(board, _PICO_BUTTON_PIN)
        )
        self._button.direction = digitalio.Direction.INPUT
        self._button.pull = digitalio.Pull.UP
        self._button_enabled: bool = True

        # ── State ─────────────────────────────────────────────────
        self._default_delay_ms: int = 0
        self._default_char_delay: int = 0
        self._saved_caps: bool = False
        self._saved_num: bool = False
        self._saved_scroll: bool = False
        self._saved_attack_mode: tuple[str, ...] | None = None

    # ── Internal helpers ──────────────────────────────────────────────

    def _keycode_for(self, key: object) -> int:
        """Resolve an ActionKey member (or raw int) to a HID keycode."""
        if isinstance(key, int):
            return key
        if isinstance(key, ActionKey):
            return _ACTION_KEY_MAP[key]
        if isinstance(key, str):
            # Single character key in modifier combo (e.g. GUI r → "R")
            if len(key) == 1:
                if "A" <= key <= "Z":
                    return getattr(_KC, key)
                if "0" <= key <= "9":
                    return getattr(_KC, _DIGIT_NAMES[ord(key) - 48])
            raise ValueError(f"Unknown key: {key!r}")
        msg = f"Unknown key: {key!r}"
        raise ValueError(msg)

    def _mod_keycodes_for(self, mods: tuple[object, ...]) -> list[int]:
        """Resolve a tuple of modifier values to a list of HID keycodes."""
        result: list[int] = []
        for m in mods:
            if isinstance(m, int):
                result.append(m)
            elif isinstance(m, ModifierKey):
                result.append(_MODIFIER_KEY_MAP[m])
            elif isinstance(m, str):
                try:
                    mk = ModifierKey.by_name(m.upper())
                    result.append(_MODIFIER_KEY_MAP[mk])
                except (KeyError, ValueError):
                    msg = f"Unknown modifier: {m!r}"
                    raise ValueError(msg) from None
            else:
                msg = f"Unknown modifier: {m!r}"
                raise ValueError(msg)
        return result

    # ── Typing ───────────────────────────────────────────────────────

    def type_string(self, text: str) -> None:
        """Type a string character by character using current layout."""
        layout = self._current_layout
        if layout is None:
            return  # no layout loaded, skip
        default_char_delay = self._default_char_delay
        for ch in text:
            mod_byte, kc_byte = layout.keycode_for(ch)
            if mod_byte == 0 and kc_byte == 0:
                continue  # unmapped character, skip
            kcs: list[int] = []
            if mod_byte & 0x02:  # SHIFT
                try:
                    kcs.append(_KC.SHIFT)
                except AttributeError:
                    kcs.append(_KC.LEFT_SHIFT)
            kcs.append(kc_byte)
            self._hid_keyboard.press(*kcs)
            self._hid_keyboard.release_all()
            if default_char_delay > 0:
                _time.sleep(default_char_delay / 1000.0)

    def type_string_ln(self, text: str) -> None:
        """Type a string followed by Enter."""
        self.type_string(text)
        self._hid_keyboard.press(_KC.ENTER)
        self._hid_keyboard.release_all()

    # ── Key control ──────────────────────────────────────────────────

    def press_key(self, modifiers: tuple[object, ...], key: object | None) -> None:
        """Press modifier(s) + optional key, then release all."""
        kcs: list[int] = []
        kcs.extend(self._mod_keycodes_for(modifiers))
        if key is not None:
            kcs.append(self._keycode_for(key))
        if kcs:
            self._hid_keyboard.press(*kcs)
        # ponytail: 10 ms settle delay so the host registers the combo
        _time.sleep(0.01)
        self._hid_keyboard.release_all()

    def hold_key(self, key: object) -> None:
        """Press and hold a key."""
        self._hid_keyboard.press(self._keycode_for(key))

    def release_key(self, key: object) -> None:
        """Release a previously held key."""
        self._hid_keyboard.release(self._keycode_for(key))

    def release_all(self) -> None:
        """Release all pressed keys immediately."""
        self._hid_keyboard.release_all()

    # ── Timing ───────────────────────────────────────────────────────

    def delay_ms(self, ms: int) -> None:
        """Blocking pause for *ms* milliseconds."""
        _time.sleep(ms / 1000.0)

    def get_default_delay_ms(self) -> int:
        """Return the current inter-statement delay in milliseconds."""
        return self._default_delay_ms

    def set_default_delay_ms(self, ms: int) -> None:
        """Set the inter-statement delay in milliseconds."""
        self._default_delay_ms = ms

    # ── LED ──────────────────────────────────────────────────────────

    def set_led(self, state: LedState) -> None:
        """Set the onboard LED.

        The Pico W has a single monochrome LED (green/white).
        * ``OFF`` → LED off
        * ``G``   → LED on
        * ``R``, ``B`` → no operation (no RGB LED on this board)
        """
        if state is LedState.OFF:
            self._led.value = False
        elif state is LedState.G:
            self._led.value = True
        # R and B: no-op — the Pico W has no multicolor LED

    # ── Buttons ──────────────────────────────────────────────────────

    def wait_for_button_press(self) -> None:
        """Block until the hardware button is pressed (GPIO pulled low)."""
        while self._button_enabled and self._button.value:
            _time.sleep(0.01)
        # Short debounce delay
        _time.sleep(0.05)

    def enable_button(self) -> None:
        """Enable the hardware button handler."""
        self._button_enabled = True

    def disable_button(self) -> None:
        """Disable the hardware button handler."""
        self._button_enabled = False

    # ── Lock keys ────────────────────────────────────────────────────

    def get_caps_lock(self) -> bool:
        """Return the current Caps Lock state (from USB LED report)."""
        return bool(self._hid_keyboard.led_state & _LED_CAPS)

    def get_num_lock(self) -> bool:
        """Return the current Num Lock state (from USB LED report)."""
        return bool(self._hid_keyboard.led_state & _LED_NUM)

    def get_scroll_lock(self) -> bool:
        """Return the current Scroll Lock state (from USB LED report)."""
        return bool(self._hid_keyboard.led_state & _LED_SCROLL)

    def save_lock_state(self) -> None:
        """Save the current host lock key state."""
        self._saved_caps = self.get_caps_lock()
        self._saved_num = self.get_num_lock()
        self._saved_scroll = self.get_scroll_lock()

    def restore_lock_state(self) -> None:
        """Restore a previously saved host lock key state.

        .. note::
            A USB HID keyboard cannot *set* the host's lock-LED state.
            This method is a no-op on Pico for that reason.  The host
            controls its own lock state; we can only observe it.
        """
        # ponytail: Can't set host lock state via USB HID output report
        # from the adafruit_hid library. The saved values are retained
        # in self._saved_{caps,num,scroll} for informational purposes.
        pass

    # ── Attack mode ──────────────────────────────────────────────────

    def set_attack_mode(self, params: tuple[str, ...]) -> None:
        """Configure USB device mode.

        Writes the parameters to an on-device config file that
        ``boot.py`` reads on the next restart.  Changing the USB
        descriptor requires a reboot on CircuitPython.
        """
        # ponytail: writes config for boot.py to consume on next restart
        try:
            with open("/attack_mode.cfg", "w") as f:
                for param in params:
                    f.write(param + "\n")
        except OSError:
            pass  # ponytail: filesystem may be readonly

    def save_attack_mode(self) -> None:
        """Save the current attack mode configuration."""
        # ponytail: save current mode params for later restore
        try:
            with open("/attack_mode.cfg") as f:
                self._saved_attack_mode = tuple(
                    line.strip() for line in f if line.strip()
                )
        except OSError:
            self._saved_attack_mode = ("HID",)

    def restore_attack_mode(self) -> None:
        """Restore a previously saved attack mode configuration."""
        if self._saved_attack_mode is not None:
            self.set_attack_mode(self._saved_attack_mode)

    # ── Payload control ──────────────────────────────────────────────

    def restart_payload(self) -> None:
        """Restart the entire payload from the beginning."""
        raise RestartPayloadSignal()

    def stop_payload(self) -> None:
        """Stop payload execution immediately."""
        raise StopPayloadSignal()

    def hide_payload(self) -> None:
        """Hide the payload file from mass storage (dot-prefix rename)."""
        hidden_path = "/" + _HIDDEN_PREFIX + "payload.dd"
        try:
            storage.remount("/", readonly=False)
            _os.rename(_PAYLOAD_PATH, hidden_path)
        except OSError:
            pass  # ponytail: file may already be hidden

    def restore_payload(self) -> None:
        """Restore a previously hidden payload file to visibility."""
        hidden_path = "/" + _HIDDEN_PREFIX + "payload.dd"
        try:
            storage.remount("/", readonly=False)
            _os.rename(hidden_path, _PAYLOAD_PATH)
        except OSError:
            pass  # ponytail: hidden file may not exist

    # ── Random ───────────────────────────────────────────────────────

    def random_int(self, min_val: int, max_val: int) -> int:
        """Return a random integer in [*min_val*, *max_val*] (inclusive)."""
        return _RNG.randint(min_val, max_val)

    # ── Keyboard Layout ──────────────────────────────────────────────

    def set_layout(self, code: str) -> None:
        """Switch keyboard layout by language code."""
        try:
            self._current_layout = _load_layout(code)
            self._current_layout_code = code
        except ValueError:
            pass  # Unknown layout — keep current

    def get_layout(self) -> str:
        """Return the current keyboard layout code."""
        return self._current_layout_code
