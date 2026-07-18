# AGENTS.md — Project Operating Manual

> DuckyScript 3 Interpreter for Raspberry Pi Pico 2 W (RP2350) · CircuitPython 10.x  

---

## 1. Project Overview

**Project name:** kducky  
**Purpose:** A modular, portable DuckyScript 3 interpreter that runs on the Raspberry Pi Pico 2 W, allowing users to execute USB Rubber Ducky payloads from an embedded microcontroller.  
**Target hardware:** Raspberry Pi Pico 2 W (RP2350) — CircuitPython 10.x  
**Supported language:** DuckyScript 3 (Hak5 USB Rubber Ducky language) with project extensions  
**Current status:** M9 complete. M10 — Interpreter: Control Flow is next.  
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
│   └── ducky/
│       ├── __init__.py
│       ├── lexer/         # Lexer: character stream → token stream
│       ├── parser/        # Parser: token stream → AST
│       ├── ast/           # AST node definitions (pure data, no logic)
│       ├── interpreter/   # Interpreter: AST → platform actions
│       ├── runtime/       # Runtime state (variables, functions, stack)
│       ├── platform/      # PlatformInterface protocols + shared types
│       └── utils/         # Shared utilities (errors, helpers)
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
| Project Version       | 0.1.0 (alpha)                    |
| Completed Milestone   | M9 — Interpreter Core            |
| Current Branch        | main                             |
| Last Commit           | `be09601`                        |
| Repository Status     | Clean working tree               |
| Next Milestone        | M10 — Interpreter: Control Flow  |
| Blocking Issues       | None                             |
| Ready to Continue     | YES (awaiting user approval)     |

### Files Created

- `src/ducky/interpreter.py` — `Interpreter` (extends `NodeVisitor`) with `interpret(script, platform)` method, expression evaluator for all operators (spec §4.2), variable storage, delay semantics, REPEAT, and payload control statements
- `tests/test_interpreter_core.py` — 65 test methods covering variable declarations, assignment, expression evaluation (arithmetic, bitwise, comparison, logical, unary, grouping), error conditions (div/0, mod/0, undeclared variables), delay statements, REPEAT semantics, payload control, and default delay inter-statement timing

### Files Modified

- `AGENTS.md` — Session handoff updated to M9

### Tests Executed

- `pytest tests/test_interpreter_core.py` — 65 passed in 0.12s
- `pytest tests/` — 431 passed (65 interpreter + 366 existing) in 0.41s
- `ruff check src/ducky/interpreter.py tests/test_interpreter_core.py` — All checks passed
- `mypy src/ducky/interpreter.py` — Success: no issues found

### Acceptance Criteria Completed

- [x] `VAR $x = 42` stores and retrieves the value
- [x] `VAR $x` without initializer defaults to 0
- [x] `$x = $x + 1` reads, increments, stores
- [x] `4 + 3 * 2` evaluates to 10 (correct precedence)
- [x] `65535 + 1` wraps to 0
- [x] `/ 0` and `% 0` produce runtime errors
- [x] `DELAY 500` calls `platform.delay_ms(500)`
- [x] `DEFAULTDELAY 100` causes subsequent statements to call `delay_ms(100)` after execution
- [x] `REPEAT 3` repeats the immediately preceding statement 3 extra times
- [x] Undeclared variable access produces an error
- [x] All 431 tests pass, ruff clean, mypy clean

### Remaining Milestones

Milestones 10–20 from the implementation roadmap.

### Known Issues

None.

### Technical Debt

- `DesktopPlatform.restore_attack_mode()` is a no-op on desktop (marked `# ponytail:`). A real Pico backend would restore actual HID state. Add when M14 (Pico Platform) is implemented.

### Assumptions Made

- Flat `PlatformInterface` protocol (all methods directly on the protocol) rather than the hierarchical sub-backend structure in spec §6.1. The spec shows sub-backends as a logical grouping; the protocol follows the flat interface that the interpreter actually calls. This matches the general pattern used in the interpreter where it calls methods directly on the platform object.
- `DesktopPlatform` does NOT explicitly inherit from `PlatformInterface` — it satisfies the protocol structurally, which is the idiomatic Python Protocol pattern.
- `press_key` signature uses `tuple[object, ...]` for modifiers to accept any iterable of modifier identifiers (strings).

### Notes for the Next Session

Milestone 9 is complete. The interpreter core can now execute DuckyScript programs on the desktop platform mock: variable storage, expression evaluation with all operators (spec §4.2), delay management, REPEAT, and payload control. The interpreter uses the NodeVisitor pattern and drives the `PlatformInterface` protocol.

The next milestone (M10 — Interpreter: Control Flow) depends on M9 (this milestone). It adds IF/ELSE IF/ELSE, WHILE, BREAK, and CONTINUE to the interpreter.

---

## 9. Continuation Prompt

```
Continue development of the kducky project.

Before making any changes:
1. Read AGENTS.md.
2. Read the three planning documents under plans/.
3. Read the latest Session Handoff in AGENTS.md (§8).
4. Verify the Git working tree is clean.
5. Resume from Milestone 10 — Interpreter: Control Flow.

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
