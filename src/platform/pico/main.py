# ruff: noqa: E402 — sys.path manipulation before imports is intentional
"""Pico entry point — CircuitPython auto-run.

Place this file as ``main.py`` or ``code.py`` on the Pico's CIRCUITPY drive.
"""

import sys as _sys
import traceback as _traceback

_sys.path.insert(0, "/")
_sys.path.insert(0, "/lib")

print("[pico] starting...")

from platform.pico.runtime import Runtime

# ── Global exception handler ────────────────────────────────────────────

def _handle_error(e: Exception) -> None:
    """Log exception, do NOT bump a crash counter (lockout removed)."""
    _traceback.print_exception(type(e), e, e.__traceback__)
    from platform.pico import logger as _logger
    _logger.write_line(f"[main] error: {e!r}")
    _logger.write_line(
        "".join(_traceback.format_exception(None, e, e.__traceback__))
    )
    raise  # let CircuitPython show the traceback

# ── Main ────────────────────────────────────────────────────────────────

def main() -> None:
    """Initialize Runtime, start subsystems, execute or serve."""
    from supervisor import runtime as _runtime
    _runtime.autoreload = False

    rt = Runtime()
    try:
        rt.start()
    except Exception as e:
        _handle_error(e)

    try:
        rt.run()
    except Exception as e:
        _handle_error(e)

    try:
        rt.stop()
    except Exception:
        pass

    print("[pico] done")


if __name__ == "__main__":
    main()
