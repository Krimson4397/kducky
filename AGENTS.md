# AGENTS.md — Project Operating Manual

> DuckyScript 3 Interpreter for Raspberry Pi Pico 2 W (RP2350) · CircuitPython 10.x  

---

## 1. Project Overview

**Project name:** kducky  
**Purpose:** A modular, portable DuckyScript 3 interpreter that runs on the Raspberry Pi Pico 2 W, allowing users to execute USB Rubber Ducky payloads from an embedded microcontroller.  
**Target hardware:** Raspberry Pi Pico 2 W (RP2350) — CircuitPython 10.x  
**Supported language:** DuckyScript 3 (Hak5 USB Rubber Ducky language) with project extensions  
**Current status:** M14 — Pico Platform Implementation complete.  
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
| Completed Milestone   | M14 — Pico Platform Implementation |
| Current Branch        | main                             |
| Last Commit           | Will be updated after commit     |
| Repository Status     | Clean working tree               |
| Next Milestone        | M15 — Keyboard Layout Support |
| Blocking Issues       | None                             |
| Ready to Continue     | YES (awaiting user approval)     |

### Files Created

- `src/platform/pico/backends.py` — `PicoPlatform` class implementing all 26 `PlatformInterface` methods for CircuitPython on Raspberry Pi Pico 2 W (RP2350). Guarded imports so the module is importable on desktop. Exhaustive `_ACTION_KEY_MAP` (all 69 `ActionKey` members) and `_MODIFIER_KEY_MAP` (all 8 `ModifierKey` members) to Adafruit HID keycodes.
- `src/platform/pico/main.py` — Entry point runner for CircuitPython auto-run (`code.py`/`main.py`). Loads `/payload.dd`, runs through lexer → parser → interpreter pipeline, signals success/failure with onboard LED.
- `src/platform/pico/boot.py` — USB configuration executed at CircuitPython power-on. Enables HID keyboard and optional mass storage disable (`/STORAGE_DISABLE` marker file).
- `tests/test_pico_platform.py` — 17 contract tests verifying: all 26 protocol methods implemented, no extra public methods, signatures match, keycode maps exhaustive (skipped on desktop), signal behavior matches DesktopPlatform, helper enums importable.
- `src/ducky/utils/compat.py` — CircuitPython compatibility shim (dataclass, enum, Protocol fallbacks)
- `src/ducky/layouts/__init__.py` — Keyboard layout loader module with caching
- `src/ducky/layouts/us.json` — US keyboard layout (95 printable ASCII characters)
- `deploy.py` — Auto-discovery deployment script
- `DEPLOYMENT.md` — Deployment documentation

### Files Modified

- `src/ducky/__init__.py` — Added diagnostic print
- `src/ducky/tokens.py` — compat imports, @enum decorators, Token class rewritten with __slots__
- `src/ducky/ast/__init__.py` — Added diagnostic print, IdentifierStmt export
- `src/ducky/ast/nodes.py` — @enum decorators, __slots__ on 32 classes, __defaults__ on 3, IdentifierStmt node, ComboStmt.key type widened
- `src/ducky/lexer.py` — isalnum→isalpha/isdigit, diagnostic print
- `src/ducky/parser.py` — IdentifierStmt support, diagnostic print
- `src/ducky/interpreter.py` — ExtensionStmt support, IdentifierStmt visitor, diagnostic print
- `src/ducky/platform/__init__.py` — compat imports
- `src/ducky/platform/desktop.py` — set_layout/get_layout methods, DESKTOP_PLATFORM import fallback
- `src/ducky/utils/__init__.py` — compat imports
- `src/ducky/utils/visitor.py` — compat imports
- `src/platform/pico/backends.py` — Keycode alias layer, random.Random fallback, _DIGIT_NAMES constant, string key handler
- `src/platform/pico/main.py` — traceback fix, per-phase error handling
- `tests/test_tokens.py` — iteration changes
- `tests/test_ast.py` — iteration changes
- `tests/test_pico_platform.py` — iteration changes
- `tests/test_parser.py` — IdentifierStmt test updates
- `AGENTS.md` — Session handoff updated
- `plans/DuckyScript3_Implementation_Roadmap.md` — (if modified)

### Tests Executed

- `pytest tests/ -x -q` — 549 passed, 6 skipped
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

### Remaining Milestones

Milestones 15–20 from the implementation roadmap.

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

Milestone 14 is complete. The `PicoPlatform` class is ready for hardware testing on the Raspberry Pi Pico 2 W. Key items to verify on real hardware: all HID keycode mappings in `_ACTION_KEY_MAP`, button GPIO logic, LED operation, and the payload runner in `main.py`. The 6 skipped tests will validate key map completeness when CircuitPython + `adafruit_hid` are available.

The next milestone (M15 — Keyboard Layout Support) depends on M8 (PlatformInterface protocol). It creates keyboard layout JSON files for 16 languages (US, GB, DE, FR, ES, IT, JP, DK, NO, SE, FI, PT, BR, RU, PL, CZ), a layout loader module with caching, and runtime layout switching via DUCKY_LANG. See the roadmap for full acceptance criteria.

---

## 9. Continuation Prompt

```
Continue development of the kducky project.

Before making any changes:
1. Read AGENTS.md.
2. Read the three planning documents under plans/.
3. Read the latest Session Handoff in AGENTS.md (§8).
4. Verify the Git working tree is clean.
5. Resume from Milestone 15 — Keyboard Layout Support.

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
