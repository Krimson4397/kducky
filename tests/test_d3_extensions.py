"""Tests for DuckyScript 3 extensions: REBOOT, REPLAY, JITTER, INJECT_VAR."""

import pytest

from ducky.ast import (
    AssignStmt,
    BinaryOp,
    DollarIdentifierExpr,
    ExfilStmt,
    InjectVarStmt,
    IntegerExpr,
    JitterStmt,
    MouseAction,
    MouseButton,
    RebootStmt,
    ReplayStmt,
    Script,
    StringStmt,
)
from ducky.errors import LexerError, ParseError
from ducky.interpreter import Interpreter
from ducky.lexer import DuckyLexer
from ducky.parser import DuckyParser
from ducky.platform import RestartPayloadSignal
from ducky.platform.desktop import DesktopPlatform
from ducky.preprocessor import Preprocessor
from ducky.tokens import ActionKey, Operator, TokenType

# ── Helpers ──────────────────────────────────────────────────────────────────


def _execute(source: str) -> DesktopPlatform:
    """Tokenize, parse, and interpret *source* on a DesktopPlatform."""
    preprocessed = Preprocessor().preprocess(source)
    tokens = DuckyLexer().tokenize(preprocessed)
    script = DuckyParser(tokens).parse()
    platform = DesktopPlatform()
    Interpreter(platform).interpret(script)
    return platform


def _parse(source: str) -> Script:
    """Tokenize and parse *source*, returning the AST script."""
    preprocessed = Preprocessor().preprocess(source)
    tokens = DuckyLexer().tokenize(preprocessed)
    return DuckyParser(tokens).parse()


# ── REBOOT tests ─────────────────────────────────────────────────────────────


class TestReboot:
    def test_reboot_parses(self) -> None:
        """Source ``REBOOT`` parses to RebootStmt."""
        script = _parse("REBOOT\n")
        assert len(script.statements) == 1
        stmt = script.statements[0]
        assert isinstance(stmt, RebootStmt)

    def test_reboot_calls_platform(self) -> None:
        """Interpreter visits RebootStmt, platform.reboot_target() is called."""
        platform = DesktopPlatform()
        Interpreter(platform).visit(RebootStmt())
        assert ("reboot_target",) in platform.calls

    def test_reboot_in_full_pipeline(self) -> None:
        """Full pipeline produces reboot_target call."""
        platform = _execute("REBOOT\n")
        assert ("reboot_target",) in platform.calls


# ── REPLAY tests ─────────────────────────────────────────────────────────────


class TestReplay:
    def test_replay_parses(self) -> None:
        """Source ``REPLAY`` parses to ReplayStmt."""
        script = _parse("REPLAY\n")
        assert len(script.statements) == 1
        stmt = script.statements[0]
        assert isinstance(stmt, ReplayStmt)

    def test_replay_raises_signal(self) -> None:
        """Interpreter visit_ReplayStmt raises RestartPayloadSignal."""
        platform = DesktopPlatform()
        interp = Interpreter(platform)
        with pytest.raises(RestartPayloadSignal):
            interp.visit(ReplayStmt())

    def test_replay_in_pipeline(self) -> None:
        """Full pipeline raises RestartPayloadSignal."""
        with pytest.raises(RestartPayloadSignal):
            _execute("REPLAY\n")


# ── JITTER tests ─────────────────────────────────────────────────────────────


class TestJitter:
    def test_jitter_on_parses(self) -> None:
        """Source ``JITTER ON`` parses to JitterStmt(mode='on')."""
        script = _parse("JITTER ON\n")
        assert len(script.statements) == 1
        stmt = script.statements[0]
        assert isinstance(stmt, JitterStmt)
        assert stmt.mode == "on"
        assert stmt.min_delay == 0
        assert stmt.max_delay == 0

    def test_jitter_off_parses(self) -> None:
        """Source ``JITTER OFF`` parses to JitterStmt(mode='off')."""
        script = _parse("JITTER OFF\n")
        assert len(script.statements) == 1
        stmt = script.statements[0]
        assert isinstance(stmt, JitterStmt)
        assert stmt.mode == "off"

    def test_jitter_delay_parses(self) -> None:
        """Source ``JITTER DELAY 10 50`` parses correctly."""
        script = _parse("JITTER DELAY 10 50\n")
        assert len(script.statements) == 1
        stmt = script.statements[0]
        assert isinstance(stmt, JitterStmt)
        assert stmt.mode == "delay"
        assert stmt.min_delay == 10
        assert stmt.max_delay == 50

    def test_jitter_delay_enables_jitter(self) -> None:
        """JITTER DELAY sets min/max and enables jitter."""
        stmt = JitterStmt(mode="delay", min_delay=5, max_delay=20)
        platform = DesktopPlatform()
        interp = Interpreter(platform)
        assert interp._jitter_enabled is False
        interp.visit(stmt)
        assert interp._jitter_enabled is True
        assert interp._jitter_min == 5
        assert interp._jitter_max == 20

    def test_jitter_on_enables(self) -> None:
        """JITTER ON enables jitter with existing min/max."""
        platform = DesktopPlatform()
        interp = Interpreter(platform)
        # First set delay
        interp.visit(JitterStmt(mode="delay", min_delay=10, max_delay=50))
        assert interp._jitter_enabled is True
        # Then turn off
        interp.visit(JitterStmt(mode="off"))
        assert interp._jitter_enabled is False
        # Then turn back on
        interp.visit(JitterStmt(mode="on"))
        assert interp._jitter_enabled is True

    def test_jitter_off_disables(self) -> None:
        """JITTER OFF disables jitter."""
        platform = DesktopPlatform()
        interp = Interpreter(platform)
        interp.visit(JitterStmt(mode="on"))
        assert interp._jitter_enabled is True
        interp.visit(JitterStmt(mode="off"))
        assert interp._jitter_enabled is False

    def test_jitter_delay_on_string(self) -> None:
        """STRING with jitter enabled causes delay_ms per character."""
        platform = DesktopPlatform()
        interp = Interpreter(platform)
        interp.visit(JitterStmt(mode="delay", min_delay=0, max_delay=1))
        interp.visit(StringStmt(text="AB"))
        delay_calls = [
            c for c in platform.calls if c[0] == "delay_ms"
        ]
        # Each char gets one delay_ms from jitter, plus no default_char_delay
        assert len(delay_calls) == 2

    def test_jitter_delay_with_char_delay(self) -> None:
        """STRING with jitter AND default char delay produces both delays."""
        from ducky.ast import DefaultCharDelayStmt, IntegerExpr

        platform = DesktopPlatform()
        interp = Interpreter(platform)
        interp.visit(DefaultCharDelayStmt(delay=IntegerExpr(10)))
        interp.visit(JitterStmt(mode="delay", min_delay=0, max_delay=1))
        interp.visit(StringStmt(text="AB"))
        delay_calls = [
            c for c in platform.calls if c[0] == "delay_ms"
        ]
        # 2 jitter delays + 2 char delays = 4 delay_ms calls
        assert len(delay_calls) == 4


# ── INJECT_VAR tests ─────────────────────────────────────────────────────────


class TestInjectVar:
    def test_inject_var_parses(self) -> None:
        """Source ``INJECT_VAR $x`` parses to InjectVarStmt(variable='x')."""
        script = _parse("INJECT_VAR $x\n")
        assert len(script.statements) == 1
        stmt = script.statements[0]
        assert isinstance(stmt, InjectVarStmt)
        assert stmt.variable == "x"

    def test_inject_var_types_variable(self) -> None:
        """``VAR $x = 42`` then ``INJECT_VAR $x`` types '42'."""
        platform = _execute("VAR $x = 42\nINJECT_VAR $x\n")
        type_calls = [c for c in platform.calls if c[0] == "type_string"]
        assert any(c[1] == "42" for c in type_calls)

    def test_inject_var_undefined_errors(self) -> None:
        """``INJECT_VAR $nonexistent`` raises InterpreterError."""
        from ducky.errors import InterpreterError

        with pytest.raises(InterpreterError, match="Undefined variable"):
            _execute("INJECT_VAR $nonexistent\n")

    def test_inject_var_reassignment(self) -> None:
        """Reassign variable, INJECT_VAR types the updated value."""
        platform = _execute("VAR $x = 1\n$x = 99\nINJECT_VAR $x\n")
        type_calls = [c for c in platform.calls if c[0] == "type_string"]
        assert not any(c[1] == "1" for c in type_calls)
        assert any(c[1] == "99" for c in type_calls)


# ── EXFIL tests ─────────────────────────────────────────────────────────────


class TestExfil:
    def test_exfil_parses(self) -> None:
        """Source ``EXFIL $x`` parses to ExfilStmt(variable='x')."""
        script = _parse("EXFIL $x\n")
        assert len(script.statements) == 1
        stmt = script.statements[0]
        assert isinstance(stmt, ExfilStmt)
        assert stmt.variable == "x"

    def test_exfil_missing_argument_errors(self) -> None:
        """``EXFIL`` without a $identifier is a parse error."""
        with pytest.raises(ParseError):
            _parse("EXFIL\n")

    def test_exfil_calls_platform_with_value(self) -> None:
        """``VAR $x = 42`` then ``EXFIL $x`` passes '42' to platform.exfil."""
        platform = _execute("VAR $x = 42\nEXFIL $x\n")
        exfil_calls = [c for c in platform.calls if c[0] == "exfil"]
        assert exfil_calls == [("exfil", "42")]

    def test_exfil_writes_loot_bin_line(self, tmp_path) -> None:
        """EXFIL writes the variable value as a line to loot.bin."""
        loot = tmp_path / "loot.bin"
        platform = DesktopPlatform(loot_path=str(loot))
        interp = Interpreter(platform)
        script = _parse("VAR $FOO = 1337\nEXFIL $FOO\n")
        interp.interpret(script)
        assert loot.read_text(encoding="utf-8") == "1337\n"

    def test_exfil_appends_multiple_lines(self, tmp_path) -> None:
        """Repeated EXFIL calls append lines without overwriting."""
        loot = tmp_path / "loot.bin"
        platform = DesktopPlatform(loot_path=str(loot))
        interp = Interpreter(platform)
        script = _parse(
            "VAR $a = 1\nEXFIL $a\n"
            "VAR $b = 2\nEXFIL $b\n"
            "EXFIL $a\n"
        )
        interp.interpret(script)
        assert loot.read_text(encoding="utf-8") == "1\n2\n1\n"

    def test_exfil_undefined_variable_errors(self) -> None:
        """``EXFIL $nonexistent`` raises InterpreterError."""
        from ducky.errors import InterpreterError

        with pytest.raises(InterpreterError, match="Undefined variable"):
            _execute("EXFIL $nonexistent\n")

    def test_exfil_does_not_type_text(self) -> None:
        """EXFIL writes loot; it never emits keystrokes."""
        platform = _execute("VAR $x = 7\nEXFIL $x\n")
        assert not any(c[0] == "type_string" for c in platform.calls)

    def test_exfil_internal_variable(self) -> None:
        """Internal $_ variables can be exfiltrated too."""
        platform = _execute("EXFIL $_RANDOM_INT\n")
        exfil_calls = [c for c in platform.calls if c[0] == "exfil"]
        assert exfil_calls == [("exfil", "0")]


# ── Internal ($_) variable tests ────────────────────────────────────────────


class TestInternalVars:
    """$_ internal variables populated at interpreter init."""

    def test_internal_vars_exist(self) -> None:
        """All 7 $_ variables exist in _globals as ints."""
        platform = DesktopPlatform()
        interp = Interpreter(platform)
        names = (
            "_IS_CAPSLOCK_ON",
            "_IS_NUMLOCK_ON",
            "_IS_SCROLLLOCK_ON",
            "_RANDOM_MIN",
            "_RANDOM_MAX",
            "_RANDOM_INT",
            "_BUTTON_ENABLED",
        )
        for name in names:
            assert name in interp._globals, f"Missing $_ variable: {name}"
            assert isinstance(interp._globals[name], int), (
                f"$_ variable {name} is not int"
            )

    def test_is_capslock_on(self) -> None:
        """Platform caps lock on → $_IS_CAPSLOCK_ON == 1."""
        platform = DesktopPlatform()
        platform._caps_lock = True
        interp = Interpreter(platform)
        assert interp._globals["_IS_CAPSLOCK_ON"] == 1

    def test_is_numlock_on(self) -> None:
        """Platform num lock on → $_IS_NUMLOCK_ON == 1."""
        platform = DesktopPlatform()
        platform._num_lock = True
        interp = Interpreter(platform)
        assert interp._globals["_IS_NUMLOCK_ON"] == 1

    def test_is_scrolllock_on(self) -> None:
        """Platform scroll lock on → $_IS_SCROLLLOCK_ON == 1."""
        platform = DesktopPlatform()
        platform._scroll_lock = True
        interp = Interpreter(platform)
        assert interp._globals["_IS_SCROLLLOCK_ON"] == 1

    def test_internal_var_readable(self) -> None:
        """$_ variables can be read via DollarIdentifierExpr."""
        platform = DesktopPlatform()
        interp = Interpreter(platform)
        node = DollarIdentifierExpr("_RANDOM_MIN")
        assert interp.visit_DollarIdentifierExpr(node) == 0

    def test_internal_var_writable(self) -> None:
        """RW $_ variables can be assigned via AssignStmt."""
        platform = DesktopPlatform()
        interp = Interpreter(platform)
        interp.visit(AssignStmt("_RANDOM_MIN", IntegerExpr(100)))
        node = DollarIdentifierExpr("_RANDOM_MIN")
        assert interp.visit_DollarIdentifierExpr(node) == 100

    def test_internal_vars_in_expression(self) -> None:
        """$_ vars work in arithmetic expressions."""
        platform = DesktopPlatform()
        interp = Interpreter(platform)
        expr = BinaryOp(
            DollarIdentifierExpr("_RANDOM_MIN"), Operator.ADD, IntegerExpr(5),
        )
        assert interp.visit_BinaryOp(expr) == 5


# ── END_STRING / END_STRINGLN (block mode) tests ────────────────────────────


class TestEndString:
    """STRING/STRINGLN block mode (END_STRING / END_STRINGLN)."""

    def test_end_string_block_parses(self) -> None:
        """STRING block mode produces tokens."""
        source = "STRING\nhello world\nEND_STRING"
        tokens = DuckyLexer().tokenize(source)
        types = [t.type for t in tokens]
        assert TokenType.STRING in types
        assert TokenType.STRING_BODY in types

    def test_end_string_block_content(self) -> None:
        """STRING block mode concatenates lines without newlines."""
        tokens = DuckyLexer().tokenize("STRING\nhello\nworld\nEND_STRING")
        stmts = DuckyParser(tokens).parse().statements
        assert len(stmts) == 1
        body = stmts[0].text
        assert "\n" not in body
        assert body == "helloworld"

    def test_end_stringln_block_content(self) -> None:
        """STRINGLN block mode joins lines with newlines."""
        tokens = DuckyLexer().tokenize("STRINGLN\nhello\nworld\nEND_STRINGLN")
        stmts = DuckyParser(tokens).parse().statements
        assert len(stmts) == 1
        body = stmts[0].text
        assert "\n" in body
        assert body == "hello\nworld"

    def test_end_string_block_with_indent(self) -> None:
        """STRING block mode strips leading whitespace."""
        tokens = DuckyLexer().tokenize("STRING\n  hello\n  world\nEND_STRING")
        stmts = DuckyParser(tokens).parse().statements
        body = stmts[0].text
        assert body == "helloworld"

    def test_end_stringln_block_with_indent(self) -> None:
        """STRINGLN block mode strips only the first tab of each line."""
        tokens = DuckyLexer().tokenize("STRINGLN\n\thello\n\tworld\nEND_STRINGLN")
        stmts = DuckyParser(tokens).parse().statements
        body = stmts[0].text
        assert body == "hello\nworld"

    def test_end_stringln_block_preserves_additional_tabs(self) -> None:
        """STRINGLN keeps tabs beyond the first on each line."""
        tokens = DuckyLexer().tokenize(
            "STRINGLN\n\thello\n\t\tworld\nEND_STRINGLN"
        )
        stmts = DuckyParser(tokens).parse().statements
        body = stmts[0].text
        assert body == "hello\n\tworld"

    def test_end_stringln_block_preserves_leading_spaces(self) -> None:
        """STRINGLN preserves leading spaces (only a leading tab is stripped)."""
        tokens = DuckyLexer().tokenize("STRINGLN\n  hello\n  world\nEND_STRINGLN")
        stmts = DuckyParser(tokens).parse().statements
        body = stmts[0].text
        assert body == "  hello\n  world"

    def test_end_string_inline_still_works(self) -> None:
        """Regular inline STRING still works (backward compat)."""
        tokens = DuckyLexer().tokenize("STRING hello world")
        stmts = DuckyParser(tokens).parse().statements
        assert len(stmts) == 1
        assert stmts[0].text == "hello world"

    def test_end_stringln_inline_still_works(self) -> None:
        """Regular inline STRINGLN still works (backward compat)."""
        tokens = DuckyLexer().tokenize("STRINGLN hello world")
        stmts = DuckyParser(tokens).parse().statements
        assert len(stmts) == 1
        assert stmts[0].text == "hello world"

    def test_end_string_empty_body(self) -> None:
        """Empty STRING block produces no STRING_BODY."""
        tokens = DuckyLexer().tokenize("STRING\nEND_STRING")
        types = [t.type for t in tokens]
        assert TokenType.STRING_BODY not in types

    def test_end_stringln_execution(self) -> None:
        """STRINGLN block executes via interpreter, typing each line with ENTER."""
        platform = DesktopPlatform()
        interp = Interpreter(platform)
        tokens = DuckyLexer().tokenize("STRINGLN\nline1\nline2\nEND_STRINGLN")
        script = DuckyParser(tokens).parse()
        interp.interpret(script)
        calls = platform.calls
        assert ("type_string", "line1") in calls
        assert ("type_string", "line2") in calls
        # ENTER press happens between lines (from _type_text newline handling)
        assert ("press_key", (), ActionKey.ENTER) in calls

    def test_end_string_block_execution(self) -> None:
        """STRING block executes, typing concatenated text."""
        platform = DesktopPlatform()
        interp = Interpreter(platform)
        tokens = DuckyLexer().tokenize("STRING\nhello\nEND_STRING")
        script = DuckyParser(tokens).parse()
        interp.interpret(script)
        calls = platform.calls
        assert ("type_string", "hello") in calls

    def test_end_string_block_with_jitter(self) -> None:
        """Jitter + block mode works together."""
        platform = DesktopPlatform()
        interp = Interpreter(platform)
        source = "JITTER ON\nSTRINGLN\na\nb\nEND_STRINGLN"
        tokens = DuckyLexer().tokenize(source)
        script = DuckyParser(tokens).parse()
        interp.interpret(script)
        assert ("press_key", (), ActionKey.ENTER) in interp.platform.calls

    def test_end_string_indentation_does_not_affect_end_marker(self) -> None:
        """END_STRING can have indentation before it."""
        tokens = DuckyLexer().tokenize("STRING\n  hello\n  END_STRING")
        stmts = DuckyParser(tokens).parse().statements
        body = stmts[0].text
        assert body == "hello"


# ── STRING_* / STRINGLN_* block aliases ────────────────────────────────────


class TestStringBlockAliases:
    """STRING_POWERSHELL etc. behave exactly like STRING/STRINGLN blocks."""

    def test_string_powershell_block_parses_as_string(self) -> None:
        """STRING_POWERSHELL closes with END_STRING and types as a STRING."""
        tokens = DuckyLexer().tokenize(
            "STRING_POWERSHELL\nClear-Host;\n$c = 1\nEND_STRING"
        )
        types = [t.type for t in tokens]
        assert TokenType.STRING in types
        assert TokenType.STRING_BODY in types
        stmts = DuckyParser(tokens).parse().statements
        assert len(stmts) == 1
        assert isinstance(stmts[0], StringStmt)
        # STRING block semantics: leading whitespace stripped, lines joined
        assert stmts[0].text == "Clear-Host;$c = 1"

    def test_string_aliases_all_parse_as_string(self) -> None:
        """Every STRING_* alias produces a STRING token and joins lines."""
        aliases = (
            "STRING_POWERSHELL",
            "STRING_BATCH",
            "STRING_BASH",
            "STRING_JAVASCRIPT",
            "STRING_PYTHON",
            "STRING_RUBY",
            "STRING_HTML",
        )
        for alias in aliases:
            tokens = DuckyLexer().tokenize(
                f"{alias}\nline one\nline two\nEND_STRING"
            )
            assert tokens[0].type is TokenType.STRING, (
                f"{alias} should tokenize as STRING, got {tokens[0].type}"
            )
            stmts = DuckyParser(tokens).parse().statements
            assert len(stmts) == 1
            assert stmts[0].text == "line oneline two"

    def test_stringln_aliases_all_parse_as_stringln(self) -> None:
        """Every STRINGLN_* alias produces a STRINGLN token and joins lines."""
        aliases = (
            "STRINGLN_POWERSHELL",
            "STRINGLN_BATCH",
            "STRINGLN_BASH",
            "STRINGLN_JAVASCRIPT",
            "STRINGLN_PYTHON",
            "STRINGLN_RUBY",
            "STRINGLN_HTML",
        )
        for alias in aliases:
            tokens = DuckyLexer().tokenize(
                f"{alias}\nline one\nline two\nEND_STRINGLN"
            )
            assert tokens[0].type is TokenType.STRINGLN, (
                f"{alias} should tokenize as STRINGLN, got {tokens[0].type}"
            )
            stmts = DuckyParser(tokens).parse().statements
            assert len(stmts) == 1
            assert stmts[0].text == "line one\nline two"

    def test_string_alias_case_insensitive(self) -> None:
        """Alias keywords are case-insensitive like all keywords."""
        tokens = DuckyLexer().tokenize(
            "string_python\nx = 1\nend_string"
        )
        assert tokens[0].type is TokenType.STRING
        stmts = DuckyParser(tokens).parse().statements
        assert stmts[0].text == "x = 1"

    def test_string_powershell_inline_body(self) -> None:
        """An alias with inline content behaves like an inline STRING."""
        tokens = DuckyLexer().tokenize("STRING_BASH echo hi")
        assert tokens[0].type is TokenType.STRING
        assert tokens[1].type is TokenType.STRING_BODY
        assert tokens[1].value == "echo hi"

    def test_string_powershell_block_execution(self) -> None:
        """STRING_POWERSHELL block types its text via the interpreter."""
        platform = DesktopPlatform()
        interp = Interpreter(platform)
        tokens = DuckyLexer().tokenize(
            "STRING_POWERSHELL\nWrite-Host hi\nEND_STRING"
        )
        script = DuckyParser(tokens).parse()
        interp.interpret(script)
        assert ("type_string", "Write-Host hi") in platform.calls

    def test_stringln_bash_block_strips_first_tab(self) -> None:
        """STRINGLN_BASH block applies the STRINGLN first-tab rule."""
        tokens = DuckyLexer().tokenize(
            "STRINGLN_BASH\n\techo hi\n\t\tls -la\nEND_STRINGLN"
        )
        stmts = DuckyParser(tokens).parse().statements
        assert stmts[0].text == "echo hi\n\tls -la"

    def test_string_block_mismatched_terminator_raises(self) -> None:
        """STRING block closed with END_STRINGLN raises LexerError."""
        with pytest.raises(LexerError):
            DuckyLexer().tokenize("STRING\nhello\nEND_STRINGLN")

    def test_stringln_block_mismatched_terminator_raises(self) -> None:
        """STRINGLN block closed with END_STRING raises LexerError."""
        with pytest.raises(LexerError):
            DuckyLexer().tokenize("STRINGLN\nhello\nEND_STRING")

    def test_string_alias_mismatched_terminator_raises(self) -> None:
        """STRING_* alias closed with END_STRINGLN raises LexerError."""
        with pytest.raises(LexerError):
            DuckyLexer().tokenize(
                "STRING_POWERSHELL\nWrite-Host hi\nEND_STRINGLN"
            )

    def test_stringln_alias_mismatched_terminator_raises(self) -> None:
        """STRINGLN_* alias closed with END_STRING raises LexerError."""
        with pytest.raises(LexerError):
            DuckyLexer().tokenize(
                "STRINGLN_BASH\n\techo hi\nEND_STRING"
            )


# ── MOUSE tests ────────────────────────────────────────────────────────────


class TestMouse:
    """MOUSE_* statement parsing and execution."""

    def test_mouse_move_parses(self) -> None:
        """MOUSE_MOVE x y parses correctly."""
        tokens = DuckyLexer().tokenize("MOUSE_MOVE 100 200\n")
        stmts = DuckyParser(tokens).parse().statements
        assert len(stmts) == 1
        s = stmts[0]
        assert s.action == MouseAction.MOVE
        assert s.x == 100
        assert s.y == 200

    def test_mouse_move_to_parses(self) -> None:
        """MOUSE_MOVE_TO x y parses correctly."""
        tokens = DuckyLexer().tokenize("MOUSE_MOVE_TO 500 300\n")
        stmts = DuckyParser(tokens).parse().statements
        assert len(stmts) == 1
        assert stmts[0].action == MouseAction.MOVE_TO
        assert stmts[0].x == 500
        assert stmts[0].y == 300

    def test_mouse_click_left(self) -> None:
        """MOUSE_CLICK LEFT parses."""
        tokens = DuckyLexer().tokenize("MOUSE_CLICK LEFT\n")
        stmts = DuckyParser(tokens).parse().statements
        assert len(stmts) == 1
        assert stmts[0].action == MouseAction.CLICK
        assert stmts[0].button == MouseButton.LEFT

    def test_mouse_click_right(self) -> None:
        """MOUSE_CLICK RIGHT parses."""
        tokens = DuckyLexer().tokenize("MOUSE_CLICK RIGHT\n")
        stmts = DuckyParser(tokens).parse().statements
        assert stmts[0].action == MouseAction.CLICK
        assert stmts[0].button == MouseButton.RIGHT

    def test_mouse_click_middle(self) -> None:
        """MOUSE_CLICK MIDDLE parses (MIDDLE is IDENTIFIER)."""
        tokens = DuckyLexer().tokenize("MOUSE_CLICK MIDDLE\n")
        stmts = DuckyParser(tokens).parse().statements
        assert stmts[0].action == MouseAction.CLICK
        assert stmts[0].button == MouseButton.MIDDLE

    def test_mouse_down_up(self) -> None:
        """MOUSE_DOWN / MOUSE_UP parse correctly."""
        tokens = DuckyLexer().tokenize("MOUSE_DOWN LEFT\nMOUSE_UP LEFT\n")
        stmts = DuckyParser(tokens).parse().statements
        assert len(stmts) == 2
        assert stmts[0].action == MouseAction.DOWN
        assert stmts[1].action == MouseAction.UP

    def test_mouse_scroll(self) -> None:
        """MOUSE_SCROLL amount parses."""
        tokens = DuckyLexer().tokenize("MOUSE_SCROLL 5\n")
        stmts = DuckyParser(tokens).parse().statements
        assert len(stmts) == 1
        assert stmts[0].action == MouseAction.SCROLL
        assert stmts[0].scroll_amount == 5

    def test_mouse_bad_button_errors(self) -> None:
        """Invalid mouse button raises ParseError."""
        tokens = DuckyLexer().tokenize("MOUSE_CLICK UP\n")
        with pytest.raises(ParseError):
            DuckyParser(tokens).parse()

    def test_mouse_move_executes(self) -> None:
        """MOUSE_MOVE calls platform.mouse_move."""
        platform = DesktopPlatform()
        interp = Interpreter(platform)
        tokens = DuckyLexer().tokenize("MOUSE_MOVE 10 20\n")
        script = DuckyParser(tokens).parse()
        interp.interpret(script)
        assert ("mouse_move", 10, 20) in platform.calls

    def test_mouse_click_executes(self) -> None:
        """MOUSE_CLICK calls platform.mouse_click."""
        platform = DesktopPlatform()
        interp = Interpreter(platform)
        tokens = DuckyLexer().tokenize("MOUSE_CLICK LEFT\n")
        script = DuckyParser(tokens).parse()
        interp.interpret(script)
        assert ("mouse_click", "LEFT") in platform.calls

    def test_mouse_scroll_executes(self) -> None:
        """MOUSE_SCROLL calls platform.mouse_scroll."""
        platform = DesktopPlatform()
        interp = Interpreter(platform)
        tokens = DuckyLexer().tokenize("MOUSE_SCROLL -3\n")
        script = DuckyParser(tokens).parse()
        interp.interpret(script)
        assert ("mouse_scroll", -3) in platform.calls
