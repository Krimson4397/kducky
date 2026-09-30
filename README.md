# kducky
<p align="center"> <a href="https://www.youtube.com/watch?v=gdXXOYqnnxM"> <img src="https://img.youtube.com/vi/gdXXOYqnnxM/maxresdefault.jpg" alt="Kducky Demo" width="100%"> </a> </p>

<p align="center"> <strong>▶ Click the video above to watch the Kducky demo</strong> </p>
DuckyScript 3 Interpreter for **Raspberry Pi Pico 2 W** (RP2350) · CircuitPython 10.x

Run USB Rubber Ducky payloads from a $6 microcontroller that appears as a
keyboard to any computer. All D3 core commands are implemented, with desktop
testing and hardware validation on Pico.

---

## Architecture

```
Source → Preprocessor → Lexer → Parser → AST → Interpreter → PlatformInterface
                                                                ↙         ↘
                                                     DesktopPlatform  PicoPlatform
```

Language modules (preprocessor, lexer, parser, AST, interpreter) are fully
decoupled from hardware. A `PlatformInterface` protocol abstracts all I/O —
keyboard, mouse, LED, buttons, attack mode — so the same interpreter runs on
desktop CPython (for development and testing) and on CircuitPython (for Pico
production). The language core never imports CircuitPython.

---

## Quick Start (Pico)

1. Download **CircuitPython 10.x** for the Pico 2 W
   ([circuitpython.org](https://circuitpython.org/board/raspberry_pi_pico2_w/)) and flash it via BOOTSEL mode.
2. Download the **Adafruit HID library** from the
   [CircuitPython library bundle](https://circuitpython.org/libraries) and copy `adafruit_hid/`
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
| **Typing** | `STRING`, `STRINGLN`, `DELAY`, `DEFAULT_DELAY`, `DEFAULT_CHAR_DELAY`, `STRINGDELAY` |
| **Modifier combos** | `GUI`, `CTRL`, `SHIFT`, `ALT` + any key (e.g. `GUI r`, `CTRL ALT DEL`) |
| **Hold / Release** | `HOLD`, `RELEASE`, `INJECT_MOD` |
| **Control flow** | `IF` / `ELSE` / `END_IF`, `WHILE` / `END_WHILE`, `BREAK`, `CONTINUE`, `REPEAT` |
| **Functions** | `FUNCTION` / `END_FUNCTION`, `CALL`, `RETURN` |
| **Variables** | `VAR $x = 5`, `$x = $x + 1`, full expression support |
| **Arithmetic** | `+`, `-`, `*`, `/`, `%`, `&`, `\|`, comparisons, parentheses |
| **Random** | `RANDOM_MIN_MAX`, `RANDOM_CHAR` |
| **Comments** | `REM` |
| **Preprocessor** | `DEFINE #NAME value`, `#NAME` substitution (skipped inside quotes) |
| **Keyboard layouts** | `DUCKY_LANG DE` — 16 layouts (US, GB, DE, FR, ES, IT, JP, DK, NO, SE, FI, PT, BR, RU, PL, CZ) |
| **Reboot** | `REBOOT` — GUI r → shutdown /r /t 0 |
| **Replay** | `REPLAY` — restart payload from beginning |
| **Jitter** | `JITTER ON` / `OFF` / `DELAY min max` |
| **Inject Var** | `INJECT_VAR $name` — type variable value as keystrokes |
| **Internal vars** | `$_IS_CAPSLOCK_ON`, `$_IS_NUMLOCK_ON`, `$_IS_SCROLLLOCK_ON`, `$_RANDOM_MIN`, `$_RANDOM_MAX`, `$_RANDOM_INT`, `$_BUTTON_ENABLED` |
| **Block strings** | `STRING` / `STRINGLN` block mode with `END_STRING` / `END_STRINGLN` |
| **Mouse** | `MOUSE_MOVE`, `MOUSE_MOVE_TO`, `MOUSE_CLICK`, `MOUSE_DOWN`, `MOUSE_UP`, `MOUSE_SCROLL` (LEFT / RIGHT / MIDDLE) |
| **LED** | `LED OFF` / `R` / `G` / `B` |
| **Attack mode** | `ATTACKMODE`, `SAVE_ATTACKMODE`, `RESTORE_ATTACKMODE` |
| **Lock keys** | `SAVE_HOST_LOCK_STATE`, `RESTORE_HOST_LOCK_STATE`, `WAIT_FOR_KEY` |
| **Buttons** | `BUTTON_DEF`, `ENABLE_BUTTON`, `DISABLE_BUTTON`, `WAIT_FOR_BUTTON_PRESS` |
| **Payload control** | `HIDE_PAYLOAD`, `RESTORE_PAYLOAD` |
| **Error hierarchy** | `LexerError`, `ParseError`, `InterpreterError`, `PreprocessorError` — all with standard format `[ERROR] line N: message` |
| **Desktop mock** | Full `PlatformInterface` implementation for testing on any Python 3.10+ without hardware |

---

## Roadmap — Next Features

Features we plan to implement, ranked by feasibility. This section guides the next development session.

### Tier 1: Easy / Well-Understood
| Feature | Notes | Approach |
|---------|-------|----------|
| `EXFIL` (LED encoding) | Exfiltrate data via Caps Lock/Num Lock LED states | Encode bits via keyboard LED state toggling, read back from HID reports, store in loot.bin. No WiFi needed. Pattern from pico-ducky. |
| `RANDOM_LINE` | Read a random line from a file | Built-in `os.listdir()` + `open()` + `random.choice()`. Filesystem access available. |
| `RANDOM_STRING` | Generate random printable strings | Built-in `random` module. Configurable length and character set. |
| `F13`–`F24` | Extended function keys | Standard USB HID usage IDs — add to keycode maps in PicoPlatform backend. |
| Extended media keys | Beyond basic set | Standard USB HID consumer page codes — update keycode maps. |
| `JIGGLER` | Periodic mouse movement | Simple DuckyScript loop with MOUSE_MOVE, or a new language command. |

### Tier 2: Moderate Effort
| Feature | Notes | Approach |
|---------|-------|----------|
| `EXFIL` (WiFi) | Exfiltrate data via HTTP POST | Use built-in `wifi` + `socketpool` + `ssl` (zero deps) or `adafruit_requests` + `adafruit_connection_manager` (~40KB from Adafruit Bundle). Needs WiFi credentials. |
| Embedded language blocks | `STRING_POWERSHELL`, `STRING_BATCH`, `STRING_BASH`, `STRING_JAVASCRIPT`, `STRING_PYTHON`, `STRING_RUBY`, `STRING_HTML` | Preprocessor-like transform on string content before typing. Language-specific escaping and newline conventions. |

### Tier 3: Not Feasible (CircuitPython Constraints)
| Feature | Notes | Why |
|---------|-------|-----|
| `KEYCODE` | Raw HID report injection | O.MG-specific. Requires low-level USB descriptor manipulation. CircuitPython's `adafruit_hid` doesn't expose raw HID reports. Not feasible without firmware-level changes. |

---

## Development

```bash
pip install -e ".[dev]"
pytest              # 784 tests, all passing
ruff check src/ tests/
mypy src/ tests/
```

The interpreter runs on **any Python 3.10+** machine for development. A desktop
platform backend (`DesktopPlatform`) simulates all HID operations so you can
test and debug payloads without a Pico. The full test suite runs in seconds.

---

## Project Status

**~95% of DuckyScript 3** (core spec plus project extensions) is implemented.
The interpreter passes 784 tests and is clean under ruff and mypy. Hardware
validation has been completed on Raspberry Pi Pico 2 W.

See
[`plans/DuckyScript3_Implementation_Roadmap.md`](plans/DuckyScript3_Implementation_Roadmap.md)
for the remaining milestones (HW validation documentation, CLI, CI).
