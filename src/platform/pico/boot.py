"""boot.py — USB configuration for Raspberry Pi Pico 2 W.

CircuitPython executes ``boot.py`` at power-on *before* the filesystem is
mounted.  This file configures USB HID (keyboard) and optional mass-storage.

To disable mass-storage (payload-only mode), create an empty file named
``/STORAGE_DISABLE`` on the CIRCUITPY drive before disconnecting.
"""

import storage

# ── HID keyboard ───────────────────────────────────────────────────────
# The RP2350 firmware enables a standard HID keyboard by default — no
# explicit ``usb_hid`` import or configuration is needed in ``boot.py``.
# The keyboard driver in ``main.py`` binds via ``Keyboard(usb_hid.devices)``
# which auto-selects the first keyboard HID device using ``find_device()``.

# ── Mass storage ───────────────────────────────────────────────────────
# Allow optional storage disable for "read-only" payload delivery mode.
# Create /STORAGE_DISABLE before disconnecting the USB cable to prevent
# the host from accessing/modifying the Pico's filesystem at the cost of
# being unable to edit payloads without re-enabling storage.

try:
    with open("/STORAGE_DISABLE") as _f:
        storage.disable_usb_drive()
except OSError:
    pass  # No disable file → mass storage enabled (default)
