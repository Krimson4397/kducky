"""Abstract syntax tree node definitions for DuckyScript 3.

Every grammar production from the specification (§2) has a corresponding
frozen dataclass.  These are pure data containers — no methods, no logic.

Imports are limited to the standard library (``enum``, ``dataclasses``,
``__future__``) and ``ducky.tokens``.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto, unique

from ducky.tokens import ActionKey, ModifierKey, Operator

# ── Base classes ────────────────────────────────────────────────────


class Stmt:
    """Base class for all statement AST nodes."""


class Expr:
    """Base class for all expression AST nodes."""


# ── Script (top-level program) ──────────────────────────────────────


@dataclass(frozen=True)
class Script:
    """Top-level program: an ordered sequence of statements."""

    statements: tuple[Stmt, ...]


# ── Control flow ────────────────────────────────────────────────────


@dataclass(frozen=True)
class IfStmt(Stmt):
    """Conditional branch with optional else/else-if chain."""

    condition: Expr
    body: tuple[Stmt, ...]
    else_body: tuple[Stmt, ...] | None = None


@dataclass(frozen=True)
class WhileStmt(Stmt):
    """Pre-check loop: repeat body while condition is truthy."""

    condition: Expr
    body: tuple[Stmt, ...]


@dataclass(frozen=True)
class RepeatStmt(Stmt):
    """Repeat the immediately preceding statement *count* additional times."""

    count: Expr


# ── Variables ───────────────────────────────────────────────────────


@dataclass(frozen=True)
class VarDef(Stmt):
    """Variable declaration with optional initializer."""

    name: str
    initializer: Expr


@dataclass(frozen=True)
class AssignStmt(Stmt):
    """Assignment to an existing variable."""

    name: str
    value: Expr


# ── Keyboard ────────────────────────────────────────────────────────


@dataclass(frozen=True)
class KeyStmt(Stmt):
    """Press a single action key (no modifiers)."""

    key: ActionKey


@dataclass(frozen=True)
class StringStmt(Stmt):
    """Type a literal string character by character."""

    text: str


@dataclass(frozen=True)
class StringLnStmt(Stmt):
    """Type a literal string followed by ENTER."""

    text: str


@dataclass(frozen=True)
class InjectModStmt(Stmt):
    """Inject a standalone modifier press+release."""


@dataclass(frozen=True)
class HoldStmt(Stmt):
    """Press and hold a key until released."""

    key: ActionKey


@dataclass(frozen=True)
class ReleaseStmt(Stmt):
    """Release a previously held key."""

    key: ActionKey


# ── Delays ──────────────────────────────────────────────────────────


@dataclass(frozen=True)
class DelayStmt(Stmt):
    """Blocking pause for a fixed number of milliseconds."""

    milliseconds: int


@dataclass(frozen=True)
class DefaultDelayStmt(Stmt):
    """Set the inter-statement delay (applied after every subsequent statement)."""

    delay: Expr


@dataclass(frozen=True)
class DefaultCharDelayStmt(Stmt):
    """Set the delay between individual characters in STRING/STRINGLN."""

    delay: Expr


# ── Attack mode ─────────────────────────────────────────────────────


@dataclass(frozen=True)
class AttackModeStmt(Stmt):
    """Configure USB device mode and identifiers."""

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
class RandomType(Enum):
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

    random_type: RandomType


# ── LED ─────────────────────────────────────────────────────────────


@unique
class LedState(Enum):
    """Available LED states."""

    OFF = auto()
    R = auto()
    G = auto()
    B = auto()


@dataclass(frozen=True)
class LedStmt(Stmt):
    """Set the device LED to a specific state."""

    state: LedState


# ── Button ──────────────────────────────────────────────────────────


@dataclass(frozen=True)
class ButtonDefStmt(Stmt):
    """Define a button handler with a name and body statements."""

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
class LockKeyType(Enum):
    """Host lock key types that can be waited on."""

    CAPS = auto()
    NUM = auto()
    SCROLL = auto()


@unique
class LockKeyState(Enum):
    """Expected state transitions for lock key wait commands."""

    ON = auto()
    OFF = auto()
    CHANGE = auto()


@dataclass(frozen=True)
class WaitForKeyStmt(Stmt):
    """Block until a host lock key reaches a target state."""

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


# ── Combo ───────────────────────────────────────────────────────────


@dataclass(frozen=True)
class ComboStmt(Stmt):
    """Modifier + action key combo: press modifiers then key then release all."""

    modifiers: tuple[ModifierKey, ...]
    key: ActionKey


# ── Function & Extension ────────────────────────────────────────────


@dataclass(frozen=True)
class FunctionDef(Stmt):
    """Function definition with zero parameters."""

    name: str
    params: tuple[str, ...]
    body: tuple[Stmt, ...]


@dataclass(frozen=True)
class ExtensionStmt(Stmt):
    """Extension block (parsed but semantics are extension-specific)."""

    name: str
    body: tuple[Stmt, ...]


@dataclass(frozen=True)
class DefineStmt(Stmt):
    """Preprocessor constant definition (``DEFINE #NAME value``)."""

    name: str
    value: str


# ── Expressions ─────────────────────────────────────────────────────


@dataclass(frozen=True)
class IntegerExpr(Expr):
    """Integer literal expression."""

    value: int


@dataclass(frozen=True)
class StringExpr(Expr):
    """String literal expression (quoted string in expression context)."""

    value: str


@dataclass(frozen=True)
class IdentifierExpr(Expr):
    """Plain identifier reference (function name, not variable)."""

    name: str


@dataclass(frozen=True)
class DollarIdentifierExpr(Expr):
    """``$name`` variable reference."""

    name: str


@dataclass(frozen=True)
class HashIdentifierExpr(Expr):
    """``#NAME`` constant reference."""

    name: str


@dataclass(frozen=True)
class BinaryOp(Expr):
    """Binary operation: left *operator* right."""

    left: Expr
    operator: Operator
    right: Expr


@dataclass(frozen=True)
class UnaryOp(Expr):
    """Unary operation: *operator* operand."""

    operator: Operator
    operand: Expr


@dataclass(frozen=True)
class GroupExpr(Expr):
    """Parenthesized expression for explicit precedence."""

    expression: Expr
