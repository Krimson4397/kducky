# AGENTS.md — Project Operating Manual

> DuckyScript 3 Interpreter for Raspberry Pi Pico 2 W (RP2350) · CircuitPython 10.x  

---

## 1. Project Overview

**Project name:** kducky  
**Purpose:** A modular, portable DuckyScript 3 interpreter that runs on the Raspberry Pi Pico 2 W, allowing users to execute USB Rubber Ducky payloads from an embedded microcontroller.  
**Target hardware:** Raspberry Pi Pico 2 W (RP2350) — CircuitPython 10.x  
**Supported language:** DuckyScript 3 (Hak5 USB Rubber Ducky language) with project extensions  
**Current status:** M7 complete. M8 — Desktop Platform API is next.  
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
| Completed Milestone   | M7 — Parser Tests (Expanded)     |
| Current Branch        | main                             |
| Last Commit           | `f41fe6f`                        |
| Repository Status     | Clean working tree               |
| Next Milestone        | M8 — Desktop Platform API        |
| Blocking Issues       | None                             |
| Ready to Continue     | YES (awaiting user approval)     |

### Files Created

None (no new files)

### Files Modified

- `tests/test_parser.py` — Added 45 new parser test methods across 5 new test classes (statement edge cases, expression edge cases, error edge cases, full program edge cases, NodeVisitor edge cases)

### Tests Executed

- `pytest tests/test_parser.py` — 146 passed (99 original + 45 new) in 0.16s
- `pytest tests/` — 334 passed (146 parser + 77 lexer + 59 AST + 46 tokens + 6 ast edge cases) in 0.31s
- `ruff check src/ tests/` — All checks passed
- `mypy src/ducky/parser.py` — Success: no issues found

### Acceptance Criteria Completed

- [x] Minimum 40 test cases (45 added)
- [x] Every statement type tested with valid input (includes delay zero, combo with GUI/ALT, hold, empty bodies, F-keys)
- [x] Every error condition tested with valid diagnostic (missing END_IF/WHILE/FUNCTION/EXTENSION, REPEAT after END_FUNCTION, DEFINE without #, mismatched block closers)
- [x] Expression precedence verified with multiple test cases (hex, unary on groups, double unary, power/chained associativity, modulo, $var reference)
- [x] Full program edge cases (comments-only, defines-only, deep nesting, function call chains, CRLF)
- [x] NodeVisitor edge cases (return values, child traversal, unknown node fallback)
- [x] All 334 tests pass, ruff clean, mypy clean

### Remaining Milestones

Milestones 7–20 from the implementation roadmap.

### Known Issues

None.

### Technical Debt

None.

### Assumptions Made

- No line/column position tracking on AST nodes — source position is derived from token positions at parse time (consistent with the roadmap note added in M5)
- ELSE IF chains are represented as nested IfStmt nodes in the else_body field (no separate ElseIfStmt)
- Method names in grammar (Identifier) are treated as IdentifierExpr nodes; function calls (Identifier + ()) produce CallStmt/CallExpr

### Notes for the Next Session

Milestone 7 is complete. The parser test suite expanded from 99 to 146 tests (+45), covering edge cases the basic tests missed: statement boundaries (zero delay, empty bodies), expression corner cases (hex literals, double unary, associativity), error conditions for unterminated blocks and mismatched closers, full programs with comments/defines/deep nesting, and NodeVisitor return value propagation.

The next milestone (M8 — Desktop Platform API) depends on M1 (scaffold only — no language modules). It defines PlatformInterface protocols and desktop mock backends. This unblocks M9 (Interpreter Core).

---

## 9. Continuation Prompt

```
Continue development of the kducky project.

Before making any changes:
1. Read AGENTS.md.
2. Read the three planning documents under plans/.
3. Read the latest Session Handoff in AGENTS.md (§8).
4. Verify the Git working tree is clean.
5. Resume from Milestone 8 — Desktop Platform API.

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
