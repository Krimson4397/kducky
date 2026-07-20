"""Tests for the DuckyScript 3 recursive-descent parser.

Covers every statement type, expression precedence, error paths, and
full-program integration via the lexer -> parser pipeline.
"""

import pytest

from ducky.ast import (
    AssignStmt,
    AttackModeStmt,
    BinaryOp,
    BreakStmt,
    ButtonDefStmt,
    CallExpr,
    CallStmt,
    ComboStmt,
    ContinueStmt,
    DefaultCharDelayStmt,
    DefaultDelayStmt,
    DelayStmt,
    DisableButtonStmt,
    DollarIdentifierExpr,
    DuckyLangStmt,
    EnableButtonStmt,
    ExtensionStmt,
    FunctionDef,
    GroupExpr,
    HashIdentifierExpr,
    HidePayloadStmt,
    HoldStmt,
    IdentifierExpr,
    IdentifierStmt,
    IfStmt,
    InjectModStmt,
    IntegerExpr,
    KeyStmt,
    LedState,
    LedStmt,
    RandomStmt,
    RandomType,
    ReleaseStmt,
    RepeatStmt,
    ResetStmt,
    RestartPayloadStmt,
    RestoreAttackModeStmt,
    RestoreHostLockStateStmt,
    RestorePayloadStmt,
    ReturnStmt,
    SaveAttackModeStmt,
    SaveHostLockStateStmt,
    Script,
    StopPayloadStmt,
    StringExpr,
    StringLnStmt,
    StringStmt,
    UnaryOp,
    VarDef,
    WaitForButtonPressStmt,
    WaitForKeyStmt,
    WhileStmt,
)
from ducky.lexer import DuckyLexer
from ducky.parser import DuckyParser, ParseError
from ducky.tokens import ActionKey, ModifierKey, Operator
from ducky.utils.visitor import NodeVisitor

# ── Helpers ───────────────────────────────────────────────────────────────────


def parse(source: str) -> Script:
    """Tokenize *source* and parse into an AST."""
    tokens = DuckyLexer().tokenize(source)
    return DuckyParser(tokens).parse()


def assert_single_stmt(source: str, expected_type: type) -> object:
    """Parse a single-statement source and return the statement node."""
    script = parse(source)
    assert len(script.statements) == 1
    stmt = script.statements[0]
    assert isinstance(stmt, expected_type), (
        f"Expected {expected_type.__name__}, got {type(stmt).__name__}"
    )
    return stmt


# ── Statement tests ──────────────────────────────────────────────────────────


class TestStatements:
    """Every statement type parses to the correct AST node."""

    def test_delay_stmt(self) -> None:
        stmt = assert_single_stmt("DELAY 1000\n", DelayStmt)
        assert isinstance(stmt.milliseconds, IntegerExpr)
        assert stmt.milliseconds.value == 1000

    def test_delay_expr(self) -> None:
        stmt = assert_single_stmt("DELAY 500 + 100\n", DelayStmt)
        assert isinstance(stmt.milliseconds, BinaryOp)
        assert stmt.milliseconds.operator == Operator.ADD

    def test_default_delay_stmt(self) -> None:
        stmt = assert_single_stmt("DEFAULTDELAY 200\n", DefaultDelayStmt)
        assert isinstance(stmt.delay, IntegerExpr)
        assert stmt.delay.value == 200

    def test_default_delay_alt(self) -> None:
        stmt = assert_single_stmt("DEFAULT_DELAY 300\n", DefaultDelayStmt)
        assert isinstance(stmt.delay, IntegerExpr)
        assert stmt.delay.value == 300

    def test_default_char_delay_stmt(self) -> None:
        stmt = assert_single_stmt("DEFAULTCHARDELAY 50\n", DefaultCharDelayStmt)
        assert isinstance(stmt.delay, IntegerExpr)
        assert stmt.delay.value == 50

    def test_default_char_delay_alt(self) -> None:
        stmt = assert_single_stmt("DEFAULT_CHAR_DELAY 75\n", DefaultCharDelayStmt)
        assert stmt.delay.value == 75

    def test_string_delay_alias(self) -> None:
        stmt = assert_single_stmt("STRINGDELAY 30\n", DefaultCharDelayStmt)
        assert stmt.delay.value == 30

    def test_string_stmt(self) -> None:
        stmt = assert_single_stmt('STRING hello world\n', StringStmt)
        assert stmt.text == "hello world"

    def test_string_empty(self) -> None:
        stmt = assert_single_stmt("STRING\n", StringStmt)
        assert stmt.text == ""

    def test_string_ln_stmt(self) -> None:
        stmt = assert_single_stmt('STRINGLN hello\n', StringLnStmt)
        assert stmt.text == "hello"

    def test_string_ln_empty(self) -> None:
        stmt = assert_single_stmt("STRINGLN\n", StringLnStmt)
        assert stmt.text == ""

    def test_key_stmt(self) -> None:
        stmt = assert_single_stmt("ENTER\n", KeyStmt)
        assert stmt.key == ActionKey.ENTER

    def test_key_stmt_f_key(self) -> None:
        stmt = assert_single_stmt("F1\n", KeyStmt)
        assert stmt.key == ActionKey.F1

    def test_combo_stmt(self) -> None:
        stmt = assert_single_stmt("CTRL ENTER\n", ComboStmt)
        assert stmt.modifiers == (ModifierKey.CTRL,)
        assert stmt.key == ActionKey.ENTER

    def test_combo_multiple_modifiers(self) -> None:
        stmt = assert_single_stmt("CTRL SHIFT ESCAPE\n", ComboStmt)
        assert stmt.modifiers == (ModifierKey.CTRL, ModifierKey.SHIFT)
        assert stmt.key == ActionKey.ESCAPE

    def test_combo_hyphen_separator(self) -> None:
        stmt = assert_single_stmt("CTRL-SHIFT-ENTER\n", ComboStmt)
        assert stmt.modifiers == (ModifierKey.CTRL, ModifierKey.SHIFT)
        assert stmt.key == ActionKey.ENTER

    def test_combo_modifier_only(self) -> None:
        stmt = assert_single_stmt("CTRL-SHIFT\n", ComboStmt)
        assert stmt.modifiers == (ModifierKey.CTRL, ModifierKey.SHIFT)
        assert stmt.key is None

    def test_combo_single_modifier_only(self) -> None:
        stmt = assert_single_stmt("GUI\n", ComboStmt)
        assert stmt.modifiers == (ModifierKey.GUI,)
        assert stmt.key is None

    def test_inject_mod(self) -> None:
        stmt = assert_single_stmt("INJECT_MOD\n", InjectModStmt)
        assert isinstance(stmt, InjectModStmt)

    def test_hold_stmt(self) -> None:
        stmt = assert_single_stmt("HOLD ENTER\n", HoldStmt)
        assert stmt.key == ActionKey.ENTER

    def test_release_stmt(self) -> None:
        stmt = assert_single_stmt("RELEASE SPACE\n", ReleaseStmt)
        assert stmt.key == ActionKey.SPACE

    def test_repeat_stmt(self) -> None:
        stmt = assert_single_stmt("REPEAT 3\n", RepeatStmt)
        assert isinstance(stmt.count, IntegerExpr)
        assert stmt.count.value == 3

    def test_reset_stmt(self) -> None:
        stmt = assert_single_stmt("RESET\n", ResetStmt)
        assert isinstance(stmt, ResetStmt)

    def test_restart_payload_stmt(self) -> None:
        stmt = assert_single_stmt("RESTART_PAYLOAD\n", RestartPayloadStmt)
        assert isinstance(stmt, RestartPayloadStmt)

    def test_stop_payload_stmt(self) -> None:
        stmt = assert_single_stmt("STOP_PAYLOAD\n", StopPayloadStmt)
        assert isinstance(stmt, StopPayloadStmt)

    def test_var_decl(self) -> None:
        stmt = assert_single_stmt("VAR $x\n", VarDef)
        assert stmt.name == "x"
        assert isinstance(stmt.initializer, IntegerExpr)
        assert stmt.initializer.value == 0

    def test_var_decl_with_init(self) -> None:
        stmt = assert_single_stmt("VAR $x = 42\n", VarDef)
        assert stmt.name == "x"
        assert isinstance(stmt.initializer, IntegerExpr)
        assert stmt.initializer.value == 42

    def test_var_decl_with_expr_init(self) -> None:
        stmt = assert_single_stmt("VAR $x = 1 + 2\n", VarDef)
        assert isinstance(stmt.initializer, BinaryOp)

    def test_assign_stmt(self) -> None:
        stmt = assert_single_stmt("$x = 42\n", AssignStmt)
        assert stmt.name == "x"
        assert stmt.value.value == 42

    def test_assign_expr(self) -> None:
        stmt = assert_single_stmt("$x = $x + 1\n", AssignStmt)
        assert isinstance(stmt.value, BinaryOp)

    def test_if_stmt(self) -> None:
        script = parse("IF 1 THEN\nRESET\nEND_IF\n")
        assert len(script.statements) == 1
        stmt = script.statements[0]
        assert isinstance(stmt, IfStmt)
        assert stmt.condition.value == 1
        assert len(stmt.body) == 1
        assert isinstance(stmt.body[0], ResetStmt)
        assert stmt.else_body is None

    def test_if_else_stmt(self) -> None:
        script = parse("IF 1 THEN\nDELAY 100\nELSE\nDELAY 200\nEND_IF\n")
        stmt = script.statements[0]
        assert isinstance(stmt, IfStmt)
        assert len(stmt.body) == 1
        assert len(stmt.else_body) == 1

    def test_if_else_if_chain(self) -> None:
        source = "IF 1 THEN\nDELAY 10\nELSE IF 2 THEN\nDELAY 20\nELSE\nDELAY 30\nEND_IF\n"
        script = parse(source)
        stmt = script.statements[0]
        assert isinstance(stmt, IfStmt)
        # ELSE IF is represented as nested IfStmt in else_body
        assert len(stmt.else_body) == 1
        elif_stmt = stmt.else_body[0]
        assert isinstance(elif_stmt, IfStmt)
        assert elif_stmt.condition.value == 2
        assert len(elif_stmt.body) == 1
        # ELSE is in the nested IfStmt's else_body
        assert len(elif_stmt.else_body) == 1
        assert isinstance(elif_stmt.else_body[0], DelayStmt)

    def test_if_parens(self) -> None:
        script = parse("IF (1) THEN\nRESET\nEND_IF\n")
        stmt = script.statements[0]
        assert isinstance(stmt, IfStmt)
        assert stmt.condition.value == 1

    def test_while_stmt(self) -> None:
        script = parse("WHILE $x\nDELAY 100\nEND_WHILE\n")
        assert len(script.statements) == 1
        stmt = script.statements[0]
        assert isinstance(stmt, WhileStmt)
        assert isinstance(stmt.condition, DollarIdentifierExpr)
        assert len(stmt.body) == 1

    def test_while_parens(self) -> None:
        script = parse("WHILE ($x)\nDELAY 100\nEND_WHILE\n")
        stmt = script.statements[0]
        assert isinstance(stmt, WhileStmt)
        assert isinstance(stmt.condition, DollarIdentifierExpr)

    def test_break_stmt(self) -> None:
        script = parse("WHILE 1\nBREAK\nEND_WHILE\n")
        assert len(script.statements) == 1
        wh = script.statements[0]
        assert isinstance(wh, WhileStmt)
        assert len(wh.body) == 1
        assert isinstance(wh.body[0], BreakStmt)

    def test_continue_stmt(self) -> None:
        script = parse("WHILE 1\nCONTINUE\nEND_WHILE\n")
        stmt = script.statements[0]
        assert isinstance(stmt, WhileStmt)
        assert isinstance(stmt.body[0], ContinueStmt)

    def test_function_def(self) -> None:
        source = "FUNCTION foo()\nRESET\nEND_FUNCTION\n"
        script = parse(source)
        assert len(script.statements) == 1
        stmt = script.statements[0]
        assert isinstance(stmt, FunctionDef)
        assert stmt.name == "foo"
        assert len(stmt.body) == 1
        assert isinstance(stmt.body[0], ResetStmt)

    def test_call_stmt(self) -> None:
        stmt = assert_single_stmt("foo()\n", CallStmt)
        assert stmt.name == "foo"

    def test_return_stmt(self) -> None:
        source = "FUNCTION foo()\nRETURN 42\nEND_FUNCTION\n"
        script = parse(source)
        fn = script.statements[0]
        assert isinstance(fn, FunctionDef)
        ret = fn.body[0]
        assert isinstance(ret, ReturnStmt)
        assert ret.value is not None
        assert ret.value.value == 42

    def test_return_without_value(self) -> None:
        source = "FUNCTION foo()\nRETURN\nEND_FUNCTION\n"
        script = parse(source)
        fn = script.statements[0]
        assert isinstance(fn.body[0], ReturnStmt)
        assert fn.body[0].value is None

    def test_random_stmt(self) -> None:
        for token_name, random_type in [
            ("RANDOM_CHAR", RandomType.CHAR),
            ("RANDOM_LOWERCASE_LETTER", RandomType.LOWERCASE_LETTER),
            ("RANDOM_UPPERCASE_LETTER", RandomType.UPPERCASE_LETTER),
            ("RANDOM_LETTER", RandomType.LETTER),
            ("RANDOM_NUMBER", RandomType.NUMBER),
            ("RANDOM_SPECIAL", RandomType.SPECIAL),
        ]:
            stmt = assert_single_stmt(f"{token_name}\n", RandomStmt)
            assert stmt.random_type == random_type

    def test_led_stmt(self) -> None:
        for token_name, led_state in [
            ("LED_OFF", LedState.OFF),
            ("LED_R", LedState.R),
            ("LED_G", LedState.G),
            ("LED_B", LedState.B),
        ]:
            stmt = assert_single_stmt(f"{token_name}\n", LedStmt)
            assert stmt.state == led_state

    def test_attack_mode_stmt(self) -> None:
        stmt = assert_single_stmt("ATTACKMODE HID STORAGE\n", AttackModeStmt)
        assert stmt.params == ("HID", "STORAGE")

    def test_button_def_stmt(self) -> None:
        source = "BUTTON_DEF\nRESET\nEND_BUTTON\n"
        script = parse(source)
        assert len(script.statements) == 1
        stmt = script.statements[0]
        assert isinstance(stmt, ButtonDefStmt)
        assert stmt.name == ""
        assert len(stmt.body) == 1

    def test_wait_for_button(self) -> None:
        stmt = assert_single_stmt("WAIT_FOR_BUTTON_PRESS\n", WaitForButtonPressStmt)
        assert isinstance(stmt, WaitForButtonPressStmt)

    def test_disable_button(self) -> None:
        stmt = assert_single_stmt("DISABLE_BUTTON\n", DisableButtonStmt)
        assert isinstance(stmt, DisableButtonStmt)

    def test_enable_button(self) -> None:
        stmt = assert_single_stmt("ENABLE_BUTTON\n", EnableButtonStmt)
        assert isinstance(stmt, EnableButtonStmt)

    def test_ducky_lang_stmt(self) -> None:
        stmt = assert_single_stmt("DUCKY_LANG DE\n", DuckyLangStmt)
        assert stmt.language == "DE"

    def test_extension_def(self) -> None:
        source = "EXTENSION myext\nRESET\nEND_EXTENSION\n"
        script = parse(source)
        assert len(script.statements) == 1
        stmt = script.statements[0]
        assert isinstance(stmt, ExtensionStmt)
        assert stmt.name == "myext"
        assert len(stmt.body) == 1

    def test_save_attack_mode(self) -> None:
        stmt = assert_single_stmt("SAVE_ATTACKMODE\n", SaveAttackModeStmt)
        assert isinstance(stmt, SaveAttackModeStmt)

    def test_restore_attack_mode(self) -> None:
        stmt = assert_single_stmt("RESTORE_ATTACKMODE\n", RestoreAttackModeStmt)
        assert isinstance(stmt, RestoreAttackModeStmt)

    def test_wait_for_caps_on(self) -> None:
        stmt = assert_single_stmt("WAIT_FOR_CAPS_ON\n", WaitForKeyStmt)
        assert stmt.lock_key.name == "CAPS"
        assert stmt.state.name == "ON"

    def test_wait_for_num_off(self) -> None:
        stmt = assert_single_stmt("WAIT_FOR_NUM_OFF\n", WaitForKeyStmt)
        assert stmt.lock_key.name == "NUM"
        assert stmt.state.name == "OFF"

    def test_save_host_lock_state(self) -> None:
        stmt = assert_single_stmt("SAVE_HOST_KEYBOARD_LOCK_STATE\n", SaveHostLockStateStmt)
        assert isinstance(stmt, SaveHostLockStateStmt)

    def test_restore_host_lock_state(self) -> None:
        stmt = assert_single_stmt(
            "RESTORE_HOST_KEYBOARD_LOCK_STATE\n", RestoreHostLockStateStmt
        )
        assert isinstance(stmt, RestoreHostLockStateStmt)

    def test_hide_payload(self) -> None:
        stmt = assert_single_stmt("HIDE_PAYLOAD\n", HidePayloadStmt)
        assert isinstance(stmt, HidePayloadStmt)

    def test_restore_payload(self) -> None:
        stmt = assert_single_stmt("RESTORE_PAYLOAD\n", RestorePayloadStmt)
        assert isinstance(stmt, RestorePayloadStmt)


# ── Expression tests ─────────────────────────────────────────────────────────


class TestExpressions:
    """Expression parsing with correct precedence."""

    def test_integer_literal(self) -> None:
        stmt = assert_single_stmt("DELAY 42\n", DelayStmt)
        assert stmt.milliseconds.value == 42

    def test_string_literal(self) -> None:
        script = parse('VAR $x = "hello"\n')
        assert isinstance(script.statements[0], VarDef)
        assert isinstance(script.statements[0].initializer, StringExpr)
        assert script.statements[0].initializer.value == "hello"

    def test_unary_not(self) -> None:
        script = parse("VAR $x = !0\n")
        vardef = script.statements[0]
        assert isinstance(vardef, VarDef)
        assert isinstance(vardef.initializer, UnaryOp)
        assert vardef.initializer.operator == Operator.NOT
        assert vardef.initializer.operand.value == 0

    def test_unary_minus(self) -> None:
        script = parse("VAR $x = -5\n")
        vardef = script.statements[0]
        assert isinstance(vardef, VarDef)
        assert isinstance(vardef.initializer, UnaryOp)
        assert vardef.initializer.operator == Operator.SUBTRACT
        assert vardef.initializer.operand.value == 5

    def test_precedence_mul_before_add(self) -> None:
        """5 + 3 * 2 should parse as 5 + (3 * 2)."""
        script = parse("VAR $x = 5 + 3 * 2\n")
        expr = script.statements[0].initializer
        assert isinstance(expr, BinaryOp)
        assert expr.operator == Operator.ADD
        assert expr.left.value == 5
        assert isinstance(expr.right, BinaryOp)
        assert expr.right.operator == Operator.MULTIPLY
        assert expr.right.left.value == 3
        assert expr.right.right.value == 2

    def test_precedence_add_before_shift(self) -> None:
        """1 + 2 << 3 should parse as (1 + 2) << 3 because add binds tighter."""
        script = parse("VAR $x = 1 + 2 << 3\n")
        expr = script.statements[0].initializer
        assert isinstance(expr, BinaryOp)
        assert expr.operator == Operator.SHIFT_LEFT
        assert isinstance(expr.left, BinaryOp)
        assert expr.left.operator == Operator.ADD

    def test_precedence_relational(self) -> None:
        """5 < 3 + 2 should parse as 5 < (3 + 2)."""
        script = parse("VAR $x = 5 < 3 + 2\n")
        expr = script.statements[0].initializer
        assert isinstance(expr, BinaryOp)
        assert expr.operator == Operator.LESS
        assert expr.left.value == 5
        assert isinstance(expr.right, BinaryOp)
        assert expr.right.operator == Operator.ADD

    def test_parentheses_override(self) -> None:
        """(5 + 3) * 2 should parse differently from 5 + 3 * 2."""
        script = parse("VAR $x = (5 + 3) * 2\n")
        expr = script.statements[0].initializer
        assert isinstance(expr, BinaryOp)
        assert expr.operator == Operator.MULTIPLY
        assert isinstance(expr.left, GroupExpr)
        assert isinstance(expr.left.expression, BinaryOp)
        assert expr.left.expression.operator == Operator.ADD

    def test_assignment_right_assoc(self) -> None:
        """$a = $b = 5 should parse as $a = ($b = 5)."""
        script = parse("VAR $a\nVAR $b\n$a = $b = 5\n")
        assign = script.statements[2]
        assert isinstance(assign, AssignStmt)
        assert assign.name == "a"
        assert isinstance(assign.value, BinaryOp)
        assert assign.value.operator == Operator.ASSIGN
        assert isinstance(assign.value.left, DollarIdentifierExpr)
        assert assign.value.left.name == "b"
        assert assign.value.right.value == 5

    def test_call_expr_in_expression(self) -> None:
        """$x = foo() should parse as assignment of a call expression."""
        script = parse("$x = foo()\n")
        # The parser sees DOLLAR_IDENTIFIER followed by ASSIGN
        # so it dispatches to _parse_assign_stmt
        assert len(script.statements) == 1
        stmt = script.statements[0]
        assert isinstance(stmt, AssignStmt)
        assert isinstance(stmt.value, CallExpr)
        assert stmt.value.name == "foo"

    def test_boolean_true(self) -> None:
        script = parse("VAR $x = TRUE\n")
        expr = script.statements[0].initializer
        assert expr.value == 1

    def test_boolean_false(self) -> None:
        script = parse("VAR $x = FALSE\n")
        expr = script.statements[0].initializer
        assert expr.value == 0

    def test_identifier_expr(self) -> None:
        """Plain identifier (not followed by ()) is an IdentifierExpr."""
        script = parse("VAR $x = myvar\n")
        expr = script.statements[0].initializer
        assert isinstance(expr, IdentifierExpr)
        assert expr.name == "myvar"

    def test_hash_identifier_expr(self) -> None:
        script = parse("VAR $x = #MYCONST\n")
        expr = script.statements[0].initializer
        assert isinstance(expr, HashIdentifierExpr)
        assert expr.name == "MYCONST"

    def test_equality_chain(self) -> None:
        """1 == 2 != 3 should parse as (1 == 2) != 3."""
        script = parse("VAR $x = 1 == 2 != 3\n")
        expr = script.statements[0].initializer
        assert isinstance(expr, BinaryOp)
        assert expr.operator == Operator.NOT_EQUAL
        assert isinstance(expr.left, BinaryOp)
        assert expr.left.operator == Operator.EQUAL

    def test_logical_and_or(self) -> None:
        """1 && 0 || 1 should parse as (1 && 0) || 1."""
        script = parse("VAR $x = 1 && 0 || 1\n")
        expr = script.statements[0].initializer
        assert isinstance(expr, BinaryOp)
        assert expr.operator == Operator.LOGICAL_OR
        assert isinstance(expr.left, BinaryOp)
        assert expr.left.operator == Operator.LOGICAL_AND

    def test_bitwise_ops(self) -> None:
        """1 & 2 | 3 should parse as (1 & 2) | 3."""
        script = parse("VAR $x = 1 & 2 | 3\n")
        expr = script.statements[0].initializer
        assert isinstance(expr, BinaryOp)
        assert expr.operator == Operator.BITWISE_OR
        assert isinstance(expr.left, BinaryOp)
        assert expr.left.operator == Operator.BITWISE_AND

    def test_shift_ops(self) -> None:
        """1 << 2 + 3 should parse as 1 << (2 + 3)."""
        script = parse("VAR $x = 1 << 2 + 3\n")
        expr = script.statements[0].initializer
        assert isinstance(expr, BinaryOp)
        assert expr.operator == Operator.SHIFT_LEFT
        assert expr.left.value == 1
        assert isinstance(expr.right, BinaryOp)
        assert expr.right.operator == Operator.ADD

    def test_power_operator(self) -> None:
        """2 ^ 3 should parse as exponentiation."""
        script = parse("VAR $x = 2 ^ 3\n")
        expr = script.statements[0].initializer
        assert isinstance(expr, BinaryOp)
        assert expr.operator == Operator.POWER
        assert expr.left.value == 2
        assert expr.right.value == 3


# ── Error tests ──────────────────────────────────────────────────────────────


class TestErrors:
    """Syntax errors produce correct diagnostics."""

    def test_return_outside_function(self) -> None:
        with pytest.raises(ParseError, match="RETURN outside function"):
            parse("RETURN\n")

    def test_break_outside_loop(self) -> None:
        with pytest.raises(ParseError, match="BREAK outside loop"):
            parse("BREAK\n")

    def test_continue_outside_loop(self) -> None:
        with pytest.raises(ParseError, match="CONTINUE outside loop"):
            parse("CONTINUE\n")

    def test_repeat_after_end_if(self) -> None:
        with pytest.raises(ParseError, match="REPEAT must follow"):
            parse("IF 1 THEN\nRESET\nEND_IF\nREPEAT 3\n")

    def test_repeat_after_end_while(self) -> None:
        with pytest.raises(ParseError, match="REPEAT must follow"):
            parse("WHILE 1\nDELAY 100\nEND_WHILE\nREPEAT 3\n")

    def test_missing_then(self) -> None:
        with pytest.raises(ParseError, match="Expected THEN"):
            parse("IF 1\nRESET\nEND_IF\n")

    def test_unexpected_else(self) -> None:
        with pytest.raises(ParseError, match="Unexpected ELSE"):
            parse("ELSE\nRESET\n")

    def test_unexpected_end_if(self) -> None:
        with pytest.raises(ParseError, match="Unexpected END_IF"):
            parse("END_IF\n")

    def test_unexpected_token(self) -> None:
        """Bare identifier now parses as IdentifierStmt (runtime error, not parse error)."""
        script = parse("NOT_A_KEYWORD\n")
        assert len(script.statements) == 1
        assert isinstance(script.statements[0], IdentifierStmt)
        assert script.statements[0].name == "NOT_A_KEYWORD"

    def test_invalid_dollar_standalone(self) -> None:
        with pytest.raises(ParseError, match="without assignment"):
            parse("$x\n")

    def test_identifier_not_call(self) -> None:
        """Bare identifier now parses as IdentifierStmt (runtime error, not parse error)."""
        script = parse("myfunc\n")
        assert len(script.statements) == 1
        assert isinstance(script.statements[0], IdentifierStmt)
        assert script.statements[0].name == "myfunc"


# ── Full program tests ───────────────────────────────────────────────────────


class TestFullPrograms:
    """Multi-statement programs parse correctly."""

    def test_empty_program(self) -> None:
        script = parse("")
        assert len(script.statements) == 0

    def test_blank_lines(self) -> None:
        script = parse("\n\n\n")
        assert len(script.statements) == 0

    def test_simple_program(self) -> None:
        source = (
            "DELAY 1000\n"
            "STRING hello world\n"
            "ENTER\n"
        )
        script = parse(source)
        assert len(script.statements) == 3
        assert isinstance(script.statements[0], DelayStmt)
        assert isinstance(script.statements[1], StringStmt)
        assert isinstance(script.statements[2], KeyStmt)

    def test_nested_if_while(self) -> None:
        source = (
            "IF 1 THEN\n"
            "  WHILE 2\n"
            "    BREAK\n"
            "  END_WHILE\n"
            "END_IF\n"
        )
        script = parse(source)
        assert len(script.statements) == 1
        if_stmt = script.statements[0]
        assert isinstance(if_stmt, IfStmt)
        assert len(if_stmt.body) == 1
        while_stmt = if_stmt.body[0]
        assert isinstance(while_stmt, WhileStmt)
        assert len(while_stmt.body) == 1
        assert isinstance(while_stmt.body[0], BreakStmt)

    def test_multiple_var_assign(self) -> None:
        source = (
            "VAR $x\n"
            "VAR $y = 10\n"
            "$x = $y + 5\n"
        )
        script = parse(source)
        assert len(script.statements) == 3
        assert isinstance(script.statements[0], VarDef)
        assert script.statements[0].name == "x"
        assert isinstance(script.statements[1], VarDef)
        assert script.statements[1].name == "y"
        assert isinstance(script.statements[2], AssignStmt)

    def test_repeat_after_delay(self) -> None:
        """REPEAT is valid after a non-block-end statement like DELAY."""
        source = "DELAY 100\nREPEAT 3\n"
        script = parse(source)
        assert len(script.statements) == 2
        assert isinstance(script.statements[1], RepeatStmt)

    def test_repeat_after_key(self) -> None:
        source = "ENTER\nREPEAT 5\n"
        script = parse(source)
        assert len(script.statements) == 2
        assert isinstance(script.statements[1], RepeatStmt)

    def test_function_with_body(self) -> None:
        source = (
            "FUNCTION foo()\n"
            "DELAY 500\n"
            "VAR $x = 1\n"
            "RETURN $x\n"
            "END_FUNCTION\n"
            "foo()\n"
        )
        script = parse(source)
        assert len(script.statements) == 2
        assert isinstance(script.statements[0], FunctionDef)
        assert len(script.statements[0].body) == 3
        assert isinstance(script.statements[1], CallStmt)

    def test_attack_mode_params(self) -> None:
        source = "ATTACKMODE HID STORAGE VID_05AC PID_RANDOM\n"
        stmt = assert_single_stmt(source, AttackModeStmt)
        assert stmt.params == ("HID", "STORAGE", "VID_05AC", "PID_RANDOM")


# ── NodeVisitor tests ────────────────────────────────────────────────────────


class TestNodeVisitor:
    """NodeVisitor base class dispatches correctly."""

    def test_visitor_dispatch(self) -> None:
        class TestVisitor(NodeVisitor):
            def __init__(self) -> None:
                self.visited: list[str] = []

            def visit_ResetStmt(self, node: ResetStmt) -> object:  # noqa: N802
                self.visited.append("ResetStmt")
                return None

            def visit_IntegerExpr(self, node: IntegerExpr) -> object:  # noqa: N802
                self.visited.append("IntegerExpr")
                return None

        visitor = TestVisitor()
        visitor.visit(ResetStmt())
        visitor.visit(IntegerExpr(42))
        assert visitor.visited == ["ResetStmt", "IntegerExpr"]

    def test_generic_visit_raises(self) -> None:
        visitor = NodeVisitor()
        with pytest.raises(NotImplementedError, match="No visit method"):
            visitor.visit(IntegerExpr(42))


# ── Statement edge cases ──────────────────────────────────────────────────


class TestStatementEdgeCases:
    """Edge cases for statement parsing beyond basic happy paths."""

    def test_delay_zero(self) -> None:
        """DELAY 0 is valid and parses correctly."""
        stmt = assert_single_stmt("DELAY 0\n", DelayStmt)
        assert stmt.milliseconds.value == 0

    def test_delay_expr_with_parens(self) -> None:
        """DELAY with parenthesized expression."""
        stmt = assert_single_stmt("DELAY (100 + 50)\n", DelayStmt)
        assert isinstance(stmt.milliseconds, GroupExpr)

    def test_key_stmt_many(self) -> None:
        """Many action keys parse correctly."""
        for key_name in [
            "ENTER", "SPACE", "TAB", "BACKSPACE", "DELETE",
            "HOME", "END", "ESCAPE", "MENU", "CAPSLOCK",
        ]:
            stmt = assert_single_stmt(f"{key_name}\n", KeyStmt)
            assert stmt.key.name == key_name

    def test_key_stmt_f_keys(self) -> None:
        """All F1-F12 action keys parse correctly."""
        for i in range(1, 13):
            stmt = assert_single_stmt(f"F{i}\n", KeyStmt)
            assert stmt.key.name == f"F{i}"

    def test_combo_with_gui(self) -> None:
        """GUI modifier key works in combo."""
        stmt = assert_single_stmt("GUI ENTER\n", ComboStmt)
        assert ModifierKey.GUI in stmt.modifiers

    def test_combo_with_alt(self) -> None:
        """ALT modifier key works in combo."""
        stmt = assert_single_stmt("ALT TAB\n", ComboStmt)
        assert stmt.key == ActionKey.TAB

    def test_combo_mixed_separators(self) -> None:
        """Mixed space and hyphen separators in combo."""
        stmt = assert_single_stmt("CTRL-SHIFT ENTER\n", ComboStmt)
        assert stmt.modifiers == (ModifierKey.CTRL, ModifierKey.SHIFT)
        assert stmt.key == ActionKey.ENTER

    def test_default_delay_expr(self) -> None:
        """DEFAULTDELAY accepts expression value."""
        stmt = assert_single_stmt("DEFAULTDELAY 500 + 100\n", DefaultDelayStmt)
        assert isinstance(stmt.delay, BinaryOp)

    def test_hold_key_many(self) -> None:
        """HOLD with different action keys."""
        stmt = assert_single_stmt("HOLD SPACE\n", HoldStmt)
        assert stmt.key == ActionKey.SPACE
        stmt2 = assert_single_stmt("HOLD TAB\n", HoldStmt)
        assert stmt2.key == ActionKey.TAB

    def test_var_decl_underscore_name(self) -> None:
        """VAR $my_var parses with underscore in name."""
        stmt = assert_single_stmt("VAR $my_var\n", VarDef)
        assert stmt.name == "my_var"

    def test_assign_with_expr(self) -> None:
        """$x = (1 + 2) * 3 parses as assignment of complex expression."""
        stmt = assert_single_stmt("$x = (1 + 2) * 3\n", AssignStmt)
        assert isinstance(stmt.value, BinaryOp)
        assert stmt.value.operator == Operator.MULTIPLY

    def test_if_empty_body(self) -> None:
        """IF with no statements in body."""
        script = parse("IF 1 THEN\nEND_IF\n")
        stmt = script.statements[0]
        assert isinstance(stmt, IfStmt)
        assert len(stmt.body) == 0

    def test_while_empty_body(self) -> None:
        """WHILE with no statements in body."""
        script = parse("WHILE 1\nEND_WHILE\n")
        stmt = script.statements[0]
        assert isinstance(stmt, WhileStmt)
        assert len(stmt.body) == 0

    def test_function_empty_body(self) -> None:
        """Function with no statements in body."""
        source = "FUNCTION foo()\nEND_FUNCTION\n"
        script = parse(source)
        stmt = script.statements[0]
        assert isinstance(stmt, FunctionDef)
        assert stmt.name == "foo"
        assert len(stmt.body) == 0

    def test_multiple_else_if(self) -> None:
        """IF with multiple ELSE IF branches."""
        source = (
            "IF 1 THEN\nDELAY 10\n"
            "ELSE IF 2 THEN\nDELAY 20\n"
            "ELSE IF 3 THEN\nDELAY 30\n"
            "END_IF\n"
        )
        script = parse(source)
        stmt = script.statements[0]
        assert isinstance(stmt, IfStmt)
        # First ELSE IF
        elif1 = stmt.else_body[0]
        assert isinstance(elif1, IfStmt)
        # Second ELSE IF nested in first's else_body
        elif2 = elif1.else_body[0]
        assert isinstance(elif2, IfStmt)
        assert elif2.condition.value == 3

    def test_attack_mode_off(self) -> None:
        """ATTACKMODE OFF parses correctly."""
        stmt = assert_single_stmt("ATTACKMODE OFF\n", AttackModeStmt)
        assert stmt.params == ("OFF",)

    def test_wait_for_scroll_change(self) -> None:
        """WAIT_FOR_SCROLL_CHANGE parses correctly."""
        stmt = assert_single_stmt("WAIT_FOR_SCROLL_CHANGE\n", WaitForKeyStmt)
        assert stmt.lock_key.name == "SCROLL"
        assert stmt.state.name == "CHANGE"

    def test_extension_empty_body(self) -> None:
        """EXTENSION with empty body."""
        source = "EXTENSION myext\nEND_EXTENSION\n"
        script = parse(source)
        stmt = script.statements[0]
        assert isinstance(stmt, ExtensionStmt)
        assert len(stmt.body) == 0



# ── Expression edge cases ────────────────────────────────────────────────


class TestExpressionEdgeCases:
    """Expression edge cases beyond basic precedence."""

    def test_hex_integer_expr(self) -> None:
        """Hex integer literal in expression."""
        stmt = assert_single_stmt("DELAY 0xFF\n", DelayStmt)
        assert stmt.milliseconds.value == 255

    def test_unary_not_on_complex(self) -> None:
        """! on parenthesized expression."""
        script = parse("VAR $x = !(1 + 2)\n")
        expr = script.statements[0].initializer
        assert isinstance(expr, UnaryOp)
        assert expr.operator == Operator.NOT
        assert isinstance(expr.operand, GroupExpr)

    def test_unary_minus_on_complex(self) -> None:
        """- on parenthesized expression."""
        script = parse("VAR $x = -(5 * 2)\n")
        expr = script.statements[0].initializer
        assert isinstance(expr, UnaryOp)
        assert expr.operator == Operator.SUBTRACT
        assert isinstance(expr.operand, GroupExpr)

    def test_double_unary(self) -> None:
        """!!0 should parse as unary NOT applied twice."""
        script = parse("VAR $x = !!0\n")
        expr = script.statements[0].initializer
        assert isinstance(expr, UnaryOp)
        assert expr.operator == Operator.NOT
        assert isinstance(expr.operand, UnaryOp)
        assert expr.operand.operator == Operator.NOT

    def test_power_associativity(self) -> None:
        """2 ^ 3 ^ 4 should parse as (2 ^ 3) ^ 4 (left associativity)."""
        script = parse("VAR $x = 2 ^ 3 ^ 4\n")
        expr = script.statements[0].initializer
        assert isinstance(expr, BinaryOp)
        assert expr.operator == Operator.POWER
        assert expr.right.value == 4
        assert isinstance(expr.left, BinaryOp)
        assert expr.left.operator == Operator.POWER
        assert expr.left.left.value == 2
        assert expr.left.right.value == 3

    def test_power_precedence_vs_multiply(self) -> None:
        """2 * 3 ^ 4 parses as (2 * 3) ^ 4 per spec §4.1 (same level, left-assoc)."""
        script = parse("VAR $x = 2 * 3 ^ 4\n")
        expr = script.statements[0].initializer
        assert isinstance(expr, BinaryOp)
        assert expr.operator == Operator.POWER
        assert expr.right.value == 4
        assert isinstance(expr.left, BinaryOp)
        assert expr.left.operator == Operator.MULTIPLY
        assert expr.left.left.value == 2
        assert expr.left.right.value == 3

    def test_chained_comparison(self) -> None:
        """1 < 2 < 3 should parse as (1 < 2) < 3."""
        script = parse("VAR $x = 1 < 2 < 3\n")
        expr = script.statements[0].initializer
        assert isinstance(expr, BinaryOp)
        assert expr.operator == Operator.LESS
        assert expr.right.value == 3
        assert isinstance(expr.left, BinaryOp)
        assert expr.left.operator == Operator.LESS
        assert expr.left.left.value == 1
        assert expr.left.right.value == 2

    def test_modulo_operator(self) -> None:
        """10 % 3 parses correctly."""
        script = parse("VAR $x = 10 % 3\n")
        expr = script.statements[0].initializer
        assert isinstance(expr, BinaryOp)
        assert expr.operator == Operator.MODULO
        assert expr.left.value == 10
        assert expr.right.value == 3

    def test_dollar_identifier_expr(self) -> None:
        """$name in expression context."""
        script = parse("DELAY $timeout\n")
        stmt = script.statements[0]
        assert isinstance(stmt.milliseconds, DollarIdentifierExpr)
        assert stmt.milliseconds.name == "timeout"


# ── Additional error tests ────────────────────────────────────────────────


class TestErrorEdgeCases:
    """Additional error conditions with diagnostic validation."""

    def test_missing_end_if(self) -> None:
        """Unterminated IF block."""
        with pytest.raises(ParseError, match="Expected END_IF"):
            parse("IF 1 THEN\nDELAY 100\n")

    def test_missing_end_while(self) -> None:
        """Unterminated WHILE block."""
        with pytest.raises(ParseError, match="Expected END_WHILE"):
            parse("WHILE $x\nDELAY 100\n")

    def test_missing_end_function(self) -> None:
        """Unterminated FUNCTION block."""
        with pytest.raises(ParseError, match="Expected END_FUNCTION"):
            parse("FUNCTION foo()\nDELAY 100\n")

    def test_missing_end_extension(self) -> None:
        """Unterminated EXTENSION block."""
        with pytest.raises(ParseError, match="Expected END_EXTENSION"):
            parse("EXTENSION myext\nDELAY 100\n")

    def test_repeat_after_end_function(self) -> None:
        """REPEAT after END_FUNCTION should be invalid."""
        with pytest.raises(ParseError, match="REPEAT must follow"):
            parse("FUNCTION foo()\nRESET\nEND_FUNCTION\nREPEAT 3\n")

    def test_if_without_condition(self) -> None:
        """IF THEN without condition should fail."""
        with pytest.raises(ParseError):
            parse("IF THEN\nRESET\nEND_IF\n")

    def test_var_without_name(self) -> None:
        """VAR without $identifier should fail."""
        with pytest.raises(ParseError, match="Expected \\$identifier"):
            parse("VAR\n")

    def test_nested_block_mismatch(self) -> None:
        """END_WHILE inside IF block (mismatched closer) should fail."""
        with pytest.raises(ParseError, match="Unexpected END_WHILE"):
            parse("IF 1 THEN\nEND_WHILE\nEND_IF\n")

    def test_statement_after_repeat(self) -> None:
        """Statement after REPEAT should be valid (REPEAT applies to preceding)."""
        script = parse("DELAY 100\nREPEAT 3\nRESET\n")
        assert len(script.statements) == 3

    def test_hold_with_modifier_key_requires_inject_mod(self) -> None:
        """HOLD SHIFT without INJECT_MOD should fail."""
        with pytest.raises(ParseError, match="INJECT_MOD required"):
            parse("HOLD SHIFT\n")

    def test_release_with_modifier_key_without_inject_mod(self) -> None:
        """RELEASE SHIFT without INJECT_MOD should succeed (official Hak5 behavior)."""
        script = parse("RELEASE SHIFT\n")
        assert len(script.statements) == 1
        assert isinstance(script.statements[0], ReleaseStmt)
        assert script.statements[0].key == ModifierKey.SHIFT

    def test_hold_with_modifier_key_after_inject_mod(self) -> None:
        """INJECT_MOD then HOLD SHIFT should succeed."""
        script = parse("INJECT_MOD\nHOLD SHIFT\n")
        assert len(script.statements) == 2
        assert isinstance(script.statements[0], InjectModStmt)
        assert isinstance(script.statements[1], HoldStmt)
        assert script.statements[1].key == ModifierKey.SHIFT

    def test_release_with_modifier_key_after_inject_mod(self) -> None:
        """INJECT_MOD then RELEASE SHIFT should succeed."""
        script = parse("INJECT_MOD\nRELEASE SHIFT\n")
        assert len(script.statements) == 2
        assert isinstance(script.statements[0], InjectModStmt)
        assert isinstance(script.statements[1], ReleaseStmt)
        assert script.statements[1].key == ModifierKey.SHIFT

    def test_full_hold_release_sequence_no_inject_mod_before_release(self) -> None:
        """Full sequence: INJECT_MOD / HOLD SHIFT / RELEASE SHIFT (no INJECT_MOD before RELEASE)."""
        script = parse("INJECT_MOD\nHOLD SHIFT\nRELEASE SHIFT\n")
        assert len(script.statements) == 3
        assert isinstance(script.statements[0], InjectModStmt)
        assert isinstance(script.statements[1], HoldStmt)
        assert script.statements[1].key == ModifierKey.SHIFT
        assert isinstance(script.statements[2], ReleaseStmt)
        assert script.statements[2].key == ModifierKey.SHIFT

    def test_full_hold_release_sequence_with_delay(self) -> None:
        """Full sequence with delay: INJECT_MOD / HOLD CONTROL / DELAY 100 / RELEASE CONTROL."""
        script = parse("INJECT_MOD\nHOLD CONTROL\nDELAY 100\nRELEASE CONTROL\n")
        assert len(script.statements) == 4
        assert isinstance(script.statements[0], InjectModStmt)
        assert isinstance(script.statements[1], HoldStmt)
        assert script.statements[1].key == ModifierKey.CONTROL
        assert isinstance(script.statements[2], DelayStmt)
        assert isinstance(script.statements[3], ReleaseStmt)
        assert script.statements[3].key == ModifierKey.CONTROL

    def test_hold_multiple_modifiers(self) -> None:
        """HOLD with various modifier keys after INJECT_MOD."""
        for mod_name in ("CONTROL", "SHIFT", "ALT", "GUI", "WINDOWS", "COMMAND", "OPTION"):
            script = parse(f"INJECT_MOD\nHOLD {mod_name}\n")
            assert isinstance(script.statements[1], HoldStmt)


# ── Additional full-program tests ─────────────────────────────────────────


class TestFullProgramEdgeCases:
    """Additional multi-statement program edge cases."""

    def test_comments_only_program(self) -> None:
        """Program with only REM lines and blank lines."""
        script = parse("REM this is a comment\n\n// another comment\n\n")
        assert len(script.statements) == 0

    def test_defines_only(self) -> None:
        """Program with only DEFINE statements produces empty script after preprocessing."""
        from ducky.lexer import DuckyLexer
        from ducky.preprocessor import Preprocessor

        source = "DEFINE #DELAY 1000\nDEFINE #TEXT Hello\n"
        preprocessed = Preprocessor().preprocess(source)
        tokens = DuckyLexer().tokenize(preprocessed)
        script = DuckyParser(tokens).parse()
        assert len(script.statements) == 0

    def test_nested_if_while_compound(self) -> None:
        """Deeply nested IF inside WHILE inside IF."""
        source = (
            "IF 1 THEN\n"
            "  WHILE $x\n"
            "    IF 2 THEN\n"
            "      BREAK\n"
            "    END_IF\n"
            "    CONTINUE\n"
            "  END_WHILE\n"
            "ELSE\n"
            "  RESET\n"
            "END_IF\n"
        )
        script = parse(source)
        assert len(script.statements) == 1
        outer_if = script.statements[0]
        assert isinstance(outer_if, IfStmt)
        # WHILE is in the IF body
        wh = outer_if.body[0]
        assert isinstance(wh, WhileStmt)
        # Inner IF is in the WHILE body
        inner_if = wh.body[0]
        assert isinstance(inner_if, IfStmt)
        assert isinstance(inner_if.body[0], BreakStmt)

    def test_function_with_return_call_chain(self) -> None:
        """Function that calls another function."""
        source = (
            "FUNCTION inner()\n"
            "RETURN 42\n"
            "END_FUNCTION\n"
            "FUNCTION outer()\n"
            "VAR $x\n"
            "$x = inner()\n"
            "RETURN $x\n"
            "END_FUNCTION\n"
            "outer()\n"
        )
        script = parse(source)
        assert len(script.statements) == 3
        assert isinstance(script.statements[0], FunctionDef)
        assert script.statements[0].name == "inner"
        assert isinstance(script.statements[1], FunctionDef)
        assert script.statements[1].name == "outer"
        assert isinstance(script.statements[2], CallStmt)
        assert script.statements[2].name == "outer"

    def test_crlf_line_endings(self) -> None:
        """Program with CRLF line endings parses the same as LF."""
        script = parse("DELAY 1000\r\nENTER\r\nSTRING hello\r\n")
        assert len(script.statements) == 3
        assert isinstance(script.statements[0], DelayStmt)
        assert isinstance(script.statements[1], KeyStmt)
        assert isinstance(script.statements[2], StringStmt)


# ── NodeVisitor edge cases ───────────────────────────────────────────────


class TestNodeVisitorEdgeCases:
    """Additional NodeVisitor functionality."""

    def test_visitor_returns_values(self) -> None:
        """Visitor methods can return values that propagate."""
        class ReturnVisitor(NodeVisitor):
            def visit_IntegerExpr(self, node):  # noqa: N802
                return node.value
        visitor = ReturnVisitor()
        result = visitor.visit(IntegerExpr(42))
        assert result == 42

    def test_visitor_child_traversal(self) -> None:
        """Subclass visits children manually via visit()."""
        class TraversalVisitor(NodeVisitor):
            def __init__(self):
                self.seen = []
            def visit_IntegerExpr(self, node):  # noqa: N802
                self.seen.append(node.value)
        visitor = TraversalVisitor()
        visitor.visit(IntegerExpr(1))
        visitor.visit(IntegerExpr(2))
        assert visitor.seen == [1, 2]

    def test_visitor_unknown_node(self) -> None:
        """Visit method for unknown node type raises NotImplementedError."""
        visitor = NodeVisitor()
        with pytest.raises(NotImplementedError):
            visitor.visit(42)  # not an AST node
