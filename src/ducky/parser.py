"""Recursive-descent parser for DuckyScript 3.

Converts a token stream (from the Lexer) into an AST (from ducky.ast).
Reports the first syntax error with a diagnostic — no error recovery
beyond that point.
"""

from __future__ import annotations

from ducky.ast import (
    AssignStmt,
    AttackModeStmt,
    BinaryOp,
    BreakStmt,
    ButtonDefStmt,
    CallExpr,
    CallStmt,
    ComboStmt,
    ContinueStmt,
    DefaultCharDelayStmt,
    DefaultDelayStmt,
    DefineStmt,
    DelayStmt,
    DisableButtonStmt,
    DollarIdentifierExpr,
    DuckyLangStmt,
    EnableButtonStmt,
    Expr,
    ExtensionStmt,
    FunctionDef,
    GroupExpr,
    HashIdentifierExpr,
    HidePayloadStmt,
    HoldStmt,
    IdentifierExpr,
    IfStmt,
    InjectModStmt,
    IntegerExpr,
    KeyStmt,
    LedState,
    LedStmt,
    LockKeyState,
    LockKeyType,
    RandomStmt,
    RandomType,
    ReleaseStmt,
    RepeatStmt,
    ResetStmt,
    RestartPayloadStmt,
    RestoreAttackModeStmt,
    RestoreHostLockStateStmt,
    RestorePayloadStmt,
    ReturnStmt,
    SaveAttackModeStmt,
    SaveHostLockStateStmt,
    Script,
    Stmt,
    StopPayloadStmt,
    StringExpr,
    StringLnStmt,
    StringStmt,
    UnaryOp,
    VarDef,
    WaitForButtonPressStmt,
    WaitForKeyStmt,
    WhileStmt,
)
from ducky.tokens import ActionKey, ModifierKey, Operator, Token, TokenType
from ducky.utils.visitor import NodeVisitor

__all__ = [
    "DuckyParser",
    "NodeVisitor",
    "ParseError",
]

# ── Public error type ────────────────────────────────────────────────────────


class ParseError(Exception):
    """Raised when the parser encounters invalid syntax."""

    def __init__(self, message: str, line: int = 0, column: int = 0) -> None:
        self.message = message
        self.line = line
        self.column = column
        super().__init__(f"Line {line}, col {column}: {message}")


# ── Token-to-enum mappings ───────────────────────────────────────────────────

_TOKEN_TO_OPERATOR: dict[TokenType, Operator] = {
    TokenType.PLUS: Operator.ADD,
    TokenType.MINUS: Operator.SUBTRACT,
    TokenType.STAR: Operator.MULTIPLY,
    TokenType.SLASH: Operator.DIVIDE,
    TokenType.PERCENT: Operator.MODULO,
    TokenType.CARET: Operator.POWER,
    TokenType.BANG: Operator.NOT,
    TokenType.AMPERSAND: Operator.BITWISE_AND,
    TokenType.PIPE: Operator.BITWISE_OR,
    TokenType.LT: Operator.LESS,
    TokenType.GT: Operator.GREATER,
    TokenType.LE: Operator.LESS_EQUAL,
    TokenType.GE: Operator.GREATER_EQUAL,
    TokenType.EQ: Operator.EQUAL,
    TokenType.NE: Operator.NOT_EQUAL,
    TokenType.LSHIFT: Operator.SHIFT_LEFT,
    TokenType.RSHIFT: Operator.SHIFT_RIGHT,
    TokenType.AND: Operator.LOGICAL_AND,
    TokenType.OR: Operator.LOGICAL_OR,
    TokenType.ASSIGN: Operator.ASSIGN,
}

_TOKEN_TO_MODIFIER: dict[TokenType, ModifierKey] = {
    TokenType.CONTROL: ModifierKey.CONTROL,
    TokenType.CTRL: ModifierKey.CTRL,
    TokenType.SHIFT: ModifierKey.SHIFT,
    TokenType.ALT: ModifierKey.ALT,
    TokenType.GUI: ModifierKey.GUI,
    TokenType.WINDOWS: ModifierKey.WINDOWS,
    TokenType.COMMAND: ModifierKey.COMMAND,
    TokenType.OPTION: ModifierKey.OPTION,
}

_TOKEN_TO_ACTION_KEY: dict[TokenType, ActionKey] = {
    TokenType.ENTER: ActionKey.ENTER,
    TokenType.SPACE: ActionKey.SPACE,
    TokenType.TAB: ActionKey.TAB,
    TokenType.BACKSPACE: ActionKey.BACKSPACE,
    TokenType.DELETE: ActionKey.DELETE,
    TokenType.DEL: ActionKey.DEL,
    TokenType.INSERT: ActionKey.INSERT,
    TokenType.HOME: ActionKey.HOME,
    TokenType.END_KEY: ActionKey.END,
    TokenType.PAGEUP: ActionKey.PAGEUP,
    TokenType.PAGEDOWN: ActionKey.PAGEDOWN,
    TokenType.UP: ActionKey.UP,
    TokenType.UPARROW: ActionKey.UPARROW,
    TokenType.DOWN: ActionKey.DOWN,
    TokenType.DOWNARROW: ActionKey.DOWNARROW,
    TokenType.LEFT: ActionKey.LEFT,
    TokenType.LEFTARROW: ActionKey.LEFTARROW,
    TokenType.RIGHT: ActionKey.RIGHT,
    TokenType.RIGHTARROW: ActionKey.RIGHTARROW,
    TokenType.ESCAPE: ActionKey.ESCAPE,
    TokenType.ESC: ActionKey.ESC,
    TokenType.PRINTSCREEN: ActionKey.PRINTSCREEN,
    TokenType.SCROLLLOCK: ActionKey.SCROLLLOCK,
    TokenType.PAUSE: ActionKey.PAUSE,
    TokenType.MENU: ActionKey.MENU,
    TokenType.APP: ActionKey.APP,
    TokenType.CAPSLOCK: ActionKey.CAPSLOCK,
    TokenType.NUMLOCK: ActionKey.NUMLOCK,
    TokenType.POWER: ActionKey.POWER,
    TokenType.F1: ActionKey.F1,
    TokenType.F2: ActionKey.F2,
    TokenType.F3: ActionKey.F3,
    TokenType.F4: ActionKey.F4,
    TokenType.F5: ActionKey.F5,
    TokenType.F6: ActionKey.F6,
    TokenType.F7: ActionKey.F7,
    TokenType.F8: ActionKey.F8,
    TokenType.F9: ActionKey.F9,
    TokenType.F10: ActionKey.F10,
    TokenType.F11: ActionKey.F11,
    TokenType.F12: ActionKey.F12,
    TokenType.KP_SLASH: ActionKey.KP_SLASH,
    TokenType.KP_ASTERISK: ActionKey.KP_ASTERISK,
    TokenType.KP_MINUS: ActionKey.KP_MINUS,
    TokenType.KP_PLUS: ActionKey.KP_PLUS,
    TokenType.KP_ENTER: ActionKey.KP_ENTER,
    TokenType.KP_0: ActionKey.KP_0,
    TokenType.KP_1: ActionKey.KP_1,
    TokenType.KP_2: ActionKey.KP_2,
    TokenType.KP_3: ActionKey.KP_3,
    TokenType.KP_4: ActionKey.KP_4,
    TokenType.KP_5: ActionKey.KP_5,
    TokenType.KP_6: ActionKey.KP_6,
    TokenType.KP_7: ActionKey.KP_7,
    TokenType.KP_8: ActionKey.KP_8,
    TokenType.KP_9: ActionKey.KP_9,
    TokenType.KP_DOT: ActionKey.KP_DOT,
    TokenType.KP_EQUAL: ActionKey.KP_EQUAL,
    TokenType.KP_COMMA: ActionKey.KP_COMMA,
    TokenType.KP_00: ActionKey.KP_00,
    TokenType.KP_000: ActionKey.KP_000,
    TokenType.KEY_102ND: ActionKey.KEY_102ND,
    TokenType.COMPOSE: ActionKey.COMPOSE,
    TokenType.KPEQUAL: ActionKey.KPEQUAL,
    TokenType.PROPS: ActionKey.PROPS,
    TokenType.UNDO: ActionKey.UNDO,
    TokenType.PASTE: ActionKey.PASTE,
}

_TOKEN_TO_RANDOM_TYPE: dict[TokenType, RandomType] = {
    TokenType.RANDOM_CHAR: RandomType.CHAR,
    TokenType.RANDOM_LOWERCASE_LETTER: RandomType.LOWERCASE_LETTER,
    TokenType.RANDOM_UPPERCASE_LETTER: RandomType.UPPERCASE_LETTER,
    TokenType.RANDOM_LETTER: RandomType.LETTER,
    TokenType.RANDOM_NUMBER: RandomType.NUMBER,
    TokenType.RANDOM_SPECIAL: RandomType.SPECIAL,
}

_TOKEN_TO_LED_STATE: dict[TokenType, LedState] = {
    TokenType.LED_OFF: LedState.OFF,
    TokenType.LED_R: LedState.R,
    TokenType.LED_G: LedState.G,
    TokenType.LED_B: LedState.B,
}

_TOKEN_TO_LOCK_KEY: dict[TokenType, tuple[LockKeyType, LockKeyState]] = {
    TokenType.WAIT_FOR_CAPS_ON: (LockKeyType.CAPS, LockKeyState.ON),
    TokenType.WAIT_FOR_CAPS_OFF: (LockKeyType.CAPS, LockKeyState.OFF),
    TokenType.WAIT_FOR_CAPS_CHANGE: (LockKeyType.CAPS, LockKeyState.CHANGE),
    TokenType.WAIT_FOR_NUM_ON: (LockKeyType.NUM, LockKeyState.ON),
    TokenType.WAIT_FOR_NUM_OFF: (LockKeyType.NUM, LockKeyState.OFF),
    TokenType.WAIT_FOR_NUM_CHANGE: (LockKeyType.NUM, LockKeyState.CHANGE),
    TokenType.WAIT_FOR_SCROLL_ON: (LockKeyType.SCROLL, LockKeyState.ON),
    TokenType.WAIT_FOR_SCROLL_OFF: (LockKeyType.SCROLL, LockKeyState.OFF),
    TokenType.WAIT_FOR_SCROLL_CHANGE: (LockKeyType.SCROLL, LockKeyState.CHANGE),
}

_MODIFIER_TOKEN_TYPES = frozenset(_TOKEN_TO_MODIFIER.keys())
_ACTION_KEY_TOKEN_TYPES = frozenset(_TOKEN_TO_ACTION_KEY.keys())

# ── Parser ───────────────────────────────────────────────────────────────────


class DuckyParser:
    """Recursive-descent parser for DuckyScript 3.

    Usage::

        tokens = DuckyLexer().tokenize(source)
        parser = DuckyParser(tokens)
        script = parser.parse()
    """

    def __init__(self, tokens: list[Token]) -> None:
        self._tokens = tokens
        self._pos = 0
        self._in_function = False
        self._loop_depth = 0
        self._previous_stmt_was_block_end = False

    # ── Public API ───────────────────────────────────────────────────────────

    def parse(self) -> Script:
        """Parse the full token stream into a ``Script`` AST node."""
        statements: list[Stmt] = []
        self._previous_stmt_was_block_end = False
        while not self._at_end():
            stmt = self._parse_statement()
            if stmt is not None:
                statements.append(stmt)
        return Script(tuple(statements))

    # ── Token helpers ────────────────────────────────────────────────────────

    def _peek(self) -> Token:
        return self._tokens[self._pos]

    def _previous(self) -> Token:
        return self._tokens[self._pos - 1]

    def _advance(self) -> Token:
        token = self._tokens[self._pos]
        self._pos += 1
        return token

    def _check(self, type_: TokenType) -> bool:
        if self._at_end():
            return False
        return self._peek().type == type_

    def _match(self, *types: TokenType) -> bool:
        for t in types:
            if self._check(t):
                self._advance()
                return True
        return False

    def _consume(self, type_: TokenType, message: str) -> Token:
        if self._check(type_):
            return self._advance()
        token = self._peek()
        raise ParseError(
            f"{message}. Got {token.type.name} ('{token.value}')",
            token.line,
            token.column,
        )

    def _at_end(self) -> bool:
        return self._peek().type == TokenType.EOF

    def _consume_newline(self) -> None:
        """Consume a NEWLINE token or raise ParseError if not at EOF."""
        if not self._match(TokenType.NEWLINE):
            if not self._at_end():
                token = self._peek()
                raise ParseError(
                    f"Expected NEWLINE after statement. Got {token.type.name}",
                    token.line,
                    token.column,
                )

    # ── Statement list helper ────────────────────────────────────────────────

    def _parse_statements_until(
        self, stop_tokens: set[TokenType]
    ) -> list[Stmt]:
        """Parse statements until one of *stop_tokens* is reached (not consumed)."""
        stmts: list[Stmt] = []
        while not self._at_end() and self._peek().type not in stop_tokens:
            stmt = self._parse_statement()
            if stmt is not None:
                stmts.append(stmt)
        return stmts

    # ── Statement dispatch ───────────────────────────────────────────────────

    def _parse_statement(self) -> Stmt | None:
        """Parse a single statement. Returns ``None`` for blank lines."""
        # Skip blank lines
        while self._match(TokenType.NEWLINE):
            pass

        if self._at_end():
            return None

        token = self._peek()

        # ── Compound / flow-control statements ──
        if token.type == TokenType.IF:
            return self._parse_if_stmt()
        if token.type == TokenType.WHILE:
            return self._parse_while_stmt()
        if token.type == TokenType.FUNCTION:
            return self._parse_function_def()
        if token.type == TokenType.EXTENSION:
            return self._parse_extension_def()

        # ── Block-end keywords are errors as standalone statements ──
        if token.type in (
            TokenType.END_IF,
            TokenType.END_WHILE,
            TokenType.END_FUNCTION,
            TokenType.END_BUTTON,
            TokenType.END_EXTENSION,
            TokenType.ELSE,
            TokenType.END_REM,
        ):
            raise ParseError(
                f"Unexpected {token.type.name}",
                token.line,
                token.column,
            )

        # ── Variable declaration ──
        if token.type == TokenType.VAR:
            return self._parse_var_decl_stmt()

        # ── Assignment ──
        if token.type == TokenType.DOLLAR_IDENTIFIER:
            # Look ahead: ASSIGN means assignment
            if (
                self._pos + 1 < len(self._tokens)
                and self._tokens[self._pos + 1].type == TokenType.ASSIGN
            ):
                return self._parse_assign_stmt()
            raise ParseError(
                f"$identifier '{token.value}' without assignment",
                token.line,
                token.column,
            )

        # ── Flow control ──
        if token.type == TokenType.RETURN:
            return self._parse_return_stmt()
        if token.type == TokenType.BREAK:
            return self._parse_loop_control_stmt()
        if token.type == TokenType.CONTINUE:
            return self._parse_loop_control_stmt()
        if token.type == TokenType.REPEAT:
            return self._parse_repeat_stmt()

        # ── Delays ──
        if token.type == TokenType.DELAY:
            return self._parse_delay_stmt()
        if token.type in (
            TokenType.DEFAULTDELAY,
            TokenType.DEFAULT_DELAY,
        ):
            return self._parse_default_delay_stmt()
        if token.type in (
            TokenType.DEFAULTCHARDELAY,
            TokenType.DEFAULT_CHAR_DELAY,
            TokenType.STRINGDELAY,
        ):
            return self._parse_default_char_delay_stmt()

        # ── String output ──
        if token.type == TokenType.STRING:
            return self._parse_string_stmt()
        if token.type == TokenType.STRINGLN:
            return self._parse_string_ln_stmt()

        # ── Keyboard commands ──
        if token.type == TokenType.INJECT_MOD:
            return self._parse_inject_mod_stmt()
        if token.type == TokenType.HOLD:
            return self._parse_hold_stmt()
        if token.type == TokenType.RELEASE:
            return self._parse_release_stmt()
        if token.type == TokenType.RESET:
            return self._parse_reset_stmt()
        if token.type == TokenType.RESTART_PAYLOAD:
            return self._parse_restart_payload_stmt()
        if token.type == TokenType.STOP_PAYLOAD:
            return self._parse_stop_payload_stmt()

        # ── Random ──
        if token.type in _TOKEN_TO_RANDOM_TYPE:
            return self._parse_random_stmt()

        # ── LED ──
        if token.type in _TOKEN_TO_LED_STATE:
            return self._parse_led_stmt()

        # ── Button ──
        if token.type == TokenType.BUTTON_DEF:
            return self._parse_button_def_stmt()
        if token.type == TokenType.WAIT_FOR_BUTTON_PRESS:
            return self._parse_wait_for_button_stmt()
        if token.type in (
            TokenType.DISABLE_BUTTON,
            TokenType.ENABLE_BUTTON,
        ):
            return self._parse_button_control_stmt()

        # ── Attack mode ──
        if token.type == TokenType.ATTACKMODE:
            return self._parse_attack_mode_stmt()
        if token.type == TokenType.SAVE_ATTACKMODE:
            return self._parse_save_attack_mode_stmt()
        if token.type == TokenType.RESTORE_ATTACKMODE:
            return self._parse_restore_attack_mode_stmt()

        # ── Lock key wait ──
        if token.type in _TOKEN_TO_LOCK_KEY:
            return self._parse_wait_for_lock_key_stmt()

        # ── Save/restore lock state ──
        if token.type == TokenType.SAVE_HOST_KEYBOARD_LOCK_STATE:
            return self._parse_save_restore_lock_state_stmt()
        if token.type == TokenType.RESTORE_HOST_KEYBOARD_LOCK_STATE:
            return self._parse_save_restore_lock_state_stmt()

        # ── Hide/restore payload ──
        if token.type == TokenType.HIDE_PAYLOAD:
            return self._parse_hide_restore_payload_stmt()
        if token.type == TokenType.RESTORE_PAYLOAD:
            return self._parse_hide_restore_payload_stmt()

        # ── Ducky language ──
        if token.type == TokenType.DUCKY_LANG:
            return self._parse_ducky_lang_stmt()

        # ── DEFINE ──
        if token.type == TokenType.DEFINE:
            return self._parse_define_stmt()

        # ── Modifier keys → combo statement ──
        if token.type in _MODIFIER_TOKEN_TYPES:
            return self._parse_modifier_combo_stmt()

        # ── Action keys → key statement ──
        if token.type in _ACTION_KEY_TOKEN_TYPES:
            return self._parse_key_stmt()

        # ── Identifier → function call or error ──
        if token.type == TokenType.IDENTIFIER:
            # Check if followed by LPAREN → call statement
            if (
                self._pos + 1 < len(self._tokens)
                and self._tokens[self._pos + 1].type == TokenType.LPAREN
            ):
                return self._parse_call_stmt()
            raise ParseError(
                f"Unexpected identifier '{token.value}'",
                token.line,
                token.column,
            )

        # ── Nothing matched ──
        raise ParseError(
            f"Unexpected token: {token.type.name} ('{token.value}')",
            token.line,
            token.column,
        )

    # ── Delay statements ─────────────────────────────────────────────────────

    def _parse_delay_stmt(self) -> DelayStmt:
        self._consume(TokenType.DELAY, "Expected DELAY")
        expr = self._parse_expression()
        self._consume_newline()
        self._previous_stmt_was_block_end = False
        return DelayStmt(milliseconds=expr)

    def _parse_default_delay_stmt(self) -> DefaultDelayStmt:
        self._match(TokenType.DEFAULTDELAY, TokenType.DEFAULT_DELAY)
        expr = self._parse_expression()
        self._consume_newline()
        self._previous_stmt_was_block_end = False
        return DefaultDelayStmt(delay=expr)

    def _parse_default_char_delay_stmt(self) -> DefaultCharDelayStmt:
        self._match(
            TokenType.DEFAULTCHARDELAY,
            TokenType.DEFAULT_CHAR_DELAY,
            TokenType.STRINGDELAY,
        )
        expr = self._parse_expression()
        self._consume_newline()
        self._previous_stmt_was_block_end = False
        return DefaultCharDelayStmt(delay=expr)

    # ── String statements ────────────────────────────────────────────────────

    def _parse_string_stmt(self) -> StringStmt:
        self._consume(TokenType.STRING, "Expected STRING")
        text = ""
        if self._match(TokenType.STRING_BODY):
            text = self._previous().value
        self._consume_newline()
        self._previous_stmt_was_block_end = False
        return StringStmt(text=text)

    def _parse_string_ln_stmt(self) -> StringLnStmt:
        self._consume(TokenType.STRINGLN, "Expected STRINGLN")
        text = ""
        if self._match(TokenType.STRING_BODY):
            text = self._previous().value
        self._consume_newline()
        self._previous_stmt_was_block_end = False
        return StringLnStmt(text=text)

    # ── Keyboard statements ──────────────────────────────────────────────────

    def _parse_key_stmt(self) -> KeyStmt:
        token = self._advance()
        key = _TOKEN_TO_ACTION_KEY[token.type]
        self._consume_newline()
        self._previous_stmt_was_block_end = False
        return KeyStmt(key=key)

    def _parse_modifier_combo_stmt(self) -> ComboStmt:
        modifiers: list[ModifierKey] = []
        key: ActionKey | None = None

        # Consume first modifier
        token = self._advance()
        modifiers.append(_TOKEN_TO_MODIFIER[token.type])

        # Consume additional modifiers (separated by optional MINUS/space)
        while not self._at_end() and not self._check(TokenType.NEWLINE):
            # Skip optional MINUS separator
            self._match(TokenType.MINUS)

            if self._check(TokenType.NEWLINE) or self._at_end():
                break

            if self._check(TokenType.EOF):
                break

            # Check for another modifier
            if self._peek().type in _MODIFIER_TOKEN_TYPES:
                modifiers.append(_TOKEN_TO_MODIFIER[self._advance().type])
            elif self._peek().type in _ACTION_KEY_TOKEN_TYPES:
                key = _TOKEN_TO_ACTION_KEY[self._advance().type]
                break
            else:
                break

        self._consume_newline()
        self._previous_stmt_was_block_end = False
        return ComboStmt(modifiers=tuple(modifiers), key=key)

    def _parse_inject_mod_stmt(self) -> InjectModStmt:
        self._consume(TokenType.INJECT_MOD, "Expected INJECT_MOD")
        self._consume_newline()
        self._previous_stmt_was_block_end = False
        return InjectModStmt()

    def _parse_hold_stmt(self) -> HoldStmt:
        self._consume(TokenType.HOLD, "Expected HOLD")
        key_token = self._advance()
        # Per spec §2 grammar: HOLD only accepts action keys (not modifiers).
        if key_token.type not in _ACTION_KEY_TOKEN_TYPES:
            raise ParseError(
                f"Expected action key after HOLD. Got {key_token.type.name}",
                key_token.line,
                key_token.column,
            )
        key = _TOKEN_TO_ACTION_KEY[key_token.type]
        self._consume_newline()
        self._previous_stmt_was_block_end = False
        return HoldStmt(key=key)

    def _parse_release_stmt(self) -> ReleaseStmt:
        self._consume(TokenType.RELEASE, "Expected RELEASE")
        key_token = self._advance()
        # Per spec §2 grammar: RELEASE only accepts action keys (not modifiers).
        if key_token.type not in _ACTION_KEY_TOKEN_TYPES:
            raise ParseError(
                f"Expected action key after RELEASE. Got {key_token.type.name}",
                key_token.line,
                key_token.column,
            )
        key = _TOKEN_TO_ACTION_KEY[key_token.type]
        self._consume_newline()
        self._previous_stmt_was_block_end = False
        return ReleaseStmt(key=key)

    def _parse_repeat_stmt(self) -> RepeatStmt:
        if self._previous_stmt_was_block_end:
            token = self._peek()
            raise ParseError(
                "REPEAT must follow a statement, not a block-end keyword",
                token.line,
                token.column,
            )
        self._consume(TokenType.REPEAT, "Expected REPEAT")
        count = self._parse_expression()
        self._consume_newline()
        self._previous_stmt_was_block_end = False
        return RepeatStmt(count=count)

    def _parse_reset_stmt(self) -> ResetStmt:
        self._consume(TokenType.RESET, "Expected RESET")
        self._consume_newline()
        self._previous_stmt_was_block_end = False
        return ResetStmt()

    def _parse_restart_payload_stmt(self) -> RestartPayloadStmt:
        self._consume(TokenType.RESTART_PAYLOAD, "Expected RESTART_PAYLOAD")
        self._consume_newline()
        self._previous_stmt_was_block_end = False
        return RestartPayloadStmt()

    def _parse_stop_payload_stmt(self) -> StopPayloadStmt:
        self._consume(TokenType.STOP_PAYLOAD, "Expected STOP_PAYLOAD")
        self._consume_newline()
        self._previous_stmt_was_block_end = False
        return StopPayloadStmt()

    # ── Variable statements ──────────────────────────────────────────────────

    def _parse_var_decl_stmt(self) -> VarDef:
        self._consume(TokenType.VAR, "Expected VAR")
        dollar = self._consume(
            TokenType.DOLLAR_IDENTIFIER, "Expected $identifier after VAR"
        )
        name = dollar.value
        initializer: Expr = IntegerExpr(0)
        if self._match(TokenType.ASSIGN):
            initializer = self._parse_expression()
        self._consume_newline()
        self._previous_stmt_was_block_end = False
        return VarDef(name=name, initializer=initializer)

    def _parse_assign_stmt(self) -> AssignStmt:
        dollar = self._consume(
            TokenType.DOLLAR_IDENTIFIER, "Expected $identifier"
        )
        name = dollar.value
        self._consume(TokenType.ASSIGN, "Expected =")
        value = self._parse_expression()
        self._consume_newline()
        self._previous_stmt_was_block_end = False
        return AssignStmt(name=name, value=value)

    # ── Control flow ─────────────────────────────────────────────────────────

    def _parse_if_stmt(self) -> IfStmt:
        self._consume(TokenType.IF, "Expected IF")
        paren = self._match(TokenType.LPAREN)
        condition = self._parse_expression()
        if paren:
            self._consume(TokenType.RPAREN, "Expected ')' after IF condition")
        self._consume(TokenType.THEN, "Expected THEN after IF condition")
        self._consume_newline()

        body = self._parse_statements_until(
            {TokenType.ELSE, TokenType.END_IF}
        )
        else_body = self._parse_else_chain()

        self._consume(TokenType.END_IF, "Expected END_IF")
        self._consume_newline()
        self._previous_stmt_was_block_end = True
        return IfStmt(
            condition=condition, body=tuple(body), else_body=else_body
        )

    def _parse_else_chain(self) -> tuple[Stmt, ...] | None:
        """Parse an optional ELSE / ELSE IF chain.

        Returns ``None`` (no else), a tuple of statements (plain ELSE), or a
        tuple containing a single ``IfStmt`` (ELSE IF chain).
        """
        if not self._match(TokenType.ELSE):
            return None

        if self._match(TokenType.IF):
            # ELSE IF branch
            paren = self._match(TokenType.LPAREN)
            condition = self._parse_expression()
            if paren:
                self._consume(
                    TokenType.RPAREN, "Expected ')' after ELSE IF condition"
                )
            self._consume(
                TokenType.THEN, "Expected THEN after ELSE IF condition"
            )
            self._consume_newline()
            body = self._parse_statements_until(
                {TokenType.ELSE, TokenType.END_IF}
            )
            else_body = self._parse_else_chain()
            return (
                IfStmt(
                    condition=condition,
                    body=tuple(body),
                    else_body=else_body,
                ),
            )

        # Plain ELSE branch
        self._consume_newline()
        body = self._parse_statements_until(
            {TokenType.ELSE, TokenType.END_IF}
        )
        return tuple(body)

    def _parse_while_stmt(self) -> WhileStmt:
        self._consume(TokenType.WHILE, "Expected WHILE")
        paren = self._match(TokenType.LPAREN)
        condition = self._parse_expression()
        if paren:
            self._consume(
                TokenType.RPAREN, "Expected ')' after WHILE condition"
            )
        self._consume_newline()

        self._loop_depth += 1
        body = self._parse_statements_until({TokenType.END_WHILE})
        self._loop_depth -= 1

        self._consume(TokenType.END_WHILE, "Expected END_WHILE")
        self._consume_newline()
        self._previous_stmt_was_block_end = True
        return WhileStmt(condition=condition, body=tuple(body))

    def _parse_loop_control_stmt(self) -> BreakStmt | ContinueStmt:
        token = self._advance()
        if self._loop_depth == 0:
            name = token.type.name
            raise ParseError(
                f"{name} outside loop",
                token.line,
                token.column,
            )
        self._consume_newline()
        self._previous_stmt_was_block_end = False
        if token.type == TokenType.BREAK:
            return BreakStmt()
        return ContinueStmt()

    # ── Functions ────────────────────────────────────────────────────────────

    def _parse_function_def(self) -> FunctionDef:
        self._consume(TokenType.FUNCTION, "Expected FUNCTION")
        name_token = self._consume(
            TokenType.IDENTIFIER, "Expected function name"
        )
        self._consume(TokenType.LPAREN, "Expected '(' after function name")
        # Functions take zero arguments per spec; we still parse empty params
        params: list[str] = []
        self._consume(TokenType.RPAREN, "Expected ')' after function params")
        self._consume_newline()

        saved_in_function = self._in_function
        self._in_function = True
        body = self._parse_statements_until({TokenType.END_FUNCTION})
        self._in_function = saved_in_function

        self._consume(TokenType.END_FUNCTION, "Expected END_FUNCTION")
        self._consume_newline()
        self._previous_stmt_was_block_end = True
        return FunctionDef(
            name=name_token.value,
            params=tuple(params),
            body=tuple(body),
        )

    def _parse_call_stmt(self) -> CallStmt:
        name_token = self._consume(
            TokenType.IDENTIFIER, "Expected function name"
        )
        self._consume(TokenType.LPAREN, "Expected '('")
        self._consume(TokenType.RPAREN, "Expected ')'")
        self._consume_newline()
        self._previous_stmt_was_block_end = False
        return CallStmt(name=name_token.value)

    def _parse_return_stmt(self) -> ReturnStmt:
        self._consume(TokenType.RETURN, "Expected RETURN")
        if not self._in_function:
            token = self._previous()
            raise ParseError(
                "RETURN outside function", token.line, token.column
            )
        value: Expr | None = None
        if not self._check(TokenType.NEWLINE) and not self._at_end():
            value = self._parse_expression()
        self._consume_newline()
        self._previous_stmt_was_block_end = False
        return ReturnStmt(value=value)

    # ── Random ───────────────────────────────────────────────────────────────

    def _parse_random_stmt(self) -> RandomStmt:
        token = self._advance()
        random_type = _TOKEN_TO_RANDOM_TYPE[token.type]
        self._consume_newline()
        self._previous_stmt_was_block_end = False
        return RandomStmt(random_type=random_type)

    # ── LED ──────────────────────────────────────────────────────────────────

    def _parse_led_stmt(self) -> LedStmt:
        token = self._advance()
        state = _TOKEN_TO_LED_STATE[token.type]
        self._consume_newline()
        self._previous_stmt_was_block_end = False
        return LedStmt(state=state)

    # ── Button ───────────────────────────────────────────────────────────────

    def _parse_button_def_stmt(self) -> ButtonDefStmt:
        self._consume(TokenType.BUTTON_DEF, "Expected BUTTON_DEF")
        name = ""
        if self._check(TokenType.IDENTIFIER):
            name = self._advance().value
        self._consume_newline()
        body = self._parse_statements_until({TokenType.END_BUTTON})
        self._consume(TokenType.END_BUTTON, "Expected END_BUTTON")
        self._consume_newline()
        self._previous_stmt_was_block_end = True
        return ButtonDefStmt(name=name, body=tuple(body))

    def _parse_wait_for_button_stmt(self) -> WaitForButtonPressStmt:
        self._consume(
            TokenType.WAIT_FOR_BUTTON_PRESS, "Expected WAIT_FOR_BUTTON_PRESS"
        )
        self._consume_newline()
        self._previous_stmt_was_block_end = False
        return WaitForButtonPressStmt()

    def _parse_button_control_stmt(
        self,
    ) -> DisableButtonStmt | EnableButtonStmt:
        token = self._advance()
        self._consume_newline()
        self._previous_stmt_was_block_end = False
        if token.type == TokenType.DISABLE_BUTTON:
            return DisableButtonStmt()
        return EnableButtonStmt()

    # ── Attack mode ──────────────────────────────────────────────────────────

    def _parse_attack_mode_stmt(self) -> AttackModeStmt:
        self._consume(TokenType.ATTACKMODE, "Expected ATTACKMODE")
        params: list[str] = []
        while self._match(TokenType.ATTACKMODE_PARAM):
            params.append(self._previous().value)
        self._consume_newline()
        self._previous_stmt_was_block_end = False
        return AttackModeStmt(params=tuple(params))

    def _parse_save_attack_mode_stmt(self) -> SaveAttackModeStmt:
        self._consume(
            TokenType.SAVE_ATTACKMODE, "Expected SAVE_ATTACKMODE"
        )
        self._consume_newline()
        self._previous_stmt_was_block_end = False
        return SaveAttackModeStmt()

    def _parse_restore_attack_mode_stmt(self) -> RestoreAttackModeStmt:
        self._consume(
            TokenType.RESTORE_ATTACKMODE, "Expected RESTORE_ATTACKMODE"
        )
        self._consume_newline()
        self._previous_stmt_was_block_end = False
        return RestoreAttackModeStmt()

    # ── Lock key wait ────────────────────────────────────────────────────────

    def _parse_wait_for_lock_key_stmt(self) -> WaitForKeyStmt:
        token = self._advance()
        lock_type, state = _TOKEN_TO_LOCK_KEY[token.type]
        self._consume_newline()
        self._previous_stmt_was_block_end = False
        return WaitForKeyStmt(lock_key=lock_type, state=state)

    # ── Save/restore lock state ──────────────────────────────────────────────

    def _parse_save_restore_lock_state_stmt(
        self,
    ) -> SaveHostLockStateStmt | RestoreHostLockStateStmt:
        token = self._advance()
        self._consume_newline()
        self._previous_stmt_was_block_end = False
        if token.type == TokenType.SAVE_HOST_KEYBOARD_LOCK_STATE:
            return SaveHostLockStateStmt()
        return RestoreHostLockStateStmt()

    # ── Hide/restore payload ─────────────────────────────────────────────────

    def _parse_hide_restore_payload_stmt(
        self,
    ) -> HidePayloadStmt | RestorePayloadStmt:
        token = self._advance()
        self._consume_newline()
        self._previous_stmt_was_block_end = False
        if token.type == TokenType.HIDE_PAYLOAD:
            return HidePayloadStmt()
        return RestorePayloadStmt()

    # ── Ducky language ───────────────────────────────────────────────────────

    def _parse_ducky_lang_stmt(self) -> DuckyLangStmt:
        self._consume(TokenType.DUCKY_LANG, "Expected DUCKY_LANG")
        if self._check(TokenType.IDENTIFIER):
            lang = self._advance().value
        elif self._check(TokenType.STRING_BODY):
            lang = self._advance().value
        else:
            token = self._peek()
            raise ParseError(
                "Expected language code after DUCKY_LANG",
                token.line,
                token.column,
            )
        self._consume_newline()
        self._previous_stmt_was_block_end = False
        return DuckyLangStmt(language=lang)

    # ── Extension ────────────────────────────────────────────────────────────

    def _parse_extension_def(self) -> ExtensionStmt:
        self._consume(TokenType.EXTENSION, "Expected EXTENSION")
        name_token = self._consume(
            TokenType.IDENTIFIER, "Expected extension name"
        )
        self._consume_newline()
        body = self._parse_statements_until({TokenType.END_EXTENSION})
        self._consume(
            TokenType.END_EXTENSION, "Expected END_EXTENSION"
        )
        self._consume_newline()
        self._previous_stmt_was_block_end = True
        return ExtensionStmt(
            name=name_token.value, body=tuple(body)
        )

    # ── DEFINE ───────────────────────────────────────────────────────────────

    def _parse_define_stmt(self) -> DefineStmt:
        self._consume(TokenType.DEFINE, "Expected DEFINE")
        hash_token = self._consume(
            TokenType.HASH_IDENTIFIER,
            "Expected #NAME after DEFINE",
        )
        value_parts: list[str] = []
        while not self._check(TokenType.NEWLINE) and not self._at_end():
            value_parts.append(self._advance().value)
        if not value_parts:
            token = self._peek()
            raise ParseError(
                "Expected value after DEFINE #NAME",
                token.line,
                token.column,
            )
        self._consume_newline()
        self._previous_stmt_was_block_end = False
        return DefineStmt(
            name=hash_token.value, value=" ".join(value_parts)
        )

    # ── Expression parsing (precedence climbing) ─────────────────────────────

    def _parse_expression(self) -> Expr:
        """Parse an expression starting at the assignment level."""
        return self._parse_assignment()

    def _parse_assignment(self) -> Expr:
        """Level 2: assignment ``=`` (right-associative)."""
        expr = self._parse_logical_or()
        if self._match(TokenType.ASSIGN):
            right = self._parse_assignment()
            return BinaryOp(expr, Operator.ASSIGN, right)
        return expr

    def _parse_logical_or(self) -> Expr:
        """Level 3: logical OR ``||`` (left-associative)."""
        expr = self._parse_logical_and()
        while self._match(TokenType.OR):
            right = self._parse_logical_and()
            expr = BinaryOp(expr, Operator.LOGICAL_OR, right)
        return expr

    def _parse_logical_and(self) -> Expr:
        """Level 4: logical AND ``&&`` (left-associative)."""
        expr = self._parse_bitwise_or()
        while self._match(TokenType.AND):
            right = self._parse_bitwise_or()
            expr = BinaryOp(expr, Operator.LOGICAL_AND, right)
        return expr

    def _parse_bitwise_or(self) -> Expr:
        """Level 5: bitwise OR ``|`` (left-associative)."""
        expr = self._parse_bitwise_and()
        while self._match(TokenType.PIPE):
            right = self._parse_bitwise_and()
            expr = BinaryOp(expr, Operator.BITWISE_OR, right)
        return expr

    def _parse_bitwise_and(self) -> Expr:
        """Level 6: bitwise AND ``&`` (left-associative)."""
        expr = self._parse_equality()
        while self._match(TokenType.AMPERSAND):
            right = self._parse_equality()
            expr = BinaryOp(expr, Operator.BITWISE_AND, right)
        return expr

    def _parse_equality(self) -> Expr:
        """Level 7: equality ``==`` ``!=`` (left-associative)."""
        expr = self._parse_relational()
        while self._match(TokenType.EQ, TokenType.NE):
            op = _TOKEN_TO_OPERATOR[self._previous().type]
            right = self._parse_relational()
            expr = BinaryOp(expr, op, right)
        return expr

    def _parse_relational(self) -> Expr:
        """Level 8: relational ``<`` ``<=`` ``>`` ``>=`` (left-associative)."""
        expr = self._parse_shift()
        while self._match(TokenType.LT, TokenType.GT, TokenType.LE, TokenType.GE):
            op = _TOKEN_TO_OPERATOR[self._previous().type]
            right = self._parse_shift()
            expr = BinaryOp(expr, op, right)
        return expr

    def _parse_shift(self) -> Expr:
        """Level 9: shift ``<<`` ``>>`` (left-associative)."""
        expr = self._parse_additive()
        while self._match(TokenType.LSHIFT, TokenType.RSHIFT):
            op = _TOKEN_TO_OPERATOR[self._previous().type]
            right = self._parse_additive()
            expr = BinaryOp(expr, op, right)
        return expr

    def _parse_additive(self) -> Expr:
        """Level 10: addition/subtraction ``+`` ``-`` (left-associative)."""
        expr = self._parse_multiplicative()
        while self._match(TokenType.PLUS, TokenType.MINUS):
            op = _TOKEN_TO_OPERATOR[self._previous().type]
            right = self._parse_multiplicative()
            expr = BinaryOp(expr, op, right)
        return expr

    def _parse_multiplicative(self) -> Expr:
        """Level 11: multiplicative ``*`` ``/`` ``%`` ``^`` (left-associative).

        Per spec §4.1: ``^`` (POWER/exponentiation) is at the multiplicative
        precedence level alongside ``*``, ``/``, ``%``, all left-associative.
        Example: ``2 * 3 ^ 4`` parses as ``(2 * 3) ^ 4``.
        """
        expr = self._parse_unary()
        while self._match(
            TokenType.STAR, TokenType.SLASH, TokenType.PERCENT, TokenType.CARET
        ):
            op = _TOKEN_TO_OPERATOR[self._previous().type]
            right = self._parse_unary()
            expr = BinaryOp(expr, op, right)
        return expr

    def _parse_unary(self) -> Expr:
        """Level 12: unary ``!`` ``-`` (right-associative)."""
        if self._match(TokenType.BANG, TokenType.MINUS):
            op = _TOKEN_TO_OPERATOR[self._previous().type]
            operand = self._parse_unary()
            return UnaryOp(op, operand)
        return self._parse_primary()

    def _parse_primary(self) -> Expr:
        """Parse primary expressions: literals, identifiers, groups."""
        if self._match(TokenType.INTEGER):
            return IntegerExpr(int(self._previous().value, 0))

        if self._match(TokenType.STRING_LITERAL):
            return StringExpr(self._previous().value)

        if self._match(TokenType.TRUE):
            return IntegerExpr(1)

        if self._match(TokenType.FALSE):
            return IntegerExpr(0)

        if self._match(TokenType.DOLLAR_IDENTIFIER):
            return DollarIdentifierExpr(self._previous().value)

        if self._match(TokenType.HASH_IDENTIFIER):
            return HashIdentifierExpr(self._previous().value)

        if self._check(TokenType.IDENTIFIER):
            name = self._advance().value
            if self._match(TokenType.LPAREN):
                self._consume(TokenType.RPAREN, "Expected ')'")
                return CallExpr(name=name)
            return IdentifierExpr(name=name)

        if self._match(TokenType.LPAREN):
            expr = self._parse_expression()
            self._consume(TokenType.RPAREN, "Expected ')'")
            return GroupExpr(expr)

        token = self._peek()
        raise ParseError(
            f"Unexpected token in expression: {token.type.name}",
            token.line,
            token.column,
        )
