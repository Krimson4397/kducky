"""Token definitions for the DuckyScript 3 lexer and parser.

This module defines the shared vocabulary between the lexer and parser:
token types, the Token data class, and semantic enums for operators,
modifier keys, and action keys.

Pure data — no logic. Imports only from the standard library.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto, unique


class TokenType(Enum):
    """Every token category the lexer can produce.

    Values are auto-generated unique integers.  The enum member names
    follow DuckyScript conventions (uppercase, underscores for compound
    keywords).
    """

    # ── Control flow ──────────────────────────────────────────────
    IF = auto()
    THEN = auto()
    ELSE = auto()
    END_IF = auto()
    WHILE = auto()
    END_WHILE = auto()

    # ── Function ──────────────────────────────────────────────────
    FUNCTION = auto()
    END_FUNCTION = auto()
    RETURN = auto()

    # ── Variable ──────────────────────────────────────────────────
    VAR = auto()

    # ── Preprocessor ──────────────────────────────────────────────
    DEFINE = auto()

    # ── Comments ─────────────────────────────────────────────────
    REM = auto()
    REM_BLOCK = auto()
    END_REM = auto()

    # ── Payload control ───────────────────────────────────────────
    REPEAT = auto()
    RESET = auto()
    RESTART_PAYLOAD = auto()
    STOP_PAYLOAD = auto()

    # ── Delay ─────────────────────────────────────────────────────
    DELAY = auto()
    DEFAULTDELAY = auto()
    DEFAULT_DELAY = auto()
    DEFAULTCHARDELAY = auto()
    DEFAULT_CHAR_DELAY = auto()
    STRINGDELAY = auto()

    # ── Keyboard output ───────────────────────────────────────────
    STRING = auto()
    STRINGLN = auto()
    INJECT_MOD = auto()
    HOLD = auto()
    RELEASE = auto()

    # ── Attack mode ───────────────────────────────────────────────
    ATTACKMODE = auto()
    SAVE_ATTACKMODE = auto()
    RESTORE_ATTACKMODE = auto()

    # ── LED ───────────────────────────────────────────────────────
    LED_OFF = auto()
    LED_R = auto()
    LED_G = auto()
    LED_B = auto()

    # ── Button ────────────────────────────────────────────────────
    BUTTON_DEF = auto()
    END_BUTTON = auto()
    DISABLE_BUTTON = auto()
    ENABLE_BUTTON = auto()
    WAIT_FOR_BUTTON_PRESS = auto()

    # ── Lock key wait ─────────────────────────────────────────────
    WAIT_FOR_CAPS_ON = auto()
    WAIT_FOR_CAPS_OFF = auto()
    WAIT_FOR_CAPS_CHANGE = auto()
    WAIT_FOR_NUM_ON = auto()
    WAIT_FOR_NUM_OFF = auto()
    WAIT_FOR_NUM_CHANGE = auto()
    WAIT_FOR_SCROLL_ON = auto()
    WAIT_FOR_SCROLL_OFF = auto()
    WAIT_FOR_SCROLL_CHANGE = auto()
    SAVE_HOST_KEYBOARD_LOCK_STATE = auto()
    RESTORE_HOST_KEYBOARD_LOCK_STATE = auto()

    # ── Random ────────────────────────────────────────────────────
    RANDOM_CHAR = auto()
    RANDOM_LOWERCASE_LETTER = auto()
    RANDOM_UPPERCASE_LETTER = auto()
    RANDOM_LETTER = auto()
    RANDOM_NUMBER = auto()
    RANDOM_SPECIAL = auto()

    # ── File ──────────────────────────────────────────────────────
    HIDE_PAYLOAD = auto()
    RESTORE_PAYLOAD = auto()

    # ── Constants ─────────────────────────────────────────────────
    TRUE = auto()
    FALSE = auto()

    # ── Extension keywords ────────────────────────────────────────
    BREAK = auto()  # loop control (BREAK keyword)
    CONTINUE = auto()
    EXTENSION = auto()
    END_EXTENSION = auto()
    DUCKY_LANG = auto()

    # ── Operators (token types) ───────────────────────────────────
    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()
    PERCENT = auto()
    CARET = auto()
    BANG = auto()
    AMPERSAND = auto()
    PIPE = auto()
    LT = auto()
    GT = auto()
    LE = auto()
    GE = auto()
    EQ = auto()
    NE = auto()
    LSHIFT = auto()
    RSHIFT = auto()
    AND = auto()
    OR = auto()
    ASSIGN = auto()

    # ── Punctuation ───────────────────────────────────────────────
    LPAREN = auto()
    RPAREN = auto()
    COMMA = auto()

    # ── Literals ──────────────────────────────────────────────────
    INTEGER = auto()
    STRING_LITERAL = auto()

    # ── Identifiers ───────────────────────────────────────────────
    IDENTIFIER = auto()
    DOLLAR_IDENTIFIER = auto()
    HASH_IDENTIFIER = auto()

    # ── Special ───────────────────────────────────────────────────
    NEWLINE = auto()
    EOF = auto()
    STRING_BODY = auto()
    ATTACKMODE_PARAM = auto()

    # ── Modifier keys (TokenType mirrors ModifierKey) ─────────────
    CONTROL = auto()
    CTRL = auto()
    SHIFT = auto()
    ALT = auto()
    GUI = auto()
    WINDOWS = auto()
    COMMAND = auto()
    OPTION = auto()

    # ── Action keys (TokenType mirrors ActionKey) ─────────────────
    ENTER = auto()
    RETURN_KEY = auto()  # disambiguate from function keyword RETURN
    SPACE = auto()
    TAB = auto()
    BACKSPACE = auto()
    DELETE = auto()
    DEL = auto()
    INSERT = auto()
    HOME = auto()
    END_KEY = auto()  # disambiguate from END_IF etc.
    PAGEUP = auto()
    PAGEDOWN = auto()
    UP = auto()
    UPARROW = auto()
    DOWN = auto()
    DOWNARROW = auto()
    LEFT = auto()
    LEFTARROW = auto()
    RIGHT = auto()
    RIGHTARROW = auto()
    ESCAPE = auto()
    ESC = auto()
    PRINTSCREEN = auto()
    SCROLLLOCK = auto()
    PAUSE = auto()
    BREAK_KEY = auto()  # disambiguate from loop keyword BREAK
    MENU = auto()
    APP = auto()
    CAPSLOCK = auto()
    NUMLOCK = auto()
    POWER = auto()
    F1 = auto()
    F2 = auto()
    F3 = auto()
    F4 = auto()
    F5 = auto()
    F6 = auto()
    F7 = auto()
    F8 = auto()
    F9 = auto()
    F10 = auto()
    F11 = auto()
    F12 = auto()
    KP_SLASH = auto()
    KP_ASTERISK = auto()
    KP_MINUS = auto()
    KP_PLUS = auto()
    KP_ENTER = auto()
    KP_0 = auto()
    KP_1 = auto()
    KP_2 = auto()
    KP_3 = auto()
    KP_4 = auto()
    KP_5 = auto()
    KP_6 = auto()
    KP_7 = auto()
    KP_8 = auto()
    KP_9 = auto()
    KP_DOT = auto()
    KP_EQUAL = auto()
    KP_COMMA = auto()
    KP_00 = auto()
    KP_000 = auto()
    KEY_102ND = auto()
    COMPOSE = auto()
    KPEQUAL = auto()
    PROPS = auto()
    UNDO = auto()
    PASTE = auto()


@dataclass(frozen=True)
class Token:
    """A single token produced by the lexer and consumed by the parser.

    Attributes:
        type: The token category.
        value: The lexeme text as it appeared in source (uppercased for
            keywords, as-is for identifiers and literals).
        line: 1-based source line number.
        column: 1-based source column number (start of the lexeme).
    """

    type: TokenType
    value: str
    line: int
    column: int


@unique
class Operator(Enum):
    """DuckyScript 3 operators mapped to their source lexemes."""

    ADD = "+"
    SUBTRACT = "-"
    MULTIPLY = "*"
    DIVIDE = "/"
    MODULO = "%"
    POWER = "^"
    NOT = "!"
    BITWISE_AND = "&"
    BITWISE_OR = "|"
    LESS = "<"
    GREATER = ">"
    LESS_EQUAL = "<="
    GREATER_EQUAL = ">="
    EQUAL = "=="
    NOT_EQUAL = "!="
    SHIFT_LEFT = "<<"
    SHIFT_RIGHT = ">>"
    LOGICAL_AND = "&&"
    LOGICAL_OR = "||"
    ASSIGN = "="


@unique
class ModifierKey(Enum):
    """Modifier key names usable in combo statements."""

    CONTROL = "CONTROL"
    CTRL = "CTRL"
    SHIFT = "SHIFT"
    ALT = "ALT"
    GUI = "GUI"
    WINDOWS = "WINDOWS"
    COMMAND = "COMMAND"
    OPTION = "OPTION"


@unique
class ActionKey(Enum):
    """Every action key the interpreter can press or release."""

    # ── Navigation ────────────────────────────────────────────────
    UP = "UP"
    UPARROW = "UPARROW"
    DOWN = "DOWN"
    DOWNARROW = "DOWNARROW"
    LEFT = "LEFT"
    LEFTARROW = "LEFTARROW"
    RIGHT = "RIGHT"
    RIGHTARROW = "RIGHTARROW"
    PAGEUP = "PAGEUP"
    PAGEDOWN = "PAGEDOWN"
    HOME = "HOME"
    END = "END"
    INSERT = "INSERT"
    DELETE = "DELETE"
    DEL = "DEL"

    # ── Editing ───────────────────────────────────────────────────
    ENTER = "ENTER"
    RETURN = "RETURN"
    SPACE = "SPACE"
    TAB = "TAB"
    BACKSPACE = "BACKSPACE"
    ESCAPE = "ESCAPE"
    ESC = "ESC"
    PRINTSCREEN = "PRINTSCREEN"
    SCROLLLOCK = "SCROLLLOCK"
    PAUSE = "PAUSE"
    BREAK = "BREAK"
    MENU = "MENU"
    APP = "APP"
    CAPSLOCK = "CAPSLOCK"
    NUMLOCK = "NUMLOCK"
    POWER = "POWER"

    # ── Function keys ─────────────────────────────────────────────
    F1 = "F1"
    F2 = "F2"
    F3 = "F3"
    F4 = "F4"
    F5 = "F5"
    F6 = "F6"
    F7 = "F7"
    F8 = "F8"
    F9 = "F9"
    F10 = "F10"
    F11 = "F11"
    F12 = "F12"

    # ── Numpad ────────────────────────────────────────────────────
    KP_SLASH = "KP_SLASH"
    KP_ASTERISK = "KP_ASTERISK"
    KP_MINUS = "KP_MINUS"
    KP_PLUS = "KP_PLUS"
    KP_ENTER = "KP_ENTER"
    KP_0 = "KP_0"
    KP_1 = "KP_1"
    KP_2 = "KP_2"
    KP_3 = "KP_3"
    KP_4 = "KP_4"
    KP_5 = "KP_5"
    KP_6 = "KP_6"
    KP_7 = "KP_7"
    KP_8 = "KP_8"
    KP_9 = "KP_9"
    KP_DOT = "KP_DOT"
    KP_EQUAL = "KP_EQUAL"
    KP_COMMA = "KP_COMMA"
    KP_00 = "KP_00"
    KP_000 = "KP_000"

    # ── Extended ──────────────────────────────────────────────────
    KEY_102ND = "102ND"
    COMPOSE = "COMPOSE"
    KPEQUAL = "KPEQUAL"
    PROPS = "PROPS"
    UNDO = "UNDO"
    PASTE = "PASTE"
