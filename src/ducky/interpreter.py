"""DuckyScript 3 interpreter — AST visitor that drives PlatformInterface."""

# ruff: noqa: N802 — visit_ClassName is the standard visitor pattern

print("[ducky.interpreter] loading module...")  # noqa: E402

from ducky.ast import (  # noqa: E402
    AssignStmt,
    BinaryOp,
    BreakStmt,
    CallExpr,
    CallStmt,
    ComboStmt,
    ContinueStmt,
    DefaultCharDelayStmt,
    DefaultDelayStmt,
    DelayStmt,
    DollarIdentifierExpr,
    DuckyLangStmt,
    Expr,
    ExtensionStmt,
    FunctionDef,
    GroupExpr,
    HoldStmt,
    IdentifierStmt,
    IfStmt,
    InjectModStmt,
    IntegerExpr,
    KeyStmt,
    RandomStmt,
    RandomType,
    ReleaseStmt,
    RepeatStmt,
    ResetStmt,
    RestartPayloadStmt,
    ReturnStmt,
    Script,
    Stmt,
    StopPayloadStmt,
    StringExpr,
    StringLnStmt,
    StringStmt,
    UnaryOp,
    VarDef,
    WhileStmt,
)
from ducky.platform import PlatformInterface  # noqa: E402
from ducky.tokens import ActionKey, Operator  # noqa: E402
from ducky.utils.visitor import NodeVisitor  # noqa: E402


class InterpreterError(Exception):
    """Runtime error during payload execution."""


class _BreakSignal(BaseException):
    """Internal signal to exit the innermost WHILE loop."""


class _ContinueSignal(BaseException):
    """Internal signal to skip to the next WHILE iteration."""


class _ReturnSignal(BaseException):
    """Internal signal to exit a function with a return value."""

    def __init__(self, value: int = 0) -> None:
        self.value = value
        super().__init__(value)


class Interpreter(NodeVisitor):
    """AST-walking interpreter that drives a PlatformInterface."""

    def __init__(self, platform: PlatformInterface) -> None:
        self.platform = platform
        self._globals: dict[str, int] = {}
        self._functions: dict[str, tuple[tuple[str, ...], tuple[Stmt, ...]]] = {}
        self._locals: list[dict[str, int]] = []
        self._default_delay: int = 0
        self._default_char_delay: int = 0
        self._last_stmt: Stmt | None = None
        self._loop_depth: int = 0
        self._extensions: dict[str, tuple[Stmt, ...]] = {}

    def interpret(self, script: Script) -> None:
        """Execute a parsed Script against the platform."""
        self.visit(script)

    # ── Script (top-level) ─────────────────────────────────────────────

    def visit_Script(self, node: Script) -> None:
        # Phase 1: register all FunctionDef and ExtensionStmt nodes
        for stmt in node.statements:
            if isinstance(stmt, FunctionDef):
                self._functions[stmt.name] = (stmt.params, stmt.body)
            elif isinstance(stmt, ExtensionStmt):
                self._extensions[stmt.name] = stmt.body
        # Phase 2: execute all non-FunctionDef, non-ExtensionStmt statements
        for stmt in node.statements:
            if not isinstance(stmt, (FunctionDef, ExtensionStmt)):
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
        elif isinstance(stmt, (BreakStmt, ContinueStmt, ReturnStmt)):
            self.visit(stmt)
            # Do NOT track as _last_stmt — loop controls and return aren't repeatable
        else:
            if isinstance(stmt, self._KEYBOARD_STMTS):
                try:
                    self.visit(stmt)
                except BaseException:
                    self.platform.release_all()
                    raise
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
        target = self._locals[-1] if self._locals else self._globals
        target[node.name] = value & 0xFFFF

    def visit_AssignStmt(self, node: AssignStmt) -> None:
        value = self._eval_expr(node.value)
        wrapped = value & 0xFFFF
        if self._locals:
            # Inside a function: check locals top-down, then globals
            for scope in reversed(self._locals):
                if node.name in scope:
                    scope[node.name] = wrapped
                    return
            if node.name in self._globals:
                self._globals[node.name] = wrapped
                return
            # Not found in any scope: create in innermost local scope
            self._locals[-1][node.name] = wrapped
            return
        # Top level: require prior declaration
        if node.name not in self._globals:
            raise InterpreterError(f"Undeclared variable: ${node.name}")
        self._globals[node.name] = wrapped

    # ── Delay statements ───────────────────────────────────────────────

    def visit_DelayStmt(self, node: DelayStmt) -> None:
        ms = self._eval_expr(node.milliseconds)
        ms = max(20, ms)
        self.platform.delay_ms(ms)

    def visit_DefaultDelayStmt(self, node: DefaultDelayStmt) -> None:
        ms = self._eval_expr(node.delay)
        self._default_delay = ms & 0xFFFF
        self.platform.set_default_delay_ms(self._default_delay)

    def visit_DefaultCharDelayStmt(self, node: DefaultCharDelayStmt) -> None:
        ms = self._eval_expr(node.delay)
        self._default_char_delay = ms & 0xFFFF

    # ── Keyboard commands ──────────────────────────────────────────────

    _KEYBOARD_STMTS: tuple[type[Stmt], ...] = (
        StringStmt, StringLnStmt, KeyStmt, ComboStmt,
        HoldStmt, ReleaseStmt, InjectModStmt, RandomStmt,
    )

    def _type_text(self, text: str) -> None:
        """Type text, respecting _default_char_delay."""
        if self._default_char_delay > 0:
            for ch in text:
                self.platform.type_string(ch)
                self.platform.delay_ms(self._default_char_delay)
        else:
            self.platform.type_string(text)

    def visit_StringStmt(self, node: StringStmt) -> None:
        self._type_text(node.text)

    def visit_StringLnStmt(self, node: StringLnStmt) -> None:
        self._type_text(node.text)
        self.platform.press_key((), ActionKey.ENTER)

    def visit_KeyStmt(self, node: KeyStmt) -> None:
        self.platform.press_key((), node.key)

    def visit_ComboStmt(self, node: ComboStmt) -> None:
        self.platform.press_key(node.modifiers, node.key)

    def visit_HoldStmt(self, node: HoldStmt) -> None:
        self.platform.hold_key(node.key)

    def visit_ReleaseStmt(self, node: ReleaseStmt) -> None:
        self.platform.release_key(node.key)

    def visit_InjectModStmt(self, node: InjectModStmt) -> None:
        self.platform.release_all()

    def visit_RandomStmt(self, node: RandomStmt) -> None:
        rtype = node.random_type
        if rtype == RandomType.CHAR:
            n = self.platform.random_int(0x21, 0x7E)
        elif rtype == RandomType.LOWERCASE_LETTER:
            n = self.platform.random_int(0x61, 0x7A)
        elif rtype == RandomType.UPPERCASE_LETTER:
            n = self.platform.random_int(0x41, 0x5A)
        elif rtype == RandomType.LETTER:
            letters = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
            idx = self.platform.random_int(0, len(letters) - 1)
            self.platform.type_string(letters[idx])
            return
        elif rtype == RandomType.NUMBER:
            n = self.platform.random_int(0x30, 0x39)
        elif rtype == RandomType.SPECIAL:
            specials = "!@#$%^&*()"
            idx = self.platform.random_int(0, len(specials) - 1)
            self.platform.type_string(specials[idx])
            return
        else:
            raise InterpreterError(f"Unknown RandomType: {rtype}")
        self.platform.type_string(chr(n))

    # ── Payload control ────────────────────────────────────────────────

    def visit_ResetStmt(self, node: ResetStmt) -> None:
        self.platform.release_all()

    def visit_StopPayloadStmt(self, node: StopPayloadStmt) -> None:
        self.platform.stop_payload()

    def visit_RestartPayloadStmt(self, node: RestartPayloadStmt) -> None:
        self.platform.restart_payload()

    # ── Control flow ──────────────────────────────────────────────────

    def visit_IfStmt(self, node: IfStmt) -> None:
        """Conditional branch with optional else/else-if."""
        if self._eval_expr(node.condition) != 0:
            for stmt in node.body:
                self._visit_statement(stmt)
        elif node.else_body is not None:
            # ELSE IF is represented as a single IfStmt in else_body
            if len(node.else_body) == 1 and isinstance(node.else_body[0], IfStmt):
                self.visit_IfStmt(node.else_body[0])
            else:
                for stmt in node.else_body:
                    self._visit_statement(stmt)

    def visit_WhileStmt(self, node: WhileStmt) -> None:
        """Pre-check loop: repeat body while condition is truthy."""
        self._loop_depth += 1
        try:
            while self._eval_expr(node.condition) != 0:
                try:
                    for stmt in node.body:
                        self._visit_statement(stmt)
                except _ContinueSignal:
                    continue
        except _BreakSignal:
            pass
        finally:
            self._loop_depth -= 1

    def visit_BreakStmt(self, node: BreakStmt) -> None:
        """Exit the innermost WHILE loop."""
        if self._loop_depth == 0:
            raise InterpreterError("BREAK outside WHILE loop")
        raise _BreakSignal()

    def visit_ContinueStmt(self, node: ContinueStmt) -> None:
        """Skip to the next iteration of the innermost WHILE loop."""
        if self._loop_depth == 0:
            raise InterpreterError("CONTINUE outside WHILE loop")
        raise _ContinueSignal()

    # ── Functions ──────────────────────────────────────────────────────

    def visit_CallStmt(self, node: CallStmt) -> None:
        """Execute a function call as a statement (return value discarded)."""
        if node.name not in self._functions:
            raise InterpreterError(f"Undefined function: {node.name}()")
        _params, body = self._functions[node.name]
        self._locals.append({})
        try:
            for stmt in body:
                self._visit_statement(stmt)
        except _ReturnSignal:
            pass
        finally:
            self._locals.pop()

    def visit_CallExpr(self, node: CallExpr) -> int:
        """Execute a function call as an expression (returns value)."""
        if node.name not in self._functions:
            raise InterpreterError(f"Undefined function: {node.name}()")
        _params, body = self._functions[node.name]
        self._locals.append({})
        try:
            for stmt in body:
                self._visit_statement(stmt)
        except _ReturnSignal as signal:
            return signal.value & 0xFFFF
        finally:
            self._locals.pop()
        return 0

    def visit_ReturnStmt(self, node: ReturnStmt) -> None:
        """Exit the current function, optionally returning a value."""
        if not self._locals:
            raise InterpreterError("RETURN outside function")
        value = self._eval_expr(node.value) if node.value is not None else 0
        raise _ReturnSignal(value & 0xFFFF)

    # ── Extensions ──────────────────────────────────────────────────────

    def visit_ExtensionStmt(self, node: ExtensionStmt) -> None:
        """Register an extension block (no execution)."""
        if node.name in self._extensions:
            raise InterpreterError(
                f"Duplicate extension: {node.name} already defined"
            )
        self._extensions[node.name] = node.body

    def visit_IdentifierStmt(self, node: IdentifierStmt) -> None:
        """Execute an extension body if registered, otherwise error."""
        if node.name in self._extensions:
            for stmt in self._extensions[node.name]:
                self._visit_statement(stmt)
        else:
            raise InterpreterError(
                f"Unknown identifier: {node.name}"
            )

    def visit_DuckyLangStmt(self, node: DuckyLangStmt) -> None:
        """Switch keyboard layout at runtime per DUCKY_LANG."""
        self.platform.set_layout(node.language)

    # ── Expression evaluation ──────────────────────────────────────────

    def _eval_expr(self, expr: Expr) -> int:
        return self.visit(expr)  # type: ignore[return-value]

    def visit_IntegerExpr(self, node: IntegerExpr) -> int:
        return node.value & 0xFFFF

    def visit_StringExpr(self, node: StringExpr) -> int:
        raise InterpreterError("String literal not supported in expression context")

    def visit_DollarIdentifierExpr(self, node: DollarIdentifierExpr) -> int:
        # Check local scopes top-down (innermost first)
        for scope in reversed(self._locals):
            if node.name in scope:
                return scope[node.name]
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
