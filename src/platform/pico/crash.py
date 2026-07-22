"""Crash counter and lockout manager for kducky Pico 2 W runtime.

All state is persisted as plain-text files under /system/.
Uses only CircuitPython stdlib (os).
"""

import os

LOCKOUT_THRESHOLD = 3
CRASH_COUNT_PATH = "/system/crash_count"
FORCE_VISIBLE_PATH = "/system/FORCE_USB_VISIBLE"
LAST_ERROR_PATH = "/system/last_error"


def _ensure_system_dir() -> None:
    """Create /system/ directory if it doesn't exist."""
    try:
        os.stat("/system")
    except OSError:
        try:
            os.mkdir("/system")
        except OSError:
            pass


def get_count() -> int:
    """Read crash counter. Returns 0 if missing or invalid."""
    try:
        with open(CRASH_COUNT_PATH) as f:
            raw = f.read().strip()
        count = int(raw)
        if count < 0 or count > LOCKOUT_THRESHOLD:
            reset()
            return 0
        return count
    except (OSError, ValueError):
        return 0


def increment() -> int:
    """Increment crash counter and return new count."""
    count = get_count() + 1
    _ensure_system_dir()
    try:
        with open(CRASH_COUNT_PATH, "w") as f:
            f.write(str(count))
    except OSError:
        pass
    return count


def reset() -> None:
    """Set crash counter to 0."""
    _ensure_system_dir()
    try:
        with open(CRASH_COUNT_PATH, "w") as f:
            f.write("0")
    except OSError:
        pass


def should_lockout() -> bool:
    """Return True if crash count >= lockout threshold."""
    return get_count() >= LOCKOUT_THRESHOLD


def force_visible() -> None:
    """Create FORCE_USB_VISIBLE flag file."""
    _ensure_system_dir()
    try:
        with open(FORCE_VISIBLE_PATH, "w"):
            pass
    except OSError:
        pass


def clear_force_visible() -> None:
    """Remove FORCE_USB_VISIBLE flag file."""
    try:
        os.remove(FORCE_VISIBLE_PATH)
    except OSError:
        pass


def set_last_error(message: str) -> None:
    """Write error message to /system/last_error."""
    _ensure_system_dir()
    try:
        with open(LAST_ERROR_PATH, "w") as f:
            f.write(message)
    except OSError:
        pass
