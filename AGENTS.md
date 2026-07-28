# AGENTS.md — Project Operating Manual

> DuckyScript 3 Interpreter for Raspberry Pi Pico 2 W (RP2350) · CircuitPython 10.x  

---

## 1. Project Overview

**Project name:** kducky  
**Purpose:** A modular, portable DuckyScript 3 interpreter that runs on the Raspberry Pi Pico 2 W, allowing users to execute USB Rubber Ducky payloads from an embedded microcontroller.  
**Target hardware:** Raspberry Pi Pico 2 W (RP2350) — CircuitPython 10.x  
**Supported language:** DuckyScript 3 (Hak5 USB Rubber Ducky language) with project extensions  
**Current status:** Payload-only execution on 3 GPIO-selected boot modes (NS / EWOS / EWIS).  
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

| Field             | Value                                                                   |
| ----------------- | ----------------------------------------------------------------------- |
| Project Version   | 1.0.0                                                                   |
| Completed Feature | 3-mode boot (NS / EWOS / EWIS), bugfixes, EWOS default, 1.25s HID delay |
| Current Branch    | main                                                                    |
| Last Commit       | 27357c1                                                                 |
| Repository Status | Clean — all files committed and pushed to origin/main                   |
| Next Milestone    | (post-payload WiFi retrieval — see plans/Post_Payload_WiFi_Plan.md)     |
| Blocking Issues   | None                                                                    |
| Ready to Continue | YES (awaiting user approval)                                            |

### Boot Modes (Current)

Three modes selected by two GPIO jumpers (GP0, GP15), each a pulled-up input that reads HIGH when no jumper is present and LOW when jumped to GND:

| GP0  | GP15 | Mode           | Behavior                                                                                                  |
| ---- | ---- | -------------- | --------------------------------------------------------------------------------------------------------- |
| high | high | **EWOS** (default) | Payload runs, HID active, MSC visible read-only to host. Pico writes via `storage.remount(readonly=False)`. |
| low  | high | EWOS           | Same as default.                                                                                          |
| high | low  | EWIS           | Payload runs, HID active, MSC hidden via `storage.disable_usb_drive()`.                                     |
| low  | low  | NS             | Safe fallback. No payload, MSC visible host read-write, no HID. Serial console enabled.                   |

- **EWOS** is the no-jumper default. Payloads execute AND can save files to the Pico filesystem; the host can read/edit files on the MSC drive between runs.
- **EWIS** is true USB stealth — no drive appears on the host. Payload still runs.
- **NS** is developer mode — drive visible, serial console for code upload, no HID.

### Runtime Behavior

- All payload execution starts after a **1.25-second `time.sleep()`** in `_run_payload_pipeline()` (runtime.py:79), giving the host time to enumerate the HID keyboard device.
- `ATTACKMODE` is a no-op on Pico (CircuitPython USB descriptors are fixed at boot — set in `boot.py`, never changed at runtime).
- After payload completion in EWOS mode, `Runtime.stop()` remounts the filesystem host-writable so results can be copied off without power-cycling to NS.

### Key Files

| File                          | Purpose                                                                                                                      |
| ----------------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| `src/platform/pico/mode.py`     | Pure-logic mode selection: `select_mode(gp0_high, gp15_high)`, `is_executable(mode)`, `EXECUTABLE_MODES`. Importable on desktop.   |
| `src/platform/pico/boot.py`     | CircuitPython boot.py: reads GP0+GP15, calls `select_mode`, writes `/system/boot_reason`, configures USB HID + storage per mode. |
| `src/platform/pico/runtime.py`  | Lifecycle coordinator: `start()` → `run()` (payload pipeline) → `stop()` (teardown + EWOS host-writable remount).                  |
| `src/platform/pico/main.py`     | Entry point: creates Runtime, delegates lifecycle. `_handle_error` logs + re-raises (no crash counter).                        |
| `src/platform/pico/backends.py` | `PicoPlatform` class implementing all 26 `PlatformInterface` methods. Guarded imports (`_HAS_HW`) for desktop testability.         |
| `src/platform/pico/logger.py`   | Rotating dual-file log (`/logs/latest.log`, `/logs/previous.log`).                                                               |
| `src/platform/pico/payload.py`  | Payload file manager: `read()`, `exists()`, CRC32 `fingerprint()`, atomic `update()` with validate.                                  |
| `tests/test_mode.py`            | 9 pure-logic tests for mode selection and executability.                                                                     |

### Previously Committed (da5be05) — Interpreter fixes from hardware validation

- `src/ducky/lexer.py` — REM_BLOCK: skip leading whitespace before END_REM check
- `src/ducky/parser.py` — Pratt parser: iterative precedence climbing (fixes pystack exhaustion on CircuitPython); WINDOWS keyword → StringExpr fallthrough; blank line before block terminator
- `src/ducky/interpreter.py` — $_ vars auto-create on assign/read (default 0); StringExpr/IdentifierExpr/HashIdentifierExpr visitors return 0; ExtensionStmt revert to skip
- `tests/test_interpreter_core.py` — Updated for StringExpr behavior
- `tests/test_parser_edge_cases.py` — Updated for new parser behaviors

### Bugs Fixed (commit afb60fc)

1. **ATTACKMODE no-op** — `set_attack_mode()` is now an explicit no-op with ponytail comment (CircuitPython USB descriptors fixed at boot). `save_attack_mode` returns `("HID",)` directly instead of reading the never-written `/attack_mode.cfg`.
2. **`hide_payload`/`restore_payload`** — Removed redundant `storage.remount()` and silent `except` swallows. Errors now propagate to `_handle_error`.
3. **EWOS post-run host-writable** — `Runtime.stop()` remounts filesystem host-writable after payload completes in EWOS mode.
4. **Serial console in stealth** — `usb_cdc.enable()` gated on NS mode only. EWOS/EWIS skip it.

### Tests Executed

- `python -m pytest tests/ -x -q` — **793 passed, 6 skipped** (6 skipped are `_HAS_HW`-gated keycode map tests)
- `ruff check src/ tests/` — All checks passed

### User Validation

- Payload execution on Pico confirmed working (EWOS).
- Payload can save files to Pico filesystem; host can read/edit files manually between runs.
- No regressions observed.

---

## 9. Next Session — What to Build

The kducky project is currently in a stable state with a fully working interpreter and 3-mode boot runtime. The post-payload WiFi retrieval plan exists in `plans/Post_Payload_WiFi_Plan.md` but is not yet implemented.

Current capabilities:
- DuckyScript 3 interpreter (full language spec) with ~800 passing tests
- 3 GPIO-selected boot modes: EWOS (default, payload + visible MSC), EWIS (stealth), NS (dev)
- 1.25s HID enumeration delay before payload execution
- Payload pipeline: Preprocessor → Lexer → Parser → Interpreter → PicoPlatform (HID)
- Preprocessor with `DEFINE` support
- Keyboard layouts (US + 15 international)
- All DuckyScript 3 statements implemented (REBOOT, REPLAY, JITTER, INJECT_VAR, $_ vars, END_STRING block mode, MOUSE, HOLD/RELEASE, etc.)
- Rotating log, payload file manager
- Desktop test suite with structural `PlatformInterface` contract tests

---

## 10. Continuation Prompt

```
Continue development of the kducky project.

Before making any changes:
1. Read AGENTS.md.
2. Read the three planning documents under plans/.
3. Read the latest Session Handoff in AGENTS.md (§8).
4. Verify the Git working tree is clean.

Current boot modes (GP0+GP15 GPIO, both pulled high by default, jumper-to-GND = LOW):

  GP0  GP15  Mode   Description
  high high  EWOS   No-jumper default — payload runs, HID, MSC read-only to host
  low  high  EWOS   Same behavior as default
  high low   EWIS   Payload runs, HID, MSC hidden (usb drive disabled)
  low  low   NS     Safe fallback — no payload, MSC visible, serial console

Key architectural notes:
- `mode.py` contains pure-logic select_mode/is_executable — no CircuitPython imports
- `boot.py` runs as top-level module on hardware (absolute imports: from platform.pico.mode)
- ATTACKMODE is a no-op on Pico (USB descriptors set at boot, not runtime)
- 1.25s delay in _run_payload_pipeline() before any HID keystrokes
- EWOS: Pico writes via storage.remount(readonly=False); host reads via MSC read-only
- crash/lockout/FORCE_USB_VISIBLE were removed — mode selection is pure GPIO

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
