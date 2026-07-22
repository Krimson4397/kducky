"""WiFi connection manager for kducky Pico 2 W runtime.

Manages station (connect to existing WiFi) and access-point (fallback) modes
using CircuitPython's built-in ``wifi`` module.  All functions degrade
gracefully when the ``wifi`` module is unavailable (desktop import).
"""

# ── Hardware availability ──────────────────────────────────────────────

try:
    import socketpool  # noqa: F401 — needed by webapp; wifi owns the radio
except ImportError:
    pass

try:
    import wifi as _wifi

    _HAS_WIFI: bool = True
except ImportError:
    _HAS_WIFI: bool = False

# ── Secrets ────────────────────────────────────────────────────────────

_secrets: dict[str, str] = {}
try:
    from secrets import secrets as _s  # type: ignore[import-untyped]

    _secrets = dict(_s)
except (ImportError, NameError, ValueError):
    pass

# ── State ──────────────────────────────────────────────────────────────

_mode: str = "off"  # "station", "ap", "off"
_ip: str = ""
_ssid: str = ""


def start() -> bool:
    """Connect as station or start access point.

    Tries station mode first when *ssid* is configured in ``secrets``.
    Falls back to AP mode using ``ap_ssid`` / ``ap_password`` from
    ``secrets`` (defaults: ``"kducky-AP"`` / ``"ducky123"``).

    Returns ``True`` when any mode is active, ``False`` otherwise.
    """
    # ── Guard: no hardware ────────────────────────────────────────
    if not _HAS_WIFI:
        return _set_off()

    # ── Station mode ──────────────────────────────────────────────
    ssid_st = _secrets.get("ssid")
    if ssid_st is not None:
        password = _secrets.get("password", "")
        try:
            _wifi.radio.connect(ssid=ssid_st, password=password, timeout=10)
        except (ConnectionError, OSError, RuntimeError, ValueError):
            pass
        if _wifi.radio.ipv4_address is not None:
            return _set_station(ssid_st)

    # ── Access-point mode (fallback) ──────────────────────────────
    ap_ssid = _secrets.get("ap_ssid", "kducky-AP")
    ap_password = _secrets.get("ap_password", "ducky123")
    try:
        _wifi.radio.start_ap(ssid=ap_ssid, password=ap_password)
    except (OSError, RuntimeError, ValueError):
        return _set_off()

    return _set_ap(ap_ssid)


def stop() -> None:
    """Disconnect station or stop access point."""
    if not _HAS_WIFI:
        return
    try:
        if _mode == "station":
            _wifi.radio.disconnect()
        elif _mode == "ap":
            _wifi.radio.stop_ap()
    except (OSError, RuntimeError):
        pass
    _set_off()


def is_connected() -> bool:
    """Return ``True`` when station is connected and has an IP address."""
    if not _HAS_WIFI:
        return False
    if _mode == "station":
        return _wifi.radio.ipv4_address is not None
    return _mode == "ap"


def mode() -> str:
    """Return current WiFi mode: ``"station"``, ``"ap"``, or ``"off"``."""
    return _mode


def ip() -> str:
    """Return current IP address string, or ``""`` when not connected."""
    return _ip


def ssid() -> str:
    """Return connected station SSID or access-point SSID, or ``""``."""
    return _ssid


def radio():
    """Return the wifi radio object, or None if wifi hardware unavailable."""
    return _wifi.radio if _HAS_WIFI else None


# ── Internal helpers ───────────────────────────────────────────────────


def _set_off() -> bool:
    global _mode, _ip, _ssid
    _mode = "off"
    _ip = ""
    _ssid = ""
    return False


def _set_station(ssid_st: str) -> bool:
    global _mode, _ip, _ssid
    _mode = "station"
    _ip = str(_wifi.radio.ipv4_address)
    _ssid = ssid_st
    return True


def _set_ap(ap_ssid: str) -> bool:
    global _mode, _ip, _ssid
    _mode = "ap"
    _ip = "192.168.4.1"
    _ssid = ap_ssid
    return True
