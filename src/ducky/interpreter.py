"""DuckyScript 3 interpreter — AST visitor that drives PlatformInterface."""

# ruff: noqa: N802 — visit_ClassName is the standard visitor pattern

from __future__ import annotations

from ducky.ast import (
    AssignStmt,
    BinaryOp,
    DefaultCharDelayStmt,
    DefaultDelayStmt,
    DelayStmt,
    DollarIdentifierExpr,
    Expr,
    GroupExpr,
    IntegerExpr,
    RepeatStmt,
    ResetStmt,
    RestartPayloadStmt,
    Script,
    Stmt,
    StopPayloadStmt,
    StringExpr,
    UnaryOp,
    VarDef,
)
from ducky.platform import PlatformInterface
from ducky.tokens import Operator
from ducky.utils.visitor import NodeVisitor


class InterpreterError(Exception):
    """Runtime error during payload execution."""


class Interpreter(NodeVisitor):
    """AST-walking interpreter that drives a PlatformInterface."""

    def __init__(self, platform: PlatformInterface) -> None:
        self.platform = platform
        self._globals: dict[str, int] = {}
        self._default_delay: int = 0
        self._default_char_delay: int = 0
        self._last_stmt: Stmt | None = None

    def interpret(self, script: Script) -> None:
        """Execute a parsed Script against the platform."""
        self.visit(script)

    # ── Script (top-level) ─────────────────────────────────────────────

    def visit_Script(self, node: Script) -> None:
        for stmt in node.statements:
            self._visit_statement(stmt)

    def _visit_statement(self, stmt: Stmt) -> None:
        """Execute one statement and track it for REPEAT."""
        if isinstance(stmt, RepeatStmt):
            if self._last_stmt is None:
                raise InterpreterError("REPEAT without preceding statement")
            count = self._eval_expr(stmt.count)
            for _ in range(count):
                self.visit(self._last_stmt)
                self._apply_default_delay()
        else:
            self.visit(stmt)
            self._last_stmt = stmt
            self._apply_default_delay()

    def _apply_default_delay(self) -> None:
        """Apply inter-statement delay unless it would be redundant."""
        if self._default_delay > 0 and not isinstance(
            self._last_stmt,
            (DelayStmt, DefaultDelayStmt, DefaultCharDelayStmt),
        ):
            self.platform.delay_ms(self._default_delay)

    # ── Variable declarations & assignment ─────────────────────────────

    def visit_VarDef(self, node: VarDef) -> None:
        value = self._eval_expr(node.initializer)
        self._globals[node.name] = value & 0xFFFF

    def visit_AssignStmt(self, node: AssignStmt) -> None:
        if node.name not in self._globals:
            raise InterpreterError(f"Undeclared variable: ${node.name}")
        value = self._eval_expr(node.value)
        self._globals[node.name] = value & 0xFFFF

    # ── Delay statements ───────────────────────────────────────────────

    def visit_DelayStmt(self, node: DelayStmt) -> None:
        ms = self._eval_expr(node.milliseconds)
        self.platform.delay_ms(ms)

    def visit_DefaultDelayStmt(self, node: DefaultDelayStmt) -> None:
        ms = self._eval_expr(node.delay)
        self._default_delay = ms & 0xFFFF
        self.platform.set_default_delay_ms(self._default_delay)

    def visit_DefaultCharDelayStmt(self, node: DefaultCharDelayStmt) -> None:
        ms = self._eval_expr(node.delay)
        self._default_char_delay = ms & 0xFFFF

    # ── Payload control ────────────────────────────────────────────────

    def visit_ResetStmt(self, node: ResetStmt) -> None:
        self.platform.release_all()

    def visit_StopPayloadStmt(self, node: StopPayloadStmt) -> None:
        self.platform.stop_payload()

    def visit_RestartPayloadStmt(self, node: RestartPayloadStmt) -> None:
        self.platform.restart_payload()

    # ── Expression evaluation ──────────────────────────────────────────

    def _eval_expr(self, expr: Expr) -> int:
        return self.visit(expr)  # type: ignore[return-value]

    def visit_IntegerExpr(self, node: IntegerExpr) -> int:
        return node.value & 0xFFFF

    def visit_StringExpr(self, node: StringExpr) -> int:
        raise InterpreterError("String literal not supported in expression context")

    def visit_DollarIdentifierExpr(self, node: DollarIdentifierExpr) -> int:
        if node.name not in self._globals:
            raise InterpreterError(f"Undeclared variable: ${node.name}")
        return self._globals[node.name]

    def visit_GroupExpr(self, node: GroupExpr) -> int:
        return self._eval_expr(node.expression)

    def visit_UnaryOp(self, node: UnaryOp) -> int:
        operand = self._eval_expr(node.operand)
        if node.operator == Operator.SUBTRACT:
            return (-operand) & 0xFFFF
        elif node.operator == Operator.NOT:
            return 1 if operand == 0 else 0
        raise InterpreterError(f"Unknown unary operator: {node.operator}")

    def visit_BinaryOp(self, node: BinaryOp) -> int:
        # Short-circuit logical operators (right side may not be evaluated)
        if node.operator == Operator.LOGICAL_AND:
            left = self._eval_expr(node.left)
            return 1 if (left != 0 and self._eval_expr(node.right) != 0) else 0
        elif node.operator == Operator.LOGICAL_OR:
            left = self._eval_expr(node.left)
            return 1 if (left != 0 or self._eval_expr(node.right) != 0) else 0

        left = self._eval_expr(node.left)
        right = self._eval_expr(node.right)
        op = node.operator

        # Arithmetic (wrapping 16-bit)
        if op in (
            Operator.ADD,
            Operator.SUBTRACT,
            Operator.MULTIPLY,
            Operator.DIVIDE,
            Operator.MODULO,
            Operator.POWER,
        ):
            if op == Operator.ADD:
                return (left + right) & 0xFFFF
            elif op == Operator.SUBTRACT:
                return (left - right) & 0xFFFF
            elif op == Operator.MULTIPLY:
                return (left * right) & 0xFFFF
            elif op == Operator.DIVIDE:
                if right == 0:
                    raise InterpreterError("Division by zero")
                return (left // right) & 0xFFFF
            elif op == Operator.MODULO:
                if right == 0:
                    raise InterpreterError("Division by zero (modulo)")
                return (left % right) & 0xFFFF
            elif op == Operator.POWER:
                return pow(left, right, 65536)

        # Bitwise
        elif op in (
            Operator.SHIFT_LEFT,
            Operator.SHIFT_RIGHT,
            Operator.BITWISE_AND,
            Operator.BITWISE_OR,
        ):
            if op == Operator.SHIFT_LEFT:
                return (left << (right & 0x0F)) & 0xFFFF
            elif op == Operator.SHIFT_RIGHT:
                return (left >> (right & 0x0F)) & 0xFFFF
            elif op == Operator.BITWISE_AND:
                return (left & right) & 0xFFFF
            elif op == Operator.BITWISE_OR:
                return (left | right) & 0xFFFF

        # Comparison (return 1 or 0)
        elif op in (
            Operator.LESS,
            Operator.LESS_EQUAL,
            Operator.GREATER,
            Operator.GREATER_EQUAL,
            Operator.EQUAL,
            Operator.NOT_EQUAL,
        ):
            if op == Operator.LESS:
                return 1 if left < right else 0
            elif op == Operator.LESS_EQUAL:
                return 1 if left <= right else 0
            elif op == Operator.GREATER:
                return 1 if left > right else 0
            elif op == Operator.GREATER_EQUAL:
                return 1 if left >= right else 0
            elif op == Operator.EQUAL:
                return 1 if left == right else 0
            elif op == Operator.NOT_EQUAL:
                return 1 if left != right else 0

        # Assignment (=) not valid in expression context
        elif op == Operator.ASSIGN:
            raise InterpreterError(
                "Assignment (=) not valid in expression context"
            )

        raise InterpreterError(f"Unknown binary operator: {op}")
