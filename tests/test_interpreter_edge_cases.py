"""Edge case and stress tests for the DuckyScript 3 interpreter.

Covers: nested functions, recursion limits, nested loops, variable
shadowing, 16-bit overflow/wrapping, REPEAT corner cases, and function
registration edge cases.  Uses direct AST construction for interpreter-
level tests and the ``_execute`` helper for full-pipeline tests.
"""

import pytest

from ducky.ast import (
    AssignStmt,
    BinaryOp,
    BreakStmt,
    CallExpr,
    CallStmt,
    ContinueStmt,
    DelayStmt,
    DollarIdentifierExpr,
    FunctionDef,
    IfStmt,
    IntegerExpr,
    KeyStmt,
    RepeatStmt,
    ReturnStmt,
    Script,
    StringLnStmt,
    UnaryOp,
    VarDef,
    WhileStmt,
)
from ducky.interpreter import Interpreter, InterpreterError
from ducky.platform.desktop import DesktopPlatform
from ducky.tokens import ActionKey, Operator


def _execute(source: str) -> DesktopPlatform:
    """Preprocess, tokenize, parse, interpret *source* and return the platform mock."""
    from ducky.lexer import DuckyLexer
    from ducky.parser import DuckyParser
    from ducky.preprocessor import Preprocessor

    preprocessed = Preprocessor().preprocess(source)
    tokens = DuckyLexer().tokenize(preprocessed)
    script = DuckyParser(tokens).parse()
    platform = DesktopPlatform()
    Interpreter(platform).interpret(script)
    return platform


# ═══════════════════════════════════════════════════════════════════════
# A2. Nested functions
# ═══════════════════════════════════════════════════════════════════════


class TestNestedFunctions:
    """Function composition: calls, nesting, recursion."""

    def test_function_a_calls_b(self) -> None:
        """Function A calls Function B — B's body executes."""
        platform = DesktopPlatform()
        interp = Interpreter(platform)
        script = Script((
            FunctionDef("b", (), (StringLnStmt("B"),)),
            FunctionDef("a", (), (CallStmt("b"),)),
            CallStmt("a"),
        ))
        interp.interpret(script)
        assert platform.output == ["B"]

    def test_function_self_call(self) -> None:
        """Function calling itself once (direct recursion, one level)."""
        platform = DesktopPlatform()
        interp = Interpreter(platform)
        # $depth = 1
        # FUNCTION f() -> IF ($depth > 0) THEN $depth = $depth - 1; f() END_IF
        # f()
        # STRINGLN "done"
        script = Script((
            VarDef("depth", IntegerExpr(1)),
            FunctionDef("f", (), (
                IfStmt(
                    condition=BinaryOp(
                        DollarIdentifierExpr("depth"),
                        Operator.GREATER,
                        IntegerExpr(0),
                    ),
                    body=(
                        AssignStmt(
                            "depth",
                            BinaryOp(
                                DollarIdentifierExpr("depth"),
                                Operator.SUBTRACT,
                                IntegerExpr(1),
                            ),
                        ),
                        CallStmt("f"),
                    ),
                ),
            )),
            CallStmt("f"),
            StringLnStmt("done"),
        ))
        interp.interpret(script)
        assert platform.output == ["done"]

    def test_function_call_in_if_body(self) -> None:
        """Function call inside IF body executes when condition truthy."""
        platform = DesktopPlatform()
        interp = Interpreter(platform)
        script = Script((
            FunctionDef("greet", (), (StringLnStmt("hello"),)),
            IfStmt(
                condition=IntegerExpr(1),
                body=(CallStmt("greet"),),
            ),
        ))
        interp.interpret(script)
        assert platform.output == ["hello"]

    def test_function_call_in_while_body(self) -> None:
        """Function call inside WHILE body executes each iteration."""
        platform = DesktopPlatform()
        interp = Interpreter(platform)
        script = Script((
            VarDef("i", IntegerExpr(3)),
            FunctionDef("ping", (), (StringLnStmt("ping"),)),
            WhileStmt(
                condition=BinaryOp(
                    DollarIdentifierExpr("i"),
                    Operator.GREATER,
                    IntegerExpr(0),
                ),
                body=(
                    CallStmt("ping"),
                    AssignStmt(
                        "i",
                        BinaryOp(
                            DollarIdentifierExpr("i"),
                            Operator.SUBTRACT,
                            IntegerExpr(1),
                        ),
                    ),
                ),
            ),
        ))
        interp.interpret(script)
        assert platform.output == ["ping", "ping", "ping"]

    def test_function_calls_in_sequence(self) -> None:
        """Two function calls execute in declaration order."""
        platform = DesktopPlatform()
        interp = Interpreter(platform)
        script = Script((
            FunctionDef("a", (), (StringLnStmt("A"),)),
            FunctionDef("b", (), (StringLnStmt("B"),)),
            CallStmt("a"),
            CallStmt("b"),
            CallStmt("a"),
        ))
        interp.interpret(script)
        assert platform.output == ["A", "B", "A"]

    def test_mutual_recursion(self) -> None:
        """Mutual recursion (A calls B, B calls A) with base case."""
        platform = DesktopPlatform()
        interp = Interpreter(platform)
        # $depth = 3
        # FUNCTION a() -> IF depth > 0 THEN depth--; b()
        # FUNCTION b() -> IF depth > 0 THEN depth--; a()
        # a()
        script = Script((
            VarDef("depth", IntegerExpr(3)),
            FunctionDef("a", (), (
                IfStmt(
                    condition=BinaryOp(
                        DollarIdentifierExpr("depth"),
                        Operator.GREATER,
                        IntegerExpr(0),
                    ),
                    body=(
                        AssignStmt(
                            "depth",
                            BinaryOp(
                                DollarIdentifierExpr("depth"),
                                Operator.SUBTRACT,
                                IntegerExpr(1),
                            ),
                        ),
                        CallStmt("b"),
                    ),
                ),
            )),
            FunctionDef("b", (), (
                IfStmt(
                    condition=BinaryOp(
                        DollarIdentifierExpr("depth"),
                        Operator.GREATER,
                        IntegerExpr(0),
                    ),
                    body=(
                        AssignStmt(
                            "depth",
                            BinaryOp(
                                DollarIdentifierExpr("depth"),
                                Operator.SUBTRACT,
                                IntegerExpr(1),
                            ),
                        ),
                        CallStmt("a"),
                    ),
                ),
            )),
            CallStmt("a"),
            StringLnStmt("done"),
        ))
        interp.interpret(script)
        assert platform.output == ["done"]


# ═══════════════════════════════════════════════════════════════════════
# A3. Recursion limits
# ═══════════════════════════════════════════════════════════════════════


class TestRecursionLimits:
    """Deep recursion and RETURN-based base cases."""

    def test_deep_recursion_100(self) -> None:
        """Function calling itself 100 times deep completes successfully."""
        platform = DesktopPlatform()
        interp = Interpreter(platform)
        # $count = 100
        # FUNCTION f() -> IF count > 0 THEN count--; f()
        # f()
        script = Script((
            VarDef("count", IntegerExpr(100)),
            FunctionDef("f", (), (
                IfStmt(
                    condition=BinaryOp(
                        DollarIdentifierExpr("count"),
                        Operator.GREATER,
                        IntegerExpr(0),
                    ),
                    body=(
                        AssignStmt(
                            "count",
                            BinaryOp(
                                DollarIdentifierExpr("count"),
                                Operator.SUBTRACT,
                                IntegerExpr(1),
                            ),
                        ),
                        CallStmt("f"),
                    ),
                ),
            )),
            CallStmt("f"),
            StringLnStmt("done"),
        ))
        interp.interpret(script)
        assert platform.output == ["done"]

    def test_recursion_with_return_base_case(self) -> None:
        """Recursion with RETURN in the base case unwinds correctly."""
        platform = DesktopPlatform()
        interp = Interpreter(platform)
        # $depth = 3
        # FUNCTION f()
        #   $depth = $depth - 1
        #   IF ($depth == 0) THEN RETURN 42
        #   f()
        # END_FUNCTION
        # $result = f()  -- return value discarded in CallStmt context
        # STRINGLN "done"
        script = Script((
            VarDef("depth", IntegerExpr(3)),
            FunctionDef("f", (), (
                AssignStmt(
                    "depth",
                    BinaryOp(
                        DollarIdentifierExpr("depth"),
                        Operator.SUBTRACT,
                        IntegerExpr(1),
                    ),
                ),
                IfStmt(
                    condition=BinaryOp(
                        DollarIdentifierExpr("depth"),
                        Operator.EQUAL,
                        IntegerExpr(0),
                    ),
                    body=(ReturnStmt(IntegerExpr(42)),),
                ),
                CallStmt("f"),
            )),
            CallStmt("f"),
            StringLnStmt("done"),
        ))
        interp.interpret(script)
        assert platform.output == ["done"]


# ═══════════════════════════════════════════════════════════════════════
# A4. Nested loops
# ═══════════════════════════════════════════════════════════════════════


class TestNestedLoops:
    """Nested WHILE loops with BREAK and CONTINUE."""

    def test_while_inside_while_inner_break(self) -> None:
        """Inner BREAK exits only the inner WHILE, outer continues."""
        platform = DesktopPlatform()
        interp = Interpreter(platform)
        # $i = 2
        # WHILE ($i > 0)
        #   $i = $i - 1
        #   $j = 2
        #   WHILE ($j > 0)
        #     $j = $j - 1
        #     STRINGLN "inner"
        #     BREAK
        #   END_WHILE
        #   STRINGLN "outer"
        # END_WHILE
        script = Script((
            VarDef("i", IntegerExpr(2)),
            VarDef("j", IntegerExpr(0)),
            WhileStmt(
                condition=BinaryOp(
                    DollarIdentifierExpr("i"), Operator.GREATER, IntegerExpr(0),
                ),
                body=(
                    AssignStmt(
                        "i",
                        BinaryOp(DollarIdentifierExpr("i"), Operator.SUBTRACT, IntegerExpr(1)),
                    ),
                    AssignStmt("j", IntegerExpr(2)),
                    WhileStmt(
                        condition=BinaryOp(
                            DollarIdentifierExpr("j"), Operator.GREATER, IntegerExpr(0),
                        ),
                        body=(
                            AssignStmt(
                                "j",
                                BinaryOp(
                                    DollarIdentifierExpr("j"), Operator.SUBTRACT, IntegerExpr(1),
                                ),
                            ),
                            StringLnStmt("inner"),
                            BreakStmt(),
                        ),
                    ),
                    StringLnStmt("outer"),
                ),
            ),
        ))
        interp.interpret(script)
        # Each outer iteration: one "inner" (BREAK exits inner), then "outer"
        assert platform.output == ["inner", "outer", "inner", "outer"]

    def test_while_inside_while_inner_continue(self) -> None:
        """Inner CONTINUE skips to inner loop check, outer continues."""
        platform = DesktopPlatform()
        interp = Interpreter(platform)
        # $i = 2
        # WHILE ($i > 0)
        #   $i = $i - 1
        #   $j = 2
        #   WHILE ($j > 0)
        #     $j = $j - 1
        #     IF ($j > 0) THEN CONTINUE
        #     STRINGLN "inner"
        #   END_WHILE
        #   STRINGLN "outer"
        # END_WHILE
        script = Script((
            VarDef("i", IntegerExpr(2)),
            VarDef("j", IntegerExpr(0)),
            WhileStmt(
                condition=BinaryOp(
                    DollarIdentifierExpr("i"), Operator.GREATER, IntegerExpr(0),
                ),
                body=(
                    AssignStmt(
                        "i",
                        BinaryOp(DollarIdentifierExpr("i"), Operator.SUBTRACT, IntegerExpr(1)),
                    ),
                    AssignStmt("j", IntegerExpr(2)),
                    WhileStmt(
                        condition=BinaryOp(
                            DollarIdentifierExpr("j"), Operator.GREATER, IntegerExpr(0),
                        ),
                        body=(
                            AssignStmt(
                                "j",
                                BinaryOp(
                                    DollarIdentifierExpr("j"), Operator.SUBTRACT, IntegerExpr(1),
                                ),
                            ),
                            IfStmt(
                                condition=BinaryOp(
                                    DollarIdentifierExpr("j"),
                                    Operator.GREATER,
                                    IntegerExpr(0),
                                ),
                                body=(ContinueStmt(),),
                            ),
                            StringLnStmt("inner"),
                        ),
                    ),
                    StringLnStmt("outer"),
                ),
            ),
        ))
        interp.interpret(script)
        # Outer loop: 2 iterations
        # Inner loop per outer: $j starts at 2, becomes 1, CONTINUE skips
        #   "inner", then $j becomes 0, prints "inner"
        # Expected: "inner" once per outer iter + "outer" after each = 2 + 2
        assert platform.output == ["inner", "outer", "inner", "outer"]

    def test_break_outside_loop_raises_error(self) -> None:
        """BREAK outside any WHILE loop raises InterpreterError."""
        platform = DesktopPlatform()
        interp = Interpreter(platform)
        script = Script((BreakStmt(),))
        with pytest.raises(InterpreterError, match="BREAK outside WHILE loop"):
            interp.interpret(script)

    def test_continue_outside_loop_raises_error(self) -> None:
        """CONTINUE outside any WHILE loop raises InterpreterError."""
        platform = DesktopPlatform()
        interp = Interpreter(platform)
        script = Script((ContinueStmt(),))
        with pytest.raises(InterpreterError, match="CONTINUE outside WHILE loop"):
            interp.interpret(script)

    def test_if_inside_while_else_branch(self) -> None:
        """IF inside WHILE — ELSE branch taken when condition is false."""
        platform = DesktopPlatform()
        interp = Interpreter(platform)
        # $i = 2
        # WHILE ($i > 0)
        #   $i = $i - 1
        #   IF ($i == 0) THEN
        #     STRINGLN "zero"
        #   ELSE
        #     STRINGLN "nonzero"
        #   END_IF
        # END_WHILE
        script = Script((
            VarDef("i", IntegerExpr(2)),
            WhileStmt(
                condition=BinaryOp(
                    DollarIdentifierExpr("i"), Operator.GREATER, IntegerExpr(0),
                ),
                body=(
                    AssignStmt(
                        "i",
                        BinaryOp(DollarIdentifierExpr("i"), Operator.SUBTRACT, IntegerExpr(1)),
                    ),
                    IfStmt(
                        condition=BinaryOp(
                            DollarIdentifierExpr("i"), Operator.EQUAL, IntegerExpr(0),
                        ),
                        body=(StringLnStmt("zero"),),
                        else_body=(StringLnStmt("nonzero"),),
                    ),
                ),
            ),
        ))
        interp.interpret(script)
        # $i=1 (nonzero), $i=0 (zero)
        assert platform.output == ["nonzero", "zero"]


# ═══════════════════════════════════════════════════════════════════════
# A5. Variable shadowing
# ═══════════════════════════════════════════════════════════════════════


class TestVariableShadowing:
    """Local vs. global variable scoping."""

    def test_global_shadowed_by_local_in_function(self) -> None:
        """Function-local $x shadows global $x — global unchanged after call."""
        platform = DesktopPlatform()
        interp = Interpreter(platform)
        # VAR $x = 1
        # FUNCTION f()
        #   VAR $x = 2
        #   $x = 3  -- assigns to local $x
        # END_FUNCTION
        # f()
        # After function: global $x == 1
        script = Script((
            VarDef("x", IntegerExpr(1)),
            FunctionDef("f", (), (
                VarDef("x", IntegerExpr(2)),
                AssignStmt("x", IntegerExpr(3)),
            )),
            CallStmt("f"),
            # Use $x in an expression to verify global value
            # STRING "value=" then STRINGLN $x as string... we'll check _globals
        ))
        interp.interpret(script)
        assert interp._globals["x"] == 1, (
            "Global $x should be 1 — function-local $x must not leak"
        )

    def test_local_not_persist_after_function_exits(self) -> None:
        """Local $x defined inside function is gone after function returns."""
        platform = DesktopPlatform()
        interp = Interpreter(platform)
        # FUNCTION f()
        #   VAR $x = 99
        #   STRINGLN "inside"
        # END_FUNCTION
        # f()
        # VAR $x = 1  -- fresh global
        # $x should be 1, not 99
        script = Script((
            FunctionDef("f", (), (
                VarDef("x", IntegerExpr(99)),
                StringLnStmt("inside"),
            )),
            CallStmt("f"),
            VarDef("x", IntegerExpr(1)),
        ))
        interp.interpret(script)
        assert interp._globals["x"] == 1, (
            "Local $x from function must not persist"
        )

    def test_assign_to_global_from_function(self) -> None:
        """Assignment `=` to an existing global variable from inside a function."""
        platform = DesktopPlatform()
        interp = Interpreter(platform)
        # VAR $x = 10
        # FUNCTION f()
        #   $x = 20  -- no local $x, finds global
        # END_FUNCTION
        # f()
        # After: global $x == 20
        script = Script((
            VarDef("x", IntegerExpr(10)),
            FunctionDef("f", (), (
                AssignStmt("x", IntegerExpr(20)),
            )),
            CallStmt("f"),
        ))
        interp.interpret(script)
        assert interp._globals["x"] == 20, (
            "Assignment should reach and update the global $x"
        )


# ═══════════════════════════════════════════════════════════════════════
# A7. Overflow / 16-bit wrapping
# ═══════════════════════════════════════════════════════════════════════


class TestOverflowWrapping:
    """16-bit unsigned wrapping for all arithmetic operations."""

    # ── Addition ─────────────────────────────────────────────────────

    def test_add_overflow_max_plus_1(self) -> None:
        """65535 + 1 wraps to 0."""
        platform = DesktopPlatform()
        interp = Interpreter(platform)
        script = Script((
            VarDef("r", BinaryOp(IntegerExpr(65535), Operator.ADD, IntegerExpr(1))),
        ))
        interp.interpret(script)
        assert interp._globals["r"] == 0

    def test_add_overflow_half_max_double(self) -> None:
        """32768 + 32768 wraps to 0."""
        platform = DesktopPlatform()
        interp = Interpreter(platform)
        script = Script((
            VarDef("r", BinaryOp(IntegerExpr(32768), Operator.ADD, IntegerExpr(32768))),
        ))
        interp.interpret(script)
        assert interp._globals["r"] == 0

    def test_add_no_wrap_small(self) -> None:
        """100 + 200 = 300 (no wrap)."""
        platform = DesktopPlatform()
        interp = Interpreter(platform)
        script = Script((
            VarDef("r", BinaryOp(IntegerExpr(100), Operator.ADD, IntegerExpr(200))),
        ))
        interp.interpret(script)
        assert interp._globals["r"] == 300

    # ── Subtraction ──────────────────────────────────────────────────

    def test_subtract_underflow_zero_minus_1(self) -> None:
        """0 - 1 wraps to 65535."""
        platform = DesktopPlatform()
        interp = Interpreter(platform)
        script = Script((
            VarDef("r", BinaryOp(IntegerExpr(0), Operator.SUBTRACT, IntegerExpr(1))),
        ))
        interp.interpret(script)
        assert interp._globals["r"] == 65535

    def test_subtract_underflow_1_minus_2(self) -> None:
        """1 - 2 wraps to 65535."""
        platform = DesktopPlatform()
        interp = Interpreter(platform)
        script = Script((
            VarDef("r", BinaryOp(IntegerExpr(1), Operator.SUBTRACT, IntegerExpr(2))),
        ))
        interp.interpret(script)
        assert interp._globals["r"] == 65535

    def test_subtract_zero_minus_zero(self) -> None:
        """0 - 0 = 0."""
        platform = DesktopPlatform()
        interp = Interpreter(platform)
        script = Script((
            VarDef("r", BinaryOp(IntegerExpr(0), Operator.SUBTRACT, IntegerExpr(0))),
        ))
        interp.interpret(script)
        assert interp._globals["r"] == 0

    # ── Multiplication ───────────────────────────────────────────────

    def test_multiply_overflow_max_squared(self) -> None:
        """65535 * 65535 wraps to 1."""
        platform = DesktopPlatform()
        interp = Interpreter(platform)
        script = Script((
            VarDef("r", BinaryOp(IntegerExpr(65535), Operator.MULTIPLY, IntegerExpr(65535))),
        ))
        interp.interpret(script)
        assert interp._globals["r"] == 1

    def test_multiply_no_wrap_small(self) -> None:
        """10 * 10 = 100 (no wrap)."""
        platform = DesktopPlatform()
        interp = Interpreter(platform)
        script = Script((
            VarDef("r", BinaryOp(IntegerExpr(10), Operator.MULTIPLY, IntegerExpr(10))),
        ))
        interp.interpret(script)
        assert interp._globals["r"] == 100

    # ── Exponentiation ───────────────────────────────────────────────

    def test_power_2_to_16_wraps(self) -> None:
        """2 ** 16 wraps to 0 (65536 mod 65536)."""
        platform = DesktopPlatform()
        interp = Interpreter(platform)
        script = Script((
            VarDef("r", BinaryOp(IntegerExpr(2), Operator.POWER, IntegerExpr(16))),
        ))
        interp.interpret(script)
        assert interp._globals["r"] == 0

    def test_power_2_to_17_wraps(self) -> None:
        """2 ** 17 wraps to 0."""
        platform = DesktopPlatform()
        interp = Interpreter(platform)
        script = Script((
            VarDef("r", BinaryOp(IntegerExpr(2), Operator.POWER, IntegerExpr(17))),
        ))
        interp.interpret(script)
        assert interp._globals["r"] == 0

    # ── Unary negation ──────────────────────────────────────────────

    def test_unary_negation_minus_1_wraps(self) -> None:
        """-1 wraps to 65535."""
        platform = DesktopPlatform()
        interp = Interpreter(platform)
        script = Script((
            VarDef("r", UnaryOp(Operator.SUBTRACT, IntegerExpr(1))),
        ))
        interp.interpret(script)
        assert interp._globals["r"] == 65535

    def test_unary_negation_minus_0(self) -> None:
        """-0 = 0."""
        platform = DesktopPlatform()
        interp = Interpreter(platform)
        script = Script((
            VarDef("r", UnaryOp(Operator.SUBTRACT, IntegerExpr(0))),
        ))
        interp.interpret(script)
        assert interp._globals["r"] == 0

    # ── All five arithmetic ops wrap ─────────────────────────────────

    def test_all_arithmetic_ops_wrap(self) -> None:
        """All 5 arithmetic binary operators produce 16-bit wrapped results."""
        platform = DesktopPlatform()
        interp = Interpreter(platform)
        script = Script((
            VarDef("add", BinaryOp(IntegerExpr(65535), Operator.ADD, IntegerExpr(2))),
            VarDef("sub", BinaryOp(IntegerExpr(0), Operator.SUBTRACT, IntegerExpr(3))),
            VarDef("mul", BinaryOp(IntegerExpr(256), Operator.MULTIPLY, IntegerExpr(256))),
            VarDef("div", BinaryOp(IntegerExpr(7), Operator.DIVIDE, IntegerExpr(3))),
            VarDef("mod", BinaryOp(IntegerExpr(10), Operator.MODULO, IntegerExpr(3))),
        ))
        interp.interpret(script)
        # 65535 + 2 = 65537 & 0xFFFF = 1
        assert interp._globals["add"] == 1
        # 0 - 3 = -3 & 0xFFFF = 65533
        assert interp._globals["sub"] == 65533
        # 256 * 256 = 65536 & 0xFFFF = 0
        assert interp._globals["mul"] == 0
        # 7 // 3 = 2 (no wrap, integer division)
        assert interp._globals["div"] == 2
        # 10 % 3 = 1 (no wrap)
        assert interp._globals["mod"] == 1

    # ── Division by zero ────────────────────────────────────────────

    def test_divide_by_zero_raises(self) -> None:
        """Division by zero raises InterpreterError."""
        platform = DesktopPlatform()
        interp = Interpreter(platform)
        script = Script((
            VarDef("r", BinaryOp(IntegerExpr(10), Operator.DIVIDE, IntegerExpr(0))),
        ))
        with pytest.raises(InterpreterError, match="Division by zero"):
            interp.interpret(script)

    def test_modulo_by_zero_raises(self) -> None:
        """Modulo by zero raises InterpreterError."""
        platform = DesktopPlatform()
        interp = Interpreter(platform)
        script = Script((
            VarDef("r", BinaryOp(IntegerExpr(10), Operator.MODULO, IntegerExpr(0))),
        ))
        with pytest.raises(InterpreterError, match="Division by zero"):
            interp.interpret(script)


# ═══════════════════════════════════════════════════════════════════════
# A8. REPEAT corner cases
# ═══════════════════════════════════════════════════════════════════════


class TestRepeatCornerCases:
    """REPEAT semantics: counts, edge cases, and error paths."""

    def test_repeat_1(self) -> None:
        """REPEAT 1 executes the preceding statement once (total 2)."""
        platform = DesktopPlatform()
        interp = Interpreter(platform)
        script = Script((
            StringLnStmt("x"),
            RepeatStmt(IntegerExpr(1)),
        ))
        interp.interpret(script)
        assert platform.output == ["x", "x"]

    def test_repeat_0(self) -> None:
        """REPEAT 0 executes the preceding statement zero times (total 1)."""
        platform = DesktopPlatform()
        interp = Interpreter(platform)
        script = Script((
            StringLnStmt("x"),
            RepeatStmt(IntegerExpr(0)),
        ))
        interp.interpret(script)
        assert platform.output == ["x"]

    def test_repeat_2(self) -> None:
        """REPEAT 2 executes the preceding statement twice (total 3)."""
        platform = DesktopPlatform()
        interp = Interpreter(platform)
        script = Script((
            StringLnStmt("x"),
            RepeatStmt(IntegerExpr(2)),
        ))
        interp.interpret(script)
        assert platform.output == ["x", "x", "x"]

    def test_repeat_65535_no_error(self) -> None:
        """REPEAT 65535 executes many times without error."""
        platform = DesktopPlatform()
        interp = Interpreter(platform)
        script = Script((
            KeyStmt(ActionKey.ENTER),
            RepeatStmt(IntegerExpr(65535)),
        ))
        interp.interpret(script)
        # 1 original + 65535 repeats = 65536 ENTER calls
        enter_calls = [c for c in platform.calls if c[0] == "press_key"]
        assert len(enter_calls) == 65536

    def test_repeat_without_preceding_raises(self) -> None:
        """REPEAT without a preceding statement raises InterpreterError."""
        platform = DesktopPlatform()
        interp = Interpreter(platform)
        script = Script((RepeatStmt(IntegerExpr(5)),))
        with pytest.raises(InterpreterError, match="REPEAT without preceding"):
            interp.interpret(script)

    def test_repeat_after_delay(self) -> None:
        """REPEAT after DELAY repeats the delay statement."""
        platform = DesktopPlatform()
        interp = Interpreter(platform)
        script = Script((
            DelayStmt(IntegerExpr(100)),
            RepeatStmt(IntegerExpr(2)),
            StringLnStmt("done"),
        ))
        interp.interpret(script)
        delay_calls = [c for c in platform.calls if c[0] == "delay_ms"]
        # DELAY 100 (clamped to max(20, 100) = 100) executed 3 times
        # (1 original + 2 from REPEAT)
        assert len(delay_calls) == 3
        for call in delay_calls:
            assert call == ("delay_ms", 100)

    def test_repeat_chain(self) -> None:
        """Two REPEAT statements in a row both repeat the original statement.

        REPEAT does NOT update _last_stmt, so both REPEAT statements
        reference the same preceding non-control statement.
        """
        platform = DesktopPlatform()
        interp = Interpreter(platform)
        script = Script((
            StringLnStmt("x"),
            RepeatStmt(IntegerExpr(2)),  # repeats "x" 2× → 3 total
            RepeatStmt(IntegerExpr(3)),  # repeats "x" 3× → 6 total
        ))
        interp.interpret(script)
        # Original (1) + repeat-2 (2) + repeat-3 (3) = 6
        assert len(platform.output) == 6


# ═══════════════════════════════════════════════════════════════════════
# A9. FUNCTION registration edge cases
# ═══════════════════════════════════════════════════════════════════════


class TestFunctionRegistrationEdgeCases:
    """Function definition, lookup, and lifecycle."""

    def test_call_undefined_function_raises(self) -> None:
        """Calling a function that was never defined raises InterpreterError."""
        platform = DesktopPlatform()
        interp = Interpreter(platform)
        script = Script((CallStmt("nonexistent"),))
        with pytest.raises(InterpreterError, match="Undefined function"):
            interp.interpret(script)

    def test_duplicate_function_last_wins(self) -> None:
        """Defining two functions with the same name — the second overwrites the first."""
        platform = DesktopPlatform()
        interp = Interpreter(platform)
        script = Script((
            FunctionDef("f", (), (StringLnStmt("first"),)),
            FunctionDef("f", (), (StringLnStmt("second"),)),
            CallStmt("f"),
        ))
        interp.interpret(script)
        assert platform.output == ["second"]

    def test_function_return_no_value(self) -> None:
        """RETURN with no expression returns 0 in expression context."""
        platform = DesktopPlatform()
        interp = Interpreter(platform)
        # FUNCTION f() -> RETURN
        # VAR $r = f()    -> $r should be 0
        script = Script((
            FunctionDef("f", (), (ReturnStmt(None),)),
            VarDef("r", CallExpr("f")),
            StringLnStmt("done"),
        ))
        interp.interpret(script)
        assert interp._globals["r"] == 0
        assert platform.output == ["done"]

    def test_function_return_no_value_statement(self) -> None:
        """RETURN with no expression in a statement call (return value discarded)."""
        platform = DesktopPlatform()
        interp = Interpreter(platform)
        script = Script((
            FunctionDef("f", (), (
                ReturnStmt(None),
            )),
            CallStmt("f"),
            StringLnStmt("ok"),
        ))
        interp.interpret(script)
        assert platform.output == ["ok"]

    def test_function_multiple_statements(self) -> None:
        """Function body with multiple statements executes in order."""
        platform = DesktopPlatform()
        interp = Interpreter(platform)
        script = Script((
            FunctionDef("multi", (), (
                StringLnStmt("one"),
                StringLnStmt("two"),
                StringLnStmt("three"),
            )),
            CallStmt("multi"),
        ))
        interp.interpret(script)
        assert platform.output == ["one", "two", "three"]

    def test_function_called_multiple_times(self) -> None:
        """Same function called multiple times produces output each time."""
        platform = DesktopPlatform()
        interp = Interpreter(platform)
        script = Script((
            FunctionDef("ping", (), (StringLnStmt("ping"),)),
            CallStmt("ping"),
            CallStmt("ping"),
            CallStmt("ping"),
        ))
        interp.interpret(script)
        assert platform.output == ["ping", "ping", "ping"]

    def test_undefined_function_in_expression_raises(self) -> None:
        """CallExpr referencing undefined function raises InterpreterError."""
        platform = DesktopPlatform()
        interp = Interpreter(platform)
        script = Script((
            VarDef("x", CallExpr("undefined_func")),
        ))
        with pytest.raises(InterpreterError, match="Undefined function"):
            interp.interpret(script)


# ═══════════════════════════════════════════════════════════════════════
# Cross-cutting: combinations
# ═══════════════════════════════════════════════════════════════════════


class TestCrossCutting:
    """Tests that combine multiple edge-case areas."""

    def test_function_in_loop_with_repeat(self) -> None:
        """Function call inside a WHILE loop with REPEAT after a keyboard statement."""
        platform = DesktopPlatform()
        interp = Interpreter(platform)
        # $i = 2
        # FUNCTION f() -> STRINGLN "f"
        # WHILE ($i > 0)
        #   $i = $i - 1
        #   STRINGLN "loop"
        #   REPEAT 1   -- repeats the preceding STRINGLN "loop"
        #   f()
        # END_WHILE
        script = Script((
            VarDef("i", IntegerExpr(2)),
            FunctionDef("f", (), (StringLnStmt("f"),)),
            WhileStmt(
                condition=BinaryOp(
                    DollarIdentifierExpr("i"), Operator.GREATER, IntegerExpr(0),
                ),
                body=(
                    AssignStmt(
                        "i",
                        BinaryOp(DollarIdentifierExpr("i"), Operator.SUBTRACT, IntegerExpr(1)),
                    ),
                    StringLnStmt("loop"),
                    RepeatStmt(IntegerExpr(1)),
                    CallStmt("f"),
                ),
            ),
        ))
        interp.interpret(script)
        # Per iteration: "loop" (original) + "loop" (repeat 1) + "f"
        # 2 iterations: 4 "loop" + 2 "f"
        assert platform.output == ["loop", "loop", "f", "loop", "loop", "f"]

    def test_recursive_function_writes_global(self) -> None:
        """Recursive function writes to a global as side effect.

        Since CallStmt catches _ReturnSignal internally, recursive calls
        that need to communicate a result must use a global variable.
        """
        platform = DesktopPlatform()
        interp = Interpreter(platform)
        # $depth = 3, $result = 0
        # FUNCTION f()
        #   $depth = $depth - 1
        #   IF ($depth == 0) THEN $result = 99; RETURN
        #   f()
        # END_FUNCTION
        # f()
        # $r should be 99
        script = Script((
            VarDef("depth", IntegerExpr(3)),
            VarDef("result", IntegerExpr(0)),
            FunctionDef("f", (), (
                AssignStmt(
                    "depth",
                    BinaryOp(
                        DollarIdentifierExpr("depth"), Operator.SUBTRACT, IntegerExpr(1),
                    ),
                ),
                IfStmt(
                    condition=BinaryOp(
                        DollarIdentifierExpr("depth"), Operator.EQUAL, IntegerExpr(0),
                    ),
                    body=(
                        AssignStmt("result", IntegerExpr(99)),
                        ReturnStmt(None),
                    ),
                ),
                CallStmt("f"),
            )),
            CallStmt("f"),
            StringLnStmt("done"),
        ))
        interp.interpret(script)
        assert interp._globals["result"] == 99

    def test_return_outside_function_raises(self) -> None:
        """RETURN statement outside any function raises InterpreterError."""
        platform = DesktopPlatform()
        interp = Interpreter(platform)
        script = Script((ReturnStmt(IntegerExpr(1)),))
        with pytest.raises(InterpreterError, match="RETURN outside function"):
            interp.interpret(script)
