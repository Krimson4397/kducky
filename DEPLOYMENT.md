# kducky Deployment Guide

Deploy the DuckyScript 3 interpreter to a **Raspberry Pi Pico 2 W** running
CircuitPython 10.x.

---

## Prerequisites

### Hardware

- **Raspberry Pi Pico 2 W** (RP2350) with a USB cable (data, not charge-only)
- **Target computer** — a Windows, macOS, or Linux machine where you want the
  payload to execute (the Pico appears as a USB keyboard)

### Software

- **CircuitPython 10.x** installed on the Pico 2 W
  ([guide](https://learn.adafruit.com/getting-started-with-raspberry-pi-pico-circuitpython/circuitpython))
- **Adafruit CircuitPython Library Bundle 10.x**
  ([download](https://circuitpython.org/libraries)) — specifically the
  `adafruit_hid/` library
- **Python 3.10+** on your development machine (to run `deploy.py`)
- **USB cable** to connect the Pico to your development machine during setup

---

## CIRCUITPY Drive Layout

When you plug the Pico into your computer after installing CircuitPython, it
mounts as a mass-storage drive called **CIRCUITPY**.  The files below must be
placed at the exact paths shown.

| Repo file | CIRCUITPY path | Purpose |
|---|---|---|
| `src/platform/pico/boot.py` | `/boot.py` | USB configuration at power-on |
| `src/platform/pico/main.py` | `/code.py` | Auto-run entry point (checked first by CircuitPython) |
| `src/platform/pico/main.py` | `/main.py` | Fallback entry point (if `code.py` absent) |
| `src/platform/pico/backends.py` | `/platform/pico/backends.py` | PicoPlatform — all hardware I/O |
| `src/platform/desktop/__init__.py` | `/platform/desktop/__init__.py` | Desktop test backend package marker |
| `src/platform/__init__.py` | `/platform/__init__.py` | Platform package marker |
| `src/platform/pico/__init__.py` | `/platform/pico/__init__.py` | Pico subpackage marker |
| `src/ducky/__init__.py` | `/ducky/__init__.py` | Language core package marker |
| `src/ducky/tokens.py` | `/ducky/tokens.py` | Token and key-code enums |
| `src/ducky/lexer.py` | `/ducky/lexer.py` | DuckyScript lexer |
| `src/ducky/parser.py` | `/ducky/parser.py` | DuckyScript parser |
| `src/ducky/interpreter.py` | `/ducky/interpreter.py` | DuckyScript interpreter |
| `src/ducky/ast/__init__.py` | `/ducky/ast/__init__.py` | AST package marker |
| `src/ducky/ast/nodes.py` | `/ducky/ast/nodes.py` | All AST node definitions |
| `src/ducky/utils/__init__.py` | `/ducky/utils/__init__.py` | Utils package marker |
| `src/ducky/utils/visitor.py` | `/ducky/utils/visitor.py` | NodeVisitor base class |
| `src/ducky/utils/compat.py` | `/ducky/utils/compat.py` | CircuitPython compatibility shim for dataclasses, enum, Protocol |
| `src/ducky/platform/__init__.py` | `/ducky/platform/__init__.py` | PlatformInterface protocol |
| `src/ducky/platform/desktop.py` | `/ducky/platform/desktop.py` | DesktopPlatform — test backend for development |
| *(user creates)* | `/payload.dd` | Your DuckyScript payload file |
| *(from Adafruit bundle)* | `/lib/adafruit_hid/` | Adafruit HID library (see below) |

### Adafruit HID library files (from bundle)

| Bundle path | CIRCUITPY path |
|---|---|
| `lib/adafruit_hid/__init__.py` | `/lib/adafruit_hid/__init__.py` |
| `lib/adafruit_hid/keyboard.py` | `/lib/adafruit_hid/keyboard.py` |
| `lib/adafruit_hid/keyboard_layout_us.py` | `/lib/adafruit_hid/keyboard_layout_us.py` |
| `lib/adafruit_hid/keycode.py` | `/lib/adafruit_hid/keycode.py` |

> **Total space used:** ~70 KB for the kducky files + ~60 KB for `adafruit_hid/`
> = ~130 KB.  CIRCUITPY typically has ~2 MB free, so there is ample room.

---

## Step-by-Step Instructions

### 1. Install CircuitPython on the Pico 2 W

1. Download CircuitPython 10.x for the Raspberry Pi Pico 2 W from
   [circuitpython.org](https://circuitpython.org/board/raspberry_pi_pico2w/).
2. Press and hold the **BOOTSEL** button on the Pico while plugging it into
   your computer via USB.
3. Release BOOTSEL — the Pico appears as a **RPI-RP2** drive.
4. Copy the downloaded `.uf2` file to the **RPI-RP2** drive.  The Pico
   automatically reboots and now appears as **CIRCUITPY**.
5. Verify by opening `CIRCUITPY` — it should contain `boot_out.txt` with the
   CircuitPython version.

### 2. Download the Adafruit Library Bundle

1. Go to [circuitpython.org/libraries](https://circuitpython.org/libraries)
   and download the bundle matching your CircuitPython version (10.x).
2. Extract the ZIP archive.
3. Copy the **entire** `adafruit_hid/` folder from the bundle's `lib/`
   directory to `CIRCUITPY/lib/`:

   ```
   lib/adafruit_hid/       ← from the bundle
   ├── __init__.py
   ├── keyboard.py
   ├── keyboard_layout_us.py
   └── keycode.py
   ```

   Result on CIRCUITPY:
   ```
   /boot_out.txt
   /lib/
   └── adafruit_hid/
       ├── __init__.py
       ├── keyboard.py
       ├── keyboard_layout_us.py
       └── keycode.py
   ```

### 3. Deploy kducky Files

Run the deploy script from the repo root, pointing it at the CIRCUITPY drive:

```bash
# Windows (CIRCUITPY is typically D: or E:)
python deploy.py E:\

# macOS / Linux
python deploy.py /media/yourname/CIRCUITPY
```

You should see output similar to:

```
  COPY  ducky/interpreter.py  (17042 bytes)
  COPY  ducky/lexer.py  (20630 bytes)
  COPY  ducky/parser.py  (44391 bytes)
  COPY  ducky/tokens.py  (11997 bytes)
  COPY  ducky/__init__.py  (86 bytes)
  COPY  ducky/ast/nodes.py  (10794 bytes)
  COPY  ducky/ast/__init__.py  (2277 bytes)
  COPY  ducky/platform/desktop.py  (6277 bytes)
  COPY  ducky/platform/__init__.py  (5854 bytes)
  COPY  ducky/utils/compat.py  (7324 bytes)
  COPY  ducky/utils/visitor.py  (557 bytes)
  COPY  ducky/utils/__init__.py  (41 bytes)
  COPY  platform/__init__.py  (0 bytes)
  COPY  platform/desktop/__init__.py  (0 bytes)
  COPY  platform/pico/backends.py  (17232 bytes)
  COPY  boot.py  (1523 bytes)
  COPY  code.py  (3917 bytes)
  COPY  main.py  (3917 bytes)
  COPY  platform/pico/__init__.py  (0 bytes)

  Copied 19 file(s) (150 KB), 0 already up to date
```

The deploy script automatically discovers all `.py` files under `src/` at
runtime — no manual manifest to update.  Any file added to the `src/` tree
is deployed automatically.  Re-run the script after any code changes and it
will only overwrite files whose content has changed (MD5 content hash).

#### Dry Run

To preview what would be copied without touching the drive:

```bash
python deploy.py --dry-run E:\
```

### 4. Create a Payload

Create `payload.dd` on the CIRCUITPY drive with a DuckyScript payload:

```
REM Hello from kducky!
REM This is a simple DuckyScript test payload.

STRING Hello from Pico!
STRINGLN
DELAY 1000
STRINGLN The interpreter works!
```

You can either copy the template from the repo:

```bash
cp payloads/hello.dd E:\payload.dd
```

Or create it manually in a text editor and save directly to the CIRCUITPY
drive.

### 5. Run It

1. **Safely eject** CIRCUITPY from your development machine.
2. Plug the Pico into the **target computer** (the machine where you want the
   payload to execute).
3. Wait ~2 seconds for the Pico to boot.
4. The Pico types the payload text onto the target computer.

The onboard LED indicates status:

| LED | Meaning |
|---|---|
| **Green** (solid) | Payload running or completed successfully |
| **Red** (solid) | Error — no payload file or runtime failure |
| **Off** | After execution (or during `DELAY` commands) |

---

## LED Status Reference

| State | When |
|---|---|
| Green (solid) | `main.py` starts executing; stays green on success |
| Red (solid) | No `/payload.dd` found, or a runtime error occurred |
| Off (after green) | Payload completed normally |
| Off (after red) | Payload failed — check the payload file and syntax |

---

## Payload Template

`payloads/hello.dd` in the repo provides a minimal working payload:

```
REM Hello from kducky!
REM REM lines are comments — they are ignored by the interpreter.
REM
REM STRING types the following text as-is.
REM STRINGLN types text followed by Enter (Return).
REM DELAY pauses for the given number of milliseconds.

STRING Hello from Pico!
STRINGLN
DELAY 1000
STRINGLN The interpreter works!
```

Create your own payloads by editing `payload.dd` on the CIRCUITPY drive.
Refer to the DuckyScript 3 language specification for supported commands.

---

## Troubleshooting

### Serial Console (Debugging)

Connect a serial monitor to see Python tracebacks:

- **Windows:** [PuTTY](https://www.putty.org/) — connect to the COM port
  shown in Device Manager, baud rate **115200**.
- **macOS / Linux:** `screen /dev/tty.usbmodem* 115200` (or
  `/dev/ttyACM*`).

The serial console shows `print()` output, tracebacks, and the startup
message from `main.py`.

### Boot Button Recovery

If the Pico becomes unresponsive or you need to reinstall CircuitPython:

1. Hold the **BOOTSEL** button on the Pico.
2. Plug it into your computer via USB.
3. Release BOOTSEL — it appears as **RPI-RP2**.
4. Drop a `.uf2` firmware file onto the drive to reflash.

### STORAGE_DISABLE (Payload-Only Mode)

To prevent the target computer from accessing the CIRCUITPY filesystem,
create an empty file named `STORAGE_DISABLE` (no extension) in the root of
CIRCUITPY *before* disconnecting from your development machine:

```bash
# On your dev machine, with CIRCUITPY mounted:
touch E:\STORAGE_DISABLE
```

Then safely eject.  The Pico will no longer expose its filesystem to the
host — only the USB keyboard HID device appears.  To restore access, delete
`STORAGE_DISABLE` (requires rebooting into BOOTSEL mode and reflashing, or
using the serial console to delete the file).

### File Too Large / Disk Full

CIRCUITPY has approximately 2 MB of available space.  The kducky core + HID
library uses ~130 KB.  If you see disk-full errors:

- Remove unused files from CIRCUITPY (e.g. sample code from the initial
  install).
- Check for `.DS_Store` or `Thumbs.db` clutter from your OS.
- The deploy script skips unchanged files — so only the first copy uses
  space.

### ImportError at Runtime

If the LED turns red immediately, connect the serial console to check the
error.  Common causes:

| Error | Fix |
|---|---|
| `ImportError: no module named 'adafruit_hid'` | Copy `adafruit_hid/` from the Adafruit bundle to `/lib/` |
| `ImportError: no module named 'ducky'` | Run `deploy.py` — the `ducky/` package is missing |
| `ImportError: no module named 'ducky.utils.compat'` | Re-run `deploy.py` — the file was added after your last deployment |
| `OSError: No such file: /payload.dd` | Create a `payload.dd` file on CIRCUITPY |
| `SyntaxError` in payload | Check payload syntax — run it through the desktop tests first |

### USB Keyboard Not Working

If the Pico connects but no keystrokes register:

- Verify `boot.py` is present (it enables USB HID).
- Try a different USB port or cable (some cables are charge-only).
- Check the serial console for import errors.
- On some systems, the first USB keyboard input is ignored during driver
  initialisation — add `DELAY 2000` at the top of your payload.

### Permission Errors Running deploy.py

On **Linux**, you may need to mount the CIRCUITPY drive with write
permissions.  It usually auto-mounts as the current user; if not:

```bash
sudo mount -o uid=$(id -u),gid=$(id -g) /dev/sdX1 /media/CIRCUITPY
```

On **macOS**, the drive typically mounts with full permissions.

On **Windows**, ensure the drive letter is correct and no application has the
drive locked (close Explorer windows browsing the drive).

### Testing on Desktop Without a Pico

You can run the interpreter on any Python 3.10+ machine for development and
testing:

```bash
pip install -e ".[dev]"
pytest
```

The desktop platform backend (`src/platform/desktop.py`) simulates keyboard
output, allowing full end-to-end testing without hardware.

---

## Filesystem Layout (Complete Reference)

After following all steps, your CIRCUITPY drive should look like this:

```
/                           Root of CIRCUITPY
├── boot.py                 USB config (copied from repo)
├── code.py                 Auto-run entry point (copied from repo)
├── main.py                 Fallback entry point (copied from repo)
├── payload.dd              Your DuckyScript payload (you create)
│
├── lib/
│   └── adafruit_hid/       Adafruit HID library (from bundle)
│       ├── __init__.py
│       ├── keyboard.py
│       ├── keyboard_layout_us.py
│       └── keycode.py
│
├── ducky/                  Language core (copied from repo)
│   ├── __init__.py
│   ├── tokens.py
│   ├── lexer.py
│   ├── parser.py
│   ├── interpreter.py
│   ├── ast/
│   │   ├── __init__.py
│   │   └── nodes.py
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── compat.py
│   │   └── visitor.py
│   └── platform/
│       └── __init__.py
│
└── platform/               Hardware backend (copied from repo)
    ├── __init__.py
    ├── desktop/
    │   └── __init__.py
    └── pico/
        ├── __init__.py
        └── backends.py
```
