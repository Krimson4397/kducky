"""Platform interface protocol and payload control signals.

This module defines the ``PlatformInterface`` Protocol that the interpreter
uses for all hardware I/O.  Desktop mock and Pico CircuitPython backends
implement this protocol, keeping the interpreter platform-independent.
"""

from ducky.ast import LedState
from ducky.utils.compat import Protocol, runtime_checkable

__all__ = [
    "PayloadSignal",
    "StopPayloadSignal",
    "RestartPayloadSignal",
    "PlatformInterface",
]


class PayloadSignal(BaseException):
    """Base exception for payload control signals (stop / restart)."""


class StopPayloadSignal(PayloadSignal):
    """Raised to signal that the payload should stop immediately."""


class RestartPayloadSignal(PayloadSignal):
    """Raised to signal that the payload should restart from the beginning."""


@runtime_checkable
class PlatformInterface(Protocol):
    """Protocol that every platform backend must satisfy.

    The interpreter receives a ``PlatformInterface`` instance via dependency
    injection and performs all I/O through it.  This keeps the interpreter
    free of any hardware-specific imports.
    """

    # ── Typing ────────────────────────────────────────────────────────

    def type_string(self, text: str) -> None:
        """Type a string character by character."""
        ...

    def type_string_ln(self, text: str) -> None:
        """Type a string followed by Enter."""
        ...

    # ── Key control ───────────────────────────────────────────────────

    def press_key(self, modifiers: tuple[object, ...], key: object | None) -> None:
        """Press modifier(s) + optional key, then release all."""
        ...

    def hold_key(self, key: object) -> None:
        """Press and hold a key."""
        ...

    def release_key(self, key: object) -> None:
        """Release a previously held key."""
        ...

    def release_all(self) -> None:
        """Release all pressed keys immediately."""
        ...

    # ── Timing ────────────────────────────────────────────────────────

    def delay_ms(self, ms: int) -> None:
        """Blocking pause for *ms* milliseconds."""
        ...

    def get_default_delay_ms(self) -> int:
        """Return the current inter-statement delay in milliseconds."""
        ...

    def set_default_delay_ms(self, ms: int) -> None:
        """Set the inter-statement delay in milliseconds."""
        ...

    # ── LED ───────────────────────────────────────────────────────────

    def set_led(self, state: LedState) -> None:
        """Set the device LED to a given state."""
        ...

    # ── Buttons ───────────────────────────────────────────────────────

    def wait_for_button_press(self) -> None:
        """Block until the hardware button is pressed."""
        ...

    def enable_button(self) -> None:
        """Enable the hardware button handler."""
        ...

    def disable_button(self) -> None:
        """Disable the hardware button handler."""
        ...

    # ── Lock keys ─────────────────────────────────────────────────────

    def get_caps_lock(self) -> bool:
        """Return the current Caps Lock state of the host."""
        ...

    def get_num_lock(self) -> bool:
        """Return the current Num Lock state of the host."""
        ...

    def get_scroll_lock(self) -> bool:
        """Return the current Scroll Lock state of the host."""
        ...

    def save_lock_state(self) -> None:
        """Save the current host lock key state."""
        ...

    def restore_lock_state(self) -> None:
        """Restore a previously saved host lock key state."""
        ...

    # ── Attack mode ───────────────────────────────────────────────────

    def set_attack_mode(self, params: tuple[str, ...]) -> None:
        """Configure USB device mode and identifiers."""
        ...

    def save_attack_mode(self) -> None:
        """Save the current attack mode configuration."""
        ...

    def restore_attack_mode(self) -> None:
        """Restore a previously saved attack mode configuration."""
        ...

    # ── Payload control ───────────────────────────────────────────────

    def restart_payload(self) -> None:
        """Restart the entire payload from the beginning."""
        ...

    def stop_payload(self) -> None:
        """Stop payload execution immediately."""
        ...

    def hide_payload(self) -> None:
        """Hide the payload file from host mass storage."""
        ...

    def restore_payload(self) -> None:
        """Restore a previously hidden payload file to visibility."""
        ...

    # ── Random ────────────────────────────────────────────────────────

    def random_int(self, min_val: int, max_val: int) -> int:
        """Return a random integer in [*min_val*, *max_val*] (inclusive)."""
        ...

    # ── Keyboard Layout ──────────────────────────────────────────────

    def set_layout(self, code: str) -> None:
        """Switch keyboard layout by language code (e.g. 'DE', 'GB')."""
        ...

    def get_layout(self) -> str:
        """Return the current keyboard layout code."""
        ...
