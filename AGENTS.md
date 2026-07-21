# AGENTS.md — Project Operating Manual

> DuckyScript 3 Interpreter for Raspberry Pi Pico 2 W (RP2350) · CircuitPython 10.x  

---

## 1. Project Overview

**Project name:** kducky  
**Purpose:** A modular, portable DuckyScript 3 interpreter that runs on the Raspberry Pi Pico 2 W, allowing users to execute USB Rubber Ducky payloads from an embedded microcontroller.  
**Target hardware:** Raspberry Pi Pico 2 W (RP2350) — CircuitPython 10.x  
**Supported language:** DuckyScript 3 (Hak5 USB Rubber Ducky language) with project extensions  
**Current status:** M18 — Complete Interpreter + payload creation (all 13 AST visitors implemented, attack payloads).  
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
| Last Commit           | 25e4249                          |
| Repository Status     | Clean working tree                 |
| Next Milestone        | M19 — Hardware Validation (Pico) |
| Blocking Issues       | None                             |
| Ready to Continue     | YES (awaiting user approval)     |

### Files Created

- `tests/test_d3_extensions.py` — 14 tests for REBOOT, REPLAY, JITTER, INJECT_VAR, $_ internal vars, END_STRING block mode, MOUSE operations.
- `tests/test_parser_edge_cases.py` — 55 edge case tests (error recovery, expression precedence, function parsing corner cases, misc).
- `tests/test_interpreter_edge_cases.py` — 48 edge case tests (nested functions, recursion, nested loops, variable shadowing, overflow/wrapping, REPEAT corners, function registration).

### Files Modified

- `src/ducky/tokens.py` — Added `TokenType` members: `JITTER`, `ON`, `OFF`, `INJECT_VAR`, `END_STRING`, `END_STRINGLN`, `REBOOT`, `REPLAY`, `MOUSE_MOVE`, `MOUSE_MOVE_TO`, `MOUSE_CLICK`, `MOUSE_DOWN`, `MOUSE_UP`, `MOUSE_SCROLL`.
- `src/ducky/lexer.py` — Added 14 new keyword mappings. Modified STRING/STRINGLN handlers to detect block mode (no inline body → enter block mode, read lines until END_STRING/END_STRINGLN).
- `src/ducky/ast/nodes.py` — Added AST nodes: `RebootStmt`, `ReplayStmt`, `JitterStmt`, `InjectVarStmt`, `MouseStmt`, `MouseAction` enum, `MouseButton` enum.
- `src/ducky/ast/__init__.py` — Exported all new AST types.
- `src/ducky/parser.py` — Added dispatch and parse methods for REBOOT, REPLAY, JITTER, INJECT_VAR, and all 6 MOUSE variants. Changed `_parse_release_stmt` to not require INJECT_MOD before RELEASE of modifier.
- `src/ducky/platform/__init__.py` — Added 5 protocol methods: `reboot_target()`, plus 6 mouse methods (`mouse_move`, `mouse_move_to`, `mouse_click`, `mouse_down`, `mouse_up`, `mouse_scroll`).
- `src/ducky/platform/desktop.py` — Added stub implementations for all new protocol methods (recording via `_record()`).
- `src/platform/pico/backends.py` — Added `Mouse` import, `_mouse` init, implementations for `reboot_target()` (GUI r + shutdown), 5 mouse methods using `adafruit_hid.mouse`, and `mouse_move_to` as no-op.
- `src/ducky/interpreter.py` — Added `_jitter_enabled/min/max` state, `_inject_var_pending` flag, `_populate_internal_vars()` (pre-populates 7 `$_` vars into globals), visitor methods for all new AST nodes, and `_type_text` now handles `\n` for block-mode STRINGLN.
- `src/platform/pico/main.py` — Refactored `main()` into retry loop catching `RestartPayloadSignal` for REPLAY support. Added `_runtime.autoreload = False` to prevent file-rename restarts.
- `src/ducky/interpreter.py` — Added `visit_ReplayStmt` raising `RestartPayloadSignal`, `visit_RebootStmt` calling `platform.reboot_target()`, `visit_JitterStmt`, `visit_InjectVarStmt`, `visit_MouseStmt`, `_type_text` handles `\n` for block-mode STRINGLN.
- `tests/test_interpreter_keyboard.py` — Fixed 11 tests to account for 3 new `_populate_internal_vars()` platform calls during interpreter init.
- `tests/test_interpreter_functions.py` — Fixed 1 test expecting empty `platform.calls` (now 3 init calls).

### Tests Executed

- `python -m pytest tests/ -x -q` — **784 passed, 6 skipped** (103 edge-case + 14 REBOOT/REPLAY/JITTER + 7 INJECT_VAR + 7 $_ vars + 12 END_STRING + 13 MOUSE + backfill fixes)
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

### Remaining Milestones

Milestones 19–20 from the implementation roadmap.

### Known Issues

- `platform.pico` namespace conflicts with Python stdlib `platform` module on desktop. Tests work around this via `importlib` file-path loading. On CircuitPython (Pico) there is no conflict because stdlib `platform` is not available.
- 6 key-map completeness tests skip on desktop (require `adafruit_hid` for `_KC` constants).
- Some exotic HID keycodes (COMPOSE, PROPS, UNDO, PASTE, KEYPAD_00, KEYPAD_000) use `getattr` fallbacks that need verification on real hardware.
- `DESKTOP_PLATFORM` import fallback for `set_layout`/`get_layout` may need updating when PicoPlatform implements layout switching.
- Preprocessor cannot substitute `#NAME` references inside `"..."` double-quoted strings. For preprocessor variables in PowerShell argument strings, hardcode the value instead (e.g., `Start-Process -ArgumentList "-File filename.ps1"` instead of `"-File #PS1"`).

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

**D3 Extensions complete (B1-B7).** 784 tests (↑151 from M18's 633). All D3 Extensions implemented:

- **B1 (REBOOT):** Shuts down target via `GUI r → shutdown /r /t 0`.
- **B2 (REPLAY):** `RestartPayloadSignal` caught by `main.py` retry loop — payload restarts from beginning.
- **B3 (JITTER):** Random keystroke delays (JITTER ON/OFF/DELAY min max). Integrated into `_type_text`.
- **B4 (INJECT_VAR):** Types any variable's value as keystrokes. Uses locals→globals scope lookup.
- **B5 ($_ internal vars):** 7 pre-populated read-only/writable system variables (lock states, random control, button enabled).
- **B6 (END_STRING/END_STRINGLN):** STRING/STRINGLN block mode — multi-line string blocks with indent stripping. Parser unchanged (lexer emits STRING_BODY).
- **B7 (MOUSE):** All 6 DuckyScript MOUSE operations via new PlatformInterface mouse methods. PicoPlatform uses `adafruit_hid.mouse`. `MOUSE_MOVE_TO` is no-op (HID limitation).
- **Phase A:** 103 edge-case tests verified no bugs in existing interpreter.

**Key architectural changes:**
- Pico `main.py` autoreload disabled (`_runtime.autoreload = False`) to prevent payload loop on file rename.
- REPLAY support: `main()` wrapped in retry loop catching `RestartPayloadSignal`.
- `_type_text` handles `\n` for block-mode STRINGLN (splits on newlines, presses ENTER between segments).
- Interpreter init now calls `_populate_internal_vars()` making 3 platform calls (affects test assertions).

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
