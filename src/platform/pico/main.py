# ruff: noqa: E402 — sys.path manipulation before imports is intentional
"""Pico payload runner — entry point for CircuitPython auto-run.

Place (or symlink) this file as ``main.py`` or ``code.py`` on the Pico's
CIRCUITPY drive so CircuitPython executes it automatically at power-on.
"""

import sys as _sys
import traceback as _traceback


def _print_exc(e: BaseException) -> None:
    """Print the given exception's traceback."""
    _traceback.print_exception(type(e), e, e.__traceback__)

_sys.path.insert(0, "/")
_sys.path.insert(0, "/lib")

print("[pico] Pico payload runner starting...")

from ducky.ast import LedState  # noqa: I001 — sys.path set above for Pico
from ducky.interpreter import Interpreter
from ducky.lexer import DuckyLexer
from ducky.parser import DuckyParser
from ducky.preprocessor import Preprocessor
from ducky.platform import RestartPayloadSignal, StopPayloadSignal
from platform.pico.backends import PicoPlatform
from supervisor import runtime as _runtime

# ── Constants ──────────────────────────────────────────────────────────

_PAYLOAD_PATH: str = "/payload.dd"
_LED_BLINK: float = 0.5  # seconds between LED blinks during startup


def main() -> None:
    """Load and execute ``/payload.dd`` on the Pico."""
    _runtime.autoreload = False
    print("[pico] creating platform...")
    platform = PicoPlatform()

    # Green while starting
    print("[pico] LED green — startup")
    platform.set_led(LedState.G)

    # ── Read payload ──────────────────────────────────────────────
    try:
        print(f"[pico] reading {_PAYLOAD_PATH}...")
        with open(_PAYLOAD_PATH) as f:
            source = f.read()
    except OSError as e:
        print("[pico] ERROR: no payload file found")
        _print_exc(e)
        platform.set_led(LedState.R)
        return

    # ── Preprocess ────────────────────────────────────────────────
    try:
        print("[pico] preprocessing...")
        source = Preprocessor().preprocess(source)
    except Exception as e:
        print("[pico] ERROR during preprocessing")
        _print_exc(e)
        platform.set_led(LedState.R)
        return

    # ── Lex ───────────────────────────────────────────────────────
    try:
        print("[pico] lexing...")
        tokens = DuckyLexer().tokenize(source)
        print(f"[pico] lex OK — {len(tokens)} tokens")
    except Exception as e:
        print("[pico] ERROR during lexing")
        _print_exc(e)
        platform.set_led(LedState.R)
        return

    # ── Parse ─────────────────────────────────────────────────────
    try:
        print("[pico] parsing...")
        parser = DuckyParser(tokens)
        script = parser.parse()
        print(f"[pico] parse OK — {len(script.statements)} statements")
    except Exception as e:
        print("[pico] ERROR during parsing")
        _print_exc(e)
        platform.set_led(LedState.R)
        return

    # ── Interpret ─────────────────────────────────────────────────
    try:
        print("[pico] interpreting...")
        interp = Interpreter(platform)
        interp.interpret(script)
        print("[pico] interpret OK — payload complete")
    except StopPayloadSignal:
        print("[pico] payload stopped (STOP_PAYLOAD)")
    except RestartPayloadSignal:
        print("[pico] payload restart requested (RESTART_PAYLOAD)")
    except Exception as e:
        print("[pico] ERROR during interpretation")
        _print_exc(e)
        platform.set_led(LedState.R)
        return

    # Success — green LED steady
    print("[pico] payload finished OK")
    platform.set_led(LedState.G)


if __name__ == "__main__":
    main()
