"""Tests for interpreter function support (FUNCTION/END_FUNCTION, RETURN, call)."""

import pytest

from ducky.ast import (
    AssignStmt,
    BinaryOp,
    BreakStmt,
    CallExpr,
    CallStmt,
    ContinueStmt,
    DollarIdentifierExpr,
    FunctionDef,
    IfStmt,
    IntegerExpr,
    RepeatStmt,
    ReturnStmt,
    Script,
    VarDef,
    WhileStmt,
)
from ducky.interpreter import Interpreter, InterpreterError
from ducky.platform.desktop import DesktopPlatform
from ducky.tokens import Operator


class TestFunctionRegistration:
    """FUNCTION/END_FUNCTION are registered, not executed during registration."""

    def test_registration_only_no_execution(self) -> None:
        """Function body is NOT executed during registration."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        # Function with a DELAY — if body executed, delay_ms would be called
        script = Script((
            FunctionDef("foo", (), (CallStmt("nonexistent"),)),
        ))
        interpreter.interpret(script)
        assert "foo" in interpreter._functions
        assert len(platform.calls) == 0

    def test_multiple_functions(self) -> None:
        """Multiple function definitions are all registered."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        f1 = FunctionDef("a", (), (IntegerExpr(1),))
        f2 = FunctionDef("b", (), (IntegerExpr(2),))
        script = Script((f1, f2))
        interpreter.interpret(script)
        assert "a" in interpreter._functions
        assert "b" in interpreter._functions

    def test_empty_body_function(self) -> None:
        """Function with empty body can be called without error."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        script = Script((
            FunctionDef("do_nothing", (), ()),
            CallStmt("do_nothing"),
        ))
        interpreter.interpret(script)
        # No crash = success


class TestFunctionCallStatement:
    """Calling a function with name() as a statement."""

    def test_call_statement(self) -> None:
        """CallStmt executes the function body."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        script = Script((
            VarDef("x", IntegerExpr(0)),
            FunctionDef("set_x", (), (AssignStmt("x", IntegerExpr(42)),)),
            CallStmt("set_x"),
        ))
        interpreter.interpret(script)
        assert interpreter._globals["x"] == 42

    def test_call_twice(self) -> None:
        """Calling the same function twice executes body twice."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        script = Script((
            VarDef("x", IntegerExpr(0)),
            FunctionDef("inc_x", (), (
                AssignStmt("x", BinaryOp(
                    DollarIdentifierExpr("x"), Operator.ADD, IntegerExpr(1)
                )),
            )),
            CallStmt("inc_x"),
            CallStmt("inc_x"),
        ))
        interpreter.interpret(script)
        assert interpreter._globals["x"] == 2


class TestFunctionCallExpression:
    """Calling a function inside an expression (returns value)."""

    def test_call_expression_in_var_def(self) -> None:
        """CallExpr can be used as an initializer in VAR."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        script = Script((
            FunctionDef("five", (), (ReturnStmt(IntegerExpr(5)),)),
            VarDef("x", CallExpr("five")),
        ))
        interpreter.interpret(script)
        assert interpreter._globals["x"] == 5

    def test_call_expression_in_assign(self) -> None:
        """CallExpr can be used in assignment RHS."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        script = Script((
            VarDef("x", IntegerExpr(0)),
            FunctionDef("five", (), (ReturnStmt(IntegerExpr(5)),)),
            AssignStmt("x", CallExpr("five")),
        ))
        interpreter.interpret(script)
        assert interpreter._globals["x"] == 5

    def test_call_expression_in_binary_op(self) -> None:
        """CallExpr result can be used in expressions."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        script = Script((
            FunctionDef("val", (), (ReturnStmt(IntegerExpr(7)),)),
            VarDef("x", BinaryOp(
                CallExpr("val"), Operator.ADD, CallExpr("val")
            )),
        ))
        interpreter.interpret(script)
        assert interpreter._globals["x"] == 14


class TestReturnStmt:
    """RETURN semantics."""

    def test_return_with_value(self) -> None:
        """RETURN <expr> returns the evaluated value."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        script = Script((
            FunctionDef("get", (), (ReturnStmt(IntegerExpr(99)),)),
            VarDef("x", CallExpr("get")),
        ))
        interpreter.interpret(script)
        assert interpreter._globals["x"] == 99

    def test_return_no_value_default_zero(self) -> None:
        """RETURN without value returns 0."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        script = Script((
            FunctionDef("nothing", (), (ReturnStmt(None),)),
            VarDef("x", CallExpr("nothing")),
        ))
        interpreter.interpret(script)
        assert interpreter._globals["x"] == 0

    def test_no_return_returns_zero(self) -> None:
        """Function without RETURN returns 0 when called as expression."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        script = Script((
            FunctionDef("noop", (), ()),
            VarDef("x", CallExpr("noop")),
        ))
        interpreter.interpret(script)
        assert interpreter._globals["x"] == 0

    def test_return_exits_early(self) -> None:
        """Statements after RETURN are not executed."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        script = Script((
            VarDef("x", IntegerExpr(0)),
            FunctionDef("test", (), (
                ReturnStmt(IntegerExpr(42)),
                AssignStmt("x", IntegerExpr(99)),
            )),
            VarDef("result", CallExpr("test")),
        ))
        interpreter.interpret(script)
        assert interpreter._globals["x"] == 0  # AssignStmt should not run
        assert interpreter._globals["result"] == 42

    def test_return_from_inside_if(self) -> None:
        """RETURN works inside an IF inside a function."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        script = Script((
            FunctionDef("check", (), (
                IfStmt(IntegerExpr(1), (ReturnStmt(IntegerExpr(10)),)),
                ReturnStmt(IntegerExpr(99)),
            )),
            VarDef("x", CallExpr("check")),
        ))
        interpreter.interpret(script)
        assert interpreter._globals["x"] == 10

    def test_return_from_inside_while(self) -> None:
        """RETURN works inside a WHILE inside a function."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        script = Script((
            VarDef("i", IntegerExpr(0)),
            FunctionDef("find", (), (
                WhileStmt(
                    IntegerExpr(1),  # while true
                    (
                        AssignStmt("i", BinaryOp(
                            DollarIdentifierExpr("i"), Operator.ADD, IntegerExpr(1)
                        )),
                        IfStmt(
                            BinaryOp(
                                DollarIdentifierExpr("i"),
                                Operator.GREATER_EQUAL,
                                IntegerExpr(5),
                            ),
                            (ReturnStmt(DollarIdentifierExpr("i")),),
                        ),
                    ),
                ),
            )),
            VarDef("result", CallExpr("find")),
        ))
        interpreter.interpret(script)
        assert interpreter._globals["result"] == 5
        assert interpreter._globals["i"] == 5

    def test_return_wraps_16bit(self) -> None:
        """Return value wraps to 16-bit."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        script = Script((
            FunctionDef("big", (), (ReturnStmt(IntegerExpr(70000)),)),
            VarDef("x", CallExpr("big")),
        ))
        interpreter.interpret(script)
        assert interpreter._globals["x"] == 70000 & 0xFFFF


class TestRecursion:
    """Recursive function calls."""

    def test_simple_recursion_countdown(self) -> None:
        """Recursive countdown: decrements global $n until 0, returns count of calls.

        Uses a global variable for the parameter (no local VAR inside function)
        so the recursive call sees the updated value.
        """
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        # count(): if $n == 0 then return 0 else $n -= 1, return 1 + count()
        script = Script((
            VarDef("n", IntegerExpr(5)),
            FunctionDef("count", (), (
                IfStmt(
                    BinaryOp(
                        DollarIdentifierExpr("n"),
                        Operator.EQUAL,
                        IntegerExpr(0),
                    ),
                    (ReturnStmt(IntegerExpr(0)),),
                    (
                        AssignStmt("n", BinaryOp(
                            DollarIdentifierExpr("n"),
                            Operator.SUBTRACT,
                            IntegerExpr(1),
                        )),
                        ReturnStmt(BinaryOp(
                            IntegerExpr(1),
                            Operator.ADD,
                            CallExpr("count"),
                        )),
                    ),
                ),
            )),
            VarDef("result", CallExpr("count")),
        ))
        interpreter.interpret(script)
        # count(5): 5 recursive calls, returns 5
        assert interpreter._globals["result"] == 5
        assert interpreter._globals["n"] == 0

    def test_mutual_recursion(self) -> None:
        """Mutually recursive functions with forward reference."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        # even(n): if n == 0 then 1 else odd(n-1)
        # odd(n): if n == 0 then 0 else even(n-1)
        script = Script((
            FunctionDef("even", (), (
                VarDef("n", DollarIdentifierExpr("n")),
                IfStmt(
                    BinaryOp(
                        DollarIdentifierExpr("n"),
                        Operator.EQUAL,
                        IntegerExpr(0),
                    ),
                    (ReturnStmt(IntegerExpr(1)),),
                    (
                        AssignStmt("n", BinaryOp(
                            DollarIdentifierExpr("n"), Operator.SUBTRACT, IntegerExpr(1)
                        )),
                        ReturnStmt(CallExpr("odd")),
                    ),
                ),
            )),
            FunctionDef("odd", (), (
                VarDef("n", DollarIdentifierExpr("n")),
                IfStmt(
                    BinaryOp(
                        DollarIdentifierExpr("n"),
                        Operator.EQUAL,
                        IntegerExpr(0),
                    ),
                    (ReturnStmt(IntegerExpr(0)),),
                    (
                        AssignStmt("n", BinaryOp(
                            DollarIdentifierExpr("n"), Operator.SUBTRACT, IntegerExpr(1)
                        )),
                        ReturnStmt(CallExpr("even")),
                    ),
                ),
            )),
            VarDef("n", IntegerExpr(6)),
            VarDef("result", CallExpr("even")),
        ))
        interpreter.interpret(script)
        assert interpreter._globals["result"] == 1  # 6 is even


class TestLocalScope:
    """Function-local variable scoping."""

    def test_var_inside_function_is_local(self) -> None:
        """VAR inside a function creates a local variable, not global."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        script = Script((
            VarDef("x", IntegerExpr(10)),
            FunctionDef("foo", (), (
                VarDef("x", IntegerExpr(99)),
            )),
            CallStmt("foo"),
        ))
        interpreter.interpret(script)
        # Global x should still be 10 (local x shadows inside function)
        assert interpreter._globals["x"] == 10

    def test_local_does_not_leak(self) -> None:
        """Local scope is cleaned up after function exits."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        script = Script((
            FunctionDef("foo", (), (
                VarDef("y", IntegerExpr(42)),
            )),
            CallStmt("foo"),
        ))
        interpreter.interpret(script)
        assert "y" not in interpreter._globals

    def test_local_shadows_global_read(self) -> None:
        """Local variable shadows global of the same name when reading."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        script = Script((
            VarDef("x", IntegerExpr(10)),
            FunctionDef("foo", (), (
                VarDef("x", IntegerExpr(99)),
                ReturnStmt(DollarIdentifierExpr("x")),
            )),
            VarDef("result", CallExpr("foo")),
        ))
        interpreter.interpret(script)
        assert interpreter._globals["result"] == 99
        assert interpreter._globals["x"] == 10

    def test_global_readable_from_function(self) -> None:
        """Global variables can be read from inside a function."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        script = Script((
            VarDef("x", IntegerExpr(7)),
            FunctionDef("read_global", (), (
                ReturnStmt(DollarIdentifierExpr("x")),
            )),
            VarDef("result", CallExpr("read_global")),
        ))
        interpreter.interpret(script)
        assert interpreter._globals["result"] == 7

    def test_assign_inside_function_checks_locals_first(self) -> None:
        """Assignment inside function updates local before global."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        script = Script((
            VarDef("x", IntegerExpr(10)),
            FunctionDef("foo", (), (
                VarDef("x", IntegerExpr(99)),
                AssignStmt("x", IntegerExpr(42)),
            )),
            CallStmt("foo"),
        ))
        interpreter.interpret(script)
        assert interpreter._globals["x"] == 10  # global unchanged

    def test_assign_to_global_from_function(self) -> None:
        """Assignment to a name that only exists in global updates global."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        script = Script((
            VarDef("x", IntegerExpr(10)),
            FunctionDef("foo", (), (
                AssignStmt("x", IntegerExpr(42)),
            )),
            CallStmt("foo"),
        ))
        interpreter.interpret(script)
        assert interpreter._globals["x"] == 42

    def test_assign_new_var_from_function_creates_local(self) -> None:
        """Assigning to undeclared name inside function creates in innermost local."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        script = Script((
            VarDef("x", IntegerExpr(1)),
            FunctionDef("foo", (), (
                AssignStmt("z", IntegerExpr(99)),
            )),
            CallStmt("foo"),
        ))
        interpreter.interpret(script)
        # z should exist in the function's local scope, not global
        assert "z" not in interpreter._globals


class TestNestedFunctionCalls:
    """Functions calling other functions."""

    def test_function_calls_another(self) -> None:
        """One function can call another."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        script = Script((
            FunctionDef("one", (), (ReturnStmt(IntegerExpr(1)),)),
            FunctionDef("call_one", (), (ReturnStmt(CallExpr("one")),)),
            VarDef("x", CallExpr("call_one")),
        ))
        interpreter.interpret(script)
        assert interpreter._globals["x"] == 1

    def test_forward_reference(self) -> None:
        """Function can be called before its definition in source."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        script = Script((
            VarDef("x", IntegerExpr(0)),
            CallStmt("later"),  # called before definition
            FunctionDef("later", (), (
                AssignStmt("x", IntegerExpr(7)),
            )),
        ))
        interpreter.interpret(script)
        assert interpreter._globals["x"] == 7

    def test_calling_undefined_function_error(self) -> None:
        """Calling undefined function raises InterpreterError."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        script = Script((CallStmt("nope"),))
        with pytest.raises(InterpreterError, match="Undefined function"):
            interpreter.interpret(script)

    def test_calling_undefined_function_in_expr_error(self) -> None:
        """Calling undefined function in expression raises InterpreterError."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        script = Script((VarDef("x", CallExpr("nope")),))
        with pytest.raises(InterpreterError, match="Undefined function"):
            interpreter.interpret(script)


class TestReturnOutsideFunction:
    """RETURN outside function is an error."""

    def test_return_at_top_level(self) -> None:
        """RETURN at script top level raises error."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        script = Script((ReturnStmt(IntegerExpr(0)),))
        with pytest.raises(InterpreterError, match="RETURN outside function"):
            interpreter.interpret(script)

    def test_return_inside_if_at_top_level(self) -> None:
        """RETURN inside an IF at top level raises error."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        script = Script((
            IfStmt(IntegerExpr(1), (ReturnStmt(IntegerExpr(5)),)),
        ))
        with pytest.raises(InterpreterError, match="RETURN outside function"):
            interpreter.interpret(script)


class TestRepeatAndReturn:
    """REPEAT tracks the CallStmt, not the internal ReturnStmt."""

    def test_repeat_after_function_call_with_return(self) -> None:
        """REPEAT repeats the CallStmt, even when the function body has RETURN.

        The _last_stmt is set to CallStmt by the outer _visit_statement,
        not to ReturnStmt (which is caught internally by visit_CallStmt).
        """
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        script = Script((
            VarDef("x", IntegerExpr(0)),
            FunctionDef("inc", (), (
                AssignStmt("x", BinaryOp(
                    DollarIdentifierExpr("x"), Operator.ADD, IntegerExpr(1)
                )),
                ReturnStmt(IntegerExpr(99)),
            )),
            CallStmt("inc"),
            RepeatStmt(IntegerExpr(3)),
        ))
        interpreter.interpret(script)
        # 1 original call + 3 repeated calls = 4 total
        assert interpreter._globals["x"] == 4


class TestBreakContinueInsideFunction:
    """BREAK/CONTINUE inside a function but outside WHILE loop should error."""

    def test_break_inside_function_no_loop(self) -> None:
        """BREAK inside function but not inside a WHILE raises error."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        script = Script((
            FunctionDef("foo", (), (BreakStmt(),)),
            CallStmt("foo"),
        ))
        with pytest.raises(InterpreterError, match="BREAK outside WHILE"):
            interpreter.interpret(script)

    def test_continue_inside_function_no_loop(self) -> None:
        """CONTINUE inside function but not inside a WHILE raises error."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        script = Script((
            FunctionDef("foo", (), (ContinueStmt(),)),
            CallStmt("foo"),
        ))
        with pytest.raises(InterpreterError, match="CONTINUE outside WHILE"):
            interpreter.interpret(script)
