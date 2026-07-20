# AGENTS.md — Project Operating Manual

> DuckyScript 3 Interpreter for Raspberry Pi Pico 2 W (RP2350) · CircuitPython 10.x  

---

## 1. Project Overview

**Project name:** kducky  
**Purpose:** A modular, portable DuckyScript 3 interpreter that runs on the Raspberry Pi Pico 2 W, allowing users to execute USB Rubber Ducky payloads from an embedded microcontroller.  
**Target hardware:** Raspberry Pi Pico 2 W (RP2350) — CircuitPython 10.x  
**Supported language:** DuckyScript 3 (Hak5 USB Rubber Ducky language) with project extensions  
**Current status:** M18 — Complete Interpreter (all 13 AST visitors implemented).  
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
| Project Version       | 0.2.0 (alpha)                    |
| Completed Milestone   | M18 — Complete Interpreter       |
| Current Branch        | main                             |
| Last Commit           | b508745                          |
| Repository Status     | Clean working tree                 |
| Next Milestone        | M19 — Hardware Validation (Pico) |
| Blocking Issues       | None                             |
| Ready to Continue     | YES (awaiting user approval)     |

### Files Created

- `payloads/payload.dd` — Safe regression payload (v1.1, no system key combos). Exercises all interpreter features and runs to completion (no crashes). Replaces `safe_regression.dd`.
- `payloads/regression_test.dd` — Original regression payload (v1.0, includes Windows UI key combos for manual testing with caution).

### Files Modified

- `src/ducky/interpreter.py` — Added 13 visitor methods: `visit_LedStmt`, `visit_AttackModeStmt`, `visit_SaveAttackModeStmt`, `visit_RestoreAttackModeStmt`, `visit_SaveHostLockStateStmt`, `visit_RestoreHostLockStateStmt`, `visit_WaitForKeyStmt`, `visit_ButtonDefStmt`, `visit_WaitForButtonPressStmt`, `visit_DisableButtonStmt`, `visit_EnableButtonStmt`, `visit_HidePayloadStmt`, `visit_RestorePayloadStmt`. Added `_button_handlers` dict. Updated `visit_Script` two-phase registration to handle `ButtonDefStmt`.
- `tests/test_interpreter_keyboard.py` — 18 new tests covering all 13 new visitors.
- `payloads/payload.dd` — Removed "expected crash" section; now runs to completion with 356 tokens, 47 statements.
- `deploy.py` — Added `payloads/payload.dd` to file discovery for CIRCUITPY deployment.

### Tests Executed

- `python -m pytest tests/ -x -q` — 633 passed, 6 skipped (18 new interpreter tests)
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

### Remaining Milestones

Milestones 19–20 from the implementation roadmap.

### Known Issues

- `platform.pico` namespace conflicts with Python stdlib `platform` module on desktop. Tests work around this via `importlib` file-path loading. On CircuitPython (Pico) there is no conflict because stdlib `platform` is not available.
- 6 key-map completeness tests skip on desktop (require `adafruit_hid` for `_KC` constants).
- Some exotic HID keycodes (COMPOSE, PROPS, UNDO, PASTE, KEYPAD_00, KEYPAD_000) use `getattr` fallbacks that need verification on real hardware.
- `DESKTOP_PLATFORM` import fallback for `set_layout`/`get_layout` may need updating when PicoPlatform implements layout switching.

### Technical Debt

- `PicoPlatform.restore_attack_mode()` — attack mode changes require a USB re-enumeration (reboot) on CircuitPython, so restore is a config-file rewrite rather than real-time switch.
- `PicoPlatform.restore_lock_state()` — USB HID keyboards cannot set host lock-LED state; method is a no-op (saved values are informational only).
- Some exotic HID keycodes (COMPOSE, PROPS, UNDO, PASTE, KEYPAD_00, KEYPAD_000) use `getattr` fallbacks that need verification on real hardware.

### Assumptions Made (at commit time)

- Flat `PlatformInterface` protocol (all methods directly on protocol) rather than hierarchical sub-backends in spec §6.1.
- `DesktopPlatform` satisfies protocol structurally (idiomatic Python Protocol pattern), not via explicit inheritance.
- Onboard LED on Pico W is monochrome (green/white); `set_led(R)` and `set_led(B)` are no-ops.
- Trigger button defaults to GPIO 15 with pull-up (active low).
- `from __future__ import annotations` removed from all source files (CircuitPython doesn't populate __annotations__ on classes, making it useless).
- CircuitPython's `str` lacks `isalnum()`; replaced with `isalpha() or isdigit()`.
- CircuitPython's `random` module has no `Random()` class; uses module-level functions with manual seeding.
- MicroPython parser doesn't support PEP 570 (positional-only `/`) or `metaclass=` keyword in class definitions.

### Notes for the Next Session

Milestone 18 is complete. All 13 AST visitor methods that were missing are now implemented:

**Architecture:**
- All 13 visitors dispatch through the same `visit()` → `visit_ClassName()` pattern
- `ButtonDefStmt` uses two-phase registration (same as `FunctionDef`): registered in `visit_Script` phase-1, execution skipped in phase-2
- `WaitForKeyStmt` uses a polling loop with 50ms delay via `platform.delay_ms()`
- No new platform methods were needed — all already existed in `PlatformInterface`, `DesktopPlatform`, and `PicoPlatform`

**Visitors implemented:**
1. `visit_LedStmt` — LED control (OFF/R/G/B)
2. `visit_AttackModeStmt` — USB attack mode configuration
3. `visit_SaveAttackModeStmt` — save attack mode state
4. `visit_RestoreAttackModeStmt` — restore attack mode state
5. `visit_SaveHostLockStateStmt` — save lock key state
6. `visit_RestoreHostLockStateStmt` — restore lock key state
7. `visit_WaitForKeyStmt` — wait for lock key state (CAPS/NUM/SCROLL, ON/OFF/CHANGE)
8. `visit_ButtonDefStmt` — register button handler
9. `visit_EnableButtonStmt` — enable button handler
10. `visit_DisableButtonStmt` — disable button handler
11. `visit_WaitForButtonPressStmt` — wait for hardware button press
12. `visit_HidePayloadStmt` — hide payload file
13. `visit_RestorePayloadStmt` — restore hidden payload file

**Test count:** 633 passed, 6 skipped (same hardware-dependent skips)
**Commit:** `b508745`

The safe regression payload (`payloads/payload.dd`) now runs to completion — types all test output into Notepad, exercises LED/attack mode/etc., and types "all_done" at the end.

Next milestone: M19 — Hardware Validation (Pico). Run the interpreter on actual Pico 2 W hardware and validate against test payloads.

---

## 9. Continuation Prompt

```
Continue development of the kducky project.

Before making any changes:
1. Read AGENTS.md.
2. Read the three planning documents under plans/.
3. Read the latest Session Handoff in AGENTS.md (§8).
4. Verify the Git working tree is clean.
5. Resume from Milestone 19 — Hardware Validation (Pico).

Do not repeat completed milestones.
Wait for approval before beginning the next milestone.
```

---

## 10. Updating AGENTS.md

At the end of every milestone, the AI agent **must**:

1. Update the Session Handoff (§8) — all subsections.
2. Update the Handoff Summary table.
3. Update the Continuation Prompt (§9).
4. Save `AGENTS.md`.
5. Inform the user that `AGENTS.md` has been updated.
6. Wait for user approval before beginning the next milestone.

Failure to update AGENTS.md before concluding a session risks the next agent losing project context.
