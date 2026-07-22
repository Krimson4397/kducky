# AGENTS.md — Project Operating Manual

> DuckyScript 3 Interpreter for Raspberry Pi Pico 2 W (RP2350) · CircuitPython 10.x  

---

## 1. Project Overview

**Project name:** kducky  
**Purpose:** A modular, portable DuckyScript 3 interpreter that runs on the Raspberry Pi Pico 2 W, allowing users to execute USB Rubber Ducky payloads from an embedded microcontroller.  
**Target hardware:** Raspberry Pi Pico 2 W (RP2350) — CircuitPython 10.x  
**Supported language:** DuckyScript 3 (Hak5 USB Rubber Ducky language) with project extensions  
**Current status:** KISS runtime (WiFi removed) — payload-only execution. Post-payload WiFi retrieval planned.  
**High-level architecture:** Language modules (Lexer → Parser → AST → Interpreter) communicate through well-defined interfaces and are fully decoupled from hardware. A PlatformInterface layer abstracts all hardware I/O, enabling the same interpreter code to run on desktop CPython (for development and testing) and on CircuitPython (for production). The language core never imports CircuitPython.

---

## 2. Project Authority

The following documents are the **only authoritative** project documents. Every AI agent **must** read them completely before making any change. Read them in this exact order:

1. `plans/DuckyScript3_Engineering_Spec.md` — Frozen language specification, grammar, runtime semantics, Platform API, architecture rules.
2. `plans/DuckyScript3_Implementation_Roadmap.md` — 20 milestones with dependencies, acceptance criteria, and build order.
3. `plans/Development_Workflow.md` — Day-to-day workflow: milestone process, spec rules, git workflow, implementation principles.

**Do NOT use:** `plans/spec.md` — exists only as a historical artifact from early design work. It is not authoritative and must not influence implementation.

**Conflict resolution:** If the Engineering Specification and any other document (including this one) conflict, the Engineering Specification wins.

---

## 3. Startup Checklist

Before writing any code, an AI agent must:

- [ ] Read all three planning documents (Section 2 above).
- [ ] Review the latest Session Handoff (§8).
- [ ] Verify the current Git branch.
- [ ] Verify the working tree is clean (`git status` shows no uncommitted changes).
- [ ] Verify which milestone is active (from Session Handoff).
- [ ] Confirm the acceptance criteria for that milestone (from the roadmap).

Only after completing the checklist may implementation begin.

---

## 4. Repository Layout

```
kducky/
│
├── plans/
│   ├── DuckyScript3_Engineering_Spec.md   (frozen specification)
│   ├── DuckyScript3_Implementation_Roadmap.md  (milestone plan)
│   ├── Development_Workflow.md           (implementation guide)
│   └── spec.md                           (IGNORED — historical artifact)
│
├── src/
│   ├── ducky/
│   │   ├── __init__.py
│   │   ├── lexer/         # Lexer: character stream → token stream
│   │   ├── parser/        # Parser: token stream → AST
│   │   ├── ast/           # AST node definitions (pure data, no logic)
│   │   ├── interpreter/   # Interpreter: AST → platform actions
│   │   ├── runtime/       # Runtime state (variables, functions, stack)
│   │   ├── platform/      # PlatformInterface protocols + shared types
│   │   └── utils/         # Shared utilities (errors, helpers)
│   └── platform/          # Hardware backends (CircuitPython only)
│       └── pico/          # Raspberry Pi Pico 2 W backend
│
├── tests/                 # All tests (pytest)
│
├── pyproject.toml          # Project metadata, dependencies, tool config
├── README.md
├── LICENSE
├── .gitignore
├── AGENTS.md              # This file — project operating manual
└── ...
```

- All implementation code belongs under `src/`.
- All tests belong under `tests/`.
- Modern Python src layout — install with `pip install -e .`.

---

## 5. Development Principles

Project priorities, in order:

1. **Correctness** — Behavior matches the Engineering Specification.
2. **Maintainability** — Clear, well-structured code.
3. **Portability** — Translatable to C/C++ without redesign.
4. **Testability** — Every module testable in isolation on desktop Python.
5. **Performance** — Fast enough for the target hardware.

Never sacrifice a higher-priority criterion for a lower one. Never optimize prematurely.

---

## 6. Working Rules

Every AI agent **must**:

- Work on exactly **one** milestone at a time.
- **Never work ahead** — do not write code for future milestones.
- **Never modify future milestones** in the planning documents.
- **Never silently change the architecture** defined in the spec.
- **Never silently change language behavior** defined in the spec.
- **Never ignore acceptance criteria** for the current milestone.
- **Never skip tests** — all tests must pass before a milestone is complete.
- **Never leave placeholder implementations** unless explicitly approved.
- **Stop immediately** if an ambiguity or spec conflict is discovered.
- **Wait for user approval** before beginning the next milestone.

---

## 7. Git Workflow

Every completed milestone = exactly **one** commit.

### Process

1. Complete implementation.
2. Complete all tests.
3. Verify all acceptance criteria are met.
4. Review all modified files (`git diff`).
5. Run formatting, linting, and type checking (`ruff check src/ tests/ && mypy src/ tests/`).
6. Stage only the files belonging to this milestone.
7. Create exactly one commit.

### Commit message format

```
Milestone X: <short description>
```

**Examples:**

```
Milestone 1: Repository scaffold
Milestone 2: Token definitions
Milestone 3: Lexer implementation
```

**Never** combine multiple milestones into a single commit. **Never** commit unfinished work.

---

## 8. Session Handoff

This section **must** be updated at the completion of every milestone. It describes the current state of the repository for the next AI agent.

### Handoff Summary

| Field                 | Value                            |
| --------------------- | -------------------------------- |
| Project Version       | 1.0.0                            |
| Completed Feature     | WiFi removal (KISS runtime) + Post-payload WiFi plan |
| Current Branch        | main                             |
| Last Commit           | fb5bc7a                          |
| Repository Status     | Clean working tree |
| Next Milestone        | Post-payload WiFi retrieval (see plans/Post_Payload_WiFi_Plan.md) |
| Blocking Issues       | None                             |
| Ready to Continue     | YES (awaiting user approval) |

### Files Created

- `plans/Pico_Runtime_Features_Plan.md` — Design document for Pico runtime features
- `plans/Post_Payload_WiFi_Plan.md` — Design plan for post-payload WiFi retrieval
- `src/platform/pico/logger.py` — Rotating dual-file log (`/logs/latest.log`, `/logs/previous.log`)
- `src/platform/pico/crash.py` — Crash counter + lockout manager (threshold=3, `/system/` state files)
- `src/platform/pico/payload.py` — Payload manager with CRC32 fingerprint, atomic update with validate
- `src/platform/pico/wifi.py` — WiFi connection manager (station-first, AP fallback, secrets.py)
- `src/platform/pico/webapp.py` — HTTP server (GET /, GET /status, POST /payload, GET /logs)
- `src/platform/pico/runtime.py` — Runtime coordinator with start()/run()/stop() lifecycle

### Files Modified

- `src/platform/pico/boot.py` — Rewritten: 4 boot modes from GPIO jumpers (GP0+GP15), /system/FORCE_USB_VISIBLE recovery flag, writes /system/boot_reason
- `src/platform/pico/main.py` — Rewritten: thin entry point (56 LOC) delegating to Runtime, _crash_handler for crash counting/logging

### Files Deleted (WiFi Removal)

- `src/platform/pico/wifi.py` — DELETED
- `src/platform/pico/webapp.py` — DELETED
- `src/platform/pico/runtime.py` — Stripped of all WiFi/web imports and logic; simplified to just payload execution

### Previously Committed (da5be05) — Interpreter fixes from hardware validation

- `src/ducky/lexer.py` — REM_BLOCK: skip leading whitespace before END_REM check (fixes indented `END_REM`)
- `src/ducky/parser.py` — Pratt parser: replaced 12-method recursive cascade with iterative precedence climbing (fixes pystack exhaustion on CircuitPython); WINDOWS keyword → StringExpr fallthrough; blank line before block terminator fix
- `src/ducky/interpreter.py` — $_ vars auto-create on assign/read (default 0); StringExpr/IdentifierExpr/HashIdentifierExpr visitors return 0; ExtensionStmt revert to skip (auto-create-on-read handles missing §_ vars)
- `tests/test_interpreter_core.py` — Updated for StringExpr behavior change
- `tests/test_parser_edge_cases.py` — Updated for new parser behaviors

### Tests Executed

- `python -m pytest tests/ -x -q` — **784 passed, 6 skipped** (no regressions from pre-implementation baseline)
- `ruff check src/ tests/` — All checks passed

### Acceptance Criteria Completed

- [x] Single `PicoPlatform` class implements flat `PlatformInterface` protocol (all 26 methods)
- [x] Guarded imports allow module import on desktop (`_HAS_HW` is `False`)
- [x] `_ACTION_KEY_MAP` covers all 69 `ActionKey` members (with `getattr` fallbacks for uncommon keycodes like KEYPAD_00)
- [x] `_MODIFIER_KEY_MAP` covers all 8 `ModifierKey` members
- [x] Contract tests verify interface compliance structurally without hardware
- [x] `boot.py` configures USB HID + optional storage disable
- [x] `main.py` is a drop-in runner for auto-execution on Pico
- [x] Signal methods (`restart_payload`, `stop_payload`) raise correct exceptions
- [x] All 549 tests pass, ruff clean
- [x] 16 keyboard layout JSON files (US + 15 international) under `src/ducky/layouts/`
- [x] Layout loader module (`load`, `available`, `add_layout`) with caching and US-fallback inheritance
- [x] `set_layout`/`get_layout` added to `PlatformInterface` protocol
- [x] `DesktopPlatform` implements `set_layout`/`get_layout` with call recording
- [x] `PicoPlatform.type_string` rewritten to use `Layout.keycode_for()` instead of `KeyboardLayoutUS`
- [x] `visit_DuckyLangStmt` in interpreter calls `platform.set_layout()`
- [x] 9 layout tests pass (layout loading, inheritance, case insensitivity, platform, interpreter)
- [x] All 558 tests pass, ruff clean
- [x] HOLD/RELEASE accept `ModifierKey` (key type widened from `ActionKey` to `object`)
- [x] INJECT_MOD required before HOLD of modifier key, NOT required before RELEASE (per official Hak5 docs)
- [x] Engineering Spec §5.3 updated with official holding-keys example
- [x] `_inject_mod_pending` flag in parser tracks INJECT_MOD state across statements
- [x] `PicoPlatform._hid_keycode_for` handles `ModifierKey` instances
- [x] 7 new parser tests cover all HOLD/RELEASE modifier scenarios
- [x] Interpreter integration test verifies end-to-end SHIFT modifier sequence
- [x] All 565 tests pass, ruff clean
- [x] `src/ducky/preprocessor.py` created with `Preprocessor` class and `PreprocessorError`
- [x] Preprocessor scans source for `DEFINE #NAME value` lines (case-insensitive keyword)
- [x] DEFINE lines replaced with blank lines to preserve source line numbering
- [x] `#NAME` references substituted with literal values in all subsequent lines
- [x] Substitution skipped inside `"..."` quoted strings (handles `\"` escapes)
- [x] Undefined `#NAME` reference raises `PreprocessorError` with line number
- [x] `DEFINE #DELAY 2000` + `DELAY #DELAY` produces `DELAY 2000`
- [x] `DEFINE #TEXT Hello World` + `STRINGLN #TEXT` types "Hello World"
- [x] `DEFINE #X` with no value yields empty string for `#X`
- [x] Preprocessor integrated into integration test pipeline (`_execute` helper)
- [x] 25 preprocessor-specific tests pass
- [x] 3 new integration tests for DEFINE
- [x] Pico runner `main.py` calls Preprocessor before Lexer (architectural fix)
- [x] `DefineStmt` AST node class removed — DEFINE is exclusively preprocessor-only
- [x] `TokenType.DEFINE` removed from lexer — no token path for DEFINE exists
- [x] Parser no longer has `_parse_define_stmt` — no AST path for DEFINE exists
- [x] All existing parser/lexer tests updated to remove DEFINE references
- [x] All 587 tests pass, ruff clean
- [x] `src/ducky/errors.py` created with `DuckyError` base class
- [x] All four error types (`LexerError`, `ParseError`, `InterpreterError`, `PreprocessorError`) inherit from `DuckyError`
- [x] Standard format `[ERROR] line N, col M: message` for `LexerError` and `ParseError`
- [x] Standard format `[ERROR] line N: message` for `PreprocessorError`
- [x] Standard format `[ERROR] message` for `InterpreterError` (no line/col from AST)
- [x] Backward compatibility: `from ducky.lexer import LexerError` (etc.) still works
- [x] `InterpreterError` retained (not renamed to `RuntimeError` — Python built-in conflict)
- [x] `source_snippet` and `cause` stored as attributes, not included in `str()`
- [x] All 22 error-hierarchy tests pass
- [x] All 615 tests pass, ruff clean
- [x] All 13 missing interpreter visitor methods implemented in `interpreter.py`
- [x] `visit_LedStmt` — calls `platform.set_led()` for all 4 LedState values (OFF/R/G/B)
- [x] `visit_AttackModeStmt` — calls `platform.set_attack_mode(params)`
- [x] `visit_SaveAttackModeStmt` / `visit_RestoreAttackModeStmt` — save/restore attack mode
- [x] `visit_SaveHostLockStateStmt` / `visit_RestoreHostLockStateStmt` — save/restore lock state
- [x] `visit_WaitForKeyStmt` — polls platform getter until target lock key state (ON/OFF/CHANGE)
- [x] `visit_ButtonDefStmt` — registered in phase-1 like FunctionDef, skipped in phase-2
- [x] `visit_EnableButtonStmt` / `visit_DisableButtonStmt` — calls platform enable/disable
- [x] `visit_WaitForButtonPressStmt` — calls `platform.wait_for_button_press()`
- [x] `visit_HidePayloadStmt` / `visit_RestorePayloadStmt` — calls platform hide/restore
- [x] 18 tests covering all 13 visitors pass
- [x] `payloads/payload.dd` updated — runs to completion, types "all_done" as last line
- [x] `deploy.py` copies `payload.dd` to CIRCUITPY drive
- [x] Full suite: 633 tests pass, ruff clean, working tree clean
- [x] **B1: REBOOT** — `reboot_target()` sends GUI r → shutdown /r /t 0; full pipeline (token → AST → parser → interpreter → PicoPlatform)
- [x] **B2: REPLAY** — `ReplayStmt` raises `RestartPayloadSignal`; `main.py` retry loop catches signal and restarts
- [x] **B3: JITTER** — `JITTER ON/OFF/DELAY min max`; `_maybe_jitter()` adds random per-char delay; integrated into `_type_text`
- [x] **B4: INJECT_VAR** — `INJECT_VAR $name` types variable value as keystrokes; searches locals → globals; keyboard error guard
- [x] **B5: $_ internal variables** — `_populate_internal_vars()` pre-populates `$_IS_CAPSLOCK_ON`, `$_IS_NUMLOCK_ON`, `$_IS_SCROLLLOCK_ON` (from platform), `$_RANDOM_MIN=0`, `$_RANDOM_MAX=65535`, `$_RANDOM_INT=0`, `$_BUTTON_ENABLED=1`
- [x] **B6: END_STRING** — STRING/STRINGLN block mode: no inline body → enter block, read lines until `END_STRING`/`END_STRINGLN`, strip leading whitespace, join STRING with `""` or STRINGLN with `"\n"`, `_type_text` handles `\n` by pressing ENTER
- [x] **B7: MOUSE** — All 6 variants (MOUSE_MOVE, MOUSE_MOVE_TO, MOUSE_CLICK, MOUSE_DOWN, MOUSE_UP, MOUSE_SCROLL) through full pipeline; LEFT/RIGHT/MIDDLE buttons via existing tokens + IDENTIFIER("MIDDLE"); PicoPlatform uses `adafruit_hid.mouse`; `mouse_move_to` is HID no-op
- [x] Phase A: 103 edge-case tests (error recovery, nested functions, recursion, nested loops, variable shadowing, overflow, REPEAT corners, function registration)
- [x] **Full suite: 784 tests pass, ruff clean, working tree clean**
- [x] **REM_BLOCK whitespace:** Lexer skips leading whitespace before END_REM check (fixes indented END_REM in payloads)
- [x] **Pratt parser:** Single iterative `_parse_expression(min_precedence)` replaces 12-method recursive cascade (stack depth per paren nesting: 12→1)
- [x] **WINDOWS keyword as StringExpr:** `_parse_primary` fallthrough converts keyword tokens to StringExpr (e.g., `$_OS = WINDOWS`)
- [x] **Blank line before block terminator:** NEWLINEs skipped inside `_parse_statements_until` loop before stop-token check
- [x] **$_ vars auto-create on assign:** Top-level `$_OS = ...` auto-creates `$_`-prefixed vars in globals
- [x] **$_ vars auto-create on read:** Undeclared `$_`-prefixed read returns 0 (FALSE)
- [x] **Expression visitor stubs:** `visit_StringExpr`, `visit_IdentifierExpr`, `visit_HashIdentifierExpr` all return 0
- [x] **boot.py:** 4 boot modes from GPIO jumpers (GP0+GP15), /system/FORCE_USB_VISIBLE override, writes /system/boot_reason
- [x] **logger.py:** Rotating dual-file log (`/logs/latest.log` + `/logs/previous.log`), module-level guard flag, try/except for all OSError
- [x] **crash.py:** Crash counter at /system/crash_count, LOCKOUT_THRESHOLD=3, force_visible()/clear_force_visible() for recovery, set_last_error()
- [x] **payload.py:** payload.content()/exists()/fingerprint() (CRC32 via binascii.crc32), update() with atomic write→validate→rename, delete()
- [x] **wifi.py:** Station-first (secrets.py ssid/password), AP fallback (kducky-AP/ducky123), start()/stop()/is_connected()/mode()/ip()/ssid()
- [x] **webapp.py:** HTTP server with GET / (dark HTML status), GET /status (JSON), POST /payload (upload+validate+reset crashes), GET /logs; non-blocking serve_once() poll loop
- [x] **runtime.py:** Coordinator with start()→WiFi→WebServer ordering→PicoPlatform→run() payload pipeline (preprocess→lex→parse→interpret with REPLAY/STOP support)→stop() teardown
- [x] **main.py:** Minimal entry point (56 LOC), delegates to Runtime, _crash_handler for crash counting/logging
- [x] Full suite: 784 tests pass, ruff clean

## 9. Next Session — What to Build

**Pico Runtime Features complete.** 784 tests pass (unchanged from baseline). All hardware validation fixes from NullSec payload testing applied.

## What was built

8 interpreter fixes + 8 Pico runtime modules:

**Interpreter fixes** (committed in da5be05):
- REM_BLOCK whitespace — indented END_REM now terminates block comments
- Pratt parser — pystack exhaustion fixed for deeply nested WHILE(...) expressions
- WINDOWS keyword as StringExpr — keyword tokens can appear in value positions
- Blank line before block terminator — any block terminator preceded by blank line now parses
- $_ vars auto-create on assign — `$_OS = ...` works without prior VAR $OS
- $_ vars auto-create on read — undeclared `$_` var reads return 0 (FALSE)
- Expression visitor stubs — StringExpr/IdentifierExpr/HashIdentifierExpr all return 0
- ExtensionStmt phase-2 skip — auto-create-on-read handles missing vars instead of double-executing extensions

**Pico Runtime** (committed in fb5bc7a):
- boot.py — 4 boot modes from GPIO jumpers (GP0=setup, GP15=stealth, both=dev, none=development)
- logger.py — rotating dual-file log (/logs/latest.log + /logs/previous.log)
- crash.py — crash counter + lockout at threshold 3, /system/FORCE_USB_VISIBLE recovery flag
- payload.py — payload manager: read, CRC32 fingerprint, atomic update with full validation pipeline
- wifi.py — station-first (secrets.py), AP fallback (kducky-AP), mode/ip/ssid queries
- webapp.py — HTTP server: GET / (dark HTML status), GET /status (JSON), POST /payload (upload), GET /logs
- runtime.py — coordinator: start() initializes WiFi→WebServer→PicoPlatform; run() executes payload or serves UI; stop() tears down
- main.py — 56-LOC entry point, delegates to Runtime, crash handler

## Key architectural decisions
- ConfigManager rejected (YAGNI — no shared config files exist)
- WiFiManager split from WebServer (different concerns, different change rates)
- `fingerprint()` abstraction on PayloadManager (CRC32 today, swap for stronger hash later)
- Explicit start()/run()/stop() lifecycle on Runtime (slot for future teardown)
- Log path centralized in logs.py module (single source of truth)
- /system/FORCE_USB_VISIBLE flag instead of crash counter logic in boot.py
- EXFIL rule: GP15 jumper always overrides software intent (USB stealth is hardware-enforced)

## Known Issues
- Pico runtime modules are untested on actual hardware (CircuitPython desktop import tests pass)
- WiFi AP mode IP hardcoded to 192.168.4.1 (CircuitPython default)
- POST /payload upload does not reboot after successful upload (caller must power-cycle)
- No authentication on web UI (intentional — recovery mode must be accessible without configuration)

---

## 10. Continuation Prompt

```
Continue development of the kducky project.

Before making any changes:
1. Read AGENTS.md.
2. Read the three planning documents under plans/.
3. Read the latest Session Handoff in AGENTS.md (§8).
4. Verify the Git working tree is clean.
5. Resume from Pico Runtime Features completion.

Do not repeat completed milestones.
Wait for approval before beginning the next milestone.
```

---

## 11. Updating AGENTS.md

At the end of every milestone, the AI agent **must**:

1. Update the Session Handoff (§8) — all subsections.
2. Update the Handoff Summary table.
3. Update the Continuation Prompt (§10).
4. Save `AGENTS.md`.
5. Inform the user that `AGENTS.md` has been updated.
6. Wait for user approval before beginning the next milestone.

Failure to update AGENTS.md before concluding a session risks the next agent losing project context.
