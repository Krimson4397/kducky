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

def _crash_handler(e: BaseException) -> None:
    """Handle uncaught exception: increment crash counter, log, re-raise."""
    _traceback.print_exception(type(e), e, e.__traceback__)
    from platform.pico import crash as _crash
    from platform.pico import logger as _logger
    _crash.increment()
    _crash.set_last_error(f"{type(e).__name__}: {e}")
    _logger.write_line(f"[pico] uncaught crash: {e}")
    raise

# ── Main ────────────────────────────────────────────────────────────────

def main() -> None:
    """Initialize Runtime, start subsystems, execute or serve."""
    from supervisor import runtime as _runtime
    _runtime.autoreload = False

    rt = Runtime()
    try:
        rt.start()
    except Exception as e:
        _crash_handler(e)

    try:
        rt.run()
    except Exception as e:
        _crash_handler(e)

    try:
        rt.stop()
    except Exception:
        pass

    print("[pico] done")


if __name__ == "__main__":
    main()
