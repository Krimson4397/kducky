"""Dual-file rotating log for CircuitPython on Raspberry Pi Pico 2 W."""

import os

_LOG_DIR = "/logs"
_LATEST = "/logs/latest.log"
_PREVIOUS = "/logs/previous.log"
_rotated: bool = False


def _ensure_dir() -> None:
    try:
        os.stat(_LOG_DIR)
    except OSError:
        try:
            os.mkdir(_LOG_DIR)
        except OSError:
            pass


def _rotate() -> None:
    global _rotated
    if _rotated:
        return
    _rotated = True
    try:
        os.stat(_LATEST)
    except OSError:
        return
    try:
        os.remove(_PREVIOUS)
    except OSError:
        pass
    os.rename(_LATEST, _PREVIOUS)


def write_line(message: str) -> None:
    """Append a line to latest.log, rotating on first boot-time write."""
    _ensure_dir()
    _rotate()
    with open(_LATEST, "a") as f:
        f.write(message + "\n")


def read_latest() -> str:
    """Return contents of latest.log, or empty string if missing."""
    try:
        with open(_LATEST) as f:
            return f.read()
    except OSError:
        return ""


def clear() -> None:
    """Wipe latest.log clean."""
    try:
        with open(_LATEST, "w") as f:
            f.write("")
    except OSError:
        pass
