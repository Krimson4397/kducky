"""End-to-end integration tests — full DuckyScript payloads through the pipeline.

Each test runs source text through the entire chain:
    DuckyLexer → DuckyParser → Interpreter → DesktopPlatform
and asserts on the recorded platform call sequence or output.
"""

import pytest

from ducky.interpreter import Interpreter, InterpreterError
from ducky.lexer import DuckyLexer
from ducky.parser import DuckyParser
from ducky.platform.desktop import DesktopPlatform
from ducky.tokens import ActionKey, ModifierKey


def _execute(source: str) -> DesktopPlatform:
    """Tokenize, parse, interpret *source* and return the platform mock."""
    tokens = DuckyLexer().tokenize(source)
    script = DuckyParser(tokens).parse()
    platform = DesktopPlatform()
    Interpreter(platform).interpret(script)
    return platform


class TestIntegration:
    """Full-pipeline integration tests."""

    def test_hello_world(self) -> None:
        """STRING "Hello World" types the text."""
        platform = _execute("STRING Hello World\n")
        assert platform.output == ["Hello World"]

    def test_hello_world_stringln(self) -> None:
        """STRINGLN types text then presses ENTER."""
        platform = _execute("STRINGLN Hello World\n")
        assert platform.output == ["Hello World"]
        assert ("press_key", (), ActionKey.ENTER) in platform.calls

    def test_variable_and_delay(self) -> None:
        """VAR $x = 42 then DELAY $x produces delay_ms(42)."""
        platform = _execute("VAR $x = 42\nDELAY $x\n")
        delay_calls = [c for c in platform.calls if c[0] == "delay_ms"]
        assert delay_calls == [("delay_ms", 42)]

    def test_var_delay_multi(self) -> None:
        """DELAY 500 then DELAY $x=42 produce two delays with correct values."""
        platform = _execute("VAR $x = 42\nDELAY 500\nDELAY $x\n")
        delay_calls = [c for c in platform.calls if c[0] == "delay_ms"]
        assert delay_calls == [("delay_ms", 500), ("delay_ms", 42)]

    def test_if_true_branch(self) -> None:
        """IF (1) executes the body, not the ELSE."""
        platform = _execute(
            "IF (1) THEN\n"
            "STRINGLN yes\n"
            "ELSE\n"
            "STRINGLN no\n"
            "END_IF\n"
        )
        assert platform.output == ["yes"]
        assert "no" not in platform.output

    def test_if_false_branch(self) -> None:
        """IF (0) skips the body and executes ELSE."""
        platform = _execute(
            "IF (0) THEN\n"
            "STRINGLN yes\n"
            "ELSE\n"
            "STRINGLN no\n"
            "END_IF\n"
        )
        assert platform.output == ["no"]
        assert "yes" not in platform.output

    def test_while_loop(self) -> None:
        """WHILE loop repeats body until condition is false."""
        platform = _execute(
            "VAR $i = 3\n"
            "WHILE ($i > 0)\n"
            "STRINGLN count\n"
            "$i = $i - 1\n"
            "END_WHILE\n"
        )
        assert platform.output == ["count", "count", "count"]

    def test_function_call(self) -> None:
        """FUNCTION body executes when called by name()."""
        platform = _execute(
            "FUNCTION greet()\n"
            "STRINGLN Hello\n"
            "END_FUNCTION\n"
            "greet()\n"
        )
        assert platform.output == ["Hello"]

    def test_function_return_and_assign(self) -> None:
        """RETURN value propagates through a call expression."""
        platform = _execute(
            "FUNCTION f()\n"
            "RETURN 42\n"
            "END_FUNCTION\n"
            "VAR $r = f()\n"
            "STRINGLN done\n"
        )
        assert platform.output == ["done"]

    def test_modifier_combo(self) -> None:
        """CTRL SHIFT ESC presses all three keys."""
        platform = _execute("CTRL SHIFT ESC\n")
        assert ("press_key", (ModifierKey.CTRL, ModifierKey.SHIFT),
                ActionKey.ESC) in platform.calls

    def test_hold_release(self) -> None:
        """HOLD SPACE, DELAY, RELEASE SPACE produces hold → delay → release."""
        platform = _execute("HOLD SPACE\nDELAY 100\nRELEASE SPACE\n")
        hold_calls = [c for c in platform.calls if c[0] == "hold_key"]
        release_calls = [c for c in platform.calls if c[0] == "release_key"]
        assert hold_calls == [("hold_key", ActionKey.SPACE)]
        assert release_calls == [("release_key", ActionKey.SPACE)]
        delay_calls = [c for c in platform.calls if c[0] == "delay_ms"]
        assert ("delay_ms", 100) in delay_calls

    def test_random_char(self) -> None:
        """RANDOM_CHAR calls random_int then type_string with one char."""
        platform = _execute("RANDOM_CHAR\n")
        random_calls = [c for c in platform.calls if c[0] == "random_int"]
        assert len(random_calls) == 1
        assert random_calls[0] == ("random_int", 0x21, 0x7E)
        type_calls = [c for c in platform.calls if c[0] == "type_string"]
        assert len(type_calls) == 1
        ch = type_calls[0][1]
        assert isinstance(ch, str) and len(ch) == 1

    def test_default_delay_between_statements(self) -> None:
        """DEFAULTDELAY inserts delay_ms between consecutive statements."""
        platform = _execute("DEFAULTDELAY 50\nSTRINGLN a\nSTRINGLN b\n")
        delay_calls = [c for c in platform.calls if c[0] == "delay_ms"]
        assert ("delay_ms", 50) in delay_calls

    def test_max_delay(self) -> None:
        """DELAY 30000 passes the value through (no clamping upper bound)."""
        platform = _execute("DELAY 30000\n")
        assert ("delay_ms", 30000) in platform.calls

    def test_undeclared_variable_error(self) -> None:
        """DELAY with undeclared $x raises InterpreterError."""
        with pytest.raises(InterpreterError, match="Undeclared variable"):
            _execute("DELAY $x\n")

    def test_nested_if(self) -> None:
        """Nested IF statements execute correctly."""
        platform = _execute(
            "IF (1) THEN\n"
            "IF (1) THEN\n"
            "STRINGLN nested\n"
            "END_IF\n"
            "END_IF\n"
        )
        assert platform.output == ["nested"]

    def test_variable_assignment_before_use(self) -> None:
        """VAR then DELAY $var uses the declared variable."""
        platform = _execute("VAR $x = 100\nDELAY $x\n")
        assert ("delay_ms", 100) in platform.calls

    def test_stringln_after_var(self) -> None:
        """STRINGLN works after variable declaration."""
        platform = _execute("VAR $x = 1\nSTRINGLN hello\n")
        assert platform.output == ["hello"]

    def test_while_zero_iterations(self) -> None:
        """WHILE (0) skips the body entirely."""
        platform = _execute(
            "WHILE (0)\n"
            "STRINGLN never\n"
            "END_WHILE\n"
        )
        assert platform.output == []

    def test_else_if_chain(self) -> None:
        """ELSE IF branch executes when first condition is false."""
        platform = _execute(
            "IF (0) THEN\n"
            "STRINGLN first\n"
            "ELSE IF (1) THEN\n"
            "STRINGLN second\n"
            "ELSE\n"
            "STRINGLN third\n"
            "END_IF\n"
        )
        assert platform.output == ["second"]

    def test_string_with_default_char_delay(self) -> None:
        """DEFAULTCHARDELAY causes per-character typing."""
        platform = _execute("DEFAULTCHARDELAY 10\nSTRING ab\n")
        # Each char typed individually: "a", delay, "b", delay
        assert ("type_string", "a") in platform.calls
        assert ("type_string", "b") in platform.calls
