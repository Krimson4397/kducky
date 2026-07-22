# Post-Payload WiFi Retrieval — Implementation Plan

> kducky · Raspberry Pi Pico 2 W · CircuitPython 10.x  

---

## 1. Problem

Payloads save `.txt` result files to the Pico's filesystem. Users must currently unplug, jumper GP0→GND, replug to see the USB drive, copy files, then unplug and remove jumper. This is 3–4 plug/unplug cycles per iteration.

**Root cause:** USB MSC fundamentally prevents concurrent host+device writes to FAT. CircuitPython's `storage.remount(readonly=False)` lets the Pico write but makes the host see a read-only drive. No workaround exists in any firmware.

---

## 2. Solution

Start WiFi **after** the payload finishes executing, serve result files over HTTP, then shut down.

```
BOOT → run payload (instant, no WiFi) → interpreter exits → flush logs → os.sync()
  → check /results/ for files?
    → NO:  blink LED, done
    → YES: start WiFi → start HTTP server → serve files → timeout → shutdown
```

WiFi is NEVER initialized before payload execution. Payload timing is identical to today.

---

## 3. Architecture

### Runtime lifecycle

```python
Runtime:
    start()     # create platform, detect mode
    run()       # execute payload pipeline (no change)
    post_run()  # NEW — flush logs, check results, serve if needed
    stop()      # cleanup (no change)
```

### State machine

```
INIT → EXECUTE_PAYLOAD → FLUSH → CHECK_RESULTS
                                    ├── empty → DONE (blink green)
                                    └── files → CONNECT_WIFI
                                                  ├── fail → DONE (blink red)
                                                  └── ok → SERVE_FILES
                                                            ├── timeout 5m → DONE
                                                            ├── idle 30s → DONE
                                                            └── all downloaded → DONE
```

---

## 4. Module layout

### `results.py` (NEW — ~30 lines)

Minimal module for result file discovery and serving:

```python
DIR = "/results"

def available() -> bool          # os.stat() check
def list_files() -> list[str]    # os.listdir(), filter to known files
def read(name: str) -> bytes     # whitelist-checked, returns raw bytes or raises
```

Whitelist: filenames must match `[a-zA-Z0-9._-]+`, no path separators, no `.`, no `..`.

### `wifi.py` (NEW — ~80 lines)

Station-only WiFi manager:

```python
def start(retries: int = 3) -> bool   # wifi.radio.connect(), retry on failure
def stop() -> None                     # disconnect
def connected() -> bool
def ip() -> str
```

- No AP fallback
- No captive portal
- No configuration pages

### `webserver.py` (NEW — ~120 lines)

Minimal HTTP server:

```python
def start(timeout_minutes: int = 5) -> None
def serve_once() -> None          # non-blocking poll, returns after timeout
def stop() -> None                # close socket
```

**Endpoints:**

| Method | Path                    | Response                     |
| ------ | ----------------------- | ---------------------------- |
| GET    | `/`                     | `{"files": ["results.txt"]}` |
| GET    | `/download/<filename>`  | Raw file bytes               |

No HTML, no uploads, no log viewer, no configuration.

### `runtime.py` (MODIFIED — +20 lines)

```python
def run(self):
    self._run_payload_pipeline()   # existing, unchanged

def post_run(self):
    logger.flush()
    os.sync()
    if not results.available():
        return
    if not wifi.start(retries=3):
        return
    webserver.start(timeout_minutes=5)
    while not webserver.done():
        webserver.serve_once()
        # serve_once returns False on timeout/idle/all-downloaded
    webserver.stop()
    wifi.stop()
```

---

## 5. Failure modes

| Failure                     | Handling                                         |
| --------------------------- | ------------------------------------------------ |
| `/results/` missing        | `available()` returns False → skip WiFi entirely |
| Empty `/results/`          | Same as above                                    |
| WiFi unavailable            | Retry 3x, then give up — payload already ran     |
| Browser disconnect mid-download | Stream in 512B chunks, close on error       |
| Multiple clients            | Sequential — `listen(1)`, one at a time          |
| Power loss during serving   | No different from power loss during payload run  |
| Corrupted result file       | `read()` returns what's on disk — up to user     |

---

## 6. Open questions (for DeepSeek review)

1. **`post_run()` vs inside `run()`** — Is an explicit lifecycle phase cleaner, or just put the code at the end of `run()`?
2. **Timeout policy** — Should we serve until timeout (5 min), after idle (30s), or after all files downloaded?
3. **mDNS** — Is `kducky.local` reliable enough, or should we only display the IP?
4. **sendall()** — Does CircuitPython 10.x on RP2350 support `sendall()`?
5. **gc.collect()** — Recommended after each request, or unnecessary on Pico 2 W with 520KB SRAM?
6. **HID notification** — Should we type the URL into Notepad after payload, or is that too fragile?

---

## 7. Files not modified

The following are explicitly **not touched**:
- `src/ducky/` — interpreter, parser, lexer, AST, preprocessor, errors (frozen)
- `src/platform/` — PlatformInterface, DesktopPlatform (unchanged)
- `tests/` — all existing tests (no behavior changes)
- `boot.py` — no changes needed (GPIO detection already works)
- `main.py` — no changes needed (still calls Runtime)

---

## 8. Risk assessment

| Risk                          | Likelihood | Impact | Mitigation                                         |
| ----------------------------- | ---------- | ------ | -------------------------------------------------- |
| WiFi crashes payload          | None       | N/A    | WiFi starts AFTER payload, completely isolated     |
| HTTP server memory leak       | Low        | Low    | Preallocated buffer, gc.collect(), 5-min timeout   |
| Path traversal exploit        | Low        | Med    | Whitelist filenames, never accept raw paths        |
| WiFi never connects           | Med        | Low    | Retry 3x, skip gracefully — payload already ran    |
| Socket resource leak          | Low        | Low    | try/finally on socket close, gc.collect()          |
| sendall() not available       | Med        | Low    | Use manual send() loop (planned)                     |

---

## 9. Estimated size

| Module        | LOC   | Type     |
| ------------- | ----- | -------- |
| `results.py`    | ~30   | new      |
| `wifi.py`       | ~80   | new      |
| `webserver.py`  | ~120  | new      |
| `runtime.py`    | +20   | modified |
| **Total**     | **~250** |       |

---

## 10. Implementation order

1. `results.py` — standalone, testable on desktop immediately
2. `wifi.py` — standalone, needs hardware for full test
3. `webserver.py` — depends on results.py + wifi.py
4. `runtime.py` — add `post_run()`, wire everything together

Each step is independently revertible. If WiFi proves unreliable, `wifi.py` and `webserver.py` can be deleted without touching the interpreter.
