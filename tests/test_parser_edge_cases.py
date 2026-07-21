"""Edge-case tests for the DuckyScript 3 recursive-descent parser.

Covers three areas not explored in ``test_parser.py``:

1. **Parser error recovery (A1)** — first-error-only behavior, newline handling,
   incomplete statements, bad tokens.
2. **Expression precedence (A6)** — full precedence climbing through all levels
   via direct ``_parse_expression()`` access.
3. **FUNCTION/EXTENSION registration (A9)** — edge cases around definitions
   with missing names, rejected parameters, and invalid tokens.

All tests are self-contained and use the public pipeline
(DuckyLexer → DuckyParser) with no shared state.
"""

import pytest

from ducky.ast import (
    BinaryOp,
    DelayStmt,
    Expr,
    GroupExpr,
    IdentifierExpr,
    IntegerExpr,
    KeyStmt,
    Script,
    UnaryOp,
)
from ducky.lexer import DuckyLexer
from ducky.parser import DuckyParser, ParseError
from ducky.tokens import Operator

# ── Helpers ───────────────────────────────────────────────────────────────────


def _parse(source: str) -> Script:
    """Tokenize *source* and parse into an AST."""
    tokens = DuckyLexer().tokenize(source)
    return DuckyParser(tokens).parse()


def _parse_expr(source: str) -> Expr:
    """Tokenize *source* and parse the expression at position 0.

    This gives direct access to the parser's expression-precedence
    climber without wrapping in a statement.
    """
    tokens = DuckyLexer().tokenize(source)
    parser = DuckyParser(tokens)
    return parser._parse_expression()


# ═══════════════════════════════════════════════════════════════════════════════
# Section 1: Parser error recovery (A1)
# ═══════════════════════════════════════════════════════════════════════════════


class TestErrorRecovery:
    """The parser stops at the first error with ParseError — no recovery."""

    def test_single_bad_token_statement(self) -> None:
        """A single operator token as a statement raises ParseError."""
        with pytest.raises(ParseError, match="Unexpected token"):
            _parse("+\n")

    def test_logical_operator_as_statement(self) -> None:
        """Logical operator && as a statement raises ParseError."""
        with pytest.raises(ParseError, match="Unexpected token"):
            _parse("&&\n")

    def test_assign_as_statement(self) -> None:
        """Assignment = as a top-level statement raises ParseError."""
        with pytest.raises(ParseError, match="Unexpected token"):
            _parse("=\n")

    def test_bad_token_after_valid_statement(self) -> None:
        """A valid statement followed by an invalid one stops at the error."""
        with pytest.raises(ParseError, match="Unexpected token"):
            _parse("DELAY 100\n+\n")

    def test_bad_after_delay_expression(self) -> None:
        """Bad token after a complete DELAY expression stops at the error."""
        with pytest.raises(ParseError, match="Unexpected token"):
            _parse("DELAY 100\n||\n")

    def test_incomplete_if_missing_then(self) -> None:
        """IF without THEN raises ParseError."""
        with pytest.raises(ParseError, match="Expected THEN"):
            _parse("IF (1)\n")

    def test_incomplete_if_missing_rparen_then(self) -> None:
        """IF with unclosed paren raises ParseError."""
        with pytest.raises(ParseError, match="Expected '\\).*IF condition"):
            _parse("IF (1\nTHEN\nRESET\nEND_IF\n")

    def test_incomplete_function_no_rparen(self) -> None:
        """FUNCTION without closing paren raises ParseError."""
        with pytest.raises(ParseError, match="Expected '\\).*function params"):
            _parse("FUNCTION foo(\n")

    def test_incomplete_call_no_rparen(self) -> None:
        """Function-call statement without closing paren raises ParseError."""
        with pytest.raises(ParseError, match="Expected '\\).*"):
            _parse("foo(\n")

    def test_missing_newline_separator(self) -> None:
        """Two statements on one line without NEWLINE raises ParseError.

        After DELAY consumes its expression, _consume_newline sees ENTER
        (not NEWLINE) and raises.
        """
        with pytest.raises(ParseError, match="Expected NEWLINE after statement"):
            _parse("DELAY 100 ENTER\n")

    def test_missing_newline_after_key(self) -> None:
        """Action key followed by another token on the same line fails.

        SPACE consumes as a KeyStmt, then _consume_newline finds DELAY
        instead of NEWLINE.
        """
        with pytest.raises(ParseError, match="Expected NEWLINE after statement"):
            _parse("SPACE DELAY 100\n")

    def test_statement_after_block_end_no_separator(self) -> None:
        """No NEWLINE between END_IF and next statement raises ParseError.

        After consume of END_IF, _consume_newline sees ENTER instead of NEWLINE.
        """
        with pytest.raises(ParseError, match="Expected NEWLINE.*ENTER"):
            _parse("IF 1 THEN\nRESET\nEND_IF ENTER\n")

    def test_multiple_newlines_between_statements(self) -> None:
        """Multiple consecutive blank lines between statements are handled."""
        script = _parse("DELAY 100\n\n\nENTER\n")
        assert len(script.statements) == 2
        assert isinstance(script.statements[0], DelayStmt)
        assert isinstance(script.statements[1], KeyStmt)

    def test_leading_blank_lines(self) -> None:
        """Leading blank lines before the first statement are handled."""
        script = _parse("\n\nDELAY 50\n")
        assert len(script.statements) == 1
        assert isinstance(script.statements[0], DelayStmt)
        assert script.statements[0].milliseconds.value == 50

    def test_trailing_blank_lines(self) -> None:
        """Trailing blank lines after the last statement are handled."""
        script = _parse("DELAY 50\n\n\n")
        assert len(script.statements) == 1
        assert isinstance(script.statements[0], DelayStmt)

    def test_blank_lines_inside_if_body(self) -> None:
        """Blank lines between statements inside an IF block body are handled."""
        script = _parse(
            "IF 1 THEN\n"
            "\n"
            "DELAY 100\n"
            "\n"
            "DELAY 200\n"
            "END_IF\n"
        )
        assert len(script.statements) == 1
        if_stmt = script.statements[0]
        assert len(if_stmt.body) == 2
        assert isinstance(if_stmt.body[0], DelayStmt)
        assert isinstance(if_stmt.body[1], DelayStmt)

    def test_blank_lines_inside_while_body(self) -> None:
        """Blank lines between statements inside a WHILE block body are handled."""
        script = _parse(
            "WHILE 1\n"
            "DELAY 50\n"
            "\n"
            "DELAY 100\n"
            "END_WHILE\n"
        )
        assert len(script.statements) == 1
        while_stmt = script.statements[0]
        assert len(while_stmt.body) == 2
        assert isinstance(while_stmt.body[0], DelayStmt)
        assert isinstance(while_stmt.body[1], DelayStmt)

    def test_expression_with_leading_operator_error(self) -> None:
        """Lone binary operator in expression context raises ParseError."""
        with pytest.raises(ParseError, match="Unexpected token in expression"):
            _parse("DELAY +\n")

    def test_expression_with_trailing_operator_error(self) -> None:
        """Trailing binary operator with no RHS raises ParseError."""
        with pytest.raises(ParseError, match="Unexpected token in expression"):
            _parse("DELAY 1 +\n")


# ═══════════════════════════════════════════════════════════════════════════════
# Section 2: Expression precedence (A6)
# ═══════════════════════════════════════════════════════════════════════════════


class TestExpressionPrecedence:
    """Expression parsing produces correct AST structure per spec §4.1."""

    # ── Multiplicative vs Additive ─────────────────────────────────────────

    def test_mul_binds_tighter_than_add(self) -> None:
        """1 + 2 * 3 → +(1, *(2, 3)).

        Multiplication binds tighter than addition.
        """
        expr = _parse_expr("1 + 2 * 3")
        assert isinstance(expr, BinaryOp)
        assert expr.operator == Operator.ADD
        assert isinstance(expr.left, IntegerExpr)
        assert expr.left.value == 1
        assert isinstance(expr.right, BinaryOp)
        assert expr.right.operator == Operator.MULTIPLY
        assert expr.right.left.value == 2
        assert expr.right.right.value == 3

    def test_add_before_mul_different_order(self) -> None:
        """2 * 3 + 1 → +(*(2, 3), 1)."""
        expr = _parse_expr("2 * 3 + 1")
        assert isinstance(expr, BinaryOp)
        assert expr.operator == Operator.ADD
        assert isinstance(expr.left, BinaryOp)
        assert expr.left.operator == Operator.MULTIPLY
        assert expr.left.left.value == 2
        assert expr.left.right.value == 3
        assert isinstance(expr.right, IntegerExpr)
        assert expr.right.value == 1

    def test_additive_left_associative(self) -> None:
        """1 + 2 + 3 → +(+[1, 2], 3)."""
        expr = _parse_expr("1 + 2 + 3")
        assert isinstance(expr, BinaryOp)
        assert expr.operator == Operator.ADD
        assert isinstance(expr.left, BinaryOp)
        assert expr.left.operator == Operator.ADD
        assert expr.left.left.value == 1
        assert expr.left.right.value == 2
        assert expr.right.value == 3

    def test_multiplicative_left_associative(self) -> None:
        """4 / 2 % 3 → %(/(4, 2), 3)."""
        expr = _parse_expr("4 / 2 % 3")
        assert isinstance(expr, BinaryOp)
        assert expr.operator == Operator.MODULO
        assert isinstance(expr.left, BinaryOp)
        assert expr.left.operator == Operator.DIVIDE
        assert expr.left.left.value == 4
        assert expr.left.right.value == 2
        assert expr.right.value == 3

    # ── Exponentiation (^ at multiplicative level) ─────────────────────────

    def test_power_binds_tighter_than_add_left(self) -> None:
        """1 ^ 2 + 3 → +(^(1, 2), 3).

        Exponentiation is at the multiplicative level (11), which binds
        tighter than additive (10). So 1 ^ 2 + 3 = (1 ^ 2) + 3.
        """
        expr = _parse_expr("1 ^ 2 + 3")
        assert isinstance(expr, BinaryOp)
        assert expr.operator == Operator.ADD
        assert isinstance(expr.left, BinaryOp)
        assert expr.left.operator == Operator.POWER
        assert expr.left.left.value == 1
        assert expr.left.right.value == 2
        assert expr.right.value == 3

    def test_power_binds_tighter_than_add_right(self) -> None:
        """1 + 2 ^ 3 → +(1, ^(2, 3))."""
        expr = _parse_expr("1 + 2 ^ 3")
        assert isinstance(expr, BinaryOp)
        assert expr.operator == Operator.ADD
        assert expr.left.value == 1
        assert isinstance(expr.right, BinaryOp)
        assert expr.right.operator == Operator.POWER
        assert expr.right.left.value == 2
        assert expr.right.right.value == 3

    def test_power_at_mul_level(self) -> None:
        """1 * 2 ^ 3 → *(1, ^(2, 3)).

        ^ is at the multiplicative level, same as *, so left-to-right:
        1 * 2 ^ 3 = (1 * 2) ^ 3 per spec §4.1 (left-associative at same level).
        """
        expr = _parse_expr("1 * 2 ^ 3")
        assert isinstance(expr, BinaryOp)
        assert expr.operator == Operator.POWER
        assert isinstance(expr.left, BinaryOp)
        assert expr.left.operator == Operator.MULTIPLY
        assert expr.left.left.value == 1
        assert expr.left.right.value == 2
        assert expr.right.value == 3

    # ── Grouping / parentheses ─────────────────────────────────────────────

    def test_parens_override_precedence(self) -> None:
        """(1 + 2) * 3 → *(group(+(1, 2)), 3)."""
        expr = _parse_expr("(1 + 2) * 3")
        assert isinstance(expr, BinaryOp)
        assert expr.operator == Operator.MULTIPLY
        assert isinstance(expr.left, GroupExpr)
        inner = expr.left.expression
        assert isinstance(inner, BinaryOp)
        assert inner.operator == Operator.ADD
        assert inner.left.value == 1
        assert inner.right.value == 2
        assert expr.right.value == 3

    def test_nested_parens(self) -> None:
        """((1 + 2)) * 3 → group(group(+(1, 2)))."""
        expr = _parse_expr("((1 + 2)) * 3")
        assert isinstance(expr, BinaryOp)
        assert expr.operator == Operator.MULTIPLY
        outer_group = expr.left
        assert isinstance(outer_group, GroupExpr)
        inner_group = outer_group.expression
        assert isinstance(inner_group, GroupExpr)
        assert isinstance(inner_group.expression, BinaryOp)
        assert inner_group.expression.operator == Operator.ADD

    # ── Unary operators ────────────────────────────────────────────────────

    def test_unary_minus_with_addition(self) -> None:
        """-1 + 2 → +(-(1), 2).

        Unary minus binds tighter than binary plus.
        """
        expr = _parse_expr("-1 + 2")
        assert isinstance(expr, BinaryOp)
        assert expr.operator == Operator.ADD
        assert isinstance(expr.left, UnaryOp)
        assert expr.left.operator == Operator.SUBTRACT
        assert expr.left.operand.value == 1
        assert expr.right.value == 2

    def test_unary_not(self) -> None:
        """!1 → !(1)."""
        expr = _parse_expr("!1")
        assert isinstance(expr, UnaryOp)
        assert expr.operator == Operator.NOT
        assert expr.operand.value == 1

    def test_double_unary_not(self) -> None:
        """!!1 → !(!(1))."""
        expr = _parse_expr("!!1")
        assert isinstance(expr, UnaryOp)
        assert expr.operator == Operator.NOT
        assert isinstance(expr.operand, UnaryOp)
        assert expr.operand.operator == Operator.NOT
        assert expr.operand.operand.value == 1

    def test_unary_not_then_minus(self) -> None:
        """!-1 → !(-(1))."""
        expr = _parse_expr("!-1")
        assert isinstance(expr, UnaryOp)
        assert expr.operator == Operator.NOT
        assert isinstance(expr.operand, UnaryOp)
        assert expr.operand.operator == Operator.SUBTRACT
        assert expr.operand.operand.value == 1

    # ── Logical operators ──────────────────────────────────────────────────

    def test_logical_and_before_or(self) -> None:
        """1 && 2 || 3 → ||(&&(1, 2), 3).

        AND binds tighter than OR.
        """
        expr = _parse_expr("1 && 2 || 3")
        assert isinstance(expr, BinaryOp)
        assert expr.operator == Operator.LOGICAL_OR
        assert isinstance(expr.left, BinaryOp)
        assert expr.left.operator == Operator.LOGICAL_AND
        assert expr.left.left.value == 1
        assert expr.left.right.value == 2
        assert expr.right.value == 3

    def test_logical_or_left_assoc(self) -> None:
        """1 || 2 || 3 → ||(||(1, 2), 3)."""
        expr = _parse_expr("1 || 2 || 3")
        assert isinstance(expr, BinaryOp)
        assert expr.operator == Operator.LOGICAL_OR
        assert isinstance(expr.left, BinaryOp)
        assert expr.left.operator == Operator.LOGICAL_OR
        assert expr.left.left.value == 1
        assert expr.left.right.value == 2
        assert expr.right.value == 3

    # ── Bitwise operators ──────────────────────────────────────────────────

    def test_bitwise_or_before_and(self) -> None:
        """1 & 2 | 3 → |(&(1, 2), 3).

        AND binds tighter than OR (for bitwise too).
        """
        expr = _parse_expr("1 & 2 | 3")
        assert isinstance(expr, BinaryOp)
        assert expr.operator == Operator.BITWISE_OR
        assert isinstance(expr.left, BinaryOp)
        assert expr.left.operator == Operator.BITWISE_AND
        assert expr.left.left.value == 1
        assert expr.left.right.value == 2
        assert expr.right.value == 3

    # ── Relational + equality chains ───────────────────────────────────────

    def test_chain_less_than_greater(self) -> None:
        """1 < 2 > 3 → >(<(1, 2), 3)."""
        expr = _parse_expr("1 < 2 > 3")
        assert isinstance(expr, BinaryOp)
        assert expr.operator == Operator.GREATER
        assert isinstance(expr.left, BinaryOp)
        assert expr.left.operator == Operator.LESS
        assert expr.left.left.value == 1
        assert expr.left.right.value == 2
        assert expr.right.value == 3

    def test_chain_relational_equality_mixed(self) -> None:
        """1 < 2 == 3 > 4 → ==(<(1, 2), >(3, 4)).

        Relational (<, >) binds tighter than equality (==).
        """
        expr = _parse_expr("1 < 2 == 3 > 4")
        assert isinstance(expr, BinaryOp)
        assert expr.operator == Operator.EQUAL
        assert isinstance(expr.left, BinaryOp)
        assert expr.left.operator == Operator.LESS
        assert expr.left.left.value == 1
        assert expr.left.right.value == 2
        assert isinstance(expr.right, BinaryOp)
        assert expr.right.operator == Operator.GREATER
        assert expr.right.left.value == 3
        assert expr.right.right.value == 4

    def test_chain_equals_not_equals(self) -> None:
        """1 == 2 != 3 → !=(==(1, 2), 3)."""
        expr = _parse_expr("1 == 2 != 3")
        assert isinstance(expr, BinaryOp)
        assert expr.operator == Operator.NOT_EQUAL
        assert isinstance(expr.left, BinaryOp)
        assert expr.left.operator == Operator.EQUAL
        assert expr.left.left.value == 1
        assert expr.left.right.value == 2
        assert expr.right.value == 3

    # ── Shift operators ────────────────────────────────────────────────────

    def test_shift_before_additive(self) -> None:
        """1 << 2 + 3 → <<(1, +(2, 3)).

        Additive binds tighter than shift.
        """
        expr = _parse_expr("1 << 2 + 3")
        assert isinstance(expr, BinaryOp)
        assert expr.operator == Operator.SHIFT_LEFT
        assert expr.left.value == 1
        assert isinstance(expr.right, BinaryOp)
        assert expr.right.operator == Operator.ADD
        assert expr.right.left.value == 2
        assert expr.right.right.value == 3

    def test_shift_left_assoc(self) -> None:
        """1 << 2 >> 3 → >>(<<(1, 2), 3)."""
        expr = _parse_expr("1 << 2 >> 3")
        assert isinstance(expr, BinaryOp)
        assert expr.operator == Operator.SHIFT_RIGHT
        assert isinstance(expr.left, BinaryOp)
        assert expr.left.operator == Operator.SHIFT_LEFT
        assert expr.left.left.value == 1
        assert expr.left.right.value == 2
        assert expr.right.value == 3


# ═══════════════════════════════════════════════════════════════════════════════
# Section 3: FUNCTION / EXTENSION edge cases (A9)
# ═══════════════════════════════════════════════════════════════════════════════


class TestFunctionExtensionEdgeCases:
    """Edge cases around function and extension definitions."""

    def test_function_with_params_rejected(self) -> None:
        """FUNCTION with parameters (a, b) raises ParseError (zero params per spec)."""
        with pytest.raises(ParseError, match="Expected '\\).*function params"):
            _parse("FUNCTION foo(a, b)\nEND_FUNCTION\n")

    def test_function_without_identifier(self) -> None:
        """FUNCTION followed by ( ) without a name raises ParseError."""
        with pytest.raises(ParseError, match="Expected function name"):
            _parse("FUNCTION ()\nEND_FUNCTION\n")

    def test_function_no_name(self) -> None:
        """FUNCTION on its own without a name raises ParseError."""
        with pytest.raises(ParseError, match="Expected function name"):
            _parse("FUNCTION\n")

    def test_function_no_body(self) -> None:
        """FUNCTION with only name and empty parens but without END_FUNCTION raises error."""
        with pytest.raises(ParseError, match="Expected END_FUNCTION"):
            _parse("FUNCTION foo()\n")

    def test_function_no_newline_after_parens(self) -> None:
        """Missing newline after FUNCTION foo() header raises ParseError."""
        with pytest.raises(ParseError, match="Expected NEWLINE"):
            _parse("FUNCTION foo() RESET\nEND_FUNCTION\n")

    def test_function_body_ends_with_wrong_closer(self) -> None:
        """FUNCTION body closed with END_IF instead of END_FUNCTION raises error.

        _parse_statement catches END_IF as an unexpected block-end keyword
        before _parse_statements_until ever gets to check for END_FUNCTION.
        """
        with pytest.raises(ParseError, match="Unexpected END_IF"):
            _parse("FUNCTION foo()\nDELAY 100\nEND_IF\n")

    def test_extension_without_name(self) -> None:
        """EXTENSION without a name raises ParseError."""
        with pytest.raises(ParseError, match="Expected extension name"):
            _parse("EXTENSION\n")

    def test_extension_no_end(self) -> None:
        """EXTENSION without END_EXTENSION raises ParseError."""
        with pytest.raises(ParseError, match="Expected END_EXTENSION"):
            _parse("EXTENSION myext\nDELAY 100\n")

    def test_nested_function_parses(self) -> None:
        """Nested FUNCTION definitions parse (inner function becomes body of outer).

        The parser's _parse_statements_until correctly stops at each
        END_FUNCTION via its stop-token set, allowing nested definitions.
        """
        script = _parse(
            "FUNCTION outer()\n"
            "FUNCTION inner()\n"
            "END_FUNCTION\n"
            "END_FUNCTION\n"
        )
        assert len(script.statements) == 1
        outer = script.statements[0]
        assert outer.name == "outer"
        assert len(outer.body) == 1
        inner = outer.body[0]
        assert inner.name == "inner"
        assert len(inner.body) == 0

    def test_function_inside_extension(self) -> None:
        """A FUNCTION inside an EXTENSION block parses (no nesting restriction)."""
        script = _parse(
            "EXTENSION myext\n"
            "FUNCTION helper()\n"
            "RETURN 1\n"
            "END_FUNCTION\n"
            "END_EXTENSION\n"
        )
        assert len(script.statements) == 1
        ext = script.statements[0]
        assert ext.name == "myext"
        assert len(ext.body) == 1
        assert ext.body[0].name == "helper"


# ═══════════════════════════════════════════════════════════════════════════════
# Section 4: Assorted field-verified edge cases
# ═══════════════════════════════════════════════════════════════════════════════


class TestMiscEdgeCases:
    """Additional tests covering discovered edge cases in the wild."""

    def test_comment_only_lines_with_blank_lines(self) -> None:
        """REM comments, // comments, and blank lines all yield zero statements."""
        script = _parse(
            "// line comment\n"
            "\n"
            "REM block style\n"
            "\n"
        )
        assert len(script.statements) == 0

    def test_blank_line_before_block_end(self) -> None:
        """Blank line immediately before END_IF raises ParseError.

        _parse_statement treats block-end keywords as unexpected tokens,
        so a NEWLINE before END_IF causes the while loop in
        _parse_statements_until to enter _parse_statement, which then
        sees END_IF and errors.
        """
        with pytest.raises(ParseError, match="Unexpected END_IF"):
            _parse(
                "IF 1 THEN\n"
                "DELAY 10\n"
                "\n"
                "END_IF\n"
            )

    def test_delay_with_zero_expr(self) -> None:
        """DELAY 0 is a valid expression (parseable, not an error)."""
        script = _parse("DELAY 0\n")
        assert isinstance(script.statements[0], DelayStmt)
        assert script.statements[0].milliseconds.value == 0

    def test_delay_with_negative_expr(self) -> None:
        """DELAY -5 parses as delay of unary minus expression."""
        script = _parse("DELAY -5\n")
        assert isinstance(script.statements[0], DelayStmt)
        assert isinstance(script.statements[0].milliseconds, UnaryOp)

    def test_expression_identifier_not_followed_by_paren(self) -> None:
        """A bare identifier in expression context becomes IdentifierExpr."""
        tokens = DuckyLexer().tokenize("myFunc")
        parser = DuckyParser(tokens)
        expr = parser._parse_expression()
        assert isinstance(expr, IdentifierExpr)
        assert expr.name == "myFunc"
