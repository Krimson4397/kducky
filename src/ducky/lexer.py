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
    "END_STRING": TokenType.END_STRING,
    "END_STRINGLN": TokenType.END_STRINGLN,
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
    # D3 extensions
    "REBOOT": TokenType.REBOOT,
    "REPLAY": TokenType.REPLAY,
    "JITTER": TokenType.JITTER,
    "INJECT_VAR": TokenType.INJECT_VAR,
    "EXFIL": TokenType.EXFIL,
    "ON": TokenType.ON,
    "OFF": TokenType.OFF,
    # Mouse
    "MOUSE_MOVE": TokenType.MOUSE_MOVE,
    "MOUSE_MOVE_TO": TokenType.MOUSE_MOVE_TO,
    "MOUSE_CLICK": TokenType.MOUSE_CLICK,
    "MOUSE_DOWN": TokenType.MOUSE_DOWN,
    "MOUSE_UP": TokenType.MOUSE_UP,
    "MOUSE_SCROLL": TokenType.MOUSE_SCROLL,
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
    "F13": TokenType.F13,
    "F14": TokenType.F14,
    "F15": TokenType.F15,
    "F16": TokenType.F16,
    "F17": TokenType.F17,
    "F18": TokenType.F18,
    "F19": TokenType.F19,
    "F20": TokenType.F20,
    "F21": TokenType.F21,
    "F22": TokenType.F22,
    "F23": TokenType.F23,
    "F24": TokenType.F24,
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
    # Media keys (project extension)
    "VOLUME_UP": TokenType.VOLUME_UP,
    "VOLUME_DOWN": TokenType.VOLUME_DOWN,
    "MUTE": TokenType.MUTE,
    "PLAY_PAUSE": TokenType.PLAY_PAUSE,
    "STOP": TokenType.STOP,
    "NEXT_TRACK": TokenType.NEXT_TRACK,
    "PREV_TRACK": TokenType.PREV_TRACK,
}

# STRING / STRINGLN and their embedded-language block aliases.
#
# STRING_POWERSHELL, STRING_BATCH, STRING_BASH, STRING_JAVASCRIPT,
# STRING_PYTHON, STRING_RUBY, STRING_HTML (and the STRINGLN_* variants)
# are NOT separate runtime commands — they are the block forms of
# STRING/STRINGLN with editor language modes.  Each alias tokenizes as
# its base keyword and closes with END_STRING (STRING_*) or
# END_STRINGLN (STRINGLN_*).
_STRING_KEYWORDS: tuple[tuple[str, bool], ...] = (
    ("STRINGLN_POWERSHELL", True),
    ("STRINGLN_BATCH", True),
    ("STRINGLN_BASH", True),
    ("STRINGLN_JAVASCRIPT", True),
    ("STRINGLN_PYTHON", True),
    ("STRINGLN_RUBY", True),
    ("STRINGLN_HTML", True),
    ("STRING_POWERSHELL", False),
    ("STRING_BATCH", False),
    ("STRING_BASH", False),
    ("STRING_JAVASCRIPT", False),
    ("STRING_PYTHON", False),
    ("STRING_RUBY", False),
    ("STRING_HTML", False),
    ("STRINGLN", True),
    ("STRING", False),
)


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
                # Skip leading whitespace before checking for END_REM
                while i < len(source) and source[i] in " \t\r":
                    i += 1
                    col += 1
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

            # 7. STRING / STRINGLN and their embedded-language aliases.
            #    STRING_* / STRINGLN_* behave exactly like their base
            #    keyword: inline body or END_STRING / END_STRINGLN block.
            if ch in "sS":
                _result = self._scan_string_statement(source, i, line, col)
                if _result is not None:
                    _new_tokens, i, line, col = _result
                    tokens.extend(_new_tokens)
                    continue

            # 8. ATTACKMODE — remaining tokens on line are ATTACKMODE_PARAM
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

            # 9. General token (operators, identifiers, literals, etc.)
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
        """Raise ``LexerError`` if the current line exceeds 1024 characters."""
        if col > 1025:
            raise LexerError("Line exceeds 1024 characters", line, 1025)

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

    def _scan_string_statement(
        self, source: str, i: int, line: int, col: int
    ) -> tuple[list[Token], int, int, int] | None:
        """Scan a STRING/STRINGLN statement or one of their aliases.

        Tries every ``_STRING_KEYWORDS`` entry (embedded-language aliases
        first, then the base keywords) and returns ``(tokens, i, line, col)``
        on the first match, else ``None``.
        """
        # Quick prefix gate: only words beginning with STRING/STRINGLN
        # (case-insensitive) can be string keywords.  This avoids slicing
        # and uppercasing all 16 candidates for every word that starts
        # with 's'.  Each candidate still applies its own boundary check,
        # so STRING_POWERSHELL2 continues to lex as a plain identifier.
        if not source[i : i + 8].upper().startswith("STRING"):
            return None
        for keyword, is_ln in _STRING_KEYWORDS:
            result = self._scan_string_keyword(
                source, i, line, col, keyword, is_ln
            )
            if result is not None:
                return result
        return None

    def _scan_string_keyword(
        self, source: str, i: int, line: int, col: int,
        keyword: str, is_ln: bool,
    ) -> tuple[list[Token], int, int, int] | None:
        """Scan one STRING-style keyword at position *i*.

        Handles inline bodies and END_STRING / END_STRINGLN block mode
        identically for STRING, STRINGLN, and the STRING_* / STRINGLN_*
        aliases.  Returns ``(tokens, i, line, col)`` if *keyword* matches,
        else ``None``.
        """
        kw_len = len(keyword)
        if not (
            i + kw_len <= len(source)
            and source[i : i + kw_len].upper() == keyword
            and self._at_boundary(source, i + kw_len)
        ):
            return None

        tokens: list[Token] = []
        token_type = TokenType.STRINGLN if is_ln else TokenType.STRING
        tokens.append(Token(token_type, keyword, line, col))
        i += kw_len
        col += kw_len

        # Strip leading spaces (inline body per spec §1.10)
        while i < len(source) and source[i] == " ":
            i += 1
            col += 1
        body_start = i
        body_col = col
        while i < len(source) and source[i] != "\n":
            i += 1
            col += 1
        body = source[body_start:i].rstrip(" ")

        if not body:
            # Block mode — keyword was on a line by itself
            if i < len(source) and source[i] == "\n":
                i += 1
                line += 1
                col = 1
            end_keyword = "END_STRINGLN" if is_ln else "END_STRING"
            end_keyword_len = len(end_keyword)
            block_lines: list[str] = []
            body_line_col = col
            nl_line = line
            nl_col = col
            while i < len(source):
                line_start = i
                # Skip leading whitespace to check for end marker
                while i < len(source) and source[i] in " \t":
                    i += 1
                if (
                    i + end_keyword_len <= len(source)
                    and source[i : i + end_keyword_len].upper() == end_keyword
                    and self._at_boundary(source, i + end_keyword_len)
                ):
                    # Consume rest of END_STRING(LN) line
                    while i < len(source) and source[i] != "\n":
                        i += 1
                    nl_line = line
                    nl_col = col
                    if i < len(source) and source[i] == "\n":
                        i += 1
                        line += 1
                        col = 1
                    break
                # Not the expected terminator — but a mismatched
                # STRING/STRINGLN terminator is an error, not body text.
                # END_STRINGLN starts with END_STRING, so probe the
                # longer token first.
                other = "END_STRINGLN" if not is_ln else "END_STRING"
                if (
                    i + len(other) <= len(source)
                    and source[i : i + len(other)].upper() == other
                    and self._at_boundary(source, i + len(other))
                ):
                    raise LexerError(
                        f"Mismatched block terminator: found {other} "
                        f"while scanning a "
                        f"{'STRINGLN' if is_ln else 'STRING'} block",
                        line,
                        col + (i - line_start),
                    )
                # Not an end marker — reset and collect full line
                i = line_start
                while i < len(source) and source[i] != "\n":
                    i += 1
                    col += 1
                raw_line = source[line_start:i]
                if is_ln:
                    # STRINGLN strips only a single leading tab per line;
                    # all other formatting and whitespace is preserved.
                    if raw_line.startswith("\t"):
                        raw_line = raw_line[1:]
                    block_lines.append(raw_line)
                else:
                    # STRING strips leading whitespace and joins lines.
                    block_lines.append(raw_line.lstrip())
                if i < len(source) and source[i] == "\n":
                    i += 1
                    line += 1
                    col = 1
            separator = "\n" if is_ln else ""
            combined = separator.join(block_lines)
            if combined:
                tokens.append(
                    Token(TokenType.STRING_BODY, combined, line, body_line_col)
                )
            if nl_line is not None:
                tokens.append(Token(TokenType.NEWLINE, "\n", nl_line, nl_col))
            return (tokens, i, line, col)

        # Inline mode
        if body:
            tokens.append(Token(TokenType.STRING_BODY, body, line, body_col))
        return (tokens, i, line, col)

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
