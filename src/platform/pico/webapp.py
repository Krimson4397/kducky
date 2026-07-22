"""Minimal HTTP server for kducky Pico 2 W runtime.

Serves a status page, JSON status endpoint, payload upload, and log viewer.
Pure CircuitPython stdlib — no external dependencies.
"""

import json as _json
import time as _time

# ── Injected state ───────────────────────────────────────────────────

_pool = None
_sock = None

_boot_reason: str = "unknown"
_duckyscript_version: str = "3.0"
_version: str = "1.0.0"
_usb_visible: bool = True
_uptime_start: float = 0.0

# ── Sibling module imports (guarded — modules may not exist yet) ─────

try:
    from platform.pico import crash as _crash
except ImportError:
    _crash = None

try:
    from platform.pico import payload as _payload
except ImportError:
    _payload = None

try:
    from platform.pico import wifi as _wifi
except ImportError:
    _wifi = None

try:
    from platform.pico import logger as _logger
except ImportError:
    _logger = None


# ── Setters ──────────────────────────────────────────────────────────


def set_socketpool(pool) -> None:
    """Inject the socketpool from the wifi/network manager."""
    global _pool
    _pool = pool


def set_boot_reason(reason: str) -> None:
    """Set the boot reason string displayed in status."""
    global _boot_reason
    _boot_reason = reason


def set_usb_visible(v: bool) -> None:
    """Set whether USB mass storage is currently visible."""
    global _usb_visible
    _usb_visible = v


# ── Lifecycle ────────────────────────────────────────────────────────


def start() -> None:
    """Bind and listen on port 80. Must call set_socketpool() first."""
    global _sock, _uptime_start
    if _pool is None:
        raise RuntimeError("set_socketpool() must be called before start()")
    _sock = _pool.socket()
    _sock.settimeout(0.1)
    _sock.bind(("0.0.0.0", 80))
    _sock.listen(1)
    _sock.settimeout(0.1)
    _uptime_start = _time.monotonic()


def stop() -> None:
    """Close the listening socket."""
    global _sock
    if _sock is None:
        return
    try:
        _sock.close()
    except OSError:
        pass
    _sock = None


# ── Response helper ──────────────────────────────────────────────────


def _response(conn, status: str, content_type: str, body: str) -> None:
    """Send a complete HTTP/1.0 response."""
    encoded = body.encode("utf-8")
    conn.send(f"HTTP/1.0 {status}\r\n".encode("utf-8"))
    conn.send(f"Content-Type: {content_type}\r\n".encode("utf-8"))
    conn.send(f"Content-Length: {len(encoded)}\r\n".encode("utf-8"))
    conn.send(b"Connection: close\r\n\r\n")
    conn.send(encoded)


# ── Helpers ──────────────────────────────────────────────────────────


def _read_line(conn) -> bytes:
    """Read bytes until ``\\n``. Returns empty bytes on timeout/error."""
    buf = b""
    while True:
        try:
            ch = conn.recv(1)
        except OSError:
            return buf
        if not ch:
            return buf
        buf += ch
        if ch == b"\n":
            return buf


def _read_exact(conn, n: int) -> bytes:
    """Read exactly *n* bytes. Returns fewer on connection close."""
    buf = b""
    while len(buf) < n:
        try:
            chunk = conn.recv(n - len(buf))
        except OSError:
            break
        if not chunk:
            break
        buf += chunk
    return buf


def _wifi_info() -> dict:
    """Return wifi status dict with safe defaults if the module is missing."""
    if _wifi is None:
        return {"mode": "unknown", "ssid": "", "ip": ""}
    try:
        return {
            "mode": _wifi.mode(),
            "ssid": _wifi.ssid(),
            "ip": _wifi.ip(),
        }
    except Exception:
        return {"mode": "error", "ssid": "", "ip": ""}


def _get_last_error() -> str | None:
    """Read the last error message from the crash module's file."""
    if _crash is None:
        return None
    try:
        with open("/system/last_error") as f:
            raw = f.read().strip()
        return raw if raw else None
    except OSError:
        return None


# ── Route handlers ───────────────────────────────────────────────────


def _handle_status(conn) -> None:
    """GET /status — JSON status response."""
    uptime = int(_time.monotonic() - _uptime_start) if _uptime_start > 0 else 0
    if _payload is not None:
        payload_loaded = _payload.exists()
        payload_fingerprint = _payload.fingerprint()
        payload_size = len(_payload.read()) if payload_loaded else 0
    else:
        payload_loaded = False
        payload_fingerprint = "00000000"
        payload_size = 0

    data = {
        "boot_reason": _boot_reason,
        "duckyscript_version": _duckyscript_version,
        "payload": {
            "loaded": payload_loaded,
            "fingerprint": payload_fingerprint,
            "size": payload_size,
        },
        "crash_count": _crash.get_count() if _crash else 0,
        "wifi": _wifi_info(),
        "usb_visible": _usb_visible,
        "version": _version,
        "uptime_seconds": uptime,
        "last_error": _get_last_error(),
    }
    _response(conn, "200 OK", "application/json", _json.dumps(data))


def _handle_root(conn) -> None:
    """GET / — HTML status page (self-contained, dark theme)."""
    uptime = int(_time.monotonic() - _uptime_start) if _uptime_start > 0 else 0
    crash_count = _crash.get_count() if _crash else 0
    crash_class = "err" if crash_count > 0 else "ok"
    if _payload is not None:
        payload_loaded = _payload.exists()
        payload_fingerprint = _payload.fingerprint() if payload_loaded else "00000000"
    else:
        payload_loaded = False
        payload_fingerprint = "00000000"
    wifi = _wifi_info()

    body = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>kducky Status</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:#0d1117;color:#c9d1d9;
font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif;
padding:2rem 1rem;display:flex;flex-direction:column;align-items:center}}
.card{{background:#161b22;border:1px solid #30363d;border-radius:8px;
padding:2rem;max-width:640px;width:100%}}
h1{{font-size:1.4rem;margin-bottom:1.5rem;color:#58a6ff}}
h2{{font-size:1rem;margin:1.2rem 0 0.5rem;color:#8b949e;
text-transform:uppercase;letter-spacing:0.05em}}
table{{width:100%;border-collapse:collapse}}
td{{padding:0.4rem 0;border-bottom:1px solid #21262d;font-size:0.9rem}}
td:first-child{{color:#8b949e;width:45%}}
td:last-child{{font-family:'SFMono-Regular',Consolas,'Liberation Mono',monospace}}
.ok{{color:#3fb950}}
.err{{color:#f85149}}
.footer{{margin-top:1.5rem;font-size:0.75rem;color:#484f58;text-align:center}}
</style>
</head>
<body>
<div class="card">
<h1>kducky — DuckyScript 3</h1>
<table>
<tr><td>Version</td><td>{_version}</td></tr>
<tr><td>Boot Reason</td><td>{_boot_reason}</td></tr>
<tr><td>Uptime</td><td>{uptime}s</td></tr>
<tr><td>USB Visible</td><td class="{'ok' if _usb_visible else 'err'}">{_usb_visible}</td></tr>
</table>
<h2>Payload</h2>
<table>
<tr><td>Loaded</td><td class="{'ok' if payload_loaded else 'err'}">{payload_loaded}</td></tr>
<tr><td>Fingerprint</td><td>{payload_fingerprint}</td></tr>
</table>
<h2>System</h2>
<table>
<tr><td>Crash Count</td><td class="{crash_class}">{crash_count}</td></tr>
<tr><td>WiFi Mode</td><td>{wifi["mode"]}</td></tr>
<tr><td>SSID</td><td>{wifi["ssid"]}</td></tr>
<tr><td>IP</td><td>{wifi["ip"]}</td></tr>
</table>
<div class="footer">kducky v{_version}</div>
</div>
</body>
</html>"""
    _response(conn, "200 OK", "text/html", body)


def _handle_payload(conn, body: bytes) -> None:
    """POST /payload — upload and validate a new payload file."""
    if _payload is None:
        _response(conn, "503 Service Unavailable", "application/json",
                  _json.dumps({"status": "error", "message": "Payload module unavailable"}))
        return

    body_str = body.decode("utf-8", errors="replace")
    if not body_str.strip():
        _response(conn, "400 Bad Request", "application/json",
                  _json.dumps({"status": "error", "message": "Empty body"}))
        return

    if not _payload.update(body_str):
        _response(conn, "400 Bad Request", "application/json",
                  _json.dumps({"status": "error", "message": "Payload validation failed"}))
        return

    if _crash is not None:
        _crash.reset()
        _crash.clear_force_visible()

    fp = _payload.fingerprint()
    _response(conn, "200 OK", "application/json",
              _json.dumps({"status": "ok", "fingerprint": fp}))


def _handle_logs(conn) -> None:
    """GET /logs — return latest log content as plain text."""
    content = _logger.read_latest() if _logger else ""
    _response(conn, "200 OK", "text/plain", content)


# ── Request dispatcher ───────────────────────────────────────────────


def serve_once() -> None:
    """Accept and handle one HTTP request (non-blocking poll).

    Call this from your main loop. Returns immediately if no connection
    is pending.
    """
    if _sock is None:
        return
    try:
        conn, _addr = _sock.accept()
    except OSError:
        return  # timeout — no connection pending

    try:
        # ── Read request line ──────────────────────────────────
        req_line = _read_line(conn)
        if not req_line:
            return
        parts = req_line.decode("utf-8", errors="replace").strip().split(" ")
        if len(parts) < 2:
            return
        method = parts[0]
        path = parts[1]

        # ── Read headers ───────────────────────────────────────
        content_length = 0
        while True:
            header = _read_line(conn)
            if not header or header == b"\r\n" or header == b"\n":
                break
            decoded = header.decode("utf-8", errors="replace").strip()
            if decoded.lower().startswith("content-length:"):
                try:
                    content_length = int(decoded.split(":", 1)[1].strip())
                except (ValueError, IndexError):
                    pass

        # ── Read body (POST only) ─────────────────────────────
        body = b""
        if content_length > 0:
            body = _read_exact(conn, content_length)

        # ── Route ─────────────────────────────────────────────
        if method == "GET" and path == "/status":
            _handle_status(conn)
        elif method == "GET" and (path == "/" or path == ""):
            _handle_root(conn)
        elif method == "POST" and path == "/payload":
            _handle_payload(conn, body)
        elif method == "GET" and path == "/logs":
            _handle_logs(conn)
        else:
            _response(conn, "404 Not Found", "text/plain",
                      f"404 Not Found: {method} {path}")
    finally:
        try:
            conn.close()
        except OSError:
            pass
