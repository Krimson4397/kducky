"""Abstract syntax tree node definitions for DuckyScript 3.

Every grammar production from the specification (§2) has a corresponding
frozen dataclass.  These are pure data containers — no methods, no logic.

Imports use the compat shim (``ducky.utils.compat``) for CircuitPython
portability, plus ``ducky.tokens`` for shared types.
"""

from ducky.tokens import ActionKey, ModifierKey, Operator
from ducky.utils.compat import auto, dataclass, enum, unique

# ── Base classes ────────────────────────────────────────────────────


class Stmt:
    """Base class for all statement AST nodes."""


class Expr:
    """Base class for all expression AST nodes."""


# ── Script (top-level program) ──────────────────────────────────────


@dataclass(frozen=True)
class Script:
    """Top-level program: an ordered sequence of statements."""

    __slots__ = ("statements",)

    statements: tuple[Stmt, ...]


# ── Control flow ────────────────────────────────────────────────────


@dataclass(frozen=True)
class IfStmt(Stmt):
    """Conditional branch with optional else/else-if chain."""

    __slots__ = ("condition", "body")
    __defaults__ = {"else_body": None}

    condition: Expr
    body: tuple[Stmt, ...]
    else_body: tuple[Stmt, ...] | None = None


@dataclass(frozen=True)
class WhileStmt(Stmt):
    """Pre-check loop: repeat body while condition is truthy."""

    __slots__ = ("condition", "body")

    condition: Expr
    body: tuple[Stmt, ...]


@dataclass(frozen=True)
class RepeatStmt(Stmt):
    """Repeat the immediately preceding statement *count* additional times."""

    __slots__ = ("count",)

    count: Expr


@dataclass(frozen=True)
class BreakStmt(Stmt):
    """Exit the innermost WHILE loop."""


@dataclass(frozen=True)
class ContinueStmt(Stmt):
    """Skip to the next iteration of the innermost WHILE loop."""


@dataclass(frozen=True)
class CallStmt(Stmt):
    """Function call as a standalone statement (return value discarded)."""

    __slots__ = ("name",)

    name: str


@dataclass(frozen=True)
class IdentifierStmt(Stmt):
    """Statement consisting of a bare identifier (extension call or error)."""

    __slots__ = ("name",)

    name: str


# ── Variables ───────────────────────────────────────────────────────


@dataclass(frozen=True)
class VarDef(Stmt):
    """Variable declaration with optional initializer."""

    __slots__ = ("name", "initializer")

    name: str
    initializer: Expr


@dataclass(frozen=True)
class AssignStmt(Stmt):
    """Assignment to an existing variable."""

    __slots__ = ("name", "value")

    name: str
    value: Expr


# ── Keyboard ────────────────────────────────────────────────────────


@dataclass(frozen=True)
class KeyStmt(Stmt):
    """Press a single action key (no modifiers)."""

    __slots__ = ("key",)

    key: ActionKey


@dataclass(frozen=True)
class StringStmt(Stmt):
    """Type a literal string character by character."""

    __slots__ = ("text",)

    text: str


@dataclass(frozen=True)
class StringLnStmt(Stmt):
    """Type a literal string followed by ENTER."""

    __slots__ = ("text",)

    text: str


@dataclass(frozen=True)
class InjectModStmt(Stmt):
    """Inject a standalone modifier press+release."""


@dataclass(frozen=True)
class InjectVarStmt(Stmt):
    """Inject a variable's value as keystrokes."""

    __slots__ = ("variable",)

    variable: str


@dataclass(frozen=True)
class HoldStmt(Stmt):
    """Press and hold a key until released."""

    __slots__ = ("key",)

    key: object


@dataclass(frozen=True)
class ReleaseStmt(Stmt):
    """Release a previously held key."""

    __slots__ = ("key",)

    key: object


# ── Delays ──────────────────────────────────────────────────────────


@dataclass(frozen=True)
class DelayStmt(Stmt):
    """Blocking pause for a fixed number of milliseconds."""

    __slots__ = ("milliseconds",)

    milliseconds: Expr


@dataclass(frozen=True)
class DefaultDelayStmt(Stmt):
    """Set the inter-statement delay (applied after every subsequent statement)."""

    __slots__ = ("delay",)

    delay: Expr


@dataclass(frozen=True)
class DefaultCharDelayStmt(Stmt):
    """Set the delay between individual characters in STRING/STRINGLN."""

    __slots__ = ("delay",)

    delay: Expr


# ── Attack mode ─────────────────────────────────────────────────────


@dataclass(frozen=True)
class AttackModeStmt(Stmt):
    """Configure USB device mode and identifiers."""

    __slots__ = ("params",)

    params: tuple[str, ...]


@dataclass(frozen=True)
class SaveAttackModeStmt(Stmt):
    """Save the current attack mode configuration for later restore."""


@dataclass(frozen=True)
class RestoreAttackModeStmt(Stmt):
    """Restore a previously saved attack mode configuration."""


# ── Return & payload control ────────────────────────────────────────


@dataclass(frozen=True)
class ReturnStmt(Stmt):
    """Exit a function, optionally returning a value."""

    __defaults__ = {"value": None}

    value: Expr | None = None


@dataclass(frozen=True)
class ResetStmt(Stmt):
    """Release all keys immediately."""


@dataclass(frozen=True)
class RestartPayloadStmt(Stmt):
    """Restart the entire payload from the beginning."""


@dataclass(frozen=True)
class StopPayloadStmt(Stmt):
    """Stop payload execution immediately."""


# ── Random ──────────────────────────────────────────────────────────


@unique
@enum
class RandomType:
    """Categories of random character generation."""

    CHAR = auto()
    LOWERCASE_LETTER = auto()
    UPPERCASE_LETTER = auto()
    LETTER = auto()
    NUMBER = auto()
    SPECIAL = auto()


@dataclass(frozen=True)
class RandomStmt(Stmt):
    """Generate and type a random character from the given category."""

    __slots__ = ("random_type",)

    random_type: RandomType


# ── LED ─────────────────────────────────────────────────────────────


@unique
@enum
class LedState:
    """Available LED states."""

    OFF = auto()
    R = auto()
    G = auto()
    B = auto()


@dataclass(frozen=True)
class LedStmt(Stmt):
    """Set the device LED to a specific state."""

    __slots__ = ("state",)

    state: LedState


# ── Button ──────────────────────────────────────────────────────────


@dataclass(frozen=True)
class ButtonDefStmt(Stmt):
    """Define a button handler with a name and body statements."""

    __slots__ = ("name", "body")

    name: str
    body: tuple[Stmt, ...]


@dataclass(frozen=True)
class WaitForButtonPressStmt(Stmt):
    """Block until the hardware button is pressed."""


@dataclass(frozen=True)
class DisableButtonStmt(Stmt):
    """Disable the hardware button handler."""


@dataclass(frozen=True)
class EnableButtonStmt(Stmt):
    """Enable the hardware button handler."""


# ── Lock key wait ───────────────────────────────────────────────────


@unique
@enum
class LockKeyType:
    """Host lock key types that can be waited on."""

    CAPS = auto()
    NUM = auto()
    SCROLL = auto()


@unique
@enum
class LockKeyState:
    """Expected state transitions for lock key wait commands."""

    ON = auto()
    OFF = auto()
    CHANGE = auto()


@dataclass(frozen=True)
class WaitForKeyStmt(Stmt):
    """Block until a host lock key reaches a target state."""

    __slots__ = ("lock_key", "state")

    lock_key: LockKeyType
    state: LockKeyState


@dataclass(frozen=True)
class SaveHostLockStateStmt(Stmt):
    """Save current host lock key state for later restore."""


@dataclass(frozen=True)
class RestoreHostLockStateStmt(Stmt):
    """Restore previously saved host lock key state."""


# ── File ────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class HidePayloadStmt(Stmt):
    """Hide the payload file from host mass storage."""


@dataclass(frozen=True)
class RestorePayloadStmt(Stmt):
    """Restore a previously hidden payload file to visibility."""


@dataclass(frozen=True)
class DuckyLangStmt(Stmt):
    """Set the keyboard layout language."""

    __slots__ = ("language",)

    language: str


@dataclass(frozen=True)
class RebootStmt(Stmt):
    """REBOOT — restart the target computer."""


@dataclass(frozen=True)
class ReplayStmt(Stmt):
    """REPLAY — restart the current payload from the beginning."""


@dataclass(frozen=True)
class JitterStmt(Stmt):
    """JITTER ON|OFF|DELAY min max — random keystroke delays."""

    __slots__ = ("mode",)
    __defaults__ = {"min_delay": 0, "max_delay": 0}

    mode: str  # "on", "off", "delay"
    min_delay: int = 0
    max_delay: int = 0


# ── Mouse ──────────────────────────────────────────────────────────


@unique
@enum
class MouseAction:
    """Mouse operation types."""
    MOVE = auto()
    MOVE_TO = auto()
    CLICK = auto()
    DOWN = auto()
    UP = auto()
    SCROLL = auto()


@unique
@enum
class MouseButton:
    """Mouse button identifiers."""
    LEFT = auto()
    RIGHT = auto()
    MIDDLE = auto()


@dataclass(frozen=True)
class MouseStmt(Stmt):
    """Mouse operation (move, click, scroll, etc.)."""
    __slots__ = ("action",)
    __defaults__ = {"button": None, "x": None, "y": None, "scroll_amount": None}

    action: MouseAction
    button: MouseButton | None = None
    x: int | None = None
    y: int | None = None
    scroll_amount: int | None = None


# ── Combo ───────────────────────────────────────────────────────────


@dataclass(frozen=True)
class ComboStmt(Stmt):
    """Modifier + action key combo: press modifiers then key then release all."""

    __slots__ = ("modifiers",)
    __defaults__ = {"key": None}

    modifiers: tuple[ModifierKey, ...]
    key: str | ActionKey | None = None


# ── Function & Extension ────────────────────────────────────────────


@dataclass(frozen=True)
class FunctionDef(Stmt):
    """Function definition with zero parameters."""

    __slots__ = ("name", "params", "body")

    name: str
    params: tuple[str, ...]
    body: tuple[Stmt, ...]


@dataclass(frozen=True)
class ExtensionStmt(Stmt):
    """Extension block (parsed but semantics are extension-specific)."""

    __slots__ = ("name", "body")

    name: str
    body: tuple[Stmt, ...]


# ── Expressions ─────────────────────────────────────────────────────


@dataclass(frozen=True)
class IntegerExpr(Expr):
    """Integer literal expression."""

    __slots__ = ("value",)

    value: int


@dataclass(frozen=True)
class StringExpr(Expr):
    """String literal expression (quoted string in expression context)."""

    __slots__ = ("value",)

    value: str


@dataclass(frozen=True)
class IdentifierExpr(Expr):
    """Plain identifier reference (function name, not variable)."""

    __slots__ = ("name",)

    name: str


@dataclass(frozen=True)
class CallExpr(Expr):
    """Function call expression (returns a value)."""

    __slots__ = ("name",)

    name: str


@dataclass(frozen=True)
class DollarIdentifierExpr(Expr):
    """``$name`` variable reference."""

    __slots__ = ("name",)

    name: str


@dataclass(frozen=True)
class HashIdentifierExpr(Expr):
    """``#NAME`` constant reference."""

    __slots__ = ("name",)

    name: str


@dataclass(frozen=True)
class BinaryOp(Expr):
    """Binary operation: left *operator* right."""

    __slots__ = ("left", "operator", "right")

    left: Expr
    operator: Operator
    right: Expr


@dataclass(frozen=True)
class UnaryOp(Expr):
    """Unary operation: *operator* operand."""

    __slots__ = ("operator", "operand")

    operator: Operator
    operand: Expr


@dataclass(frozen=True)
class GroupExpr(Expr):
    """Parenthesized expression for explicit precedence."""

    __slots__ = ("expression",)

    expression: Expr
