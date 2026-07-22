"""Runtime coordinator for kducky Pico 2 W.

Manages the startup -> run -> shutdown lifecycle.
Managers are independent — they communicate only through Runtime.
"""

from platform.pico import backends, crash, logger, payload, webapp, wifi

import socketpool

from ducky.ast import LedState


def _read_boot_reason() -> str:
    """Read boot reason from /system/boot_reason (written by boot.py)."""
    try:
        with open("/system/boot_reason") as f:
            return f.read().strip()
    except OSError:
        return "unknown"


def _is_stealth(boot_reason: str) -> bool:
    """Return True if USB mass storage should be hidden (stealth/development)."""
    return boot_reason in {"dev+usb", "development"}


class Runtime:
    """Runtime coordinator for kducky Pico 2 W.

    Manages the startup -> run -> shutdown lifecycle.
    Managers are independent — they communicate only through Runtime.
    """

    def __init__(self) -> None:
        self._boot_reason: str = _read_boot_reason()
        self._platform = None
        self._stopped: bool = False

    def start(self) -> None:
        """Initialize all subsystems."""
        logger.write_line(f"[runtime] boot: {self._boot_reason}")
        is_recovery: bool = crash.should_lockout()

        if is_recovery:
            logger.write_line("[runtime] crash lockout — entering recovery mode")
            crash.force_visible()

        # WiFi + Web UI (always start unless setup/dev mode)
        if self._boot_reason not in ("setup", "development"):
            wifi_started: bool = wifi.start()
            if wifi_started:
                webapp.set_socketpool(socketpool)
                webapp.set_boot_reason(self._boot_reason)
                webapp.set_usb_visible(not _is_stealth(self._boot_reason))
                webapp.start()
                logger.write_line(f"[runtime] web UI started ({wifi.mode()})")
            else:
                logger.write_line("[runtime] WiFi unavailable — no web UI")
        else:
            logger.write_line(f"[runtime] {self._boot_reason} mode — no WiFi/UI")

        # PicoPlatform (only deploy/dev+usb modes)
        if self._boot_reason in ("deploy", "dev+usb") and not is_recovery:
            self._create_platform()

        logger.write_line("[runtime] startup complete")

    def _create_platform(self) -> None:
        """Create PicoPlatform (guarded — HID modules may not be importable)."""
        try:
            self._platform = backends.PicoPlatform()
        except ImportError as e:
            logger.write_line(f"[runtime] ERROR creating platform: {e}")

    def run(self) -> None:
        """Main execution — run payload or serve recovery UI."""
        if self._stopped:
            return

        # Lockout / setup/dev modes — serve web UI only
        if self._platform is None:
            logger.write_line("[runtime] no platform — serving web UI only")
            self._serve_forever()
            return

        # Run payload
        try:
            self._run_payload_pipeline()
        except Exception as e:
            logger.write_line(f"[runtime] payload crashed: {e}")
            crash.increment()
            import traceback

            crash.set_last_error(traceback.format_exc())
        else:
            crash.reset()
            crash.clear_force_visible()

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
        logger.write_line("[runtime] payload complete")

    def _serve_forever(self) -> None:
        """Serve web UI with crash recovery polling."""
        from ducky.platform import RestartPayloadSignal, StopPayloadSignal

        try:
            while not self._stopped:
                webapp.serve_once()
        except (RestartPayloadSignal, StopPayloadSignal):
            pass

    def stop(self) -> None:
        """Graceful shutdown."""
        self._stopped = True
        if self._platform is not None:
            try:
                self._platform.deinit()
            except Exception:
                pass
        webapp.stop()
        wifi.stop()
        logger.write_line("[runtime] shutdown complete")
