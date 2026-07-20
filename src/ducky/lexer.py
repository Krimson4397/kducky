"""Lexer for DuckyScript 3.

Converts source text into a stream of tokens (Token data class).
Tokenization rules per the Engineering Spec, §3.2.
"""

from ducky.errors import LexerError  # noqa: E402

print("[ducky.lexer] loading module...")  # noqa: E402

from ducky.tokens import Token, TokenType  # noqa: E402

# ── Keyword map ────────────────────────────────────────────────────────────
# Case-insensitive: look up source text uppercased.
_KEYWORDS: dict[str, TokenType] = {
    # Control flow
    "IF": TokenType.IF,
    "THEN": TokenType.THEN,
    "ELSE": TokenType.ELSE,
    "END_IF": TokenType.END_IF,
    "WHILE": TokenType.WHILE,
    "END_WHILE": TokenType.END_WHILE,
    # Function
    "FUNCTION": TokenType.FUNCTION,
    "END_FUNCTION": TokenType.END_FUNCTION,
    "RETURN": TokenType.RETURN,
    # Variable
    "VAR": TokenType.VAR,
    # Comments (needed for recognition so lexer skips them)
    "REM": TokenType.REM,
    "REM_BLOCK": TokenType.REM_BLOCK,
    "END_REM": TokenType.END_REM,
    # Payload control
    "REPEAT": TokenType.REPEAT,
    "RESET": TokenType.RESET,
    "RESTART_PAYLOAD": TokenType.RESTART_PAYLOAD,
    "STOP_PAYLOAD": TokenType.STOP_PAYLOAD,
    # Delays
    "DELAY": TokenType.DELAY,
    "DEFAULTDELAY": TokenType.DEFAULTDELAY,
    "DEFAULT_DELAY": TokenType.DEFAULT_DELAY,
    "DEFAULTCHARDELAY": TokenType.DEFAULTCHARDELAY,
    "DEFAULT_CHAR_DELAY": TokenType.DEFAULT_CHAR_DELAY,
    "STRINGDELAY": TokenType.STRINGDELAY,
    # Keyboard output
    "STRING": TokenType.STRING,
    "STRINGLN": TokenType.STRINGLN,
    "INJECT_MOD": TokenType.INJECT_MOD,
    "HOLD": TokenType.HOLD,
    "RELEASE": TokenType.RELEASE,
    # Attack mode
    "ATTACKMODE": TokenType.ATTACKMODE,
    "SAVE_ATTACKMODE": TokenType.SAVE_ATTACKMODE,
    "RESTORE_ATTACKMODE": TokenType.RESTORE_ATTACKMODE,
    # LED
    "LED_OFF": TokenType.LED_OFF,
    "LED_R": TokenType.LED_R,
    "LED_G": TokenType.LED_G,
    "LED_B": TokenType.LED_B,
    # Button
    "BUTTON_DEF": TokenType.BUTTON_DEF,
    "END_BUTTON": TokenType.END_BUTTON,
    "DISABLE_BUTTON": TokenType.DISABLE_BUTTON,
    "ENABLE_BUTTON": TokenType.ENABLE_BUTTON,
    "WAIT_FOR_BUTTON_PRESS": TokenType.WAIT_FOR_BUTTON_PRESS,
    # Lock key wait
    "WAIT_FOR_CAPS_ON": TokenType.WAIT_FOR_CAPS_ON,
    "WAIT_FOR_CAPS_OFF": TokenType.WAIT_FOR_CAPS_OFF,
    "WAIT_FOR_CAPS_CHANGE": TokenType.WAIT_FOR_CAPS_CHANGE,
    "WAIT_FOR_NUM_ON": TokenType.WAIT_FOR_NUM_ON,
    "WAIT_FOR_NUM_OFF": TokenType.WAIT_FOR_NUM_OFF,
    "WAIT_FOR_NUM_CHANGE": TokenType.WAIT_FOR_NUM_CHANGE,
    "WAIT_FOR_SCROLL_ON": TokenType.WAIT_FOR_SCROLL_ON,
    "WAIT_FOR_SCROLL_OFF": TokenType.WAIT_FOR_SCROLL_OFF,
    "WAIT_FOR_SCROLL_CHANGE": TokenType.WAIT_FOR_SCROLL_CHANGE,
    "SAVE_HOST_KEYBOARD_LOCK_STATE": TokenType.SAVE_HOST_KEYBOARD_LOCK_STATE,
    "RESTORE_HOST_KEYBOARD_LOCK_STATE": TokenType.RESTORE_HOST_KEYBOARD_LOCK_STATE,
    # Random
    "RANDOM_CHAR": TokenType.RANDOM_CHAR,
    "RANDOM_LOWERCASE_LETTER": TokenType.RANDOM_LOWERCASE_LETTER,
    "RANDOM_UPPERCASE_LETTER": TokenType.RANDOM_UPPERCASE_LETTER,
    "RANDOM_LETTER": TokenType.RANDOM_LETTER,
    "RANDOM_NUMBER": TokenType.RANDOM_NUMBER,
    "RANDOM_SPECIAL": TokenType.RANDOM_SPECIAL,
    # File
    "HIDE_PAYLOAD": TokenType.HIDE_PAYLOAD,
    "RESTORE_PAYLOAD": TokenType.RESTORE_PAYLOAD,
    # Constants
    "TRUE": TokenType.TRUE,
    "FALSE": TokenType.FALSE,
    # Extension
    "BREAK": TokenType.BREAK,
    "CONTINUE": TokenType.CONTINUE,
    "EXTENSION": TokenType.EXTENSION,
    "END_EXTENSION": TokenType.END_EXTENSION,
    "DUCKY_LANG": TokenType.DUCKY_LANG,
    # Modifiers
    "CONTROL": TokenType.CONTROL,
    "CTRL": TokenType.CTRL,
    "SHIFT": TokenType.SHIFT,
    "ALT": TokenType.ALT,
    "GUI": TokenType.GUI,
    "WINDOWS": TokenType.WINDOWS,
    "COMMAND": TokenType.COMMAND,
    "OPTION": TokenType.OPTION,
    # Action keys
    "ENTER": TokenType.ENTER,
    "SPACE": TokenType.SPACE,
    "TAB": TokenType.TAB,
    "BACKSPACE": TokenType.BACKSPACE,
    "DELETE": TokenType.DELETE,
    "DEL": TokenType.DEL,
    "INSERT": TokenType.INSERT,
    "HOME": TokenType.HOME,
    "END": TokenType.END_KEY,
    "PAGEUP": TokenType.PAGEUP,
    "PAGEDOWN": TokenType.PAGEDOWN,
    "UP": TokenType.UP,
    "UPARROW": TokenType.UPARROW,
    "DOWN": TokenType.DOWN,
    "DOWNARROW": TokenType.DOWNARROW,
    "LEFT": TokenType.LEFT,
    "LEFTARROW": TokenType.LEFTARROW,
    "RIGHT": TokenType.RIGHT,
    "RIGHTARROW": TokenType.RIGHTARROW,
    "ESCAPE": TokenType.ESCAPE,
    "ESC": TokenType.ESC,
    "PRINTSCREEN": TokenType.PRINTSCREEN,
    "SCROLLLOCK": TokenType.SCROLLLOCK,
    "PAUSE": TokenType.PAUSE,
    "MENU": TokenType.MENU,
    "APP": TokenType.APP,
    "CAPSLOCK": TokenType.CAPSLOCK,
    "NUMLOCK": TokenType.NUMLOCK,
    "POWER": TokenType.POWER,
    "F1": TokenType.F1,
    "F2": TokenType.F2,
    "F3": TokenType.F3,
    "F4": TokenType.F4,
    "F5": TokenType.F5,
    "F6": TokenType.F6,
    "F7": TokenType.F7,
    "F8": TokenType.F8,
    "F9": TokenType.F9,
    "F10": TokenType.F10,
    "F11": TokenType.F11,
    "F12": TokenType.F12,
    "KP_SLASH": TokenType.KP_SLASH,
    "KP_ASTERISK": TokenType.KP_ASTERISK,
    "KP_MINUS": TokenType.KP_MINUS,
    "KP_PLUS": TokenType.KP_PLUS,
    "KP_ENTER": TokenType.KP_ENTER,
    "KP_0": TokenType.KP_0,
    "KP_1": TokenType.KP_1,
    "KP_2": TokenType.KP_2,
    "KP_3": TokenType.KP_3,
    "KP_4": TokenType.KP_4,
    "KP_5": TokenType.KP_5,
    "KP_6": TokenType.KP_6,
    "KP_7": TokenType.KP_7,
    "KP_8": TokenType.KP_8,
    "KP_9": TokenType.KP_9,
    "KP_DOT": TokenType.KP_DOT,
    "KP_EQUAL": TokenType.KP_EQUAL,
    "KP_COMMA": TokenType.KP_COMMA,
    "KP_00": TokenType.KP_00,
    "KP_000": TokenType.KP_000,
    "102ND": TokenType.KEY_102ND,
    "COMPOSE": TokenType.COMPOSE,
    "KPEQUAL": TokenType.KPEQUAL,
    "PROPS": TokenType.PROPS,
    "UNDO": TokenType.UNDO,
    "PASTE": TokenType.PASTE,
}


class DuckyLexer:
    """Tokenize DuckyScript 3 source text into a stream of Token objects."""

    # ── Public API ────────────────────────────────────────────────────────

    def tokenize(self, source: str) -> list[Token]:
        """Convert *source* to a list of tokens.

        Raises ``LexerError`` on invalid input.
        """
        tokens: list[Token] = []
        i = 0
        line = 1
        col = 1
        in_block_comment = False

        while i < len(source):
            ch = source[i]

            # 1. Block-comment mode — skip everything until END_REM
            if in_block_comment:
                if (
                    i + 7 <= len(source)
                    and source[i : i + 7].upper() == "END_REM"
                    and self._at_boundary(source, i + 7)
                ):
                    in_block_comment = False
                    i += 7
                    col += 7
                else:
                    # Skip to end of line
                    while i < len(source) and source[i] != "\n":
                        i += 1
                        col += 1
                    if i < len(source) and source[i] == "\n":
                        i += 1
                        line += 1
                        col = 1
                continue

            # 2. Newline
            if ch == "\n":
                self._check_line_length(line, col)
                tokens.append(Token(TokenType.NEWLINE, "\n", line, col))
                i += 1
                line += 1
                col = 1
                continue

            # 3. Whitespace (spaces, tabs, carriage returns)
            if ch in " \t\r":
                i += 1
                col += 1
                continue

            # 4. REM_BLOCK comment start
            if (
                i + 9 <= len(source)
                and source[i : i + 9].upper() == "REM_BLOCK"
                and self._at_boundary(source, i + 9)
            ):
                in_block_comment = True
                i += 9
                col += 9
                continue

            # 5. REM single-line comment
            if (
                i + 3 <= len(source)
                and source[i : i + 3].upper() == "REM"
                and self._at_boundary(source, i + 3)
            ):
                # Skip rest of line
                while i < len(source) and source[i] != "\n":
                    i += 1
                    col += 1
                continue

            # 6. // single-line comment
            if i + 2 <= len(source) and source[i : i + 2] == "//":
                while i < len(source) and source[i] != "\n":
                    i += 1
                    col += 1
                continue

            # 7. STRINGLN (checked before STRING because it's a longer match)
            if (
                i + 8 <= len(source)
                and source[i : i + 8].upper() == "STRINGLN"
                and self._at_boundary(source, i + 8)
            ):
                tokens.append(Token(TokenType.STRINGLN, "STRINGLN", line, col))
                i += 8
                col += 8
                # Strip leading spaces
                while i < len(source) and source[i] == " ":
                    i += 1
                    col += 1
                body_start = i
                body_col = col
                while i < len(source) and source[i] != "\n":
                    i += 1
                    col += 1
                body = source[body_start:i].rstrip(" ")
                if body:
                    tokens.append(Token(TokenType.STRING_BODY, body, line, body_col))
                continue

            # 8. STRING
            if (
                i + 6 <= len(source)
                and source[i : i + 6].upper() == "STRING"
                and self._at_boundary(source, i + 6)
            ):
                tokens.append(Token(TokenType.STRING, "STRING", line, col))
                i += 6
                col += 6
                # Strip leading spaces
                while i < len(source) and source[i] == " ":
                    i += 1
                    col += 1
                body_start = i
                body_col = col
                while i < len(source) and source[i] != "\n":
                    i += 1
                    col += 1
                body = source[body_start:i].rstrip(" ")
                if body:
                    tokens.append(Token(TokenType.STRING_BODY, body, line, body_col))
                continue

            # 9. ATTACKMODE — remaining tokens on line are ATTACKMODE_PARAM
            if (
                i + 10 <= len(source)
                and source[i : i + 10].upper() == "ATTACKMODE"
                and self._at_boundary(source, i + 10)
            ):
                tokens.append(Token(TokenType.ATTACKMODE, "ATTACKMODE", line, col))
                i += 10
                col += 10
                while i < len(source) and source[i] != "\n":
                    if source[i] in " \t":
                        i += 1
                        col += 1
                        continue
                    param_start = i
                    param_col = col
                    while i < len(source) and source[i] not in " \t\n":
                        i += 1
                        col += 1
                    param = source[param_start:i]
                    tokens.append(
                        Token(TokenType.ATTACKMODE_PARAM, param, line, param_col)
                    )
                continue

            # 10. General token (operators, identifiers, literals, etc.)
            new_tokens, new_i = self._scan_token(source, i, line, col)
            tokens.extend(new_tokens)
            consumed = new_i - i
            i = new_i
            col += consumed

        # ── End of input ──────────────────────────────────────────────────
        if in_block_comment:
            raise LexerError("Unterminated REM_BLOCK", line, col)

        self._check_line_length(line, col)

        # Every logical line ends with NEWLINE in DuckyScript
        if tokens and tokens[-1].type != TokenType.NEWLINE:
            tokens.append(Token(TokenType.NEWLINE, "\n", line, col))

        tokens.append(Token(TokenType.EOF, "", line, col))
        return tokens

    # ── Helpers ───────────────────────────────────────────────────────────

    @staticmethod
    def _at_boundary(source: str, pos: int) -> bool:
        """Return True if *pos* is at a token boundary.

        A position is a boundary if it is past the end of the source or
        the character at *pos* is not alphanumeric / underscore.
        """
        if pos >= len(source):
            return True
        ch = source[pos]
        return not ((ch.isalpha() or ch.isdigit()) or ch == "_")

    @staticmethod
    def _check_line_length(line: int, col: int) -> None:
        """Raise ``LexerError`` if the current line exceeds 256 characters."""
        if col > 257:
            raise LexerError("Line exceeds 256 characters", line, 257)

    # ── Token scanning ────────────────────────────────────────────────────

    def _scan_token(
        self, source: str, i: int, line: int, col: int
    ) -> tuple[list[Token], int]:
        """Read the next token(s) starting at position *i*.

        Returns ``(tokens, new_i)`` where *new_i* is the position after the
        consumed characters.
        """
        ch = source[i]

        # Multi-character operators (longest match first)
        if ch in "<>!=&|":
            two = source[i : i + 2]
            multi_map = {
                "<=": TokenType.LE,
                ">=": TokenType.GE,
                "==": TokenType.EQ,
                "!=": TokenType.NE,
                "<<": TokenType.LSHIFT,
                ">>": TokenType.RSHIFT,
                "&&": TokenType.AND,
                "||": TokenType.OR,
            }
            if two in multi_map:
                return ([Token(multi_map[two], two, line, col)], i + 2)

        # Single-character operators and punctuation
        single_map: dict[str, TokenType] = {
            "+": TokenType.PLUS,
            "-": TokenType.MINUS,
            "*": TokenType.STAR,
            "/": TokenType.SLASH,
            "%": TokenType.PERCENT,
            "^": TokenType.CARET,
            "!": TokenType.BANG,
            "&": TokenType.AMPERSAND,
            "|": TokenType.PIPE,
            "<": TokenType.LT,
            ">": TokenType.GT,
            "=": TokenType.ASSIGN,
            "(": TokenType.LPAREN,
            ")": TokenType.RPAREN,
            ",": TokenType.COMMA,
        }
        if ch in single_map:
            return ([Token(single_map[ch], ch, line, col)], i + 1)

        # Quoted string literal
        if ch == '"':
            return self._scan_string(source, i, line, col)

        # $ identifier
        if ch == "$":
            return self._scan_dollar(source, i, line, col)

        # # identifier
        if ch == "#":
            return self._scan_hash(source, i, line, col)

        # Word (keyword, identifier, integer)
        if (ch.isalpha() or ch.isdigit()) or ch == "_":
            return self._scan_word(source, i, line, col)

        # Nothing matched — illegal character
        raise LexerError(f"Illegal character 0x{ord(ch):02X}", line, col)

    def _scan_string(
        self, source: str, i: int, line: int, col: int
    ) -> tuple[list[Token], int]:
        """Scan a ``"..."`` string literal with escape-sequence resolution."""
        quote_col = col
        i += 1  # skip opening "
        chars: list[str] = []

        while i < len(source):
            ch = source[i]
            if ch == '"':
                i += 1  # skip closing "
                value = "".join(chars)
                return ([Token(TokenType.STRING_LITERAL, value, line, quote_col)], i)
            if ch == "\n":
                break  # unterminated
            if ch == "\\" and i + 1 < len(source):
                esc = source[i + 1]
                if esc == "\\":
                    chars.append("\\")
                    i += 2
                elif esc == '"':
                    chars.append('"')
                    i += 2
                elif esc == "n":
                    chars.append("\n")
                    i += 2
                elif esc == "r":
                    chars.append("\r")
                    i += 2
                elif esc == "t":
                    chars.append("\t")
                    i += 2
                elif esc == "x" and i + 3 < len(source):
                    hex_str = source[i + 2 : i + 4]
                    try:
                        chars.append(chr(int(hex_str, 16)))
                    except ValueError:
                        chars.append("\\x" + hex_str)
                    i += 4
                else:
                    # Unrecognised escape — keep the character as-is
                    chars.append(ch)
                    i += 1
            else:
                chars.append(ch)
                i += 1

        raise LexerError("Unterminated string literal", line, quote_col)

    def _scan_dollar(
        self, source: str, i: int, line: int, col: int
    ) -> tuple[list[Token], int]:
        """Scan a ``$identifier``."""
        i += 1  # skip $
        if i >= len(source) or not (source[i].isalpha() or source[i] == "_"):
            raise LexerError("Invalid $ identifier", line, col)
        start = i
        while i < len(source) and (
            source[i].isalpha() or source[i].isdigit() or source[i] == "_"
        ):
            i += 1
        name = source[start:i]
        return ([Token(TokenType.DOLLAR_IDENTIFIER, name, line, col)], i)

    def _scan_hash(
        self, source: str, i: int, line: int, col: int
    ) -> tuple[list[Token], int]:
        """Scan a ``#identifier`` (DEFINE constant reference)."""
        i += 1  # skip #
        if i >= len(source) or not (source[i].isalpha() or source[i] == "_"):
            raise LexerError("Invalid # identifier", line, col)
        start = i
        while i < len(source) and (
            source[i].isalpha() or source[i].isdigit() or source[i] == "_"
        ):
            i += 1
        name = source[start:i]
        return ([Token(TokenType.HASH_IDENTIFIER, name, line, col)], i)

    def _scan_word(
        self, source: str, i: int, line: int, col: int
    ) -> tuple[list[Token], int]:
        """Scan a word: keyword, identifier, integer, or ``name()`` call."""
        start = i
        while i < len(source) and (
            source[i].isalpha() or source[i].isdigit() or source[i] == "_"
        ):
            i += 1
        word = source[start:i]
        word_upper = word.upper()

        # 1. Keyword match (case-insensitive)
        if word_upper in _KEYWORDS:
            return ([Token(_KEYWORDS[word_upper], word, line, col)], i)

        # 2. Function-call pattern: name() — no whitespace between
        if (
            i + 2 <= len(source)
            and source[i] == "("
            and source[i + 1] == ")"
        ):
            id_token = Token(TokenType.IDENTIFIER, word, line, col)
            lparen = Token(TokenType.LPAREN, "(", line, col + len(word))
            rparen = Token(TokenType.RPAREN, ")", line, col + len(word) + 1)
            return ([id_token, lparen, rparen], i + 2)

        # 3. Integer literal
        if self._is_integer(word):
            return ([Token(TokenType.INTEGER, word, line, col)], i)

        # 4. Plain identifier
        return ([Token(TokenType.IDENTIFIER, word, line, col)], i)

    @staticmethod
    def _is_integer(word: str) -> bool:
        """Return True if *word* is a decimal or hex integer literal."""
        if not word:
            return False
        if word.startswith("0x") or word.startswith("0X"):
            if len(word) == 2:
                return False
            return all(c in "0123456789abcdefABCDEF" for c in word[2:])
        return all(c in "0123456789" for c in word)
