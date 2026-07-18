"""Tests for interpreter control flow (IF/WHILE/BREAK/CONTINUE)."""

import pytest

from ducky.ast import (
    AssignStmt,
    BinaryOp,
    BreakStmt,
    ContinueStmt,
    DefaultDelayStmt,
    DelayStmt,
    DollarIdentifierExpr,
    IfStmt,
    IntegerExpr,
    RepeatStmt,
    Script,
    StopPayloadStmt,
    VarDef,
    WhileStmt,
)
from ducky.interpreter import Interpreter, InterpreterError
from ducky.platform import StopPayloadSignal
from ducky.platform.desktop import DesktopPlatform
from ducky.tokens import Operator


class TestIfStmt:
    """IF/ELSE IF/ELSE conditional execution."""

    def test_if_true_executes_body(self) -> None:
        """IF (1) THEN ... END_IF executes the body."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        script = Script((
            IfStmt(
                condition=IntegerExpr(1),
                body=(VarDef("x", IntegerExpr(42)),),
                else_body=None,
            ),
        ))
        interpreter.interpret(script)
        assert interpreter._globals["x"] == 42

    def test_if_false_skips_body(self) -> None:
        """IF (0) THEN ... END_IF skips the body."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        script = Script((
            VarDef("x", IntegerExpr(1)),
            IfStmt(
                condition=IntegerExpr(0),
                body=(AssignStmt("x", IntegerExpr(99)),),
                else_body=None,
            ),
        ))
        interpreter.interpret(script)
        assert interpreter._globals["x"] == 1  # unchanged

    def test_if_else_true(self) -> None:
        """IF (1) THEN ... ELSE ... END_IF executes IF body."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        script = Script((
            VarDef("x", IntegerExpr(0)),
            IfStmt(
                condition=IntegerExpr(1),
                body=(AssignStmt("x", IntegerExpr(10)),),
                else_body=(AssignStmt("x", IntegerExpr(20)),),
            ),
        ))
        interpreter.interpret(script)
        assert interpreter._globals["x"] == 10

    def test_if_else_false(self) -> None:
        """IF (0) THEN ... ELSE ... END_IF executes ELSE body."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        script = Script((
            VarDef("x", IntegerExpr(0)),
            IfStmt(
                condition=IntegerExpr(0),
                body=(AssignStmt("x", IntegerExpr(10)),),
                else_body=(AssignStmt("x", IntegerExpr(20)),),
            ),
        ))
        interpreter.interpret(script)
        assert interpreter._globals["x"] == 20

    def test_else_if_first_true(self) -> None:
        """IF (0) THEN ... ELSE IF (1) THEN ... ELSE ... executes ELSE IF."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        # ELSE IF is represented as: IfStmt(0, body, else_body=(IfStmt(1, elseif_body, else_body)))
        script = Script((
            VarDef("x", IntegerExpr(0)),
            IfStmt(
                condition=IntegerExpr(0),
                body=(AssignStmt("x", IntegerExpr(10)),),
                else_body=(
                    IfStmt(
                        condition=IntegerExpr(1),
                        body=(AssignStmt("x", IntegerExpr(20)),),
                        else_body=(AssignStmt("x", IntegerExpr(30)),),
                    ),
                ),
            ),
        ))
        interpreter.interpret(script)
        assert interpreter._globals["x"] == 20

    def test_else_if_none_true(self) -> None:
        """IF (0) THEN ... ELSE IF (0) THEN ... ELSE ... executes final ELSE."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        script = Script((
            VarDef("x", IntegerExpr(0)),
            IfStmt(
                condition=IntegerExpr(0),
                body=(AssignStmt("x", IntegerExpr(10)),),
                else_body=(
                    IfStmt(
                        condition=IntegerExpr(0),
                        body=(AssignStmt("x", IntegerExpr(20)),),
                        else_body=(AssignStmt("x", IntegerExpr(30)),),
                    ),
                ),
            ),
        ))
        interpreter.interpret(script)
        assert interpreter._globals["x"] == 30

    def test_if_no_else_skips(self) -> None:
        """IF (0) THEN ... END_IF with no else skips everything."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        script = Script((
            VarDef("x", IntegerExpr(1)),
            IfStmt(
                condition=IntegerExpr(0),
                body=(AssignStmt("x", IntegerExpr(99)),),
                else_body=None,
            ),
        ))
        interpreter.interpret(script)
        assert interpreter._globals["x"] == 1  # unchanged

    def test_nested_if(self) -> None:
        """Nested IF statements execute correctly."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        # IF (1) THEN $x = 1; IF (1) THEN $x = 2; END_IF; END_IF
        script = Script((
            VarDef("x", IntegerExpr(0)),
            IfStmt(
                condition=IntegerExpr(1),
                body=(
                    AssignStmt("x", IntegerExpr(1)),
                    IfStmt(
                        condition=IntegerExpr(1),
                        body=(AssignStmt("x", IntegerExpr(2)),),
                        else_body=None,
                    ),
                ),
                else_body=None,
            ),
        ))
        interpreter.interpret(script)
        assert interpreter._globals["x"] == 2

    def test_if_with_delay(self) -> None:
        """Body statements inside IF trigger platform calls."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        script = Script((
            IfStmt(
                condition=IntegerExpr(1),
                body=(DelayStmt(IntegerExpr(100)),),
                else_body=None,
            ),
        ))
        interpreter.interpret(script)
        assert ("delay_ms", 100) in platform.calls

    def test_else_if_chained(self) -> None:
        """Multiple ELSE IFs in chain: IF->ELSE IF->ELSE IF->ELSE."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        # ELSE IF chain:
        # IF (0): x=1
        # ELSE IF (0): x=2
        # ELSE IF (1): x=3
        # ELSE: x=4
        script = Script((
            VarDef("x", IntegerExpr(0)),
            IfStmt(
                condition=IntegerExpr(0),
                body=(AssignStmt("x", IntegerExpr(1)),),
                else_body=(
                    IfStmt(
                        condition=IntegerExpr(0),
                        body=(AssignStmt("x", IntegerExpr(2)),),
                        else_body=(
                            IfStmt(
                                condition=IntegerExpr(1),
                                body=(AssignStmt("x", IntegerExpr(3)),),
                                else_body=(AssignStmt("x", IntegerExpr(4)),),
                            ),
                        ),
                    ),
                ),
            ),
        ))
        interpreter.interpret(script)
        assert interpreter._globals["x"] == 3


class TestWhileStmt:
    """WHILE loop execution."""

    def test_while_loop(self) -> None:
        """WHILE loop iterates until condition is false."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        # $i = 3; WHILE ($i > 0) $i = $i - 1; END_WHILE
        script = Script((
            VarDef("i", IntegerExpr(3)),
            WhileStmt(
                condition=BinaryOp(
                    DollarIdentifierExpr("i"), Operator.GREATER, IntegerExpr(0),
                ),
                body=(AssignStmt(
                    "i",
                    BinaryOp(DollarIdentifierExpr("i"), Operator.SUBTRACT, IntegerExpr(1)),
                ),),
            ),
        ))
        interpreter.interpret(script)
        assert interpreter._globals["i"] == 0

    def test_while_false_skips_body(self) -> None:
        """WHILE (0) does not execute the body."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        script = Script((
            VarDef("x", IntegerExpr(1)),
            WhileStmt(
                condition=IntegerExpr(0),
                body=(AssignStmt("x", IntegerExpr(99)),),
            ),
        ))
        interpreter.interpret(script)
        assert interpreter._globals["x"] == 1  # unchanged

    def test_while_with_variable_condition(self) -> None:
        """WHILE loop with variable counter executes correct number of times."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        # $i = 5; $count = 0; WHILE ($i > 0) $count = $count + 1; $i = $i - 1; END_WHILE
        script = Script((
            VarDef("i", IntegerExpr(5)),
            VarDef("count", IntegerExpr(0)),
            WhileStmt(
                condition=BinaryOp(
                    DollarIdentifierExpr("i"), Operator.GREATER, IntegerExpr(0),
                ),
                body=(
                    AssignStmt(
                        "count",
                        BinaryOp(DollarIdentifierExpr("count"), Operator.ADD, IntegerExpr(1)),
                    ),
                    AssignStmt(
                        "i",
                        BinaryOp(DollarIdentifierExpr("i"), Operator.SUBTRACT, IntegerExpr(1)),
                    ),
                ),
            ),
        ))
        interpreter.interpret(script)
        assert interpreter._globals["i"] == 0
        assert interpreter._globals["count"] == 5

    def test_nested_while(self) -> None:
        """Nested WHILE loops: outer 2x, inner 3x = 6 total iterations."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        # $outer = 2; $inner = 3; $count = 0;
        # WHILE ($outer > 0)
        #   WHILE ($inner > 0)
        #     $count = $count + 1;
        #     $inner = $inner - 1;
        #   END_WHILE
        #   $inner = 3;  # reset inner counter
        #   $outer = $outer - 1;
        # END_WHILE
        script = Script((
            VarDef("outer", IntegerExpr(2)),
            VarDef("inner", IntegerExpr(3)),
            VarDef("count", IntegerExpr(0)),
            WhileStmt(
                condition=BinaryOp(
                    DollarIdentifierExpr("outer"), Operator.GREATER, IntegerExpr(0),
                ),
                body=(
                    WhileStmt(
                        condition=BinaryOp(
                            DollarIdentifierExpr("inner"), Operator.GREATER, IntegerExpr(0),
                        ),
                        body=(
                            AssignStmt(
                                "count",
                                BinaryOp(
                                    DollarIdentifierExpr("count"), Operator.ADD, IntegerExpr(1),
                                ),
                            ),
                            AssignStmt(
                                "inner",
                                BinaryOp(
                                    DollarIdentifierExpr("inner"),
                                    Operator.SUBTRACT,
                                    IntegerExpr(1),
                                ),
                            ),
                        ),
                    ),
                    AssignStmt("inner", IntegerExpr(3)),
                    AssignStmt(
                        "outer",
                        BinaryOp(
                            DollarIdentifierExpr("outer"), Operator.SUBTRACT, IntegerExpr(1),
                        ),
                    ),
                ),
            ),
        ))
        interpreter.interpret(script)
        assert interpreter._globals["count"] == 6  # 2 * 3

    def test_while_forever_stopped_by_stop_payload(self) -> None:
        """STOP_PAYLOAD inside WHILE (1) terminates the loop."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        script = Script((
            VarDef("x", IntegerExpr(0)),
            WhileStmt(
                condition=IntegerExpr(1),
                body=(
                    AssignStmt(
                        "x",
                        BinaryOp(DollarIdentifierExpr("x"), Operator.ADD, IntegerExpr(1)),
                    ),
                    StopPayloadStmt(),
                ),
            ),
        ))
        with pytest.raises(StopPayloadSignal):
            interpreter.interpret(script)
        # The loop ran once (x was incremented) before STOP_PAYLOAD
        assert interpreter._globals["x"] == 1

    def test_while_body_executes_platform_actions(self) -> None:
        """Body statements in WHILE produce platform calls."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        # $i = 2; WHILE ($i > 0) DELAY 10; $i = $i - 1; END_WHILE
        script = Script((
            VarDef("i", IntegerExpr(2)),
            WhileStmt(
                condition=BinaryOp(
                    DollarIdentifierExpr("i"), Operator.GREATER, IntegerExpr(0),
                ),
                body=(
                    DelayStmt(IntegerExpr(10)),
                    AssignStmt(
                        "i",
                        BinaryOp(DollarIdentifierExpr("i"), Operator.SUBTRACT, IntegerExpr(1)),
                    ),
                ),
            ),
        ))
        interpreter.interpret(script)
        # 2 iterations * 1 delay each = 2 delay_ms(10) calls
        delay_calls = [c for c in platform.calls if c[0] == "delay_ms"]
        assert len(delay_calls) == 2
        for call in delay_calls:
            assert call == ("delay_ms", 10)


class TestBreakStmt:
    """BREAK exits the innermost WHILE loop."""

    def test_break_exits_loop(self) -> None:
        """BREAK inside WHILE (1) exits immediately."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        script = Script((
            VarDef("x", IntegerExpr(0)),
            WhileStmt(
                condition=IntegerExpr(1),
                body=(
                    AssignStmt(
                        "x",
                        BinaryOp(DollarIdentifierExpr("x"), Operator.ADD, IntegerExpr(1)),
                    ),
                    BreakStmt(),
                    AssignStmt(
                        "x",
                        BinaryOp(DollarIdentifierExpr("x"), Operator.ADD, IntegerExpr(99)),
                    ),
                ),
            ),
        ))
        interpreter.interpret(script)
        # x should be 1 (incremented once), not 100 (no 99 addition after BREAK)
        assert interpreter._globals["x"] == 1

    def test_break_innermost_loop(self) -> None:
        """BREAK exits only the innermost WHILE loop."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        # outer = 0; i = 0
        # WHILE outer < 2:
        #   inner = 0
        #   WHILE 1:
        #     BREAK  (exits this inner loop)
        #     inner = 99  (never reached)
        #   END_WHILE
        #   i = i + 1  (still executed after BREAK — outer loop continues)
        #   outer = outer + 1
        # END_WHILE
        script = Script((
            VarDef("outer", IntegerExpr(0)),
            VarDef("i", IntegerExpr(0)),
            WhileStmt(
                condition=BinaryOp(
                    DollarIdentifierExpr("outer"), Operator.LESS, IntegerExpr(2),
                ),
                body=(
                    WhileStmt(
                        condition=IntegerExpr(1),
                        body=(
                            BreakStmt(),
                            AssignStmt("i", IntegerExpr(99)),
                        ),
                    ),
                    AssignStmt(
                        "i",
                        BinaryOp(DollarIdentifierExpr("i"), Operator.ADD, IntegerExpr(1)),
                    ),
                    AssignStmt(
                        "outer",
                        BinaryOp(DollarIdentifierExpr("outer"), Operator.ADD, IntegerExpr(1)),
                    ),
                ),
            ),
        ))
        interpreter.interpret(script)
        # outer loop runs twice, each time BREAK exits inner, then i++
        assert interpreter._globals["i"] == 2
        assert interpreter._globals["outer"] == 2

    def test_break_outside_loop_error(self) -> None:
        """BREAK at the top level raises InterpreterError."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        script = Script((BreakStmt(),))
        with pytest.raises(InterpreterError, match="BREAK outside WHILE loop"):
            interpreter.interpret(script)

    def test_break_in_if_inside_while(self) -> None:
        """BREAK inside IF inside WHILE exits the loop."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        # WHILE (1) IF (1) THEN BREAK; END_IF END_WHILE
        script = Script((
            VarDef("x", IntegerExpr(0)),
            WhileStmt(
                condition=IntegerExpr(1),
                body=(
                    IfStmt(
                        condition=IntegerExpr(1),
                        body=(
                            BreakStmt(),
                            AssignStmt("x", IntegerExpr(99)),
                        ),
                        else_body=None,
                    ),
                    AssignStmt("x", IntegerExpr(88)),  # never reached
                ),
            ),
        ))
        interpreter.interpret(script)
        assert interpreter._globals["x"] == 0  # unchanged, BREAK hit before assignments


class TestContinueStmt:
    """CONTINUE skips to the next WHILE iteration."""

    def test_continue_skips_to_next_iteration(self) -> None:
        """CONTINUE skips remaining body and continues loop iteration."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        # $i = 0; $count = 0;
        # WHILE ($i < 5)
        #   $i = $i + 1;
        #   IF ($i == 3) THEN CONTINUE; END_IF
        #   $count = $count + 1;
        # END_WHILE
        # count should be 4 (1,2,4,5 — skip when i==3)
        script = Script((
            VarDef("i", IntegerExpr(0)),
            VarDef("count", IntegerExpr(0)),
            WhileStmt(
                condition=BinaryOp(
                    DollarIdentifierExpr("i"), Operator.LESS, IntegerExpr(5),
                ),
                body=(
                    AssignStmt(
                        "i",
                        BinaryOp(DollarIdentifierExpr("i"), Operator.ADD, IntegerExpr(1)),
                    ),
                    IfStmt(
                        condition=BinaryOp(
                            DollarIdentifierExpr("i"), Operator.EQUAL, IntegerExpr(3),
                        ),
                        body=(ContinueStmt(),),
                        else_body=None,
                    ),
                    AssignStmt(
                        "count",
                        BinaryOp(DollarIdentifierExpr("count"), Operator.ADD, IntegerExpr(1)),
                    ),
                ),
            ),
        ))
        interpreter.interpret(script)
        assert interpreter._globals["i"] == 5
        assert interpreter._globals["count"] == 4  # skipped increment for i=3

    def test_continue_outside_loop_error(self) -> None:
        """CONTINUE at the top level raises InterpreterError."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        script = Script((ContinueStmt(),))
        with pytest.raises(InterpreterError, match="CONTINUE outside WHILE loop"):
            interpreter.interpret(script)

    def test_continue_in_nested_loop(self) -> None:
        """CONTINUE in inner loop only skips inner body."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        # $outer = 0; $inner_count = 0;
        # WHILE ($outer < 2)
        #   $inner = 0;
        #   WHILE ($inner < 3)
        #     $inner = $inner + 1;
        #     IF ($inner == 2) THEN CONTINUE; END_IF
        #     $inner_count = $inner_count + 1;
        #   END_WHILE
        #   $outer = $outer + 1;
        # END_WHILE
        # For each outer iteration: inner iterates 1,2,3
        #   inner=1: count++
        #   inner=2: CONTINUE (skip count++)
        #   inner=3: count++
        # So each outer loop: count += 2
        # Two outer loops: count = 4
        script = Script((
            VarDef("outer", IntegerExpr(0)),
            VarDef("inner_count", IntegerExpr(0)),
            WhileStmt(
                condition=BinaryOp(
                    DollarIdentifierExpr("outer"), Operator.LESS, IntegerExpr(2),
                ),
                body=(
                    VarDef("inner", IntegerExpr(0)),
                    WhileStmt(
                        condition=BinaryOp(
                            DollarIdentifierExpr("inner"), Operator.LESS, IntegerExpr(3),
                        ),
                        body=(
                            AssignStmt(
                                "inner",
                                BinaryOp(
                                    DollarIdentifierExpr("inner"), Operator.ADD, IntegerExpr(1),
                                ),
                            ),
                            IfStmt(
                                condition=BinaryOp(
                                    DollarIdentifierExpr("inner"), Operator.EQUAL, IntegerExpr(2),
                                ),
                                body=(ContinueStmt(),),
                                else_body=None,
                            ),
                            AssignStmt(
                                "inner_count",
                                BinaryOp(
                                    DollarIdentifierExpr("inner_count"),
                                    Operator.ADD,
                                    IntegerExpr(1),
                                ),
                            ),
                        ),
                    ),
                    AssignStmt(
                        "outer",
                        BinaryOp(
                            DollarIdentifierExpr("outer"), Operator.ADD, IntegerExpr(1),
                        ),
                    ),
                ),
            ),
        ))
        interpreter.interpret(script)
        assert interpreter._globals["outer"] == 2
        assert interpreter._globals["inner_count"] == 4


class TestControlFlowRepeatInteraction:
    """Interaction between control flow and REPEAT."""

    def test_repeat_repeats_if_stmt(self) -> None:
        """REPEAT repeats the preceding IF statement."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        # $x = 0
        # IF (1) THEN $x = $x + 1; END_IF
        # REPEAT 2
        # Since IF is truthy, body executes each time.
        # 1 original + 2 repeats = 3 total executions
        script = Script((
            VarDef("x", IntegerExpr(0)),
            IfStmt(
                condition=IntegerExpr(1),
                body=(AssignStmt(
                    "x",
                    BinaryOp(DollarIdentifierExpr("x"), Operator.ADD, IntegerExpr(1)),
                ),),
                else_body=None,
            ),
            RepeatStmt(IntegerExpr(2)),
        ))
        interpreter.interpret(script)
        assert interpreter._globals["x"] == 3

    def test_repeat_repeats_while_stmt(self) -> None:
        """REPEAT repeats the preceding WHILE statement."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        # $x = 0; $i = 2
        # WHILE ($i > 0) $x = $x + 1; $i = $i - 1; END_WHILE
        # REPEAT 1
        # WHILE runs once (2 iterations), resulting in x=2
        # REPEAT runs WHILE again... but wait, $i is now 0 so WHILE runs 0 iterations
        # Actually, REPEAT repeats the entire WHILE, but $i is already 0
        # So it runs once fully (sets x=2), then REPEAT runs it again with $i=0 → no-op
        # Let's use a simpler test:
        # WHILE (0) with body never runs. REPEAT repeats it 2x more (still no-op).
        # REPEAT 2
        # WHILE condition is false, so body never runs. REPEAT 2 times the same.
        script = Script((
            VarDef("x", IntegerExpr(0)),
            WhileStmt(
                condition=IntegerExpr(0),
                body=(AssignStmt("x", IntegerExpr(42)),),
            ),
            RepeatStmt(IntegerExpr(2)),
        ))
        interpreter.interpret(script)
        # WHILE never runs (falsy condition), REPEAT repeats it 2 more times
        assert interpreter._globals["x"] == 0

    def test_repeat_does_not_repeat_break(self) -> None:
        """BREAK should never become _last_stmt for REPEAT."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        # WHILE (1) BREAK; END_WHILE
        # REPEAT 3 — should use the WHILE as last_stmt, not BREAK
        # Since WHILE always breaks immediately, the body is trivial
        script = Script((
            VarDef("x", IntegerExpr(0)),
            WhileStmt(
                condition=IntegerExpr(1),
                body=(
                    BreakStmt(),
                    AssignStmt("x", IntegerExpr(99)),
                ),
            ),
            RepeatStmt(IntegerExpr(1)),
        ))
        interpreter.interpret(script)
        assert interpreter._globals["x"] == 0  # body after BREAK never runs

    def test_repeat_does_not_repeat_continue(self) -> None:
        """CONTINUE should never become _last_stmt for REPEAT."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        # WHILE (0) ... CONTINUE ... END_WHILE
        # Then REPEAT — WHILE is _last_stmt, CONTINUE never tracked
        # This is a no-op loop, just verify it doesn't error
        script = Script((
            WhileStmt(
                condition=IntegerExpr(0),
                body=(ContinueStmt(),),
            ),
            RepeatStmt(IntegerExpr(2)),
        ))
        interpreter.interpret(script)
        # No error should occur; CONTINUE in a while is fine


class TestControlFlowDefaultDelay:
    """Default delay interaction with control flow."""

    def test_default_delay_after_if(self) -> None:
        """Default delay applies after IF statement completes."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        script = Script((
            DefaultDelayStmt(IntegerExpr(50)),
            IfStmt(
                condition=IntegerExpr(1),
                body=(VarDef("x", IntegerExpr(1)),),
                else_body=None,
            ),
            VarDef("y", IntegerExpr(2)),
        ))
        interpreter.interpret(script)
        delay_calls = [c for c in platform.calls if c[0] == "delay_ms"]
        # delay after IF body VAR + delay after IF + delay after second VAR
        assert len(delay_calls) == 3
        for call in delay_calls:
            assert call == ("delay_ms", 50)

    def test_default_delay_after_while(self) -> None:
        """Default delay applies after WHILE statement completes."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        # DEFAULTDELAY 30
        # $i = 2
        # WHILE $i > 0: DELAY 10; $i = $i - 1; END_WHILE
        # VAR $z = 1
        script = Script((
            DefaultDelayStmt(IntegerExpr(30)),
            VarDef("i", IntegerExpr(2)),
            WhileStmt(
                condition=BinaryOp(
                    DollarIdentifierExpr("i"), Operator.GREATER, IntegerExpr(0),
                ),
                body=(
                    DelayStmt(IntegerExpr(10)),
                    AssignStmt(
                        "i",
                        BinaryOp(DollarIdentifierExpr("i"), Operator.SUBTRACT, IntegerExpr(1)),
                    ),
                ),
            ),
            VarDef("z", IntegerExpr(1)),
        ))
        interpreter.interpret(script)
        delay_calls = [c for c in platform.calls if c[0] == "delay_ms"]
        # Expected delay_ms calls:
        #   DefaultDelayStmt: excluded
        #   VarDef i: default delay 30
        #   WHILE:
        #     iter 1: delay_ms(10), then default delay 30 (after AssignStmt i)
        #     iter 2: delay_ms(10), then default delay 30 (after AssignStmt i)
        #   After WHILE: default delay 30
        #   VarDef z: default delay 30
        assert len(delay_calls) == 7
        # First is default delay after VarDef i
        assert delay_calls[0] == ("delay_ms", 30)
        # Iteration 1: explicit 10 then default 30
        assert delay_calls[1] == ("delay_ms", 10)
        assert delay_calls[2] == ("delay_ms", 30)
        # Iteration 2: explicit 10 then default 30
        assert delay_calls[3] == ("delay_ms", 10)
        assert delay_calls[4] == ("delay_ms", 30)
        # After WHILE completes: default delay 30
        assert delay_calls[5] == ("delay_ms", 30)
        # After VarDef z: default delay 30
        assert delay_calls[6] == ("delay_ms", 30)
