# DuckyScript 3 Interpreter — Engineering Specification

> Version 1.0 (Frozen)  
> Target: Raspberry Pi Pico 2 W (RP2350) · CircuitPython 10.x  

## Specification Freeze

This specification is **frozen** for the implementation phase. Changes are permitted only when:

- An implementation issue is discovered that requires clarification.
- The official Hak5 DuckyScript 3 specification changes.
- A deliberate project extension is approved.

**Implementation rule**: If code conflicts with this specification during implementation, the code must be changed — unless an approved specification update is made. If an ambiguity is discovered, stop implementation and report it. Do not silently modify the specification.

---

## Specification Authority

This document is the **canonical engineering specification** for the DuckyScript 3 interpreter project. It defines what must be built and how components must interact.

- If the implementation and this specification disagree, **the specification wins**.
- If the official Hak5 DuckyScript 3 documentation conflicts with this specification, **Hak5 wins** — unless this document explicitly lists the conflict as a **Known Deviation**.
- All ambiguities not resolved by Hak5 or this specification must be escalated per the Ambiguity Policy (§11).

---

## Conformance

| Level              | Description                                                                |
| ------------------ | -------------------------------------------------------------------------- |
| Required           | All features marked **[Official]** must be implemented for Hak5 compliance. |
| Optional           | Features marked **[Extension]** may be omitted without breaking compliance. |
| Project Extensions | Features marked **[Project]** are our own additions (documented in §1.14). |
| Known Deviations   | Behaviors where we intentionally diverge from Hak5 (documented in §1.15).  |

---

## 1. Language Specification

### 1.1 Character Set

DuckyScript 3 source text uses ASCII (codepoints 0x20–0x7E) plus:

| Character       | Codepoint | Purpose                          |
| --------------- | --------- | -------------------------------- |
| Space           | 0x20      | Token separator, STRING content  |
| Tab             | 0x09      | Whitespace                       |
| Newline         | 0x0A      | Statement terminator             |
| Carriage Return | 0x0D      | Ignored (treated as whitespace)  |

All other byte values are illegal. A lexer encountering them must report an error with line number, column, and the hex value of the illegal byte.

### 1.2 Identifiers

**[Official]** Variable identifiers begin with `$` and follow: `$[a-zA-Z_][a-zA-Z0-9_]*`

**[Official]** DEFINE constant identifiers begin with `#` and follow: `#[a-zA-Z_][a-zA-Z0-9_]*`

**[Official]** Function identifiers begin with a letter or underscore, contain only letters, digits, and underscores, and must be followed by `()` in both definitions and calls.

All identifiers are **case-sensitive**.

### 1.3 Reserved Keywords

**[Official]** Keywords are case-insensitive. By convention they are written in ALL CAPS.

**Control Flow:** `IF`, `THEN`, `ELSE`, `END_IF`, `WHILE`, `END_WHILE`  
**Functions:** `FUNCTION`, `END_FUNCTION`, `RETURN`  
**Variables:** `VAR`  
**Preprocessor:** `DEFINE`  
**Comments:** `REM`, `REM_BLOCK`, `END_REM`  
**Payload Control:** `REPEAT`, `RESET`, `RESTART_PAYLOAD`, `STOP_PAYLOAD`  
**Delays:** `DELAY`, `DEFAULTDELAY`, `DEFAULT_DELAY`, `DEFAULTCHARDELAY`, `DEFAULT_CHAR_DELAY`  
**Keyboard Output:** `STRING`, `STRINGLN`, `INJECT_MOD`, `HOLD`, `RELEASE`  
**Attack Mode:** `ATTACKMODE`, `SAVE_ATTACKMODE`, `RESTORE_ATTACKMODE`  
**LED:** `LED_OFF`, `LED_R`, `LED_G`, `LED_B`  
**Button:** `BUTTON_DEF`, `END_BUTTON`, `DISABLE_BUTTON`, `ENABLE_BUTTON`, `WAIT_FOR_BUTTON_PRESS`  
**Lock Key Wait:** `WAIT_FOR_CAPS_ON`, `WAIT_FOR_CAPS_OFF`, `WAIT_FOR_CAPS_CHANGE`, `WAIT_FOR_NUM_ON`, `WAIT_FOR_NUM_OFF`, `WAIT_FOR_NUM_CHANGE`, `WAIT_FOR_SCROLL_ON`, `WAIT_FOR_SCROLL_OFF`, `WAIT_FOR_SCROLL_CHANGE`, `SAVE_HOST_KEYBOARD_LOCK_STATE`, `RESTORE_HOST_KEYBOARD_LOCK_STATE`  
**Random:** `RANDOM_CHAR`, `RANDOM_LOWERCASE_LETTER`, `RANDOM_UPPERCASE_LETTER`, `RANDOM_LETTER`, `RANDOM_NUMBER`, `RANDOM_SPECIAL`  
**Files:** `HIDE_PAYLOAD`, `RESTORE_PAYLOAD`  
**Constants:** `TRUE`, `FALSE`  

**[Extension]** The following keywords are from third-party DuckyScript implementations and are **not** official Hak5 DuckyScript 3.0 — we support them as extensions:

`BREAK`, `CONTINUE`, `EXTENSION`, `END_EXTENSION`, `STRINGDELAY`, `DUCKY_LANG`, `LED_B`

### 1.4 Modifier Keys

**[Official]** The following modifier key names are case-insensitive:

`CONTROL` / `CTRL`, `SHIFT`, `ALT`, `GUI` / `WINDOWS` / `COMMAND`, `OPTION`

In a modifier combo, every token before the last is a modifier. The last token is the action key. Modifier-only press+release requires `INJECT_MOD` before the modifier name.

### 1.5 Action Keys

**[Official]** Case-insensitive:

**Navigation:** `UP`/`UPARROW`, `DOWN`/`DOWNARROW`, `LEFT`/`LEFTARROW`, `RIGHT`/`RIGHTARROW`, `PAGEUP`, `PAGEDOWN`, `HOME`, `END`, `INSERT`, `DELETE`/`DEL`  
**Editing:** `ENTER`/`RETURN`, `SPACE`, `TAB`, `BACKSPACE`, `ESCAPE`/`ESC`, `PRINTSCREEN`, `SCROLLLOCK`, `PAUSE`/`BREAK`, `MENU`/`APP`, `CAPSLOCK`, `NUMLOCK`, `POWER`  
**Function:** `F1`–`F12`  
**Numpad:** `KP_SLASH`, `KP_ASTERISK`, `KP_MINUS`, `KP_PLUS`, `KP_ENTER`, `KP_0`–`KP_9`, `KP_DOT`, `KP_EQUAL`, `KP_COMMA`, `KP_00`, `KP_000`  
**Extended:** `102ND`, `COMPOSE`, `KPEQUAL`, `PROPS`, `UNDO`, `PASTE`

### 1.6 Literals

| Type    | Syntax            | Range     | Notes               |
| ------- | ----------------- | --------- | ------------------- |
| Integer | `[0-9]+` or `0x[0-9a-fA-F]+` | 0–65535 (uint16) | Overflow wraps modulo 65536 |
| Boolean | `TRUE` / `FALSE`  | 1 / 0     | Integer aliases     |
| String  | `"..."` (expression context) or bare text (after `STRING`) | ASCII printable | Escape sequences in quoted strings only |

### 1.7 Comments

**[Official]**  
- Single-line: `REM <text>` or `// <text>` — rest of line is ignored.  
- Multi-line: `REM_BLOCK [label]` ... `END_REM` — everything between is ignored.  

**[Extension]** `//` comment syntax is an extension. The official Hak5 syntax uses only `REM` and `REM_BLOCK`.

### 1.8 Operators

**[Official]** All operators and their behavior:

| Category     | Operators                  | Associativity | Notes                          |
| ------------ | -------------------------- | ------------- | ------------------------------ |
| Unary        | `!` `-`                    | Right         | `!` = logical NOT, `-` = negate  |
| Multiplicative | `*` `/` `%` `^`          | Left          | `^` = exponentiation per Hak5  |
| Additive     | `+` `-`                    | Left          | `+` = addition or string concat |
| Shift        | `<<` `>>`                  | Left          | Bitwise shift                  |
| Relational   | `<` `<=` `>` `>=`          | Left          | Integer comparison only        |
| Equality     | `==` `!=`                  | Left          | Cross-type → 0 (false)         |
| Bitwise AND  | `&`                        | Left          |                                |
| Bitwise OR   | `\|`                       | Left          |                                |
| Logical AND  | `&&`                       | Left          | Short-circuit                  |
| Logical OR   | `\|\|`                     | Left          | Short-circuit                  |
| Assignment   | `=`                        | Right         | LHS must be variable reference |

**[Implementation Decision]** The official Hak5 documentation lists `^` as exponentiation. Some third-party implementations treat it as bitwise XOR. This implementation follows Hak5: `^` is exponentiation with multiplicative precedence. There is no bitwise XOR operator.

**[Implementation Decision]** The official Hak5 docs say "parentheses are required to define precedence conventions." This implementation supports both: full precedence when parentheses are omitted, and explicit parentheses for override.

### 1.9 Escape Sequences

**[Official]** Bare text after `STRING`/`STRINGLN` has no escape sequences — every character is typed literally.

**[Official]** Quoted strings in expression context support: `\\` `\"` `\n` `\r` `\t` `\xNN`

### 1.10 Whitespace Rules

- Leading/trailing whitespace on each line is ignored.
- Multiple whitespace characters between tokens are collapsed to a single delimiter.
- Blank lines are ignored.
- Inside `STRING`/`STRINGLN`, content after the keyword is the text to type. Leading spaces after the keyword are stripped. Internal spaces are preserved. Trailing spaces are omitted.

### 1.11 Statement Delimiters

Each statement is terminated by a **newline**. No semicolons. Maximum line length is 256 characters.

### 1.12 Program Structure

A DuckyScript program is a sequence of statements and function definitions, one per line. `FUNCTION` definitions are **not** executed during linear flow — they are registered and execute only when called.

### 1.13 Unsupported Official Features

The following official DuckyScript 3 features are **not supported** in this implementation and must produce a clear error if encountered:

- `RANDOM_LINE` — reading random lines from files
- `RANDOM_STRING` — random string generation  
- Embedded language blocks (`STRING_POWERSHELL`, `STRING_BATCH`, `STRING_BASH`, `STRING_JAVASCRIPT`, `STRING_PYTHON`, `STRING_RUBY`, `STRING_HTML`)
- `REPLAY` command alias
- `KEYCODE` raw HID injection (O.MG-specific)
- `JIGGLER` (O.MG-specific)
- `MOUSE` commands (O.MG-specific)
- `REBOOT` (O.MG-specific)
- `F13`–`F24` function keys
- Media keys beyond basic set

### 1.14 Project Extensions

**[Project]** The following are additions unique to this implementation:

| Feature      | Syntax                 | Behavior                                          |
| ------------ | ---------------------- | ------------------------------------------------- |
| BREAK        | `BREAK`                | Exit the innermost WHILE loop                     |
| CONTINUE     | `CONTINUE`             | Skip to the next WHILE iteration                  |
| STRINGDELAY  | `STRINGDELAY <expr>`   | Alias for DEFAULT_CHAR_DELAY                      |
| DUCKY_LANG   | `DUCKY_LANG <code>`    | Change keyboard layout at runtime                 |
| LED_B        | `LED_B`                | Blue LED (on devices that support it)             |
| EXTENSION    | `EXTENSION name ... END_EXTENSION` | Extension block (parsed but semantics are extension-specific) |

### 1.15 Known Deviations from Hak5

| Feature                   | Hak5 Behavior                                  | Our Behavior                                       |
| ------------------------- | ---------------------------------------------- | -------------------------------------------------- |
| Operator precedence       | "Parentheses required" implies flat precedence | Full C-style precedence with explicit precedence table |
| `//` comments             | Not officially documented                      | Supported as equivalent to `REM`                     |
| BREAK / CONTINUE          | Not in official spec                           | Supported (marked as extension)                    |
| Runtime layout switching  | Hak5 payloads specify layout at compile time   | `DUCKY_LANG` runtime command                       |
| `^` operator              | Documented as exponentiation                   | Implemented as exponentiation                      |
| Variable type             | Unsigned 16-bit (0–65535)                      | Unsigned 16-bit with wrapping                      |
| Variable scope            | All variables are global                       | Global + function-local scope                      |

---

## 2. Formal Grammar (EBNF)

Notation: `{ }` = zero or more, `[ ]` = zero or one, `|` = alternation, `' '` = literal.

```
Program        = { Statement | FunctionDef | ExtensionDef | BlankLine }

Statement      = CommentStmt | DelayStmt | DefaultDelayStmt | DefaultCharDelayStmt
               | StringStmt | StringLnStmt | KeyStmt | ModifierComboStmt
               | InjectModStmt | HoldStmt | ReleaseStmt | RepeatStmt
               | ResetStmt | RestartPayloadStmt | StopPayloadStmt
               | VarDeclStmt | AssignStmt | IfStmt | WhileStmt
               | LoopControlStmt | CallStmt | ReturnStmt
               | RandomStmt | LedStmt | ButtonDefStmt | WaitForButtonStmt
               | ButtonControlStmt | AttackModeStmt
               | WaitForLockKeyStmt | SaveRestoreLockStateStmt
               | HideRestorePayloadStmt | DuckyLangStmt
               | SaveAttackModeStmt | RestoreAttackModeStmt
               | ExpressionStmt

CommentStmt           = ('REM' | '//') , RestOfLine
BlockComment          = 'REM_BLOCK' , [ Label ] , Newline , { any } , 'END_REM' , Newline
DelayStmt             = 'DELAY' , Expression , Newline
DefaultDelayStmt      = ('DEFAULTDELAY' | 'DEFAULT_DELAY') , Expression , Newline
DefaultCharDelayStmt  = ('DEFAULTCHARDELAY' | 'DEFAULT_CHAR_DELAY' | 'STRINGDELAY') , Expression , Newline
StringStmt            = 'STRING' , StringContent , Newline
StringLnStmt          = 'STRINGLN' , [ StringContent ] , Newline
KeyStmt               = ActionKey , Newline
ModifierComboStmt     = ModifierKey , { (' ' | '-') , (ModifierKey | ActionKey) } , Newline
InjectModStmt         = 'INJECT_MOD' , Newline
HoldStmt              = 'HOLD' , ( ActionKey | ModifierKey ) , Newline
ReleaseStmt           = 'RELEASE' , ( ActionKey | ModifierKey ) , Newline
RepeatStmt            = 'REPEAT' , IntegerLiteral , Newline
ResetStmt             = 'RESET' , Newline
RestartPayloadStmt    = 'RESTART_PAYLOAD' , Newline
StopPayloadStmt       = 'STOP_PAYLOAD' , Newline
VarDeclStmt           = 'VAR' , '$' , Identifier , [ '=' , Expression ] , Newline
AssignStmt            = '$' , Identifier , '=' , Expression , Newline
IfStmt                = 'IF' , [ '(' ] , Expression , [ ')' ] , 'THEN' , Newline
                        { Statement }
                        { 'ELSE' , 'IF' , [ '(' ] , Expression , [ ')' ] , 'THEN' , Newline , { Statement } }
                        [ 'ELSE' , Newline , { Statement } ]
                        'END_IF' , Newline
WhileStmt             = 'WHILE' , [ '(' ] , Expression , [ ')' ] , Newline
                        { Statement }
                        'END_WHILE' , Newline
LoopControlStmt       = ('BREAK' | 'CONTINUE') , Newline
FunctionDef           = 'FUNCTION' , Identifier , '(' , ')' , Newline
                        { Statement }
                        'END_FUNCTION' , Newline
CallStmt              = Identifier , '(' , ')' , Newline
ReturnStmt            = 'RETURN' , [ Expression ] , Newline
RandomStmt            = 'RANDOM_CHAR' | 'RANDOM_LOWERCASE_LETTER' | 'RANDOM_UPPERCASE_LETTER'
                      | 'RANDOM_LETTER' | 'RANDOM_NUMBER' | 'RANDOM_SPECIAL' , Newline
LedStmt               = ('LED_OFF' | 'LED_R' | 'LED_G' | 'LED_B') , Newline
ButtonDefStmt          = 'BUTTON_DEF' , Newline , { Statement } , 'END_BUTTON' , Newline
WaitForButtonStmt      = 'WAIT_FOR_BUTTON_PRESS' , Newline
ButtonControlStmt      = ('DISABLE_BUTTON' | 'ENABLE_BUTTON') , Newline
AttackModeStmt         = 'ATTACKMODE' , AttackModeParam , { AttackModeParam } , Newline
AttackModeParam        = 'HID' | 'STORAGE' | 'OFF'
                       | 'VID_' HexValue | 'PID_' HexValue
                       | 'MAN_' AlphaNum | 'PROD_' AlphaNum | 'SERIAL_' Digits
                       | 'VID_RANDOM' | 'PID_RANDOM' | 'MAN_RANDOM' | 'PROD_RANDOM' | 'SERIAL_RANDOM'
WaitForLockKeyStmt     = 'WAIT_FOR_' ('CAPS'|'NUM'|'SCROLL') '_' ('ON'|'OFF'|'CHANGE') , Newline
SaveRestoreLockStateStmt = ('SAVE_HOST_KEYBOARD_LOCK_STATE' | 'RESTORE_HOST_KEYBOARD_LOCK_STATE') , Newline
HideRestorePayloadStmt = ('HIDE_PAYLOAD' | 'RESTORE_PAYLOAD') , Newline
DuckyLangStmt          = 'DUCKY_LANG' , LanguageCode , Newline
ExtensionDef           = 'EXTENSION' , Identifier , Newline , { Statement } , 'END_EXTENSION' , Newline
SaveAttackModeStmt     = 'SAVE_ATTACKMODE' , Newline
RestoreAttackModeStmt  = 'RESTORE_ATTACKMODE' , Newline
ExpressionStmt         = CallStmt

(* Expressions — precedence from highest to lowest *)
Expression           = AssignmentExpr
AssignmentExpr       = LogicalOrExpr [ '=' AssignmentExpr ]
LogicalOrExpr        = LogicalAndExpr { '||' LogicalAndExpr }
LogicalAndExpr       = BitwiseOrExpr { '&&' BitwiseOrExpr }
BitwiseOrExpr        = BitwiseAndExpr { '|' BitwiseAndExpr }
BitwiseAndExpr       = EqualityExpr { '&' EqualityExpr }
EqualityExpr         = RelationalExpr { ('==' | '!=') RelationalExpr }
RelationalExpr       = ShiftExpr { ('<' | '<=' | '>' | '>=') ShiftExpr }
ShiftExpr            = AdditiveExpr { ('<<' | '>>') AdditiveExpr }
AdditiveExpr         = MultiplicativeExpr { ('+' | '-') MultiplicativeExpr }
MultiplicativeExpr   = UnaryExpr { ('*' | '/' | '%' | '^') UnaryExpr }
UnaryExpr            = { ('!' | '-') } PrimaryExpr
PrimaryExpr          = IntegerLiteral | StringLiteral | BooleanLiteral
                     | '$' Identifier | Identifier '(' ')' | '(' Expression ')'

(* Helpers *)
Identifier     = [a-zA-Z_][a-zA-Z0-9_]*
IntegerLiteral = [0-9]+ | '0x' [0-9a-fA-F]+
StringLiteral  = '"' { EscapeSeq | printable - '"' } '"'
BooleanLiteral = 'TRUE' | 'FALSE'
StringContent  = { any - Newline }
RestOfLine     = { any - Newline }
LanguageCode   = [A-Z]{2}
HexValue       = [0-9a-fA-F]{4}
AlphaNum       = [a-zA-Z0-9_]+
Digits         = [0-9]+
ModifierKey    = 'CONTROL' | 'CTRL' | 'SHIFT' | 'ALT' | 'GUI' | 'WINDOWS' | 'COMMAND' | 'OPTION'
ActionKey      = 'ENTER' | 'RETURN' | 'SPACE' | 'TAB' | 'BACKSPACE' | 'DELETE' | 'DEL'
               | 'INSERT' | 'HOME' | 'END' | 'PAGEUP' | 'PAGEDOWN'
               | 'UP' | 'UPARROW' | 'DOWN' | 'DOWNARROW' | 'LEFT' | 'LEFTARROW' | 'RIGHT' | 'RIGHTARROW'
               | 'ESCAPE' | 'ESC' | 'PRINTSCREEN' | 'SCROLLLOCK' | 'PAUSE' | 'BREAK'
               | 'MENU' | 'APP' | 'CAPSLOCK' | 'NUMLOCK' | 'POWER'
               | 'F1'..'F12'
               | 'KP_SLASH' | 'KP_ASTERISK' | 'KP_MINUS' | 'KP_PLUS' | 'KP_ENTER'
               | 'KP_0'..'KP_9' | 'KP_DOT' | 'KP_EQUAL' | 'KP_COMMA' | 'KP_00' | 'KP_000'
               | '102ND' | 'COMPOSE' | 'KPEQUAL' | 'PROPS' | 'UNDO' | 'PASTE'
```

---

## 3. Token Specification

Each token has: **type** (enum category), **value** (lexeme text), **line** (1-based), **column** (1-based).

### 3.1 Token Categories

| Category    | Tokens                                   |
| ----------- | ---------------------------------------- |
| Keywords    | All keywords from §1.3 (case-insensitive, stored uppercase) |
| Modifiers   | CONTROL, CTRL, SHIFT, ALT, GUI, WINDOWS, COMMAND, OPTION |
| Action Keys | All action keys from §1.5                |
| Identifiers | `[a-zA-Z_][a-zA-Z0-9_]*` or `$[a-zA-Z_][a-zA-Z0-9_]*` |
| Integers    | `[0-9]+` or `0x[0-9a-fA-F]+`              |
| Strings     | `"..."` with resolved escape sequences    |
| Operators   | See §1.8                                 |
| Punctuation | `(` `)` `,`                              |
| Special     | NEWLINE, EOF, STRING_BODY, ATTACKMODE_PARAM |

### 3.2 Tokenization Rules

1. Longest match wins (e.g., `<=` is one token, not `<` + `=`).
2. Keywords are recognized only at token boundaries (delimited by whitespace, punctuation, or newline).
3. `STRING`/`STRINGLN`: after the keyword and one whitespace, all remaining characters to newline become a single `STRING_BODY` token with no escape processing.
4. `ATTACKMODE`: each whitespace-delimited parameter after the keyword becomes an `ATTACKMODE_PARAM` token until newline.
5. Comments are detected by the lexer and skipped entirely — they never produce tokens.
6. Escape sequences in quoted strings are resolved during lexing.

### 3.3 Error Detection

- Illegal characters: report line, column, and hex byte value.
- Line exceeds 256 characters: report line, column at overflow point.
- Unterminated quoted string: report line, column of opening quote.

---

## 4. Expression Evaluation

### 4.1 Precedence Table (highest to lowest)

| Level | Operators   | Associativity | Evaluation                 |
| ----- | ----------- | ------------- | -------------------------- |
| 12    | `!` `-` (unary) | Right      | Operand first              |
| 11    | `*` `/` `%` `^` | Left       | Left operand first         |
| 10    | `+` `-`     | Left          | Left operand first         |
| 9     | `<<` `>>`   | Left          | Left operand first         |
| 8     | `<` `<=` `>` `>=` | Left    | Left operand first         |
| 7     | `==` `!=`   | Left          | Left operand first         |
| 6     | `&`         | Left          | Left operand first         |
| 5     | `\|`        | Left          | Left operand first         |
| 4     | `&&`        | Left          | Short-circuit: left → right |
| 3     | `\|\|`      | Left          | Short-circuit: left → right |
| 2     | `=`         | Right         | Right operand first        |

### 4.2 Evaluation Semantics

All arithmetic operates on **unsigned 16-bit integers** (0–65535). Overflow wraps: `65535 + 1 = 0`.

| Operation   | Behavior                                               |
| ----------- | ------------------------------------------------------ |
| `+` `-` `*` | Integer arithmetic with wrapping. `+` on two strings → concatenation. |
| `/`         | Integer division, truncates toward zero.               |
| `%`         | Remainder, sign of dividend.                           |
| `^`         | Exponentiation: base raised to exponent. Large results wrap modulo 65536. |
| `<<` `>>`    | Bitwise shift. Shift amount masked to 0–15.            |
| `<` `<=` `>` `>=` | Integer comparison: result is 1 (true) or 0 (false). Cross-type → runtime error. |
| `==` `!=`    | Value equality: both ints or both strings. Cross-type → returns 0 (no implicit cast). |
| `&&` `\|\|`  | Short-circuit. 0 = false, non-zero = true. Returns 1 or 0. |
| `!`          | Logical NOT: `!0` → 1, `!nonzero` → 0.                 |
| `-` (unary)  | Two's complement negation: `-1` → 65535.               |
| `=`          | Assignment: LHS must be variable reference (`$name`). Returns assigned value. |
| `/` `%` by 0 | Runtime error: halts execution with diagnostic.         |

Truthiness: `0` and `""` are falsy. All other values are truthy.

---

## 5. Runtime Semantics

### 5.1 Variables and Scope

- **[Official]** Variables are unsigned 16-bit integers (0–65535). Boolean TRUE = 1, FALSE = 0.
- **[Official]** Variables must be declared with `VAR` before use. Undeclared variable read → runtime error.
- **[Official]** Uninitialized `VAR $x` defaults to 0.
- **[Official]** Assignment to a `$name` without prior `VAR` declaration → runtime error.
- **[Project]** Two scope levels: **global** and **function-local**. Variables declared at the top level are global. Variables declared inside a function with `VAR` are local to that function.
- **[Project]** Local variables shadow globals of the same name.
- **[Known Deviation]** Hak5 specifies all variables as global. We add function-local scoping as an extension while staying compatible with global-only payloads.

### 5.2 Functions

- **[Official]** Functions are defined with `FUNCTION name()` ... `END_FUNCTION`. They take zero arguments (use global variables for data passing).
- **[Official]** Functions are called with `name()` as a statement or inside an expression.
- **[Official]** `RETURN` exits a function. `RETURN <expr>` returns a value. No explicit RETURN returns 0.
- **[Official]** Functions can call other functions, including themselves (recursion).
- **[Implementation Decision]** All function definitions are registered before any statement executes (forward references work).

### 5.3 Keyboard Semantics

- **[Official]** `STRING <text>` types text character by character. Auto-holds SHIFT for uppercase. Auto-presses SPACE for spaces. Trailing spaces are omitted.
- **[Official]** `STRINGLN <text>` does the same then presses ENTER.
- **[Official]** Modifier combos (e.g., `CTRL SHIFT ESC`): press all modifiers in order, press action key, then release all in reverse order.
- **[Official]** `HOLD <key>`: press and hold. `RELEASE <key>`: release a held key.
- **[Official]** `INJECT_MOD` before a modifier signals a standalone modifier press+release.
- **[Official]** `HOLD <modifier>` requires `INJECT_MOD` on the preceding line.
- **[Official]** `RELEASE <modifier>` — no `INJECT_MOD` required (the modifier context was already established by the preceding `HOLD` statement). See official example below.
- **[Official]** `RESET`: release all keys immediately.
- **[Official]** Official Hak5 holding-keys example (from docs.hak5.org):
  ```
  INJECT_MOD
  HOLD WINDOWS
  DELAY 4000
  RELEASE WINDOWS
  ```
  `INJECT_MOD` is required before `HOLD <modifier>` but NOT before `RELEASE <modifier>`.
- **[Critical]** The implementation must ensure all keys are released on any error path. Modifier keys must never be left pressed.

### 5.4 Delay Semantics

- **[Official]** `DELAY <expr>`: blocking pause for `<expr>` milliseconds. Minimum 20ms (values below 20 are clamped).
- **[Official]** `DEFAULTDELAY <expr>`: sets an inter-statement delay applied after every subsequent statement except DELAY statements and control flow keywords.
- **[Official]** `DEFAULTCHARDELAY <expr>`: sets delay between individual characters in STRING/STRINGLN.
- Delays are cumulative: if DEFAULTDELAY=200 and a STRING takes 500ms, the next statement runs 700ms after STRING began.

### 5.5 Random Semantics

- `RANDOM_CHAR`: random printable ASCII (0x21–0x7E).
- `RANDOM_LOWERCASE_LETTER`: random a–z.
- `RANDOM_UPPERCASE_LETTER`: random A–Z.
- `RANDOM_LETTER`: random letter (any case).
- `RANDOM_NUMBER`: random digit 0–9.
- `RANDOM_SPECIAL`: random character from `!@#$%^&*()`.
- Each command types the character immediately via the keyboard backend.
- Internal variables `$_RANDOM_MIN`, `$_RANDOM_MAX`, `$_RANDOM_INT` control random integer generation (min/max inclusive).

### 5.6 Control Flow Semantics

- `IF (<expr>) THEN` ... `ELSE IF (<expr>) THEN` ... `ELSE` ... `END_IF`: execute the first branch whose condition is truthy. `THEN` is required. Parentheses around the condition are optional.
- `WHILE (<expr>)` ... `END_WHILE`: evaluate condition before each iteration. Zero/falsy → exit.
- **[Extension]** `BREAK`: exit the innermost WHILE. `CONTINUE`: skip to next WHILE iteration. Both outside a WHILE → parse error.
- `REPEAT <n>`: repeat the immediately preceding statement n additional times (total = n+1). REPEAT must immediately follow the statement it repeats.

### 5.7 REPEAT Semantics

`REPEAT <n>` repeats the immediately preceding statement n additional times. Total executions = 1 (original) + n (repeats). REPEAT only repeats a single preceding statement, not a sequence. REPEAT must immediately follow the statement it targets. If REPEAT follows a block-end keyword (END_IF, END_WHILE), it is a **parse error**.

---

## 6. Platform Interface

### 6.1 PlatformInterface

The `PlatformInterface` is the **sole bridge** between the interpreter and hardware. The interpreter receives a `PlatformInterface` instance via dependency injection and performs all I/O through it. The interpreter must never import CircuitPython or any hardware-specific module.

```
PlatformInterface
├── keyboard: KeyboardBackend
├── filesystem: FilesystemBackend
├── timing: TimingBackend
├── random: RandomBackend
├── gpio: GPIOBackend
├── led: LEDBackend
├── hid: HIDBackend
└── recovery: RecoveryBackend
```

### 6.2 Interface Definitions

**KeyboardBackend**
```
press(key: str)              — Press and hold a key
release(key: str)            — Release a specific key
release_all()                — Release all pressed keys immediately
write(text: str)             — Type a string using current keyboard layout
press_modifier_combo(modifiers: [str], key: str|None) — Press combo then release all
set_layout(code: str)        — Switch keyboard layout
get_layout() → str           — Return current layout code
reset()                      — Release all keys, clear HID buffer
```
Error behavior: unknown key → error. Unmappable character in write → skip silently.

**FilesystemBackend**
```
read_file(path: str) → str         — Return file contents
file_exists(path: str) → bool       — Check file existence
list_directory(path: str) → [str]   — List directory entries
hide_file(path: str)                — Hide file from host mass storage
restore_file(path: str)             — Restore hidden file
```
Error behavior: not found → error. hide/restore on unsupported platform → no-op.

**TimingBackend**
```
sleep_ms(ms: int)                — Block for at least ms milliseconds
current_time_ms() → int          — Monotonic time since boot in milliseconds
```
Error behavior: never fails.

**RandomBackend**
```
seed(value: int)                 — Seed the PRNG
random_int(min: int, max: int) → int   — Random integer in [min, max]
random_char(category: str) → str       — Random character from category
random_uint16() → int                  — Random value in 0–65535
```
Categories: `"LOWERCASE"`, `"UPPERCASE"`, `"LETTER"`, `"NUMBER"`, `"SPECIAL"`, `"CHAR"`.
Error behavior: min > max → error. Unknown category → error.

**GPIOBackend**
```
read_pin(pin_id: str) → bool      — Read GPIO pin state
read_button() → bool              — Read hardware button state (true = pressed)
```

**LEDBackend**
```
set(state: str)                  — Set LED: "OFF", "R", "G", "B"
```

**HIDBackend**
```
set_attack_mode(modes: [str], vid, pid, man, prod, serial: str|None, randomize: set)
save_attack_mode()
restore_attack_mode()
```

**RecoveryBackend**
```
should_skip_payload() → bool     — True if boot button held (recovery mode)
enter_recovery_mode()            — Expose CIRCUITPY, skip payload
```

### 6.3 Platform Implementations

Two implementations are required:

1. **Desktop (Mock)**: Records all events to an in-memory list for test assertion. Uses standard library for filesystem, timing, and random. Keyboard events are logged but not sent to hardware.

2. **Pico (CircuitPython)**: Uses `adafruit_hid.keyboard.Keyboard` for HID, `storage` module for filesystem, `time.monotonic` for timing, `board` and `digitalio` for GPIO and LED, `os.urandom` or RP2350 TRNG for random.

---

## 7. Architecture Rules

### 7.1 Import Direction

```
Allowed:
  Lexer → Token types
  Parser → AST nodes, Token types
  Interpreter → AST nodes, PlatformInterface
  Platform → Hardware libraries

Forbidden:
  Lexer → Parser, Interpreter, Platform, AST, Hardware
  Parser → Lexer, Interpreter, Platform, Hardware
  AST → Parser, Interpreter, Lexer, Platform
  Interpreter → Lexer, Parser, Platform (only PlatformInterface)
  Platform → Language modules (Lexer, Parser, AST, Interpreter)
```

### 7.2 Platform Isolation

- No code above the Platform layer may import CircuitPython (`circuitpython`, `adafruit_hid`, `usb_hid`, `storage`, `microcontroller`, `board`, etc.).
- The Platform layer must not import any language module.
- Desktop testing uses a mock PlatformInterface that logs events.
- The `src/ducky/` directory must never import CircuitPython modules. Only the platform layer (`src/platform/`) may depend on CircuitPython or hardware libraries.

### 7.3 Separation of Concerns

| Module    | Responsibilities                                   |
| --------- | -------------------------------------------------- |
| Lexer     | Character stream → token stream. Error detection.  |
| Parser    | Token stream → AST. Syntax errors.                 |
| AST       | Data container only. No logic.                     |
| Interpreter | Walk AST, call PlatformInterface. Runtime errors. |
| Platform  | Hardware abstraction. No language logic.           |

### 7.4 Module Independence

Every module must be testable in isolation on desktop Python without CircuitPython. All module boundaries operate through well-defined interfaces.

---

## 8. Compatibility Strategy

### 8.1 Target Platforms

| Platform   | Language     | When                |
| ---------- | ------------ | ------------------- |
| Desktop    | Python ≥3.10 | Development, tests  |
| Pico 2     | CircuitPython 10.x | Production     |
| Pico 2 W   | CircuitPython 10.x | Production     |
| Future C++ | Pico SDK     | Post-interpreter    |

### 8.2 What Changes Per Platform

Only the **Platform layer** changes between targets. All language modules (Lexer, Parser, AST, Interpreter) are platform-independent and run unmodified on CPython and CircuitPython. The PlatformInterface protocol ensures a clear replacement boundary.

### 8.3 Portability Rules

1. Language modules use only: `re`, `enum`, `dataclasses`, `typing`, `abc` — available in both CPython and CircuitPython.
2. Platform implementations live in separate source trees: `platform/desktop/`, `platform/pico/`, `platform/native/`.
3. The interpreter receives its PlatformInterface via dependency injection — no singleton or global.
4. All interfaces designed as abstract protocols without Python-specific constructs.

---

## 9. Development Workflow

For every feature, in order:

1. **Design** — Document syntax, semantics, and test scenarios.
2. **Review** — Peer review the design against this specification.
3. **Implement** — Build the feature per the architecture.
4. **Unit Test** — Test the module in isolation using mocks.
5. **Integration Test** — Test end-to-end with a payload on the desktop mock platform.
6. **Regression Test** — Run the full test suite; nothing may break.
7. **Document** — Update spec and examples.
8. **Refactor** — Clean up for clarity and portability.
9. **Verify** — Lint (ruff), type-check (mypy), test (pytest), check no CircuitPython leak.
10. **Commit** — Only when all previous steps pass.

### Build Order

```
Phase 0: Repository scaffold (directory structure, toolchain, CI)
Phase 1: Token types + Lexer
Phase 2: AST node definitions
Phase 3: Parser
Phase 4: Desktop Platform mock
Phase 5: Interpreter (variables, expressions, statements)
Phase 6: Interpreter (control flow: IF, WHILE)
Phase 7: Interpreter (functions, RETURN, BREAK, CONTINUE)
Phase 8: Interpreter (keyboard, delays, random, repeat)
Phase 9: Pico Platform (HID, FS, timing, GPIO, LED, recovery)
Phase 10: Advanced (ATTACKMODE, layouts, extensions)
Phase 11: Cross-platform testing
Phase 12: Documentation and examples
```

---

## 10. Decision Hierarchy

When multiple implementations are possible, evaluate in this order:

1. **Correctness** — Behavior matches this specification.
2. **Maintainability** — Clear, understandable, well-structured.
3. **Portability** — Can be translated to C/C++ without redesign.
4. **Testability** — Can be tested in isolation on desktop Python.
5. **Performance** — Fast enough for the target hardware.

Never sacrifice a higher-priority criterion for a lower one. Never optimize prematurely.

---

## 11. Ambiguity Policy

If this specification is ambiguous:

1. Do not guess. Stop and document the ambiguity.
2. Present the conflict with two or more possible designs and tradeoffs.
3. Wait for written approval before proceeding.
4. Record the resolution in this document.

Authority order for resolving ambiguity:
1. Official Hak5 documentation
2. This specification (after resolution is recorded)
3. Hak5 USB Rubber Ducky hardware behavior
4. Third-party reference implementations
5. Engineer judgment with documented rationale

---

## Appendix A: ATTACKMODE Parameter Reference

| Parameter | Format     | Example     | Description              |
| --------- | ---------- | ----------- | ------------------------ |
| `HID`     | literal    | `HID`       | Keyboard HID device      |
| `STORAGE` | literal    | `STORAGE`   | Mass storage device      |
| `OFF`     | literal    | `OFF`       | Disconnect USB           |
| `VID_`    | `VID_xxxx`  | `VID_05AC`  | Vendor ID (4 hex digits) |
| `PID_`    | `PID_xxxx`  | `PID_021E`  | Product ID (4 hex digits)|
| `MAN_`    | `MAN_text`  | `MAN_HAK5`  | Manufacturer (32 chars max, underscores → spaces) |
| `PROD_`   | `PROD_text` | `PROD_DUCKY` | Product name (32 chars max) |
| `SERIAL_` | `SERIAL_d`  | `SERIAL_1337` | Serial number (12 digits max) |
| `*_RANDOM`| suffixed    | `VID_RANDOM`| Randomize that field     |

---

## Appendix B: Keyboard Layout Format

Layouts are JSON files mapping characters to HID scancode triplets:

```json
{
  "a": "00,00,04",
  "A": "02,00,04",
  "1": "00,00,1E",
  "!": "02,00,1E"
}
```

Each entry: `"char": "modifier_byte,reserved_byte,keycode_byte"` (hex bytes).
Modifier byte bitmap: 0x01=CTRL, 0x02=SHIFT, 0x04=ALT, 0x08=GUI.

Minimum layout set: `US`, `GB`, `DE`, `FR`, `ES`, `IT`, `JP`, `DK`, `NO`, `SE`, `FI`, `PT`, `BR`, `RU`, `PL`, `CZ`
```
