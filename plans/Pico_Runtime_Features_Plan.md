# Engineering Design Plan — Pico 2 W Runtime Features

## Architecture Review Summary

The interpreter (`ducky/interpreter.py`, 692 LOC) is already cleanly decoupled from hardware via the `PlatformInterface` protocol. All Pico-specific code lives under `src/platform/pico/`. **No interpreter changes needed** — only the Pico runtime layer needs work.

**Current files:**
- `boot.py` (28 LOC) — File-based storage toggle (`/STORAGE_DISABLE`)
- `main.py` (130 LOC) — Inline pipeline: platform → read → preprocess → lex → parse → interpret
- `backends.py` (595 LOC) — `PicoPlatform`, all HID/HW, **unchanged**

---

## Proposed File Changes

| File | Change | LOC | Purpose |
|------|--------|-----|---------|
| `boot.py` | Rewrite | 28→55 | GPIO-based USB config, all 4 modes |
| `main.py` | Thin rewrite | 130→30 | Just imports and calls `Runtime` |
| `runtime.py` | **New** | ~250 | Boot orchestrator |
| `webapp.py` | **New** | ~200 | WiFi AP + HTTP server |
| `backends.py` | **Unchanged** | 595 | `PicoPlatform` — zero modifications |
| `secrets.py.example` | **New** | 3 | WiFi config template |

---

## The Four Boot Modes

CircuitPython USB APIs available in `boot.py`:
- `storage.disable_usb_drive()` — hides MSC
- `usb_hid.enable(devices)` — sets HID (empty tuple = no HID)
- `usb_cdc.enable(console, data)` — sets serial

| GP0 | GP15 | Mode | `boot.py` does | Payload | USB | HID | Serial |
|-----|------|------|----------------|---------|-----|-----|--------|
| Open | Open | **Deploy** | `storage.disable_usb_drive()` | ✅ | ❌ | ✅ | default |
| Open | GND | **Dev+USB** | (nothing — all defaults) | ✅ | ✅ | ✅ | default |
| GND | Open | **Setup** | `disable_usb_drive()` + `hid.enable(())` + `cdc.enable(console=True)` | ❌ | ❌ | ❌ | ✅ |
| GND | GND | **Dev** | `hid.enable(())` + `cdc.enable(console=True)` | ❌ | ✅ | ❌ | ✅ |

GP0 = role (deploy vs setup), GP15 = storage visibility only.

---

## Runtime (runtime.py) — Boot Flow

```
main()
  └── Runtime().run()
        ├── Disable autoreload
        ├── Read GP0 + GP15 → BootMode
        ├── If GP0 grounded →
        │     ├── Print "setup mode"
        │     ├── Start WiFi + web server
        │     └── Return (skip payload)
        ├── If GP0 floating (deploy mode) →
        │     ├── Read crash counter from /system/crash_count.txt
        │     ├── Counter >= 3 → force USB visible, start WiFi, skip payload
        │     ├── Counter < 3 → increment counter
        │     ├── PicoPlatform() → read → preprocess → lex → parse → interpret
        │     ├── On success → reset counter to 0, green LED steady
        │     └── On error → red LED fast blink, exit
        └── REPLAY loop same as current
```

**Crash counter mechanism:** Plain file `/system/crash_count.txt` — single digit 0-3. On boot N+1, `boot.py` reads this file and if >= 3, skips `storage.disable_usb_drive()` so USB appears. The runtime then also skips payload execution. This creates a 3-failure window, then auto-recovery on boot 4.

---

## WiFi Web UI (webapp.py)

### Network
- Creates WiFi AP from `secrets.py` (user-provided, gitignored)
- `ssid` and `password` in `/secrets.py`
- AP address: `192.168.4.1:80`

### Routes

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/` | Status page (HTML) |
| `GET` | `/payload` | Download current payload |
| `POST` | `/payload` | Upload replacement (safe write) |
| `DELETE` | `/payload` | Remove payload |
| `GET` | `/config` | Runtime config JSON |
| `GET` | `/logs` | Last error log |

### Safe Payload Update
```
POST /payload → body
  ↓
Write to /payload.tmp
  ↓
Try parse (lex + parse)
  ├── OK → rename /payload.tmp → /payload.dd
  └── Fail → delete /payload.tmp, return error
```

Active payload never corrupted by a bad upload.

---

## Recovery Priority

```
1. GP0 jumper          ← Hardware override
2. Crash recovery      ← 3 failures → USB visible + skip payload
3. WiFi upload         ← OTA fix (works even in safe mode)
4. USB mass storage    ← GP15→GND always re-enables
5. BOOTSEL recovery    ← Last resort (re-flash UF2)
```

**EXFIL rule:** If GP15→GND (user wants storage visible), EXFIL mode must NOT override. Hardware intent always wins.

---

## Filesystem Layout

```
/payload.dd
/payload.tmp
/system/crash_count.txt
/last_error.log
/secrets.py
```

---

## LED Signals (single green LED)

| State | LED |
|-------|-----|
| Payload executing | Steady green |
| Setup mode / WiFi ready | Slow blink (500ms) |
| Error | Fast blink (100ms) |
| Crash lockout (3 fails) | Fast blink |
| Idle / no payload | OFF |

---

## Implementation Milestones

1. **`boot.py`** — GPIO reads + USB configuration for all 4 modes
2. **`runtime.py` + `main.py`** — Mode detection, crash counter, payload pipeline
3. **`webapp.py` + `secrets.py.example`** — WiFi AP + HTTP routes
4. **Integration** — Wire WiFi into runtime's boot flow
5. **Hardware test** — All 4 modes, crash recovery, web UI upload

---

## Risks

| Risk | Mitigation |
|------|-----------|
| `usb_hid.enable(())` breaks PicoPlatform init | Guard: check `usb_hid.devices` before creating Keyboard |
| WiFi + HID on same Pico 2 W | Both work — separate hardware (verified by pico-ducky) |
| Crash counter file on readonly FS | `disable_usb_drive()` doesn't remount as readonly |
| Memory pressure (WiFi + interpreter) | RP2350 has 264KB SRAM. No WSGI dependency — raw sockets. |

**No existing tests break** — interpreter, parser, lexer, and preprocessor are all untouched.
