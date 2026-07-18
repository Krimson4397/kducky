# AGENTS.md — Project Operating Manual

> DuckyScript 3 Interpreter for Raspberry Pi Pico 2 W (RP2350) · CircuitPython 10.x  

---

## 1. Project Overview

**Project name:** kducky  
**Purpose:** A modular, portable DuckyScript 3 interpreter that runs on the Raspberry Pi Pico 2 W, allowing users to execute USB Rubber Ducky payloads from an embedded microcontroller.  
**Target hardware:** Raspberry Pi Pico 2 W (RP2350) — CircuitPython 10.x  
**Supported language:** DuckyScript 3 (Hak5 USB Rubber Ducky language) with project extensions  
**Current status:** Milestone 2 complete. M3 — Lexer is next.  
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
| Completed Milestone   | M3 — Lexer                       |
| Current Branch        | main                             |
| Last Commit           | 4301e80                          |
| Repository Status     | Clean working tree               |
| Next Milestone        | M4 — AST Node Definitions        |
| Blocking Issues       | None                             |
| Ready to Continue     | YES (awaiting user approval)     |

### Files Created

- `src/ducky/lexer.py` — `DuckyLexer` class with `tokenize()`, `LexerError` exception, keyword map (all spec keywords), and comment/string/operator/identifier handling
- `tests/test_lexer.py` — 60 tests covering STRING/STRINGLN body capture, REM/`//`/REM_BLOCK comment stripping, keyword recognition, integer/string literals, operators (multi- and single-char), punctuation, identifiers (`$`, `#`, plain, function-call pattern), ATTACKMODE params, newline/blank-line handling, error conditions (line too long, unterminated string, illegal char, invalid `$`/`#`), and edge cases

### Files Modified

- `AGENTS.md` — Updated Session Handoff

### Tests Executed

- `pytest tests/` — 106 passed (60 lexer + 46 tokens) in 0.18s
- `ruff check src/ tests/` — All checks passed
- `mypy src/ducky/lexer.py tests/test_lexer.py` — Success: no issues found

### Acceptance Criteria Completed

- [x] `STRING hello world` → `[STRING, STRING_BODY("hello world"), NEWLINE]` (with column tracking)
- [x] `CTRL-SHIFT ENTER` → `[CTRL, MINUS, SHIFT, ENTER, NEWLINE]`
- [x] `REM anything` produces zero tokens (only NEWLINE)
- [x] `// comment` produces zero tokens
- [x] `REM_BLOCK ... END_REM` produces zero tokens
- [x] `DELAY 2000` → `[DELAY, INTEGER("2000"), NEWLINE]`
- [x] `VAR $x = (5 + 3)` → full expression tokenization (VAR, DOLLAR_IDENTIFIER, ASSIGN, LPAREN, INTEGER, PLUS, INTEGER, RPAREN, NEWLINE)
- [x] Max line length error emitted at 257th character
- [x] Unterminated `"` string error emitted with line/col
- [x] 60 distinct test cases covering all token types, comments, strings, combos, errors, edge cases
- [x] All 106 tests pass

### Remaining Milestones

Milestones 4–20 from the implementation roadmap.

### Known Issues

None.

### Technical Debt

None.

### Assumptions Made

- Comment-only lines without trailing newline produce only EOF (no NEWLINE) — consistent with the rule that blank lines only produce NEWLINE when they're not the last line.
- `RETURN` and `BREAK` each map to a single `TokenType` in the keyword dictionary; the parser will disambiguate by context. Duplicate dict key entries were removed (the function/extension section entry is kept).
- All leading space (` `) characters after `STRING`/`STRINGLN` keyword are stripped (consistent with spec §1.10 "Leading spaces after the keyword are stripped").
- Trailing spaces in STRING/STRINGLN body are stripped via `rstrip(" ")` (not `rstrip()` which would strip newlines/tabs).

### Notes for the Next Session

Milestone 3 is complete. `src/ducky/lexer.py` implements the full DuckyScript 3 lexer: character-level scanner with position tracking, all keyword/operator/identifier/literal recognition, comment stripping (REM, //, REM_BLOCK), STRING/STRINGLN body capture, ATTACKMODE parameter parsing, quoted-string escape-sequence resolution, and error detection (illegal characters, line-too-long, unterminated strings, invalid $/# identifiers, unterminated block comments). The next milestone (M4 — AST Node Definitions) will define AST node classes consumed by the parser.

---

## 9. Continuation Prompt

```
Continue development of the kducky project.

Before making any changes:
1. Read AGENTS.md.
2. Read the three planning documents under plans/.
3. Read the latest Session Handoff in AGENTS.md (§8).
4. Verify the Git working tree is clean.
5. Resume from Milestone 4 — AST Node Definitions.

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
