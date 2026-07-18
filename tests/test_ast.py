"""Tests for AST node definitions.

Verifies that every node type can be instantiated with valid data, that
the frozen-dataclass immutability contract is enforced, and that import
hygiene is maintained.
"""

import ast
import sys
from dataclasses import FrozenInstanceError

import pytest

from ducky.ast import (
    AssignStmt,
    AttackModeStmt,
    BinaryOp,
    ButtonDefStmt,
    ComboStmt,
    DefaultCharDelayStmt,
    DefaultDelayStmt,
    DefineStmt,
    DelayStmt,
    DisableButtonStmt,
    DollarIdentifierExpr,
    EnableButtonStmt,
    ExtensionStmt,
    FunctionDef,
    GroupExpr,
    HashIdentifierExpr,
    HidePayloadStmt,
    HoldStmt,
    IdentifierExpr,
    IfStmt,
    InjectModStmt,
    IntegerExpr,
    KeyStmt,
    LedState,
    LedStmt,
    LockKeyState,
    LockKeyType,
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
from ducky.tokens import ActionKey, ModifierKey, Operator

# ── Statement nodes ─────────────────────────────────────────────────


class TestStmtNodes:
    """One test per statement node type."""

    def test_script(self) -> None:
        node = Script(statements=())
        assert node.statements == ()

    def test_if_stmt(self) -> None:
        node = IfStmt(condition=IntegerExpr(1), body=(ResetStmt(),))
        assert isinstance(node.condition, IntegerExpr)
        assert node.condition.value == 1
        assert len(node.body) == 1
        assert isinstance(node.body[0], ResetStmt)
        assert node.else_body is None

    def test_if_else_stmt(self) -> None:
        node = IfStmt(
            condition=IntegerExpr(1),
            body=(ResetStmt(),),
            else_body=(StopPayloadStmt(),),
        )
        assert len(node.else_body) == 1
        assert isinstance(node.else_body[0], StopPayloadStmt)

    def test_while_stmt(self) -> None:
        node = WhileStmt(condition=IntegerExpr(1), body=(ResetStmt(),))
        assert isinstance(node.condition, IntegerExpr)
        assert node.condition.value == 1
        assert len(node.body) == 1

    def test_repeat_stmt(self) -> None:
        node = RepeatStmt(count=IntegerExpr(5))
        assert isinstance(node.count, IntegerExpr)
        assert node.count.value == 5

    def test_var_def(self) -> None:
        node = VarDef(name="x", initializer=IntegerExpr(1))
        assert node.name == "x"
        assert isinstance(node.initializer, IntegerExpr)

    def test_assign_stmt(self) -> None:
        node = AssignStmt(name="x", value=IntegerExpr(1))
        assert node.name == "x"
        assert node.value.value == 1

    def test_key_stmt(self) -> None:
        node = KeyStmt(key=ActionKey.ENTER)
        assert node.key == ActionKey.ENTER

    def test_string_stmt(self) -> None:
        node = StringStmt(text="hello")
        assert node.text == "hello"

    def test_string_ln_stmt(self) -> None:
        node = StringLnStmt(text="world")
        assert node.text == "world"

    def test_inject_mod_stmt(self) -> None:
        node = InjectModStmt()
        assert isinstance(node, InjectModStmt)

    def test_hold_stmt(self) -> None:
        node = HoldStmt(key=ActionKey.SPACE)
        assert node.key == ActionKey.SPACE

    def test_release_stmt(self) -> None:
        node = ReleaseStmt(key=ActionKey.TAB)
        assert node.key == ActionKey.TAB

    def test_delay_stmt(self) -> None:
        node = DelayStmt(milliseconds=1000)
        assert node.milliseconds == 1000

    def test_default_delay_stmt(self) -> None:
        node = DefaultDelayStmt(delay=IntegerExpr(200))
        assert isinstance(node.delay, IntegerExpr)
        assert node.delay.value == 200

    def test_default_char_delay_stmt(self) -> None:
        node = DefaultCharDelayStmt(delay=IntegerExpr(50))
        assert node.delay.value == 50

    def test_attack_mode_stmt(self) -> None:
        node = AttackModeStmt(params=("STORAGE", "HID"))
        assert node.params == ("STORAGE", "HID")

    def test_save_attack_mode_stmt(self) -> None:
        node = SaveAttackModeStmt()
        assert isinstance(node, SaveAttackModeStmt)

    def test_restore_attack_mode_stmt(self) -> None:
        node = RestoreAttackModeStmt()
        assert isinstance(node, RestoreAttackModeStmt)

    def test_return_stmt(self) -> None:
        node = ReturnStmt(value=IntegerExpr(42))
        assert node.value is not None
        assert node.value.value == 42

    def test_return_stmt_none(self) -> None:
        node = ReturnStmt()
        assert node.value is None

    def test_reset_stmt(self) -> None:
        node = ResetStmt()
        assert isinstance(node, ResetStmt)

    def test_restart_payload_stmt(self) -> None:
        node = RestartPayloadStmt()
        assert isinstance(node, RestartPayloadStmt)

    def test_stop_payload_stmt(self) -> None:
        node = StopPayloadStmt()
        assert isinstance(node, StopPayloadStmt)

    def test_random_stmt(self) -> None:
        node = RandomStmt(random_type=RandomType.CHAR)
        assert node.random_type == RandomType.CHAR

    def test_led_stmt(self) -> None:
        node = LedStmt(state=LedState.G)
        assert node.state == LedState.G

    def test_button_def_stmt(self) -> None:
        node = ButtonDefStmt(name="btn1", body=(ResetStmt(),))
        assert node.name == "btn1"
        assert len(node.body) == 1

    def test_wait_for_button_press_stmt(self) -> None:
        node = WaitForButtonPressStmt()
        assert isinstance(node, WaitForButtonPressStmt)

    def test_disable_button_stmt(self) -> None:
        node = DisableButtonStmt()
        assert isinstance(node, DisableButtonStmt)

    def test_enable_button_stmt(self) -> None:
        node = EnableButtonStmt()
        assert isinstance(node, EnableButtonStmt)

    def test_wait_for_key_stmt(self) -> None:
        node = WaitForKeyStmt(lock_key=LockKeyType.CAPS, state=LockKeyState.ON)
        assert node.lock_key == LockKeyType.CAPS
        assert node.state == LockKeyState.ON

    def test_save_host_lock_state_stmt(self) -> None:
        node = SaveHostLockStateStmt()
        assert isinstance(node, SaveHostLockStateStmt)

    def test_restore_host_lock_state_stmt(self) -> None:
        node = RestoreHostLockStateStmt()
        assert isinstance(node, RestoreHostLockStateStmt)

    def test_hide_payload_stmt(self) -> None:
        node = HidePayloadStmt()
        assert isinstance(node, HidePayloadStmt)

    def test_restore_payload_stmt(self) -> None:
        node = RestorePayloadStmt()
        assert isinstance(node, RestorePayloadStmt)

    def test_combo_stmt(self) -> None:
        node = ComboStmt(modifiers=(ModifierKey.CTRL,), key=ActionKey.ENTER)
        assert node.modifiers == (ModifierKey.CTRL,)
        assert node.key == ActionKey.ENTER

    def test_combo_stmt_no_modifiers(self) -> None:
        node = ComboStmt(modifiers=(), key=ActionKey.ENTER)
        assert node.modifiers == ()
        assert node.key == ActionKey.ENTER

    def test_function_def(self) -> None:
        node = FunctionDef(name="test", params=("x",), body=(ResetStmt(),))
        assert node.name == "test"
        assert node.params == ("x",)
        assert len(node.body) == 1

    def test_extension_stmt(self) -> None:
        node = ExtensionStmt(name="ext", body=(ResetStmt(),))
        assert node.name == "ext"
        assert len(node.body) == 1

    def test_define_stmt(self) -> None:
        node = DefineStmt(name="NAME", value="value")
        assert node.name == "NAME"
        assert node.value == "value"


# ── Expression nodes ────────────────────────────────────────────────


class TestExprNodes:
    """One test per expression node type."""

    def test_integer_expr(self) -> None:
        node = IntegerExpr(42)
        assert node.value == 42

    def test_string_expr(self) -> None:
        node = StringExpr("hello")
        assert node.value == "hello"

    def test_identifier_expr(self) -> None:
        node = IdentifierExpr("foo")
        assert node.name == "foo"

    def test_dollar_identifier_expr(self) -> None:
        node = DollarIdentifierExpr("x")
        assert node.name == "x"

    def test_hash_identifier_expr(self) -> None:
        node = HashIdentifierExpr("NAME")
        assert node.name == "NAME"

    def test_binary_op(self) -> None:
        node = BinaryOp(IntegerExpr(1), Operator.ADD, IntegerExpr(2))
        assert node.left.value == 1
        assert node.operator == Operator.ADD
        assert node.right.value == 2

    def test_unary_op(self) -> None:
        node = UnaryOp(Operator.NOT, IntegerExpr(1))
        assert node.operator == Operator.NOT
        assert node.operand.value == 1

    def test_group_expr(self) -> None:
        node = GroupExpr(IntegerExpr(1))
        assert node.expression.value == 1


# ── AST enums ───────────────────────────────────────────────────────


class TestAstEnums:
    """Verify enum uniqueness and member presence."""

    def test_random_type_values_unique(self) -> None:
        values = [m.value for m in RandomType]
        assert len(values) == len(set(values))

    def test_random_type_members(self) -> None:
        expected = {
            "CHAR",
            "LOWERCASE_LETTER",
            "UPPERCASE_LETTER",
            "LETTER",
            "NUMBER",
            "SPECIAL",
        }
        assert {m.name for m in RandomType} == expected

    def test_led_state_values_unique(self) -> None:
        values = [m.value for m in LedState]
        assert len(values) == len(set(values))

    def test_led_state_members(self) -> None:
        expected = {"OFF", "R", "G", "B"}
        assert {m.name for m in LedState} == expected

    def test_lock_key_type_values_unique(self) -> None:
        values = [m.value for m in LockKeyType]
        assert len(values) == len(set(values))

    def test_lock_key_type_members(self) -> None:
        expected = {"CAPS", "NUM", "SCROLL"}
        assert {m.name for m in LockKeyType} == expected

    def test_lock_key_state_values_unique(self) -> None:
        values = [m.value for m in LockKeyState]
        assert len(values) == len(set(values))

    def test_lock_key_state_members(self) -> None:
        expected = {"ON", "OFF", "CHANGE"}
        assert {m.name for m in LockKeyState} == expected


# ── Immutability ────────────────────────────────────────────────────


class TestImmutability:
    """Frozen dataclasses must reject attribute assignment."""

    def test_frozen_node(self) -> None:
        node = IntegerExpr(42)
        with pytest.raises(FrozenInstanceError):
            node.value = 99  # type: ignore[misc]

    def test_frozen_statement(self) -> None:
        node = ResetStmt()
        with pytest.raises(FrozenInstanceError):
            node.statements = ()  # type: ignore[misc]


# ── Import hygiene ──────────────────────────────────────────────────


class TestImportHygiene:
    """AST nodes must not import from outside allowed modules."""

    def test_no_external_imports(self) -> None:
        """Parse ``ducky.ast.nodes`` and verify only allowed imports."""
        import ducky.ast.nodes as nodes_mod

        source = sys.modules[nodes_mod.__name__].__loader__.get_source(
            nodes_mod.__name__
        )
        assert source is not None, "Could not read source of ducky.ast.nodes"

        tree = ast.parse(source)
        allowed_top_level = {"enum", "dataclasses", "__future__", "ducky"}

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    top = alias.name.split(".")[0]
                    assert (
                        top in allowed_top_level
                    ), f"Disallowed import in ducky.ast.nodes: {alias.name}"
            elif isinstance(node, ast.ImportFrom):
                if node.module is None:
                    continue
                # from X import Y → check top-level of X
                top = node.module.split(".")[0]
                # Relative imports are fine (e.g. from . import ...)
                # But we have no relative imports in this file.
                if top == "ducky":
                    sub = node.module[len("ducky") :]
                    # Only allow ducky.tokens
                    assert sub in (
                        ".tokens",
                        "",
                    ), f"Disallowed import from ducky submodule: {node.module}"
                else:
                    assert (
                        top in allowed_top_level
                    ), f"Disallowed import in ducky.ast.nodes: {node.module}"
