"""boot.py — USB configuration for Raspberry Pi Pico 2 W.

CircuitPython executes ``boot.py`` at power-on *before* the filesystem is
mounted.  This file reads two GPIO jumpers (GP0, GP15) and configures USB
HID / mass-storage / serial per one of three boot modes:

    GP0=high, GP15=high  → NS    (no payload, MSC visible, no HID)
    GP0=low,  GP15=high  → EWOS  (payload runs, HID, MSC visible read-only)
    GP0=high, GP15=low   → EWIS  (payload runs, HID, MSC hidden)
    GP0=low,  GP15=low   → NS    (safe default)

Pure GPIO selection — no crash lockout, no recovery flag.
"""

import os
from platform.pico.mode import MODE_EWIS, MODE_EWOS, select_mode

try:
    import board
    import digitalio
    import storage
    import usb_cdc
    import usb_hid

    _HAS_HW: bool = True
except ImportError:
    _HAS_HW = False


def _is_high(pin_name: str) -> bool:
    """Return True if pin is high (no jumper). Default True on error → NS."""
    try:
        pin = digitalio.DigitalInOut(getattr(board, pin_name))
        pin.direction = digitalio.Direction.INPUT
        pin.pull = digitalio.Pull.UP
        return pin.value
    except Exception:
        return True


def _write_boot_reason(reason: str) -> None:
    """Persist mode name to /system/boot_reason for runtime.py to read."""
    try:
        os.stat("/system")
    except OSError:
        try:
            os.mkdir("/system")
        except OSError:
            pass
    try:
        with open("/system/boot_reason", "w") as f:
            f.write(reason)
    except OSError:
        pass


def _configure_usb(mode: str) -> None:
    """Configure USB HID + mass-storage for the selected mode."""
    if mode == MODE_EWOS:
        usb_hid.enable()
        # host sees read-only; Pico can still write via remount
        storage.remount("/", readonly=False)
    elif mode == MODE_EWIS:
        usb_hid.enable()
        storage.disable_usb_drive()
    # MODE_NS: defaults — host-writable USB MSC, no HID
    usb_cdc.enable()


if _HAS_HW:
    gp0_high: bool = _is_high("GP0")
    gp15_high: bool = _is_high("GP15")
    _mode: str = select_mode(gp0_high, gp15_high)
    _write_boot_reason(_mode)
    _configure_usb(_mode)
