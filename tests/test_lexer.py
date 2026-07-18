"""Tests for the DuckyScript 3 lexer.

Covers every tokenization rule from the Engineering Spec §3.2.
"""

from __future__ import annotations

import pytest

from ducky.lexer import DuckyLexer, LexerError
from ducky.tokens import Token, TokenType

# ── Helpers ────────────────────────────────────────────────────────────────


def tok(type_: TokenType, value: str, line: int = 1, col: int = 1) -> Token:
    """Shorthand to build a Token for assertions."""
    return Token(type_, value, line, col)


LEX = DuckyLexer()


def tokenize(source: str) -> list[Token]:
    """Shorthand to tokenize a source string."""
    return LEX.tokenize(source)


def types(result: list[Token]) -> list[TokenType]:
    """Extract just the token types from a result list."""
    return [t.type for t in result]


# ── Tests ──────────────────────────────────────────────────────────────────


class TestStringStatements:
    """STRING / STRINGLN body capture."""

    def test_string_with_body(self) -> None:
        """STRING hello world → STRING + STRING_BODY("hello world") + NEWLINE"""
        result = tokenize("STRING hello world")
        assert result[0] == tok(TokenType.STRING, "STRING")
        assert result[1] == tok(TokenType.STRING_BODY, "hello world", col=8)
        assert result[2].type is TokenType.NEWLINE
        assert result[3].type is TokenType.EOF

    def test_string_leading_spaces_stripped(self) -> None:
        """Multiple leading spaces after STRING keyword are stripped."""
        result = tokenize("STRING    hello")
        # STRING (6 chars) + 4 spaces + hello (5 chars) = 15 chars
        assert result[0] == tok(TokenType.STRING, "STRING")
        # After STRING (col=7), strip 4 spaces → body starts at col=11
        assert result[1] == tok(TokenType.STRING_BODY, "hello", col=11)
        assert result[2].type is TokenType.NEWLINE
        assert result[2].column == 16  # 15 chars + 1 for NEWLINE

    def test_string_trailing_spaces_omitted(self) -> None:
        """Trailing spaces in the body are stripped."""
        result = tokenize("STRING hello   ")
        assert result[1] == tok(TokenType.STRING_BODY, "hello", col=8)

    def test_string_ln_with_body(self) -> None:
        """STRINGLN hello → STRINGLN + STRING_BODY("hello") + NEWLINE"""
        result = tokenize("STRINGLN hello")
        assert result[0] == tok(TokenType.STRINGLN, "STRINGLN")
        assert result[1] == tok(TokenType.STRING_BODY, "hello", col=10)
        assert result[2].type is TokenType.NEWLINE
        assert result[3].type is TokenType.EOF

    def test_string_ln_without_body(self) -> None:
        """STRINGLN with no body → just STRINGLN + NEWLINE (no STRING_BODY)."""
        result = tokenize("STRINGLN")
        assert result[0] == tok(TokenType.STRINGLN, "STRINGLN")
        assert result[1].type is TokenType.NEWLINE
        assert result[1].column == 9
        assert result[2].type is TokenType.EOF

    def test_string_ln_only_spaces(self) -> None:
        """STRINGLN with only spaces after → no body (all spaces stripped)."""
        result = tokenize("STRINGLN   ")
        assert result[0] == tok(TokenType.STRINGLN, "STRINGLN")
        assert result[1].type is TokenType.NEWLINE
        assert not any(t.type == TokenType.STRING_BODY for t in result)


class TestComments:
    """Comment stripping — REM, //, REM_BLOCK."""

    def test_rem_comment(self) -> None:
        """REM with text → only NEWLINE (REM and text produce no tokens)."""
        result = tokenize("REM this is a comment\n")
        assert types(result) == [TokenType.NEWLINE, TokenType.EOF]

    def test_rem_keyword_only(self) -> None:
        """REM with no text → only NEWLINE."""
        result = tokenize("REM\n")
        assert types(result) == [TokenType.NEWLINE, TokenType.EOF]

    def test_slash_comment(self) -> None:
        """// with text → only NEWLINE."""
        result = tokenize("// this is a comment\n")
        assert types(result) == [TokenType.NEWLINE, TokenType.EOF]

    def test_block_comment(self) -> None:
        """REM_BLOCK ... END_REM → no tokens; content after resumes."""
        source = "REM_BLOCK\nsome stuff\nEND_REM\nDELAY 100"
        result = tokenize(source)
        # The block comment content produces no tokens.
        # After END_REM, line 4: DELAY 100
        assert types(result) == [
            TokenType.NEWLINE,  # \n after END_REM
            TokenType.DELAY,
            TokenType.INTEGER,
            TokenType.NEWLINE,  # final NEWLINE
            TokenType.EOF,
        ]
        assert result[1].line == 4
        assert result[1].column == 1

    def test_block_comment_no_tokens_at_all(self) -> None:
        """Content inside REM_BLOCK … END_REM produces no visible tokens."""
        # With trailing newline after END_REM:
        source = "REM_BLOCK\n// hello\nREM more\nEND_REM\nDELAY 100"
        result = tokenize(source)
        # Inside REM_BLOCK produces nothing; DELAY 100 follows END_REM
        assert types(result) == [
            TokenType.NEWLINE,  # after END_REM
            TokenType.DELAY,
            TokenType.INTEGER,
            TokenType.NEWLINE,  # final NEWLINE
            TokenType.EOF,
        ]

    def test_rem_word_boundary(self) -> None:
        """REMOTE is NOT a REM comment — tokenizes as IDENTIFIER."""
        result = tokenize("REMOTE")
        assert result[0].type is TokenType.IDENTIFIER
        assert result[0].value == "REMOTE"


class TestKeywordsAndCommands:
    """Keyword recognition and command statements."""

    def test_delay_integer(self) -> None:
        """DELAY 2000 → DELAY + INTEGER("2000") + NEWLINE."""
        result = tokenize("DELAY 2000")
        assert result[0] == tok(TokenType.DELAY, "DELAY")
        assert result[1] == tok(TokenType.INTEGER, "2000", col=7)
        assert result[2].type is TokenType.NEWLINE
        assert result[3].type is TokenType.EOF

    def test_var_declaration(self) -> None:
        """VAR $x = (5 + 3) → full expression tokenization."""
        result = tokenize("VAR $x = (5 + 3)")
        assert result[0] == tok(TokenType.VAR, "VAR")
        assert result[1] == tok(TokenType.DOLLAR_IDENTIFIER, "x", col=5)
        assert result[2] == tok(TokenType.ASSIGN, "=", col=8)
        assert result[3] == tok(TokenType.LPAREN, "(", col=10)
        assert result[4] == tok(TokenType.INTEGER, "5", col=11)
        assert result[5] == tok(TokenType.PLUS, "+", col=13)
        assert result[6] == tok(TokenType.INTEGER, "3", col=15)
        assert result[7] == tok(TokenType.RPAREN, ")", col=16)
        assert result[8].type is TokenType.NEWLINE
        assert result[9].type is TokenType.EOF

    def test_modifier_combo(self) -> None:
        """CTRL ALT DEL → modifier + modifier + action key + NEWLINE."""
        result = tokenize("CTRL ALT DEL")
        assert types(result[:4]) == [
            TokenType.CTRL, TokenType.ALT, TokenType.DEL, TokenType.NEWLINE
        ]

    def test_function_definition(self) -> None:
        """FUNCTION myFunc() → FUNCTION + IDENTIFIER + LPAREN + RPAREN + NEWLINE."""
        result = tokenize("FUNCTION myFunc()")
        assert result[0] == tok(TokenType.FUNCTION, "FUNCTION")
        assert result[1] == tok(TokenType.IDENTIFIER, "myFunc", col=10)
        assert result[2] == tok(TokenType.LPAREN, "(", col=16)
        assert result[3] == tok(TokenType.RPAREN, ")", col=17)
        assert result[4].type is TokenType.NEWLINE
        assert result[5].type is TokenType.EOF

    def test_enter_alone(self) -> None:
        """ENTER alone → ENTER + NEWLINE."""
        result = tokenize("ENTER")
        assert types(result[:2]) == [TokenType.ENTER, TokenType.NEWLINE]

    def test_case_insensitivity(self) -> None:
        """Keywords are case-insensitive — "string Hello" works like "STRING Hello"."""
        for source in ("string Hello", "STRING Hello", "StRiNg Hello"):
            result = tokenize(source)
            assert result[0].type is TokenType.STRING
            assert result[1] == tok(TokenType.STRING_BODY, "Hello", col=8)

    def test_return_keyword(self) -> None:
        """RETURN keyword (function return) is recognised."""
        result = tokenize("RETURN")
        assert result[0].type is TokenType.RETURN
        assert result[0].value == "RETURN"

    def test_break_keyword(self) -> None:
        """BREAK keyword is recognised (loop control / action key)."""
        result = tokenize("BREAK")
        assert result[0].type is TokenType.BREAK
        assert result[0].value == "BREAK"


class TestLiterals:
    """Integer and string literal tokenization."""

    def test_integer_decimal(self) -> None:
        result = tokenize("42")
        assert result[0] == tok(TokenType.INTEGER, "42")

    def test_integer_hex(self) -> None:
        result = tokenize("0xFF")
        assert result[0] == tok(TokenType.INTEGER, "0xFF")

    def test_integer_hex_lowercase(self) -> None:
        result = tokenize("0xff")
        assert result[0] == tok(TokenType.INTEGER, "0xff")

    def test_quoted_string(self) -> None:
        """Quoted string with escape sequences."""
        result = tokenize('"hello\\nworld"')
        assert result[0] == tok(TokenType.STRING_LITERAL, "hello\nworld")

    def test_quoted_string_escaped_quote(self) -> None:
        result = tokenize('"she said \\"hi\\""')
        assert result[0] == tok(TokenType.STRING_LITERAL, 'she said "hi"')

    def test_quoted_string_hex_escape(self) -> None:
        result = tokenize('"\\x41\\x42"')
        assert result[0] == tok(TokenType.STRING_LITERAL, "AB")

    def test_quoted_string_empty(self) -> None:
        result = tokenize('""')
        assert result[0] == tok(TokenType.STRING_LITERAL, "")


class TestOperators:
    """All operator token types."""

    def test_multi_char_operators(self) -> None:
        cases = [
            ("<=", TokenType.LE),
            (">=", TokenType.GE),
            ("==", TokenType.EQ),
            ("!=", TokenType.NE),
            ("<<", TokenType.LSHIFT),
            (">>", TokenType.RSHIFT),
            ("&&", TokenType.AND),
            ("||", TokenType.OR),
        ]
        for op_text, expected_type in cases:
            result = tokenize(op_text)
            assert result[0].type is expected_type, (
                f"Expected {expected_type} for {op_text!r}, got {result[0].type}"
            )
            assert result[0].value == op_text

    def test_single_char_operators(self) -> None:
        cases = [
            ("+", TokenType.PLUS),
            ("-", TokenType.MINUS),
            ("*", TokenType.STAR),
            ("/", TokenType.SLASH),
            ("%", TokenType.PERCENT),
            ("^", TokenType.CARET),
            ("!", TokenType.BANG),
            ("&", TokenType.AMPERSAND),
            ("|", TokenType.PIPE),
            ("<", TokenType.LT),
            (">", TokenType.GT),
            ("=", TokenType.ASSIGN),
        ]
        for op_text, expected_type in cases:
            result = tokenize(op_text)
            assert result[0].type is expected_type, (
                f"Expected {expected_type} for {op_text!r}, got {result[0].type}"
            )
            assert result[0].value == op_text


class TestPunctuation:
    """Parentheses and comma."""

    def test_parens(self) -> None:
        result = tokenize("()")
        assert result[0].type is TokenType.LPAREN
        assert result[1].type is TokenType.RPAREN

    def test_comma(self) -> None:
        result = tokenize(",")
        assert result[0].type is TokenType.COMMA


class TestIdentifiers:
    """Identifier tokenization ($, #, and plain)."""

    def test_dollar_identifier(self) -> None:
        result = tokenize("$myVar")
        assert result[0] == tok(TokenType.DOLLAR_IDENTIFIER, "myVar")

    def test_hash_identifier(self) -> None:
        result = tokenize("#MY_CONST")
        assert result[0] == tok(TokenType.HASH_IDENTIFIER, "MY_CONST")

    def test_plain_identifier(self) -> None:
        result = tokenize("someVar")
        assert result[0] == tok(TokenType.IDENTIFIER, "someVar")

    def test_function_call_pattern(self) -> None:
        """name() with no whitespace → IDENTIFIER + LPAREN + RPAREN."""
        result = tokenize("myFunc()")
        assert result[0] == tok(TokenType.IDENTIFIER, "myFunc")
        assert result[1] == tok(TokenType.LPAREN, "(", col=7)
        assert result[2] == tok(TokenType.RPAREN, ")", col=8)

    def test_function_call_with_whitespace(self) -> None:
        """name () → IDENTIFIER, then separate LPAREN/RPAREN tokens."""
        result = tokenize("myFunc ()")
        assert result[0] == tok(TokenType.IDENTIFIER, "myFunc")
        assert result[1].type is TokenType.LPAREN
        assert result[2].type is TokenType.RPAREN


class TestAttackMode:
    """ATTACKMODE parameter parsing."""

    def test_attackmode_with_params(self) -> None:
        result = tokenize("ATTACKMODE HID STORAGE VID_05AC")
        assert result[0] == tok(TokenType.ATTACKMODE, "ATTACKMODE")
        # ATTACKMODE = 10 chars → col=11, then space consumed → col=12
        assert result[1] == tok(TokenType.ATTACKMODE_PARAM, "HID", col=12)
        # After "HID " (col 15), STORAGE starts at 16
        assert result[2] == tok(TokenType.ATTACKMODE_PARAM, "STORAGE", col=16)
        # After "STORAGE " (col 23), VID_05AC starts at 24
        assert result[3] == tok(TokenType.ATTACKMODE_PARAM, "VID_05AC", col=24)
        assert result[4].type is TokenType.NEWLINE

    def test_attackmode_off(self) -> None:
        result = tokenize("ATTACKMODE OFF")
        assert result[0].type is TokenType.ATTACKMODE
        # ATTACKMODE = 10 chars → col=11, space consumed → col=12
        assert result[1] == tok(TokenType.ATTACKMODE_PARAM, "OFF", col=12)


class TestNewlinesAndBlankLines:
    """Newline and blank-line handling."""

    def test_multiple_newlines(self) -> None:
        """Multiple blank lines produce a NEWLINE per line."""
        result = tokenize("a\n\n\nb")
        assert types(result) == [
            TokenType.IDENTIFIER,
            TokenType.NEWLINE,
            TokenType.NEWLINE,
            TokenType.NEWLINE,
            TokenType.IDENTIFIER,
            TokenType.NEWLINE,
            TokenType.EOF,
        ]
        # Verify line numbers — EOF sits at same line as last content
        assert result[0].line == 1  # a
        assert result[1].line == 1  # \n after a
        assert result[2].line == 2  # blank line
        assert result[3].line == 3  # blank line
        assert result[4].line == 4  # b
        assert result[5].line == 4  # NEWLINE (virtual, after b)
        assert result[6].line == 4  # EOF (same line, after NEWLINE)

    def test_blank_lines_only(self) -> None:
        """Input with only blank lines → NEWLINE tokens + EOF."""
        result = tokenize("\n\n")
        assert types(result) == [TokenType.NEWLINE, TokenType.NEWLINE, TokenType.EOF]

    def test_empty_input(self) -> None:
        """Empty input → just EOF."""
        result = tokenize("")
        assert result == [tok(TokenType.EOF, "", line=1, col=1)]

    def test_no_trailing_newline(self) -> None:
        """Input without trailing newline still gets a NEWLINE token before EOF."""
        result = tokenize("DELAY 100")
        assert any(t.type == TokenType.NEWLINE for t in result)


class TestErrors:
    """Lexer error conditions."""

    def test_line_too_long(self) -> None:
        """Line exceeding 256 characters raises LexerError at column 257."""
        source = "x" * 257 + "\n"
        with pytest.raises(LexerError) as exc:
            tokenize(source)
        assert "exceeds 256" in str(exc.value)
        assert exc.value.line == 1
        assert exc.value.column == 257

    def test_unterminated_string(self) -> None:
        """Unterminated " string raises LexerError."""
        source = '"hello'
        with pytest.raises(LexerError) as exc:
            tokenize(source)
        assert "Unterminated" in str(exc.value)

    def test_illegal_character(self) -> None:
        """Non-ASCII byte outside valid range raises LexerError."""
        source = "DELAY \x80"
        with pytest.raises(LexerError) as exc:
            tokenize(source)
        assert "Illegal character" in str(exc.value)
        assert "0x80" in str(exc.value)

    def test_invalid_dollar_identifier(self) -> None:
        """$ without following identifier chars raises LexerError."""
        with pytest.raises(LexerError) as exc:
            tokenize("$")
        assert "Invalid $" in str(exc.value)

    def test_invalid_hash_identifier(self) -> None:
        """# without following identifier chars raises LexerError."""
        with pytest.raises(LexerError) as exc:
            tokenize("#")
        assert "Invalid #" in str(exc.value)

    def test_unterminated_block_comment(self) -> None:
        """REM_BLOCK without END_REM raises LexerError."""
        source = "REM_BLOCK\nstuff"
        with pytest.raises(LexerError) as exc:
            tokenize(source)
        assert "Unterminated REM_BLOCK" in str(exc.value)


class TestEdgeCases:
    """Edge cases and real-world patterns."""

    def test_whitespace_handling(self) -> None:
        """Leading/trailing whitespace is ignored."""
        result = tokenize("  DELAY  100  ")
        # First DELAY token should be at column 3 (after 2 leading spaces)
        assert result[0] == tok(TokenType.DELAY, "DELAY", col=3)
        assert result[1] == tok(TokenType.INTEGER, "100", col=10)
        assert result[2].type is TokenType.NEWLINE

    def test_tabs_as_whitespace(self) -> None:
        """Tabs are treated as whitespace."""
        result = tokenize("\tDELAY\t100")
        assert result[0] == tok(TokenType.DELAY, "DELAY", col=2)
        assert result[1] == tok(TokenType.INTEGER, "100", col=8)

    def test_carriage_return_ignored(self) -> None:
        """\\r is treated as whitespace (ignored)."""
        result = tokenize("DELAY\r100")
        assert result[0] == tok(TokenType.DELAY, "DELAY")
        assert result[1] == tok(TokenType.INTEGER, "100", col=7)

    def test_keyword_not_consumed_by_prefix_check(self) -> None:
        """'STRINGER' should not match STRING keyword."""
        result = tokenize("STRINGER")
        assert result[0].type is TokenType.IDENTIFIER
        assert result[0].value == "STRINGER"

    def test_define_preprocessor(self) -> None:
        """DEFINE #NAME pattern."""
        result = tokenize("DEFINE #DELAY 2000")
        assert result[0] == tok(TokenType.DEFINE, "DEFINE")
        assert result[1] == tok(TokenType.HASH_IDENTIFIER, "DELAY", col=8)
        # After DEFINE(6) + space(7) + #DELAY(8-13) + space(14) → "2000" at col 15
        assert result[2] == tok(TokenType.INTEGER, "2000", col=15)

    def test_mixed_operators_in_expression(self) -> None:
        """Multiple operators in one expression tokenise correctly."""
        result = tokenize("$x = $y + 1")
        assert result[0] == tok(TokenType.DOLLAR_IDENTIFIER, "x")
        assert result[1] == tok(TokenType.ASSIGN, "=", col=4)
        assert result[2] == tok(TokenType.DOLLAR_IDENTIFIER, "y", col=6)
        assert result[3] == tok(TokenType.PLUS, "+", col=9)
        assert result[4] == tok(TokenType.INTEGER, "1", col=11)

    def test_modifier_combo_with_hyphen(self) -> None:
        """Modifier combo can use hyphen separator (treated as separate tokens)."""
        result = tokenize("CTRL-SHIFT ENTER")
        assert result[0] == tok(TokenType.CTRL, "CTRL")
        assert result[1] == tok(TokenType.MINUS, "-", col=5)
        assert result[2] == tok(TokenType.SHIFT, "SHIFT", col=6)
        assert result[3] == tok(TokenType.ENTER, "ENTER", col=12)

    def test_line_exact_256_no_error(self) -> None:
        """A line with exactly 256 characters is valid."""
        source = "x" * 256 + "\n"
        result = tokenize(source)
        assert result[0].type is TokenType.IDENTIFIER
        assert result[1].type is TokenType.NEWLINE
        assert result[2].type is TokenType.EOF

    def test_line_257_no_newline_raises(self) -> None:
        """257 characters on a line with no newline raises at col 257."""
        source = "x" * 257
        with pytest.raises(LexerError) as exc:
            tokenize(source)
        assert exc.value.column == 257

    def test_rem_block_ends_at_word_boundary(self) -> None:
        """'REM_BLOCK_EXTRA' should not match REM_BLOCK keyword."""
        result = tokenize("REM_BLOCK_EXTRA")
        assert result[0].type is TokenType.IDENTIFIER

    def test_payload_fragment(self) -> None:
        """A realistic multi-line payload tokenises without errors."""
        source = (
            "REM Simple payload\n"
            "DEFAULTDELAY 10\n"
            "DELAY 1000\n"
            "STRING Hello World\n"
            "ENTER\n"
        )
        result = tokenize(source)
        # First line is REM → only NEWLINE
        assert types(result[:2]) == [TokenType.NEWLINE, TokenType.DEFAULTDELAY]
        # DEFAULTDELAY
        assert result[1].type is TokenType.DEFAULTDELAY
        assert result[2].type is TokenType.INTEGER
        # ENTER at line 5
        enter_tokens = [t for t in result if t.type is TokenType.ENTER]
        assert len(enter_tokens) == 1
        # Total should include NEWLINEs and EOF
        assert result[-1].type is TokenType.EOF

    def test_string_body_column_after_leading_spaces(self) -> None:
        """STRING with multiple leading spaces offsets body column correctly."""
        # "STRING   abc" → body starts at col 10 (STRING=6, 3 stripped spaces + 1 consumed)
        # wait: STRING=6 chars, col becomes 7. Strip 3 spaces: col becomes 10.
        result = tokenize("STRING   abc")
        assert result[1] == tok(TokenType.STRING_BODY, "abc", col=10)
