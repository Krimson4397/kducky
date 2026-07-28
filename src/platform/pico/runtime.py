"""Runtime coordinator for kducky Pico 2 W.

Manages the startup -> run -> shutdown lifecycle.
"""

import time
from platform.pico import backends, logger, payload
from platform.pico.mode import EXECUTABLE_MODES, MODE_EWOS

from ducky.ast import LedState

try:
    import storage as _storage
except ImportError:
    _storage = None  # noqa: N816 — desktop test env


def _read_boot_reason() -> str:
    """Read boot reason from /system/boot_reason (written by boot.py)."""
    try:
        with open("/system/boot_reason") as f:
            return f.read().strip()
    except OSError:
        return "unknown"


class Runtime:
    """Runtime coordinator for kducky Pico 2 W."""

    def __init__(self) -> None:
        self._boot_reason: str = _read_boot_reason()
        self._platform = None
        self._stopped: bool = False

    def start(self) -> None:
        """Initialize subsystems. PicoPlatform only in executable modes."""
        logger.write_line(f"[runtime] boot: {self._boot_reason}")
        if self._boot_reason in EXECUTABLE_MODES:
            self._create_platform()
        logger.write_line("[runtime] startup complete")

    def _create_platform(self) -> None:
        """Create PicoPlatform (guarded — HID modules may not be importable)."""
        try:
            self._platform = backends.PicoPlatform()
        except ImportError as e:
            logger.write_line(f"[runtime] ERROR creating platform: {e}")

    def run(self) -> None:
        """Main execution — run payload if platform available."""
        if self._stopped:
            return

        if self._platform is None:
            logger.write_line(f"[runtime] {self._boot_reason} mode — no payload")
            return

        try:
            self._run_payload_pipeline()
        except Exception as e:
            logger.write_line(f"[runtime] payload crashed: {e}")
            raise
        else:
            logger.write_line("[runtime] payload complete")

    def _run_payload_pipeline(self) -> None:
        """Full payload pipeline: preprocess -> lex -> parse -> interpret."""
        from ducky.interpreter import Interpreter
        from ducky.lexer import DuckyLexer
        from ducky.parser import DuckyParser
        from ducky.platform import RestartPayloadSignal, StopPayloadSignal
        from ducky.preprocessor import Preprocessor

        platform = self._platform
        if platform is None:
            return

        platform.set_led(LedState.G)
        time.sleep(1.25)  # ponytail: give host time to enumerate HID

        source: str = payload.read()
        if not source:
            logger.write_line("[runtime] no payload file found")
            platform.set_led(LedState.R)
            return

        # preprocess
        source = Preprocessor().preprocess(source)
        # lex
        tokens = DuckyLexer().tokenize(source)
        # parse
        parser = DuckyParser(tokens)
        script = parser.parse()

        # interpret (with REPLAY/STOP support)
        while True:
            try:
                interp = Interpreter(platform)
                interp.interpret(script)
                break  # normal exit
            except StopPayloadSignal:
                logger.write_line("[runtime] payload stopped")
                break
            except RestartPayloadSignal:
                logger.write_line("[runtime] payload restart")
                platform.deinit()
                self._create_platform()
                platform = self._platform
                if platform is None:
                    return
                continue

        platform.set_led(LedState.G)

    def stop(self) -> None:
        """Graceful shutdown."""
        self._stopped = True
        if self._platform is not None:
            try:
                self._platform.deinit()
            except Exception:
                pass
        # ponytail: after EWOS, host still sees a readonly drive — remount
        # host-writable so results can be copied off without power-cycling
        # to NS.  Non-fatal: a remount hiccup never stops shutdown.
        if self._boot_reason == MODE_EWOS and _storage is not None:
            try:
                _storage.remount("/", readonly=True)
            except (OSError, RuntimeError) as e:
                logger.write_line(f"[runtime] WARN remount-to-host-writable failed: {e}")
        logger.write_line("[runtime] shutdown complete")
