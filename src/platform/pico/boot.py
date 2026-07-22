"""boot.py — USB configuration for Raspberry Pi Pico 2 W.

CircuitPython executes ``boot.py`` at power-on *before* the filesystem is
mounted.  This file configures USB HID, mass-storage, and serial based on
two GPIO jumpers and a /system/FORCE_USB_VISIBLE recovery flag.

Boot modes:
  GP0=high, GP15=high  → Deploy (HID + storage, payload runs)
  GP0=low,  GP15=high  → Setup (serial + USB, no HID)
  GP0=high, GP15=low   → Dev+USB (HID + USB visible, payload runs)
  GP0=low,  GP15=low   → Development (serial + USB, no HID)

Use /system/FORCE_USB_VISIBLE to override stealth and force mass storage
visible (for crash recovery).
"""

import os

import board
import digitalio
import storage
import usb_cdc
import usb_hid


def _is_high(pin_name: str) -> bool:
    """Return True if pin is high (not grounded)."""
    try:
        pin = digitalio.DigitalInOut(getattr(board, pin_name))
        pin.direction = digitalio.Direction.INPUT
        pin.pull = digitalio.Pull.UP
        return pin.value
    except Exception:
        return True  # safe default — treat as high


def _is_crash_locked() -> bool:
    """Return True if crash_count >= 3 (lockout threshold)."""
    try:
        with open("/system/crash_count") as f:
            return int(f.read().strip()) >= 3
    except (OSError, ValueError):
        return False


def _has_force_visible() -> bool:
    """Check if /system/FORCE_USB_VISIBLE flag exists (crash recovery)."""
    try:
        os.stat("/system/FORCE_USB_VISIBLE")
        return True
    except OSError:
        return False


def _write_boot_reason(reason: str) -> None:
    """Write boot reason for runtime to consume."""
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


# ── Detect boot mode ──────────────────────────────────────────────────

gp0_high: bool = _is_high("GP0")
gp15_high: bool = _is_high("GP15")
force_visible: bool = _has_force_visible()

# ── Configure USB ─────────────────────────────────────────────────────

if not gp0_high and not gp15_high:
    # Development mode: serial + USB visible, no HID
    _write_boot_reason("development")
    # host-writable (default), no remount needed
    # usb_hid stays disabled (default)

elif not gp0_high:
    # Setup mode: serial + USB visible, no HID
    _write_boot_reason("setup")
    # host-writable (default), no remount needed
    # usb_hid stays disabled (default)

elif not gp15_high and not force_visible:
    # Dev+USB mode: HID + USB visible (no stealth)
    _write_boot_reason("dev+usb")
    storage.remount("/", readonly=False)
    usb_hid.enable()

else:
    # Deploy mode: HID + storage (hidden unless force-visible or crash lockout)
    _write_boot_reason("deploy")
    if not force_visible and not _is_crash_locked():
        storage.disable_usb_drive()
    usb_hid.enable()

# Serial console always enabled for debugging
usb_cdc.enable()
