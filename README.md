# kducky

DuckyScript 3 Interpreter for **Raspberry Pi Pico 2 W** (RP2350) · CircuitPython 10.x

Run USB Rubber Ducky payloads from a $6 microcontroller that appears as a
keyboard to any computer.

---

## Quick Start (Pico)

1. Download **CircuitPython 10.x** for the Pico 2 W
   ([circuitpython.org](http://google.com)) and flash it via BOOTSEL mode.
2. Download the **Adafruit HID library** from the
   [CircuitPython library bundle](http://google.com) and copy `adafruit_hid/`
   to `CIRCUITPY/lib/`.
3. Run the deploy script to copy kducky to your Pico:
   ```bash
   python deploy.py D:\   # or wherever CIRCUITPY mounts
   ```
4. Create `payload.dd` on CIRCUITPY with your DuckyScript payload.
5. Plug the Pico into any computer — it runs the payload immediately.

> Full deployment instructions → [`DEPLOYMENT.md`](DEPLOYMENT.md)

---

## What Works

| Category | Commands |
|----------|----------|
| **Typing** | `STRING`, `STRINGLN`, `DELAY`, `DEFAULT_DELAY`, `DEFAULT_CHAR_DELAY` |
| **Modifier combos** | `GUI`, `CTRL`, `SHIFT`, `ALT` + any key (e.g. `GUI r`, `CTRL ALT DEL`) |
| **Hold / Release** | `HOLD`, `RELEASE`, `INJECT_MOD` |
| **Variables** | `VAR $x = 5`, `$x = $x + 1` |
| **Functions** | `FUNCTION`, `CALL`, `RETURN` |
| **Control flow** | `IF`, `WHILE`, `BREAK`, `CONTINUE` |
| **Keyboard layouts** | `DUCKY_LANG DE` — 16 layouts (US, GB, DE, FR, ES, IT, JP, DK, NO, SE, FI, PT, BR, RU, PL, CZ) |
| **Random** | `RANDOM_MIN_MAX`, `RANDOM_CHAR` |
| **Arithmetic** | Full expression support (`+`, `-`, `*`, `/`, `%`, `&`, `|`, comparisons, etc.) |
| **Comments** | `REM` |
<!-- table not formatted: invalid structure -->

## Planned / Not Yet Implemented

| Command | Status |
|---------|--------|
| `REPEAT` | Parsed, no runtime yet |
| `DEFINE` (preprocessor) | Next milestone |
| `ATTACKMODE` | Planned (M18) |
| `LED` control | Planned (M18) |
| Button handling | Planned (M18) |
| `WAIT_FOR_KEY` | Planned (M18) |
| Error reporting | Planned (M17) |
<!-- table not formatted: invalid structure -->

---

## Development

```bash
pip install -e ".[dev]"
pytest              # 558 tests, all passing
ruff check src/ tests/
mypy src/ tests/
```

The interpreter runs on **any Python 3.10+** machine for development. A desktop
platform backend simulates keyboard output so you can test payloads without a
Pico.

---

## Project Status

**~95% of DuckyScript 1** (original Hak5) and **~60% of DuckyScript 3** (full
spec with variables, functions, control flow, layouts) is implemented. See
[`plans/DuckyScript3_Implementation_Roadmap.md`](plans/DuckyScript3_Implementation_Roadmap.md)
for the remaining milestones.
