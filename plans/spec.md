# DuckyScript 3 Interpreter for Raspberry Pi Pico 2 W

## Mission

Implement a production-quality, open-source DuckyScript 3 interpreter
targeting the Raspberry Pi Pico 2 W (RP2350) using CircuitPython 10.x.

The objective is not merely to execute payloads, but to build a
maintainable language implementation that is architecturally similar to
a compiler/interpreter.

The project must be modular, well-tested, and designed so that the
entire language implementation can later be ported to native C/C++ with
minimal redesign.

Whenever there are multiple possible implementations, prioritize:

1.  Correctness
2.  Maintainability
3.  Testability
4.  Portability
5.  Performance

Never sacrifice architecture for short-term convenience.

------------------------------------------------------------------------

# Overall Goals

The finished firmware should:

-   Execute DuckyScript 3 payloads.
-   Support as much of the official language as practical.
-   Be easy to debug.
-   Produce meaningful parser and runtime errors.
-   Separate language implementation from hardware.
-   Support desktop testing without a Pico.
-   Be future-proof for native firmware.

------------------------------------------------------------------------

# Existing Projects

## pico-ducky

Use as reference for:

-   HID backend
-   key mapping
-   keyboard layouts
-   recovery mode
-   boot process
-   payload loading
-   CircuitPython implementation

**Do NOT copy the interpreter architecture.**

Its parser is essentially a line interpreter.

Do not reproduce that architecture.

## rasper-ducky

Use as reference for:

-   parser organization
-   lexer organization
-   AST organization
-   testing approach

Treat the implementation as inspiration, not source of truth.

Rewrite everything necessary.

## Hak5 Documentation

The official Hak5 documentation is the language specification.

Whenever there is ambiguity, compatibility with Hak5 takes priority.

------------------------------------------------------------------------

# High-Level Architecture

``` text
payload.dd
     │
 Lexer
     │
 Parser
     │
 AST
     │
 Interpreter
     │
 Platform API
     ├── HID
     ├── Filesystem
     ├── Timing
     ├── GPIO
     └── Recovery
```

Nothing above Platform API may import CircuitPython-specific modules.

Only the Platform layer may interact with hardware.

------------------------------------------------------------------------

# Repository Structure

``` text
src/
├── lexer/
├── parser/
├── ast/
├── interpreter/
├── platform/
├── hid/
├── filesystem/
├── timing/
├── gpio/
├── recovery/
├── errors/
├── tests/
├── docs/
└── examples/
```

Keep responsibilities isolated.

No circular imports.

------------------------------------------------------------------------

# Language Requirements

Support:

-   Variables
-   Expressions
-   Arithmetic
-   Comparison operators
-   Boolean operators
-   IF
-   ELSE
-   WHILE
-   LOOP
-   Functions
-   Return values
-   Delays
-   Keyboard commands
-   Modifier keys
-   String typing
-   Comments
-   Random values
-   Keyboard layouts

Unsupported features should produce explicit errors.

Never silently ignore commands.

------------------------------------------------------------------------

# Lexer Requirements

The lexer is responsible only for tokenization.

Responsibilities:

-   Tokenize input
-   Preserve line/column information
-   Ignore comments
-   Detect invalid characters
-   Support escaped strings
-   Emit EOF token

Each token must contain:

``` text
type
value
line
column
```

------------------------------------------------------------------------

# Parser Requirements

Implement a recursive-descent parser.

Avoid parser generators.

Operator precedence must be explicit.

The parser produces an AST only.

Never execute code during parsing.

On parse failure report:

-   Line
-   Column
-   Offending token
-   Expected token(s)
-   Human-readable explanation

------------------------------------------------------------------------

# AST Requirements

Each node should be its own class.

Examples:

-   AssignmentNode
-   IfNode
-   WhileNode
-   FunctionNode
-   CallNode
-   LiteralNode
-   IdentifierNode
-   BinaryExpressionNode
-   UnaryExpressionNode

AST nodes contain data only.

------------------------------------------------------------------------

# Interpreter

The interpreter walks the AST.

It must never know about USB HID internals.

Use a Platform API:

``` text
platform.keyboard.press()
platform.keyboard.release()
platform.keyboard.write()
platform.delay()
platform.random()
platform.filesystem()
```

------------------------------------------------------------------------

# Variables

Support global and function-local scope.

Undefined variables must generate runtime errors.

------------------------------------------------------------------------

# Expressions

Support:

-   -   

-   -   

-   -   

-   /

-   \%

-   ==

-   !=

-   

-   \<

-   =

-   \<=

-   &&

-   \|\|

-   !

-   ()

------------------------------------------------------------------------

# Functions

Support parameters and return values.

Support recursion if practical.

------------------------------------------------------------------------

# Runtime Errors

Never crash Python.

Display clear diagnostics including line, column and description.

Execution should halt cleanly.

------------------------------------------------------------------------

# USB HID

Requirements:

-   Reliable typing
-   Correct modifier handling
-   Automatic key release
-   Proper delays
-   Windows/Linux/macOS compatibility
-   Keyboard layouts

Never leave modifier keys pressed.

------------------------------------------------------------------------

# Filesystem

Support:

``` text
payload.dd
config.json
layouts/
payloads/
```

Future-proof for multiple payloads.

------------------------------------------------------------------------

# Recovery Mode

If the boot button is held:

-   Do not execute payload
-   Expose CIRCUITPY drive
-   Allow editing
-   Recover from crashes

------------------------------------------------------------------------

# Debug Mode

Optional verbose logging.

Include:

-   Tokens
-   AST
-   Interpreter execution
-   HID events
-   Timing

------------------------------------------------------------------------

# Testing

Every module must have tests.

-   Lexer
-   Parser
-   AST
-   Interpreter
-   Platform abstraction

Most tests should run on desktop Python.

------------------------------------------------------------------------

# Development Workflow

For every feature:

1.  Implement
2.  Unit test
3.  Desktop test
4.  Pico test
5.  Windows test
6.  Linux test
7.  macOS test
8.  Refactor
9.  Document
10. Commit

------------------------------------------------------------------------

# Debugging Workflow

If it works:

-   Verify
-   Add regression test
-   Continue

If parser fails:

-   Inspect tokens
-   Inspect AST
-   Reduce to minimal example
-   Fix
-   Add regression test

If HID fails:

-   Check enumeration
-   Check timing
-   Check modifier release
-   Check keyboard layout
-   Test another OS

If payload fails:

Determine whether the issue is in:

-   Lexer
-   Parser
-   Interpreter
-   Platform

Never guess. Isolate first.

------------------------------------------------------------------------

# Coding Standards

-   Small functions
-   Single responsibility
-   Type hints
-   Clear naming
-   No duplicated logic
-   Minimal global mutable state
-   Document public APIs
-   Independently testable modules

------------------------------------------------------------------------

# Before Every Commit

Verify:

-   Builds successfully
-   No syntax errors
-   Tests pass
-   No regressions
-   Documentation updated
-   Consistent formatting

------------------------------------------------------------------------

# Definition of Done

A feature is complete only when:

-   It works
-   It is tested
-   It is documented
-   It follows the architecture
-   It remains portable
-   It does not break existing functionality

If any condition is false, the feature is **not complete**.
