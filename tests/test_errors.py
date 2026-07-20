"""Tests for the DuckyError hierarchy."""
from ducky.errors import (
    DuckyError,
    InterpreterError,
    LexerError,
    ParseError,
    PreprocessorError,
)


class TestHierarchy:
    def test_lexer_error_is_ducky_error(self):
        assert issubclass(LexerError, DuckyError)

    def test_parse_error_is_ducky_error(self):
        assert issubclass(ParseError, DuckyError)

    def test_interpreter_error_is_ducky_error(self):
        assert issubclass(InterpreterError, DuckyError)

    def test_preprocessor_error_is_ducky_error(self):
        assert issubclass(PreprocessorError, DuckyError)

    def test_ducky_error_is_exception(self):
        assert issubclass(DuckyError, Exception)


class TestFormatting:
    def test_lexer_error_format(self):
        err = LexerError("bad input", line=5, column=10)
        assert str(err) == "[ERROR] line 5, col 10: bad input"

    def test_parse_error_format(self):
        err = ParseError("expected THEN", line=3, column=7)
        assert str(err) == "[ERROR] line 3, col 7: expected THEN"

    def test_parse_error_no_line_col(self):
        err = ParseError("something bad")
        assert str(err) == "[ERROR] something bad"

    def test_interpreter_error_format(self):
        err = InterpreterError("Undeclared variable: $x")
        assert str(err) == "[ERROR] Undeclared variable: $x"

    def test_preprocessor_error_format(self):
        err = PreprocessorError("Undefined constant '#X'", line=12)
        assert str(err) == "[ERROR] line 12: Undefined constant '#X'"


class TestAttributes:
    def test_lexer_error_attributes(self):
        err = LexerError("msg", line=1, column=2)
        assert err.message == "msg"
        assert err.line == 1
        assert err.column == 2
        assert err.source_snippet is None
        assert err.cause is None

    def test_parse_error_attributes(self):
        err = ParseError("msg", line=3, column=7)
        assert err.message == "msg"
        assert err.line == 3
        assert err.column == 7
        assert err.source_snippet is None

    def test_interpreter_error_attributes(self):
        err = InterpreterError("msg")
        assert err.message == "msg"
        assert err.line is None
        assert err.column is None

    def test_preprocessor_error_attributes(self):
        err = PreprocessorError("msg", line=5)
        assert err.message == "msg"
        assert err.line == 5
        assert err.column is None


class TestSourceSnippetAndCause:
    def test_source_snippet_stored_not_in_string(self):
        err = DuckyError("msg", line=1, column=2, source_snippet="VAR $x = 1")
        assert err.source_snippet == "VAR $x = 1"
        assert "VAR $x" not in str(err)

    def test_cause_stored_not_in_string(self):
        inner = ValueError("inner")
        err = DuckyError("outer", cause=inner)
        assert err.cause is inner
        assert "inner" not in str(err)

    def test_both_stored(self):
        inner = ValueError("nested")
        err = DuckyError("top", line=5, column=3, source_snippet="foo", cause=inner)
        assert err.line == 5
        assert err.column == 3
        assert err.source_snippet == "foo"
        assert err.cause is inner


class TestIsInstance:
    def test_isinstance_ducky_error(self):
        assert isinstance(LexerError("msg", 1, 1), DuckyError)
        assert isinstance(ParseError("msg", 1, 1), DuckyError)
        assert isinstance(InterpreterError("msg"), DuckyError)
        assert isinstance(PreprocessorError("msg", 1), DuckyError)

    def test_isinstance_exception(self):
        assert isinstance(LexerError("msg", 1, 1), Exception)


class TestReimports:
    """Verify error classes are still accessible from their original modules."""

    def test_lexer_reimport(self):
        from ducky.lexer import LexerError as LexerErrorAlias
        assert LexerErrorAlias is LexerError

    def test_parser_reimport(self):
        from ducky.parser import ParseError as ParseErrorAlias
        assert ParseErrorAlias is ParseError

    def test_interpreter_reimport(self):
        from ducky.interpreter import InterpreterError as InterpErrorAlias
        assert InterpErrorAlias is InterpreterError

    def test_preprocessor_reimport(self):
        from ducky.preprocessor import PreprocessorError as PrepErrorAlias
        assert PrepErrorAlias is PreprocessorError


class TestThroughActualPaths:
    """Trigger actual error conditions and verify [ERROR] format."""

    def test_lexer_illegal_char_format(self):
        from ducky.lexer import DuckyLexer
        try:
            list(DuckyLexer().tokenize("STRING \x80"))
        except LexerError as e:
            assert str(e).startswith("[ERROR]")
            assert "Illegal character" in str(e)

    def test_lexer_unterminated_string_format(self):
        from ducky.lexer import DuckyLexer
        try:
            list(DuckyLexer().tokenize('STRING "hello'))
        except LexerError as e:
            assert str(e).startswith("[ERROR]")
            assert "Unterminated" in str(e)

    def test_parser_expected_then_format(self):
        from ducky.lexer import DuckyLexer
        from ducky.parser import DuckyParser
        tokens = list(DuckyLexer().tokenize("IF (1)\nSTRINGLN x\n"))
        try:
            DuckyParser(tokens).parse()
        except ParseError as e:
            assert str(e).startswith("[ERROR]")
            assert "Expected THEN" in str(e)

    def test_interpreter_undeclared_variable_format(self):
        from ducky.interpreter import Interpreter
        from ducky.lexer import DuckyLexer
        from ducky.parser import DuckyParser
        from ducky.platform.desktop import DesktopPlatform
        tokens = list(DuckyLexer().tokenize("STRINGLN $x\n"))
        ast = DuckyParser(tokens).parse()
        platform = DesktopPlatform()
        interp = Interpreter(platform)
        try:
            interp.interpret(ast)
        except InterpreterError as e:
            assert str(e).startswith("[ERROR]")
            assert "Undeclared variable" in str(e)

    def test_preprocessor_undefined_format(self):
        from ducky.preprocessor import Preprocessor
        try:
            Preprocessor().preprocess("STRINGLN #X\n")
        except PreprocessorError as e:
            assert str(e).startswith("[ERROR]")
            assert "Undefined constant" in str(e)
