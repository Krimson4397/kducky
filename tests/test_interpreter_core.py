"""Tests for the interpreter core (variables, expressions, statements)."""

import pytest

from ducky.ast import (
    AssignStmt,
    BinaryOp,
    DefaultCharDelayStmt,
    DefaultDelayStmt,
    DelayStmt,
    DollarIdentifierExpr,
    GroupExpr,
    IntegerExpr,
    RepeatStmt,
    ResetStmt,
    RestartPayloadStmt,
    Script,
    StopPayloadStmt,
    StringExpr,
    UnaryOp,
    VarDef,
)
from ducky.interpreter import Interpreter, InterpreterError
from ducky.platform import RestartPayloadSignal, StopPayloadSignal
from ducky.platform.desktop import DesktopPlatform
from ducky.tokens import Operator


class TestVariableDeclarations:
    """VAR $x = <expr> and VAR $x (defaults to 0)."""

    def test_var_def_with_initializer(self) -> None:
        """VAR $x = 42 stores the value."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        script = Script((VarDef("x", IntegerExpr(42)),))
        interpreter.interpret(script)
        assert interpreter._globals["x"] == 42

    def test_var_def_default_zero(self) -> None:
        """VAR $x without explicit initializer defaults to 0."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        # The parser produces IntegerExpr(0) when no initializer is given
        script = Script((VarDef("x", IntegerExpr(0)),))
        interpreter.interpret(script)
        assert interpreter._globals["x"] == 0

    def test_multiple_vars(self) -> None:
        """Multiple variable declarations work independently."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        script = Script((
            VarDef("a", IntegerExpr(1)),
            VarDef("b", IntegerExpr(2)),
            VarDef("c", IntegerExpr(3)),
        ))
        interpreter.interpret(script)
        assert interpreter._globals["a"] == 1
        assert interpreter._globals["b"] == 2
        assert interpreter._globals["c"] == 3

    def test_var_def_wraps_16bit(self) -> None:
        """Values exceeding 16-bit wrap via & 0xFFFF."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        script = Script((VarDef("x", IntegerExpr(70000)),))
        interpreter.interpret(script)
        assert interpreter._globals["x"] == 70000 & 0xFFFF
        assert interpreter._globals["x"] == 4464


class TestAssignment:
    """$x = <expr> assignment to existing variables."""

    def test_assign_increment(self) -> None:
        """$x = $x + 1 reads, increments, stores."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        script = Script((
            VarDef("x", IntegerExpr(5)),
            AssignStmt(
                "x",
                BinaryOp(DollarIdentifierExpr("x"), Operator.ADD, IntegerExpr(1)),
            ),
        ))
        interpreter.interpret(script)
        assert interpreter._globals["x"] == 6

    def test_assign_expression(self) -> None:
        """$x = (a + b) * 2 evaluates correctly."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        script = Script((
            VarDef("a", IntegerExpr(3)),
            VarDef("b", IntegerExpr(4)),
            VarDef("x", IntegerExpr(0)),
            AssignStmt(
                "x",
                BinaryOp(
                    BinaryOp(DollarIdentifierExpr("a"), Operator.ADD,
                             DollarIdentifierExpr("b")),
                    Operator.MULTIPLY,
                    IntegerExpr(2),
                ),
            ),
        ))
        interpreter.interpret(script)
        assert interpreter._globals["x"] == 14

    def test_assign_wraps_16bit(self) -> None:
        """Assignment wraps value to 16 bits."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        script = Script((
            VarDef("x", IntegerExpr(0)),
            AssignStmt("x", IntegerExpr(65536)),
        ))
        interpreter.interpret(script)
        assert interpreter._globals["x"] == 0

    def test_assign_to_undeclared_raises(self) -> None:
        """Assignment to undeclared variable raises InterpreterError."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        script = Script((AssignStmt("x", IntegerExpr(42)),))
        with pytest.raises(InterpreterError, match="Undeclared variable"):
            interpreter.interpret(script)


class TestExpressions:
    """Expression evaluation for all operators."""

    # ── Arithmetic ─────────────────────────────────────────────────

    def test_addition(self) -> None:
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        script = Script((
            VarDef("x", BinaryOp(IntegerExpr(10), Operator.ADD, IntegerExpr(20))),
        ))
        interpreter.interpret(script)
        assert interpreter._globals["x"] == 30

    def test_subtraction(self) -> None:
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        script = Script((
            VarDef("x", BinaryOp(IntegerExpr(20), Operator.SUBTRACT, IntegerExpr(8))),
        ))
        interpreter.interpret(script)
        assert interpreter._globals["x"] == 12

    def test_multiplication(self) -> None:
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        script = Script((
            VarDef("x", BinaryOp(IntegerExpr(7), Operator.MULTIPLY, IntegerExpr(6))),
        ))
        interpreter.interpret(script)
        assert interpreter._globals["x"] == 42

    def test_division(self) -> None:
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        script = Script((
            VarDef("x", BinaryOp(IntegerExpr(42), Operator.DIVIDE, IntegerExpr(10))),
        ))
        interpreter.interpret(script)
        assert interpreter._globals["x"] == 4

    def test_modulo(self) -> None:
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        script = Script((
            VarDef("x", BinaryOp(IntegerExpr(42), Operator.MODULO, IntegerExpr(10))),
        ))
        interpreter.interpret(script)
        assert interpreter._globals["x"] == 2

    def test_power(self) -> None:
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        script = Script((
            VarDef("x", BinaryOp(IntegerExpr(2), Operator.POWER, IntegerExpr(8))),
        ))
        interpreter.interpret(script)
        assert interpreter._globals["x"] == 256

    def test_precedence_multiplication_over_addition(self) -> None:
        """4 + 3 * 2 evaluates to 10 (multiplication first)."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        # AST as the parser would produce it: 4 + (3 * 2)
        expr = BinaryOp(
            IntegerExpr(4), Operator.ADD,
            BinaryOp(IntegerExpr(3), Operator.MULTIPLY, IntegerExpr(2)),
        )
        script = Script((VarDef("x", expr),))
        interpreter.interpret(script)
        assert interpreter._globals["x"] == 10

    # ── 16-bit wrapping ────────────────────────────────────────────

    def test_wrapping_add(self) -> None:
        """65535 + 1 wraps to 0."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        script = Script((
            VarDef("x", BinaryOp(IntegerExpr(65535), Operator.ADD, IntegerExpr(1))),
        ))
        interpreter.interpret(script)
        assert interpreter._globals["x"] == 0

    def test_wrapping_subtract_underflow(self) -> None:
        """0 - 1 wraps to 65535."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        script = Script((
            VarDef("x", BinaryOp(IntegerExpr(0), Operator.SUBTRACT, IntegerExpr(1))),
        ))
        interpreter.interpret(script)
        assert interpreter._globals["x"] == 65535

    def test_wrapping_multiply(self) -> None:
        """512 * 128 = 65536 -> wraps to 0."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        script = Script((
            VarDef("x", BinaryOp(IntegerExpr(512), Operator.MULTIPLY, IntegerExpr(128))),
        ))
        interpreter.interpret(script)
        assert interpreter._globals["x"] == 0

    def test_power_wraps_modular(self) -> None:
        """2^16 wraps: pow(2, 16, 65536) = 0."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        script = Script((
            VarDef("x", BinaryOp(IntegerExpr(2), Operator.POWER, IntegerExpr(16))),
        ))
        interpreter.interpret(script)
        assert interpreter._globals["x"] == 0

    # ── Bitwise ────────────────────────────────────────────────────

    def test_bitwise_and(self) -> None:
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        expr = BinaryOp(IntegerExpr(0xFF), Operator.BITWISE_AND, IntegerExpr(0x0F))
        script = Script((VarDef("x", expr),))
        interpreter.interpret(script)
        assert interpreter._globals["x"] == 0x0F

    def test_bitwise_or(self) -> None:
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        expr = BinaryOp(IntegerExpr(0xF0), Operator.BITWISE_OR, IntegerExpr(0x0F))
        script = Script((VarDef("x", expr),))
        interpreter.interpret(script)
        assert interpreter._globals["x"] == 0xFF

    def test_shift_left(self) -> None:
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        expr = BinaryOp(IntegerExpr(1), Operator.SHIFT_LEFT, IntegerExpr(4))
        script = Script((VarDef("x", expr),))
        interpreter.interpret(script)
        assert interpreter._globals["x"] == 16

    def test_shift_right(self) -> None:
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        expr = BinaryOp(IntegerExpr(16), Operator.SHIFT_RIGHT, IntegerExpr(2))
        script = Script((VarDef("x", expr),))
        interpreter.interpret(script)
        assert interpreter._globals["x"] == 4

    # ── Comparison ─────────────────────────────────────────────────

    @pytest.mark.parametrize("op,name", [
        (Operator.LESS, "<"),
        (Operator.LESS_EQUAL, "<="),
        (Operator.GREATER, ">"),
        (Operator.GREATER_EQUAL, ">="),
        (Operator.EQUAL, "=="),
        (Operator.NOT_EQUAL, "!="),
    ])
    def test_comparison_true(self, op: Operator, name: str) -> None:
        """Comparison that evaluates to 1 (true)."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        # 3 < 5, 3 <= 5, 5 > 3, 5 >= 3, 3 == 3, 3 != 5
        if op in (Operator.LESS, Operator.LESS_EQUAL, Operator.NOT_EQUAL):
            left, right = 3, 5
        elif op in (Operator.GREATER, Operator.GREATER_EQUAL):
            left, right = 5, 3
        else:  # EQUAL
            left, right = 3, 3
        expr = BinaryOp(IntegerExpr(left), op, IntegerExpr(right))
        script = Script((VarDef("x", expr),))
        interpreter.interpret(script)
        assert interpreter._globals["x"] == 1, f"{left} {name} {right} should be true"

    @pytest.mark.parametrize("op,name", [
        (Operator.LESS, "<"),
        (Operator.LESS_EQUAL, "<="),
        (Operator.GREATER, ">"),
        (Operator.GREATER_EQUAL, ">="),
        (Operator.EQUAL, "=="),
        (Operator.NOT_EQUAL, "!="),
    ])
    def test_comparison_false(self, op: Operator, name: str) -> None:
        """Comparison that evaluates to 0 (false)."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        # 5 < 3, 5 <= 3, 3 > 5, 3 >= 5, 5 == 3, 5 != 5
        if op == Operator.NOT_EQUAL:
            left, right = 5, 5  # 5 != 5 is False
        elif op in (Operator.LESS, Operator.LESS_EQUAL, Operator.EQUAL):
            left, right = 5, 3
        elif op in (Operator.GREATER, Operator.GREATER_EQUAL):
            left, right = 3, 5
        else:
            left, right = 3, 3
        expr = BinaryOp(IntegerExpr(left), op, IntegerExpr(right))
        script = Script((VarDef("x", expr),))
        interpreter.interpret(script)
        assert interpreter._globals["x"] == 0, f"{left} {name} {right} should be false"

    # ── Unary ──────────────────────────────────────────────────────

    def test_unary_minus(self) -> None:
        """-5 evaluates to 65531 (wrapped)."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        script = Script((VarDef("x", UnaryOp(Operator.SUBTRACT, IntegerExpr(5))),))
        interpreter.interpret(script)
        assert interpreter._globals["x"] == 65531

    def test_unary_not_zero(self) -> None:
        """!0 evaluates to 1."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        script = Script((VarDef("x", UnaryOp(Operator.NOT, IntegerExpr(0))),))
        interpreter.interpret(script)
        assert interpreter._globals["x"] == 1

    def test_unary_not_nonzero(self) -> None:
        """!42 evaluates to 0."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        script = Script((VarDef("x", UnaryOp(Operator.NOT, IntegerExpr(42))),))
        interpreter.interpret(script)
        assert interpreter._globals["x"] == 0

    # ── Grouping ───────────────────────────────────────────────────

    def test_grouping_overrides_precedence(self) -> None:
        """(4 + 3) * 2 evaluates to 14."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        expr = BinaryOp(
            GroupExpr(BinaryOp(IntegerExpr(4), Operator.ADD, IntegerExpr(3))),
            Operator.MULTIPLY,
            IntegerExpr(2),
        )
        script = Script((VarDef("x", expr),))
        interpreter.interpret(script)
        assert interpreter._globals["x"] == 14

    # ── Short-circuit logical ──────────────────────────────────────

    def test_logical_and_true(self) -> None:
        """1 && 1 evaluates to 1."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        expr = BinaryOp(IntegerExpr(1), Operator.LOGICAL_AND, IntegerExpr(1))
        script = Script((VarDef("x", expr),))
        interpreter.interpret(script)
        assert interpreter._globals["x"] == 1

    def test_logical_and_false_left(self) -> None:
        """0 && <anything> evaluates to 0 (short-circuit)."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        expr = BinaryOp(IntegerExpr(0), Operator.LOGICAL_AND, IntegerExpr(42))
        script = Script((VarDef("x", expr),))
        interpreter.interpret(script)
        assert interpreter._globals["x"] == 0

    def test_logical_or_true_left(self) -> None:
        """1 || <anything> evaluates to 1 (short-circuit)."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        expr = BinaryOp(IntegerExpr(1), Operator.LOGICAL_OR, IntegerExpr(42))
        script = Script((VarDef("x", expr),))
        interpreter.interpret(script)
        assert interpreter._globals["x"] == 1

    def test_logical_or_false(self) -> None:
        """0 || 0 evaluates to 0."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        expr = BinaryOp(IntegerExpr(0), Operator.LOGICAL_OR, IntegerExpr(0))
        script = Script((VarDef("x", expr),))
        interpreter.interpret(script)
        assert interpreter._globals["x"] == 0


class TestErrors:
    """Runtime errors during interpretation."""

    def test_divide_by_zero(self) -> None:
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        script = Script((
            VarDef("x", BinaryOp(IntegerExpr(1), Operator.DIVIDE, IntegerExpr(0))),
        ))
        with pytest.raises(InterpreterError, match="Division by zero"):
            interpreter.interpret(script)

    def test_modulo_by_zero(self) -> None:
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        script = Script((
            VarDef("x", BinaryOp(IntegerExpr(1), Operator.MODULO, IntegerExpr(0))),
        ))
        with pytest.raises(InterpreterError, match="Division by zero .modulo."):
            interpreter.interpret(script)

    def test_undeclared_variable_read(self) -> None:
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        script = Script((VarDef("x", DollarIdentifierExpr("y")),))
        with pytest.raises(InterpreterError, match="Undeclared variable"):
            interpreter.interpret(script)

    def test_undeclared_variable_assignment(self) -> None:
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        script = Script((AssignStmt("x", IntegerExpr(42)),))
        with pytest.raises(InterpreterError, match="Undeclared variable"):
            interpreter.interpret(script)

    def test_string_in_expression_context(self) -> None:
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        script = Script((VarDef("x", StringExpr("hello")),))
        interpreter.interpret(script)
        assert interpreter._globals["x"] == 0


class TestDelayStatements:
    """DELAY, DEFAULTDELAY, DEFAULTCHARDELAY."""

    def test_delay(self) -> None:
        """DELAY 500 calls platform.delay_ms(500)."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        script = Script((DelayStmt(IntegerExpr(500)),))
        interpreter.interpret(script)
        assert ("delay_ms", 500) in platform.calls

    def test_delay_minimum_clamp(self) -> None:
        """DELAY 5 is clamped to minimum 20."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        script = Script((DelayStmt(IntegerExpr(5)),))
        interpreter.interpret(script)
        # Should be 20, not 5
        delay_calls = [c for c in platform.calls if c[0] == "delay_ms"]
        assert delay_calls[0] == ("delay_ms", 20)

    def test_delay_with_expression(self) -> None:
        """DELAY $x uses variable value."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        script = Script((
            VarDef("ms", IntegerExpr(250)),
            DelayStmt(DollarIdentifierExpr("ms")),
        ))
        interpreter.interpret(script)
        assert ("delay_ms", 250) in platform.calls

    def test_default_delay_sets_value(self) -> None:
        """DEFAULTDELAY 100 calls set_default_delay_ms(100)."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        script = Script((DefaultDelayStmt(IntegerExpr(100)),))
        interpreter.interpret(script)
        assert ("set_default_delay_ms", 100) in platform.calls
        assert interpreter._default_delay == 100

    def test_default_char_delay(self) -> None:
        """DEFAULTCHARDELAY 50 sets _default_char_delay."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        script = Script((DefaultCharDelayStmt(IntegerExpr(50)),))
        interpreter.interpret(script)
        assert interpreter._default_char_delay == 50


class TestRepeat:
    """REPEAT <count> semantics."""

    def test_repeat_three_times(self) -> None:
        """REPEAT 3 repeats preceding DELAY 3 additional times."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        script = Script((
            DelayStmt(IntegerExpr(100)),
            RepeatStmt(IntegerExpr(3)),
        ))
        interpreter.interpret(script)
        # 1 original + 3 repeated = 4 delay_ms(100) calls
        delay_calls = [c for c in platform.calls if c[0] == "delay_ms"]
        assert len(delay_calls) == 4
        for call in delay_calls:
            assert call == ("delay_ms", 100)

    def test_repeat_count_from_variable(self) -> None:
        """REPEAT $n uses variable value as count."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        script = Script((
            VarDef("n", IntegerExpr(2)),
            DelayStmt(IntegerExpr(50)),
            RepeatStmt(DollarIdentifierExpr("n")),
        ))
        interpreter.interpret(script)
        # 1 original + 2 repeated = 3 delay_ms(50) calls
        delay_calls = [c for c in platform.calls if c[0] == "delay_ms"]
        assert len(delay_calls) == 3

    def test_repeat_zero_does_nothing(self) -> None:
        """REPEAT 0 adds no extra executions."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        script = Script((
            DelayStmt(IntegerExpr(100)),
            RepeatStmt(IntegerExpr(0)),
        ))
        interpreter.interpret(script)
        delay_calls = [c for c in platform.calls if c[0] == "delay_ms"]
        assert len(delay_calls) == 1

    def test_repeat_without_preceding_statement_error(self) -> None:
        """REPEAT as the first statement raises an error."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        script = Script((RepeatStmt(IntegerExpr(3)),))
        with pytest.raises(InterpreterError, match="REPEAT without preceding"):
            interpreter.interpret(script)


class TestPayloadControl:
    """Reset, StopPayload, RestartPayload."""

    def test_reset(self) -> None:
        """ResetStmt calls platform.release_all()."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        script = Script((ResetStmt(),))
        interpreter.interpret(script)
        assert ("release_all",) in platform.calls

    def test_stop_payload_raises_signal(self) -> None:
        """StopPayloadStmt raises StopPayloadSignal."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        script = Script((StopPayloadStmt(),))
        with pytest.raises(StopPayloadSignal):
            interpreter.interpret(script)
        assert ("stop_payload",) in platform.calls

    def test_restart_payload_raises_signal(self) -> None:
        """RestartPayloadStmt raises RestartPayloadSignal."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        script = Script((RestartPayloadStmt(),))
        with pytest.raises(RestartPayloadSignal):
            interpreter.interpret(script)
        assert ("restart_payload",) in platform.calls

    def test_stop_payload_no_further_statements(self) -> None:
        """Statements after StopPayload are never executed."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        script = Script((
            VarDef("x", IntegerExpr(1)),
            StopPayloadStmt(),
            VarDef("y", IntegerExpr(2)),
        ))
        with pytest.raises(StopPayloadSignal):
            interpreter.interpret(script)
        assert "y" not in interpreter._globals


class TestDefaultDelaySemantics:
    """Inter-statement delay via DEFAULTDELAY."""

    def test_default_delay_between_statements(self) -> None:
        """DEFAULTDELAY causes delay_ms calls between subsequent statements."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        script = Script((
            DefaultDelayStmt(IntegerExpr(50)),
            VarDef("x", IntegerExpr(1)),
            VarDef("y", IntegerExpr(2)),
        ))
        interpreter.interpret(script)
        delay_calls = [c for c in platform.calls if c[0] == "delay_ms"]
        # One delay after each VAR (but not after DEFAULTDELAY itself)
        assert len(delay_calls) == 2
        for call in delay_calls:
            assert call == ("delay_ms", 50)

    def test_no_default_delay_after_delay_stmt(self) -> None:
        """No default delay applied after DELAY itself."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        script = Script((
            DefaultDelayStmt(IntegerExpr(50)),
            DelayStmt(IntegerExpr(100)),
            VarDef("x", IntegerExpr(1)),
        ))
        interpreter.interpret(script)
        delay_ms_calls = [c for c in platform.calls if c[0] == "delay_ms"]
        assert len(delay_ms_calls) == 2
        assert delay_ms_calls[0] == ("delay_ms", 100)
        assert delay_ms_calls[1] == ("delay_ms", 50)

    def test_default_delay_zero_has_no_effect(self) -> None:
        """Default delay of 0 produces no extra delay_ms calls."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        script = Script((
            DefaultDelayStmt(IntegerExpr(0)),
            VarDef("x", IntegerExpr(1)),
            VarDef("y", IntegerExpr(2)),
        ))
        interpreter.interpret(script)
        delay_calls = [c for c in platform.calls if c[0] == "delay_ms"]
        assert len(delay_calls) == 0

    def test_default_delay_after_default_char_delay(self) -> None:
        """No default delay applied after DEFAULTCHARDELAY."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        script = Script((
            DefaultDelayStmt(IntegerExpr(50)),
            DefaultCharDelayStmt(IntegerExpr(30)),
            VarDef("x", IntegerExpr(1)),
        ))
        interpreter.interpret(script)
        # Default delay should NOT fire after DefaultCharDelayStmt
        # Should fire only after VarDef
        delay_calls = [c for c in platform.calls if c[0] == "delay_ms"]
        assert len(delay_calls) == 1
        assert delay_calls[0] == ("delay_ms", 50)

    def test_call_order_with_default_delay(self) -> None:
        """Full call sequence with default delay matches expected order."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        script = Script((
            VarDef("x", IntegerExpr(10)),
            DefaultDelayStmt(IntegerExpr(30)),
            VarDef("y", IntegerExpr(20)),
            DelayStmt(IntegerExpr(200)),
            VarDef("z", IntegerExpr(30)),
        ))
        interpreter.interpret(script)
        # Expected delay_ms calls:
        #   VarDef x:   _default_delay still 0 → no delay
        #   DefaultDelayStmt: excluded by isinstance check → no delay
        #   VarDef y:   default delay → delay_ms(30)
        #   DelayStmt:  explicit delay → delay_ms(200), then excluded from default
        #   VarDef z:   default delay → delay_ms(30)
        delay_calls = [c for c in platform.calls if c[0] == "delay_ms"]
        assert len(delay_calls) == 3
        assert delay_calls[0] == ("delay_ms", 30)
        assert delay_calls[1] == ("delay_ms", 200)
        assert delay_calls[2] == ("delay_ms", 30)
