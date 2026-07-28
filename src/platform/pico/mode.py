"""Boot mode selection — pure logic, importable on desktop.

Three modes selected by two GPIO jumpers (GP0, GP15), each a pulled-up
input that reads HIGH when no jumper is present and LOW when jumped to GND.

    GP0  GP15  mode   behavior
    high high  NS     no payload, USB MSC visible, no HID
    low  high  EWOS   payload runs, HID enabled, MSC visible read-only to host
    high low   EWIS   payload runs, HID enabled, MSC hidden from host
    low  low   NS     same as NS (safe default — nothing attached)
"""

from __future__ import annotations

MODE_NS: str = "ns"        # No execution, USB MSC visible, no HID
MODE_EWOS: str = "ewos"    # Execution without stealth, MSC visible read-only, HID
MODE_EWIS: str = "ewis"    # Execution with stealth, MSC hidden, HID

EXECUTABLE_MODES: frozenset[str] = frozenset({MODE_EWOS, MODE_EWIS})


def select_mode(gp0_high: bool, gp15_high: bool) -> str:
    """Return one of MODE_NS / MODE_EWOS / MODE_EWIS for the given GPIO states."""
    if not gp0_high and gp15_high:
        return MODE_EWOS
    if gp0_high and not gp15_high:
        return MODE_EWIS
    return MODE_NS


def is_executable(mode: str) -> bool:
    """True if the mode runs the payload."""
    return mode in EXECUTABLE_MODES
