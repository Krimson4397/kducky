# DuckyScript 3 Interpreter — Implementation Roadmap

> Companion to DuckyScript3_Engineering_Spec.md (Version 1.0 Frozen)  
> Target: Raspberry Pi Pico 2 W (RP2350) · CircuitPython 10.x  

---

## Ground Rules

1. **Never write untestable code.** Every milestone ends with passing tests.
2. **Desktop before Pico.** All Python/CPython implementation and tests complete before any CircuitPython-specific code.
3. **Spec wins.** If implementation reveals a spec conflict, fix the code unless the spec is formally amended.
4. **Ambiguity → stop + report.** Do not guess.
5. **Merge only on green.** No milestone merges unless its acceptance criteria and all prior milestone tests pass.

---

## Milestone 1 — Repository Scaffold

**Goal:** Create the project directory structure, virtual environment, and toolchain configuration so all subsequent work has a consistent home.

**Deliverables:**
- `pyproject.toml` with project metadata, dependencies (CircuitPython stub types for type-checking only), test framework
- `src/ducky/` package directory
- `src/platform/desktop/` package directory
- `src/platform/pico/` package directory
- `tests/` directory with empty `__init__.py`
- `README.md` with build/test/run instructions
- `.gitignore` for Python + CircuitPython
- Ruff config in `pyproject.toml`
- mypy config in `pyproject.toml`
- pytest discovery working

**Files to create:**
- `pyproject.toml`
- `README.md`
- `.gitignore`
- `src/ducky/__init__.py`
- `src/platform/__init__.py`
- `src/platform/desktop/__init__.py`
- `src/platform/pico/__init__.py`
- `tests/__init__.py`
- `tests/conftest.py`

**Dependencies:** None (foundation milestone)

**Acceptance Criteria:**
- `pytest` discovers and runs zero tests (passes with exit code 5 or 0)
- `ruff check src/` passes on empty packages
- `mypy src/` passes on empty packages
- `pip install -e .` installs the `ducky` package
- Repository layout matches the architecture rules in the spec (§7)

**Complexity:** Low

---

## Milestone 2 — Token Definitions

**Goal:** Define every token type as an enum/class, plus the source position data class. This is the shared vocabulary the Lexer produces and the Parser consumes.

**Deliverables:**
- `TokenType` enum with all token categories from spec §3.1
- `Token` data class: `type: TokenType`, `value: str`, `line: int`, `column: int`
- `Operator` enum for all operators (§1.8)
- `ModifierKey` enum for all modifier keys (§1.4)
- `ActionKey` enum for all action keys (§1.5)
- Test: all enum values are documented and unique

**Files to create:**
- `src/ducky/tokens.py`

**Dependencies:** Milestone 1

**Acceptance Criteria:**
- Every keyword, operator, modifier, and action key from the spec has a corresponding enum member
- `Token` data class can be instantiated with type, value, line, column
- No imports from modules outside the standard library
- All tests pass

**Complexity:** Low

---

## Milestone 3 — Lexer

**Goal:** Implement the lexer that converts a DuckyScript source string into a sequence of tokens. Every tokenization rule from spec §3.2 must be implemented.

**Deliverables:**
- `DuckyLexer` class with `tokenize(source: str) -> list[Token]`
- Handling of all keyword, operator, modifier, action key, identifier, literal, and punctuation tokens
- `STRING`/`STRINGLN` body capture as `STRING_BODY` tokens
- `ATTACKMODE` parameter capture
- Comment stripping (`REM`, `//`, `REM_BLOCK`/`END_REM`)
- Escape sequence resolution in quoted strings
- Error reporting for: illegal characters, lines >256 chars, unterminated strings
- Position tracking (line, column) on every token

**Files to create:**
- `src/ducky/lexer.py`
- `tests/test_lexer.py`

**Dependencies:** Milestone 2

**Acceptance Criteria:**
- `STRING hello world` → `[STRING, STRING_BODY("hello world"), NEWLINE]`
- `CTRL-SHIFT ENTER` → `[CTRL, HYPHEN?, SHIFT, SPACE, ENTER, NEWLINE]`
- `REM anything` produces zero tokens
- `// comment` produces zero tokens
- `REM_BLOCK ... END_REM` produces zero tokens
- `DELAY 2000` → `[DELAY, INT(2000), NEWLINE]`
- `VAR $x = (5 + 3)` → `[VAR, DOLLAR, IDENT(x), EQ, LPAREN, INT(5), PLUS, INT(3), RPAREN, NEWLINE]`
- Max line length error emitted at 257th character
- Unterminated `"` string error emitted with line/col
- At minimum 15 distinct test cases covering keywords, comments, strings, combos, errors
- All tests pass

**Complexity:** Medium

---

## Milestone 4 — AST Node Definitions

**Goal:** Define every AST node class. The Parser produces these; the Interpreter consumes them. Pure data — no logic.

**Deliverables:**
- Base `ASTNode` class with `line: int`, `column: int`
- Node classes for: `Program`, `VarDecl`, `Assign`, `If`, `While`, `Break`, `Continue`, `FunctionDef`, `Call`, `Return`, `Block`
- Expression node classes for every expression level: `Literal`, `Variable`, `UnaryOp`, `BinaryOp`, `Grouping`, `FuncCall`
- Statement nodes for: `Delay`, `DefaultDelay`, `DefaultCharDelay`, `String`, `StringLn`, `KeyPress`, `ModifierCombo`, `InjectMod`, `Hold`, `Release`, `Repeat`, `Reset`, `RestartPayload`, `StopPayload`, `RandomChar`, `Led`, `ButtonDef`, `WaitForButtonPress`, `EnableButton`, `DisableButton`, `AttackMode`, `SaveAttackMode`, `RestoreAttackMode`, `WaitForLockKey`, `SaveRestoreLockState`, `HidePayload`, `RestorePayload`, `DuckyLang`, `ExtensionDef`
**Files to create:**
- `src/ducky/ast.py`
- `tests/test_ast.py`

**Dependencies:** Milestone 2 (uses Token types, not Lexer)

**Acceptance Criteria:**
- Every statement type from the grammar (§2) has a corresponding AST node
- Expression hierarchy matches the precedence table (§4.1)
- Nodes store start line/column from the source token
- Test: instantiate each node type with valid data
- All tests pass

**Complexity:** Medium

---

## Milestone 5 — Lexer Tests (Expanded)

**Goal:** Comprehensive test coverage for the lexer, including edge cases, error paths, and real payload patterns.

**Deliverables:**
- Tests for every keyword tokenization
- Tests for operator recognition (all operators, including multi-char `<=`, `==`, `&&`, `||`, `<<`, `>>`)
- Tests for string body capture (STRING, STRINGLN)
- Tests for ATTACKMODE parameter parsing
- Tests for comment stripping (REM, //, REM_BLOCK)
- Tests for escape sequences in quoted strings
- Tests for integer literals (decimal and hex)
- Tests for error conditions (illegal byte, line too long, unterminated string)
- Tests for whitespace handling (blank lines, leading/trailing, tabs)
- Edge cases: sole `$` without identifier, lone `REM_BLOCK` without `END_REM`, deeply nested quotes
- Real payload fragment tests (minimal working programs)

**Files to modify:**
- `tests/test_lexer.py`

**Dependencies:** Milestone 3

**Acceptance Criteria:**
- Minimum 30 test cases
- Every keyword from spec §1.3 tokenized correctly
- All three comment styles tested
- All error conditions produce correct diagnostics
- Edge cases documented as comments in test file
- All tests pass

**Complexity:** Low

---

## Milestone 6 — Parser

**Goal:** Implement the recursive-descent parser that converts a token stream (from the Lexer) into an AST (from Milestone 4).

**Deliverables:**
- `DuckyParser` class with `parse(tokens: list[Token]) -> Program` method
- Parsing for all statement types using the grammar (§2)
- Expression parsing matching the precedence table (§4.1)
- `NodeVisitor` base class with default traversal methods for every AST node type
- Error recovery: report first syntax error with diagnostic (line, column, expected vs found)
- AST node source positions are derived from token line/column, not stored directly on nodes
- `parse` returns a `Program` node containing the full AST
- Parser rejects: `RETURN` outside function, `BREAK`/`CONTINUE` outside loop, `REPEAT` after block-end keyword, `ELSE IF` without preceding `IF`

**Files to create:**
- `src/ducky/parser.py`
- `tests/test_parser.py`

**Dependencies:** Milestones 2, 4

**Acceptance Criteria:**
- Every statement type from the grammar parses to the correct AST node
- Expressions parse with correct precedence (`5 + 3 * 2` → `5 + (3 * 2)`)
- IF/ELSE IF/ELSE/END_IF nesting produces correct tree
- WHILE/END_WHILE nesting produces correct tree
- Function definitions with bodies parse correctly
- Nested expressions with parentheses work
- Syntax error on invalid input with line/col/diagnostic
- Error on `RETURN` at top level, `BREAK` outside loop
- All tests pass

**Complexity:** High

---

## Milestone 7 — Parser Tests (Expanded)

**Goal:** Comprehensive test coverage for the parser, including edge cases and error paths.

**Deliverables:**
- Tests for every statement type producing correct AST
- Tests for expression precedence (multiple levels of nesting)
- Tests for IF/ELSE IF/ELSE chaining (all branches, varying depth)
- Tests for WHILE with conditions and bodies
- Tests for function definitions and calls
- Tests for REPEAT with valid and invalid follow positions
- Tests for parser error recovery (first error, diagnostic quality)
- Tests for empty programs (blank lines, comments-only)
- Tests for `BREAK`/`CONTINUE` context validation
- Tests for `RETURN` outside function

**Files to modify:**
- `tests/test_parser.py`

**Dependencies:** Milestones 6

**Acceptance Criteria:**
- Minimum 40 test cases
- Every statement type tested with valid input
- Every error condition tested with valid diagnostic
- Expression precedence verified with multiple test cases
- All tests pass

**Complexity:** Medium

---

## Milestone 8 — Desktop Platform API

**Goal:** Implement the platform interface protocol and a desktop mock backend. The interpreter will be tested against this mock before any hardware code is written.

**Deliverables:**
- `PlatformInterface` protocol (abstract base class) with all backend accessors from spec §6.1
- `KeyboardBackend` protocol
- `FilesystemBackend` protocol
- `TimingBackend` protocol
- `RandomBackend` protocol
- `GPIOBackend` protocol
- `LEDBackend` protocol
- `HIDBackend` protocol
- `RecoveryBackend` protocol
- `DesktopKeyboardBackend` — logs events to an in-memory list
- `DesktopFilesystemBackend` — uses `pathlib` against a temp directory
- `DesktopTimingBackend` — uses `time.monotonic` and `time.sleep`
- `DesktopRandomBackend` — uses `random` module
- `DesktopGPIOBackend` — always returns false for button
- `DesktopLEDBackend` — logs state changes
- `DesktopHIDBackend` — logs changes
- `DesktopRecoveryBackend` — always returns false for skip

**Files to create:**
- `src/ducky/platform.py` (protocol definitions)
- `src/platform/desktop/backends.py` (all desktop implementations)
- `tests/test_platform.py`

**Dependencies:** Milestone 1 (foundation only — no language modules)

**Acceptance Criteria:**
- All protocol classes defined with abstract methods matching spec §6.2
- Desktop implementations instantiable and functional
- Keyboard events recorded and retrievable
- `DEFAULTDELAY 100` causes mock timing to record ≥100ms delays
- All tests pass
- No imports from CircuitPython or hardware libraries

**Complexity:** Medium

---

## Milestone 9 — Interpreter Core (Variables, Expressions, Statements)

**Goal:** Implement the interpreter core: variable management, expression evaluation, and basic statement execution on the desktop platform.

**Deliverables:**
- `Interpreter` class with `interpret(program: Program, platform: PlatformInterface)` method
- Variable storage (global scope + function-local scope per spec §5.1)
- Expression evaluation for all operators (matching spec §4.2)
- Statement execution for: `VarDecl`, `Assign`, `Delay`, `DefaultDelay`, `DefaultCharDelay`, `Repeat`, `Reset`, `StopPayload`, `RestartPayload`
- Division/remainder by zero → runtime error with diagnostic
- Undeclared variable read → runtime error
- Assignment to undeclared variable → runtime error

**Files to create:**
- `src/ducky/interpreter.py`
- `tests/test_interpreter_core.py`

**Dependencies:** Milestones 4, 6, 8

**Acceptance Criteria:**
- `VAR $x = 42` stores and retrieves the value
- `VAR $x` without initializer defaults to 0
- `$x = $x + 1` reads, increments, stores
- `4 + 3 * 2` evaluates to 10 (correct precedence)
- `65535 + 1` wraps to 0
- `/ 0` and `% 0` produce runtime errors
- `DELAY 500` calls `timing.sleep_ms(500)`
- `DEFAULTDELAY 100` causes subsequent statements to call `sleep_ms(100)` after execution
- `REPEAT 3` repeats the immediately preceding statement 3 extra times
- Undeclared variable access produces an error
- All tests pass

**Complexity:** High

---

## Milestone 10 — Interpreter: Control Flow

**Goal:** Add IF/ELSE IF/ELSE, WHILE, BREAK, CONTINUE to the interpreter.

**Deliverables:**
- `visit_if` method handling conditional branching with short-circuit semantics
- `visit_while` method with pre-check loop
- `visit_break` statement
- `visit_continue` statement
- Truthiness per spec (§5.6): 0 and "" are false, everything else true

**Files to modify:**
- `src/ducky/interpreter.py`
- `tests/test_interpreter_control_flow.py`

**Dependencies:** Milestone 9

**Acceptance Criteria:**
- `IF (1) THEN ... END_IF` executes the branch
- `IF (0) THEN ... ELSE ... END_IF` executes the else branch
- `IF (0) THEN ... ELSE IF (1) THEN ... END_IF` executes the else-if branch
- Nested IF statements work correctly
- `WHILE ($i > 0) ... END_WHILE` loops until condition is false
- `BREAK` exits the innermost WHILE
- `CONTINUE` skips to next iteration
- `BREAK` outside WHILE → runtime error
- All tests pass

**Complexity:** Medium

---

## Milestone 11 — Interpreter: Functions

**Goal:** Add function definition, calls, RETURN, and parameter passing (via global variables per spec §5.2).

**Deliverables:**
- `visit_function_def` — registers function
- `visit_call` — jumps to function body, creates local scope
- `visit_return` — exits function with optional value
- Recursion support (forward references work — functions registered before any statement executes)
- Scope management: local variables (§5.1 project extension), global access

**Files to modify:**
- `src/ducky/interpreter.py`
- `tests/test_interpreter_functions.py`

**Dependencies:** Milestone 9

**Acceptance Criteria:**
- `FUNCTION f() ... END_FUNCTION` then `f()` executes the body
- `RETURN 42` returns value to caller
- `RETURN` without value returns 0
- Recursive function calls work
- Function calls as expressions (`$x = f()`) return values
- Local variables don't leak to global scope
- Undefined function call → runtime error
- All tests pass

**Complexity:** Medium

---

## Milestone 12 — Interpreter: Keyboard Commands

**Goal:** Implement all keyboard/output commands: STRING, STRINGLN, modifier combos, HOLD/RELEASE, INJECT_MOD, and the random character commands.

**Deliverables:**
- `visit_string` — types text via keyboard backend
- `visit_string_ln` — types text + ENTER
- `visit_modifier_combo` — calls `press_modifier_combo`
- `visit_hold` / `visit_release` — calls `press(key)` / `release(key)`
- `visit_inject_mod` — modifier-only press+release
- `visit_random_char` — generates random character via random backend
- `visit_key_press` — single action key
- Integration with `DEFAULT_CHAR_DELAY` between characters
- Key release on any error path (§5.3 critical)

**Files to modify:**
- `src/ducky/interpreter.py`
- `tests/test_interpreter_keyboard.py`

**Dependencies:** Milestone 9

**Acceptance Criteria:**
- `STRING hello` calls `keyboard.write("hello")`
- `STRINGLN hello` calls `keyboard.write("hello")` then presses ENTER
- `CTRL SHIFT ESC` presses CTRL → SHIFT → ESC, releases ESC → SHIFT → CTRL
- `HOLD a` / `DELAY 1000` / `RELEASE a` holds then releases
- `RANDOM_CHAR` types one random printable character
- Character delay is respected between keystrokes
- Error path releases all keys
- All tests pass

**Complexity:** Medium

---

## Milestone 13 — Interpreter: Integration Tests

**Goal:** Run full payloads through the interpreter on the desktop mock to verify end-to-end correctness.

**Deliverables:**
- Full program tests: realistic payloads from start to finish
- Test payloads covering: hello world, key combos, conditional execution, loops with variables, functions with return values, nested control flow, random character generation, ATTACKMODE commands, DEFINE constants (preprocessor)
- Expected event sequences verified against mock backend
- Edge case payloads: empty program, single statement, deeply nested structures, mixed official and extension features

**Files to create:**
- `tests/test_integration.py`

**Dependencies:** Milestones 9, 10, 11, 12

**Acceptance Criteria:**
- Minimum 10 integration payloads tested end-to-end
- Each payload produces the expected sequence of platform events
- Error paths produce correct diagnostics
- All tests pass

**Complexity:** Medium

---

## Milestone 14 — Pico Platform Implementation

**Goal:** Implement the hardware-specific platform backends for the Raspberry Pi Pico 2 W running CircuitPython.

**Deliverables:**
- Single `PicoPlatform` class implementing all 26 `PlatformInterface` methods from spec §6 directly (flat protocol, not hierarchical sub-backends)
- Guarded CircuitPython imports (`try/except ImportError`) so the module imports safely on desktop
- `_ACTION_KEY_MAP`: exhaustive mapping of all 69 `ActionKey` members to `adafruit_hid` keycodes
- `_MODIFIER_KEY_MAP`: exhaustive mapping of all 8 `ModifierKey` members to `adafruit_hid` keycodes
- Seeded pseudo-random number generator using `os.urandom` (RP2350 TRNG) with `random.Random`
- `main.py` entrypoint: reads `/payload.dd`, runs lexer → parser → interpreter pipeline, signals status via onboard LED
- `boot.py` USB configuration: enables HID keyboard + optional storage disable via `/STORAGE_DISABLE` marker

**Files to create:**
- `src/platform/pico/backends.py`
- `src/platform/pico/main.py`
- `src/platform/pico/boot.py`
- `tests/test_pico_platform.py` (desktop tests that validate mock matches Pico interface contract — not runnable on Pico itself)

**Dependencies:** Milestone 8 (PlatformInterface protocol)

**Acceptance Criteria:**
- Single `PicoPlatform` class satisfies `PlatformInterface` protocol (all 26 methods present with matching signatures)
- Module imports safely on desktop (`_HAS_HW` is `False`, no CircuitPython imports leak)
- `_ACTION_KEY_MAP` covers all 69 `ActionKey` members
- `_MODIFIER_KEY_MAP` covers all 8 `ModifierKey` members
- `boot.py` enables USB HID + optional storage disable
- `main.py` executes payload through full lexer → parser → interpreter pipeline
- Signal methods (`restart_payload`, `stop_payload`) raise correct payload control exceptions
- Contract tests verify interface compliance structurally without hardware
- All existing 538 desktop tests still pass
- All protocol interfaces satisfied (checked via mypy)
- Tests verify interface contract compliance (17 contract tests)

**Complexity:** High

---

## Milestone 15 — Keyboard Layout Support

**Goal:** Create and validate the minimum keyboard layout set from spec Appendix B.

**Deliverables:**
- Layout JSON files for: US, GB, DE, FR, ES, IT, JP, DK, NO, SE, FI, PT, BR, RU, PL, CZ
- Layout loader module with caching
- Layout switch at runtime via `DUCKY_LANG`
- Test: every layout maps all printable ASCII characters

**Files to create:**
- `src/ducky/layouts/` directory with 16 JSON files
- `src/ducky/layouts/__init__.py` (loader)
- `tests/test_layouts.py`

**Dependencies:** Milestone 8, 12

**Acceptance Criteria:**
- 16 layout files present with correct format
- Layout loader finds and loads each layout
- All printable ASCII characters map to valid HID scancodes
- `DUCKY_LANG DE` switches layout at runtime
- All tests pass

**Complexity:** Medium

---

## Milestone 16 — DEFINE Preprocessor

**Goal:** Implement compile-time constant substitution for `DEFINE #NAME value`.

**Deliverables:**
- Preprocessor pass that scans source for `DEFINE` lines, builds a symbol table, and substitutes `#NAME` occurrences in all subsequent lines
- Integrated into the pipeline: Source → Preprocessor → Lexer → Parser → Interpreter
- Error on undefined `#NAME` reference

**Files to create:**
- `src/ducky/preprocessor.py`
- `tests/test_preprocessor.py`

**Dependencies:** Milestone 3 (preprocessor output feeds lexer)

**Acceptance Criteria:**
- `DEFINE #DELAY 2000` followed by `DELAY #DELAY` produces `DELAY 2000`
- `DEFINE #TEXT Hello World` followed by `STRINGLN #TEXT` types "Hello World"
- Undefined `#MISSING` produces an error
- `#` in string context (between quotes) is not substituted
- All tests pass

**Complexity:** Low

---

## Milestone 17 — Error Reporting & Recovery

**Goal:** Polish error messages and add runtime diagnostics that help users debug payloads.

**Deliverables:**
- Unified `DuckyError` hierarchy: `LexerError`, `ParseError`, `RuntimeError`
- Each error carries line, column, message, and optional source line snippet
- `REPEAT` validation error on invalid follow position
- Division/remainder by zero with clear message
- Undeclared variable access with variable name
- Function call to undefined function with function name
- All error messages follow format: `[ERROR] line N, col M: description`

**Files to create:**
- `src/ducky/errors.py`

**Files to modify:**
- `src/ducky/lexer.py` (use error types)
- `src/ducky/parser.py`
- `src/ducky/interpreter.py`
- `tests/test_errors.py`

**Dependencies:** Milestones 3, 6, 9

**Acceptance Criteria:**
- Every error path produces a `DuckyError` subclass with line, col, message
- Error messages are human-readable and actionable
- At least 15 error conditions tested
- All tests pass

**Complexity:** Low

---

## Milestone 18 — ATTACKMODE / HID Configuration

**Goal:** Implement ATTACKMODE, SAVE_ATTACKMODE, RESTORE_ATTACKMODE with USB descriptor configuration.

**Deliverables:**
- `visit_attack_mode` — configures HID backend
- `visit_save_attack_mode` / `visit_restore_attack_mode` — save/restore state
- HID backend on Pico configures USB descriptors dynamically
- Desktop mock logs configuration changes for test verification

**Files to modify:**
- `src/ducky/interpreter.py`
- `src/platform/desktop/backends.py`
- `src/platform/pico/backends.py`
- `tests/test_attackmode.py`

**Dependencies:** Milestones 9, 14

**Acceptance Criteria:**
- `ATTACKMODE HID STORAGE` configures both interfaces
- `ATTACKMODE HID VID_05AC` sets vendor ID
- `ATTACKMODE OFF` disconnects USB
- `SAVE_ATTACKMODE` / `ATTACKMODE OFF` / `RESTORE_ATTACKMODE` restores saved state
- `VID_RANDOM` / `PID_RANDOM` randomize the field
- Desktop mock records all configuration calls
- All tests pass

**Complexity:** Medium

---

## Milestone 19 — Hardware Validation (Pico)

**Goal:** Run the interpreter on actual Pico 2 W hardware and validate against a test payload checklist.

**Deliverables:**
- Test payload `.dd` files for: basic typing, modifier combos, conditional execution, WHILE loop, function call, ATTACKMODE switching, LED control, button handling, recovery mode
- Test procedure document: what to observe for each payload
- LED status indicators: green = idle, blinking green = processing, red = error, blue = recovery mode
- Validation results recorded in `HARDWARE_VALIDATION.md`

**Files to create:**
- `payloads/` directory with test payloads
- `HARDWARE_VALIDATION.md` (test procedure and results)

**Dependencies:** Milestone 14, 18

**Acceptance Criteria:**
- All test payloads produce correct observable behavior on the host computer
- LED indicates correct state throughout execution
- Recovery mode (boot button held) skips payload and exposes CIRCUITPY
- Error payload shows red LED, error text on host (if possible)
- All validation results documented

**Complexity:** High

---

## Milestone 20 — Final Integration & Release Readiness

**Goal:** Full pipeline integration, documentation, release packaging, and version 1.0 readiness.

**Deliverables:**
- `ducky-run` CLI entry point (runs payload file on desktop)
- `main.py` for Pico (CircutryPython auto-run)
- Full test suite passes with 100% of tests green
- `README.md` with: architecture overview, build instructions, usage examples, payload authoring guide, troubleshooting, and contribution guide
- `CONTRIBUTING.md` with development workflow (§9)
- `CHANGELOG.md` with version history
- GitHub CI configuration (or equivalent) for: ruff, mypy, pytest on push/PR
- Version 1.0 tag

**Files to create:**
- `src/ducky/cli.py`
- `CONTRIBUTING.md`
- `CHANGELOG.md`
- `.github/workflows/ci.yml`

**Files to modify:**
- `pyproject.toml` (add CLI entry point)
- `README.md`

**Dependencies:** All prior milestones

**Acceptance Criteria:**
- `ducky-run payload.dd` executes payload on desktop and prints event log
- Pico `main.py` auto-runs on power-up
- Full test suite passes
- ruff, mypy, pytest all green in CI
- Documentation covers architecture, usage, contributing
- Version 1.0 tagged

**Complexity:** Medium

---

## Dependency Graph (Topological Order)

```
M1 (Scaffold)
  ├─ M2 (Tokens) → M3 (Lexer) → M5 (Lexer Tests)
  │                 └→ M16 (Preprocessor)
  ├─ M4 (AST) → M6 (Parser) → M7 (Parser Tests)
  ├─ M8 (Desktop Platform)
  │    ├─ M14 (Pico Platform)
  │    ├─ M15 (Layouts)
  │    └─ M19 (HW Validation)
  │
  M3 + M4 + M8 → M9 (Interpreter Core)
  ├─ M10 (Control Flow)
  ├─ M11 (Functions)
  ├─ M12 (Keyboard Commands)
  │
  M9 + M10 + M11 + M12 → M13 (Integration Tests)
  M9 + M18 → M18 (ATTACKMODE)
  
  M17 (Error Reporting) — applies to M3, M6, M9
  M20 (Final Integration) — requires all
```

---

## Recommended First Milestone

**Milestone 1 — Repository Scaffold.**

**Why:** It is the only milestone with zero dependencies upon any other. Everything else — tokens, lexer, parser, interpreter — requires a place to live, a way to be discovered, and a toolchain to validate. Attempting Milestone 2 (Tokens) without a scaffold means writing code that has no module structure, no test runner, no linter, and no CI. Milestone 1 is small (Low complexity), gives us `pytest`, `ruff`, and `mypy` from day one, and ensures every subsequent line of code is validated immediately.

**Expected outcome:** A working project skeleton at `D:\kducky\` where:
- `pip install -e .` installs the `ducky` package
- `pytest` discovers and runs tests
- `ruff check src/` passes linting
- `mypy src/` passes type checking
- The directory structure cleanly separates src (language core, platform backends) and tests

This takes approximately 15–30 minutes to complete and unblocks every subsequent milestone.
