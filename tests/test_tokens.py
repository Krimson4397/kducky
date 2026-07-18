"""Tests for the DuckyScript 3 token definitions module.

Every enum member created in tokens.py should be documented and unique.
"""

import ast
import inspect

import pytest

from ducky.tokens import (
    ActionKey,
    ModifierKey,
    Operator,
    Token,
    TokenType,
)


class TestTokenType:
    """TokenType enum — every keyword, operator token, modifier,
    and action key from the spec has a member."""

    def test_values_are_unique(self) -> None:
        """All TokenType members must have unique auto() values."""
        values = [m.value for m in TokenType]
        assert len(values) == len(set(values)), (
            f"Expected {len(set(values))} unique values, got {len(values)}"
        )

    def test_control_flow_present(self) -> None:
        for name in ("IF", "THEN", "ELSE", "END_IF", "WHILE", "END_WHILE"):
            assert hasattr(TokenType, name), f"Missing control-flow token: {name}"

    def test_function_keywords_present(self) -> None:
        for name in ("FUNCTION", "END_FUNCTION", "RETURN"):
            assert hasattr(TokenType, name), f"Missing function token: {name}"

    def test_variable_keyword_present(self) -> None:
        assert hasattr(TokenType, "VAR")

    def test_preprocessor_keyword_present(self) -> None:
        assert hasattr(TokenType, "DEFINE")

    def test_comment_keywords_present(self) -> None:
        for name in ("REM", "REM_BLOCK", "END_REM"):
            assert hasattr(TokenType, name), f"Missing comment token: {name}"

    def test_payload_control_present(self) -> None:
        for name in ("REPEAT", "RESET", "RESTART_PAYLOAD", "STOP_PAYLOAD"):
            assert hasattr(TokenType, name), f"Missing payload-control token: {name}"

    def test_delay_keywords_present(self) -> None:
        for name in (
            "DELAY",
            "DEFAULTDELAY",
            "DEFAULT_DELAY",
            "DEFAULTCHARDELAY",
            "DEFAULT_CHAR_DELAY",
            "STRINGDELAY",
        ):
            assert hasattr(TokenType, name), f"Missing delay token: {name}"

    def test_keyboard_output_present(self) -> None:
        for name in ("STRING", "STRINGLN", "INJECT_MOD", "HOLD", "RELEASE"):
            assert hasattr(TokenType, name), f"Missing keyboard-output token: {name}"

    def test_attack_mode_present(self) -> None:
        for name in ("ATTACKMODE", "SAVE_ATTACKMODE", "RESTORE_ATTACKMODE"):
            assert hasattr(TokenType, name), f"Missing attack-mode token: {name}"

    def test_led_keywords_present(self) -> None:
        for name in ("LED_OFF", "LED_R", "LED_G", "LED_B"):
            assert hasattr(TokenType, name), f"Missing LED token: {name}"

    def test_button_keywords_present(self) -> None:
        for name in (
            "BUTTON_DEF",
            "END_BUTTON",
            "DISABLE_BUTTON",
            "ENABLE_BUTTON",
            "WAIT_FOR_BUTTON_PRESS",
        ):
            assert hasattr(TokenType, name), f"Missing button token: {name}"

    def test_lock_key_wait_present(self) -> None:
        for name in (
            "WAIT_FOR_CAPS_ON",
            "WAIT_FOR_CAPS_OFF",
            "WAIT_FOR_CAPS_CHANGE",
            "WAIT_FOR_NUM_ON",
            "WAIT_FOR_NUM_OFF",
            "WAIT_FOR_NUM_CHANGE",
            "WAIT_FOR_SCROLL_ON",
            "WAIT_FOR_SCROLL_OFF",
            "WAIT_FOR_SCROLL_CHANGE",
            "SAVE_HOST_KEYBOARD_LOCK_STATE",
            "RESTORE_HOST_KEYBOARD_LOCK_STATE",
        ):
            assert hasattr(TokenType, name), f"Missing lock-key-wait token: {name}"

    def test_random_keywords_present(self) -> None:
        for name in (
            "RANDOM_CHAR",
            "RANDOM_LOWERCASE_LETTER",
            "RANDOM_UPPERCASE_LETTER",
            "RANDOM_LETTER",
            "RANDOM_NUMBER",
            "RANDOM_SPECIAL",
        ):
            assert hasattr(TokenType, name), f"Missing random token: {name}"

    def test_file_keywords_present(self) -> None:
        for name in ("HIDE_PAYLOAD", "RESTORE_PAYLOAD"):
            assert hasattr(TokenType, name), f"Missing file token: {name}"

    def test_constant_keywords_present(self) -> None:
        for name in ("TRUE", "FALSE"):
            assert hasattr(TokenType, name), f"Missing constant token: {name}"

    def test_extension_keywords_present(self) -> None:
        for name in ("BREAK", "CONTINUE", "EXTENSION", "END_EXTENSION", "DUCKY_LANG"):
            assert hasattr(TokenType, name), f"Missing extension token: {name}"

    def test_operator_token_types_present(self) -> None:
        for name in (
            "PLUS",
            "MINUS",
            "STAR",
            "SLASH",
            "PERCENT",
            "CARET",
            "BANG",
            "AMPERSAND",
            "PIPE",
            "LT",
            "GT",
            "LE",
            "GE",
            "EQ",
            "NE",
            "LSHIFT",
            "RSHIFT",
            "AND",
            "OR",
            "ASSIGN",
        ):
            assert hasattr(TokenType, name), f"Missing operator token type: {name}"

    def test_punctuation_present(self) -> None:
        for name in ("LPAREN", "RPAREN", "COMMA"):
            assert hasattr(TokenType, name), f"Missing punctuation token: {name}"

    def test_literal_types_present(self) -> None:
        for name in ("INTEGER", "STRING_LITERAL"):
            assert hasattr(TokenType, name), f"Missing literal token: {name}"

    def test_identifier_types_present(self) -> None:
        for name in ("IDENTIFIER", "DOLLAR_IDENTIFIER", "HASH_IDENTIFIER"):
            assert hasattr(TokenType, name), f"Missing identifier token: {name}"

    def test_special_types_present(self) -> None:
        for name in ("NEWLINE", "EOF", "STRING_BODY", "ATTACKMODE_PARAM"):
            assert hasattr(TokenType, name), f"Missing special token: {name}"

    def test_modifier_key_tokens_present(self) -> None:
        for name in ("CONTROL", "CTRL", "SHIFT", "ALT", "GUI", "WINDOWS", "COMMAND", "OPTION"):
            assert hasattr(TokenType, name), f"Missing modifier-key token: {name}"

    def test_action_key_tokens_present(self) -> None:
        for name in (
            "ENTER",
            "RETURN_KEY",
            "SPACE",
            "TAB",
            "BACKSPACE",
            "DELETE",
            "DEL",
            "INSERT",
            "HOME",
            "END_KEY",
            "PAGEUP",
            "PAGEDOWN",
            "UP",
            "UPARROW",
            "DOWN",
            "DOWNARROW",
            "LEFT",
            "LEFTARROW",
            "RIGHT",
            "RIGHTARROW",
            "ESCAPE",
            "ESC",
            "PRINTSCREEN",
            "SCROLLLOCK",
            "PAUSE",
            "BREAK_KEY",
            "MENU",
            "APP",
            "CAPSLOCK",
            "NUMLOCK",
            "POWER",
            "F1",
            "F2",
            "F3",
            "F4",
            "F5",
            "F6",
            "F7",
            "F8",
            "F9",
            "F10",
            "F11",
            "F12",
            "KP_SLASH",
            "KP_ASTERISK",
            "KP_MINUS",
            "KP_PLUS",
            "KP_ENTER",
            "KP_0",
            "KP_1",
            "KP_2",
            "KP_3",
            "KP_4",
            "KP_5",
            "KP_6",
            "KP_7",
            "KP_8",
            "KP_9",
            "KP_DOT",
            "KP_EQUAL",
            "KP_COMMA",
            "KP_00",
            "KP_000",
            "KEY_102ND",
            "COMPOSE",
            "KPEQUAL",
            "PROPS",
            "UNDO",
            "PASTE",
        ):
            assert hasattr(TokenType, name), f"Missing action-key token: {name}"


class TestToken:
    """Token data class — instantiation and field access."""

    def test_instantiation(self) -> None:
        token = Token(type=TokenType.STRING, value="STRING", line=1, column=1)
        assert token.type is TokenType.STRING
        assert token.value == "STRING"
        assert token.line == 1
        assert token.column == 1

    def test_immutable(self) -> None:
        token = Token(type=TokenType.INTEGER, value="42", line=2, column=5)
        with pytest.raises(AttributeError):
            token.value = "43"  # type: ignore[misc]

    def test_position_tracking(self) -> None:
        token = Token(type=TokenType.DELAY, value="DELAY", line=10, column=3)
        assert token.line == 10
        assert token.column == 3


class TestOperator:
    """Operator enum — all spec operators are present with correct values."""

    def test_values_are_unique(self) -> None:
        values = [m.value for m in Operator]
        assert len(values) == len(set(values)), (
            f"Expected {len(set(values))} unique values, got {len(values)}"
        )

    def test_arithmetic(self) -> None:
        assert Operator.ADD.value == "+"
        assert Operator.SUBTRACT.value == "-"
        assert Operator.MULTIPLY.value == "*"
        assert Operator.DIVIDE.value == "/"
        assert Operator.MODULO.value == "%"
        assert Operator.POWER.value == "^"

    def test_unary(self) -> None:
        assert Operator.NOT.value == "!"

    def test_bitwise(self) -> None:
        assert Operator.BITWISE_AND.value == "&"
        assert Operator.BITWISE_OR.value == "|"

    def test_relational(self) -> None:
        assert Operator.LESS.value == "<"
        assert Operator.GREATER.value == ">"
        assert Operator.LESS_EQUAL.value == "<="
        assert Operator.GREATER_EQUAL.value == ">="

    def test_equality(self) -> None:
        assert Operator.EQUAL.value == "=="
        assert Operator.NOT_EQUAL.value == "!="

    def test_shift(self) -> None:
        assert Operator.SHIFT_LEFT.value == "<<"
        assert Operator.SHIFT_RIGHT.value == ">>"

    def test_logical(self) -> None:
        assert Operator.LOGICAL_AND.value == "&&"
        assert Operator.LOGICAL_OR.value == "||"

    def test_assignment(self) -> None:
        assert Operator.ASSIGN.value == "="


class TestModifierKey:
    """ModifierKey enum — all modifier names present."""

    def test_values_are_unique(self) -> None:
        values = [m.value for m in ModifierKey]
        assert len(values) == len(set(values))

    def test_all_modifiers_present(self) -> None:
        expected = {"CONTROL", "CTRL", "SHIFT", "ALT", "GUI", "WINDOWS", "COMMAND", "OPTION"}
        actual = {m.value for m in ModifierKey}
        assert actual == expected

    def test_case_sensitivity(self) -> None:
        assert ModifierKey.CONTROL.value == "CONTROL"
        assert ModifierKey.CTRL.value == "CTRL"


class TestActionKey:
    """ActionKey enum — all action keys present."""

    def test_values_are_unique(self) -> None:
        values = [m.value for m in ActionKey]
        assert len(values) == len(set(values))

    def test_navigation_present(self) -> None:
        for name in (
            "UP", "UPARROW", "DOWN", "DOWNARROW",
            "LEFT", "LEFTARROW", "RIGHT", "RIGHTARROW",
            "PAGEUP", "PAGEDOWN", "HOME", "END",
            "INSERT", "DELETE", "DEL",
        ):
            assert hasattr(ActionKey, name), f"Missing navigation key: {name}"

    def test_editing_present(self) -> None:
        for name in (
            "ENTER", "RETURN", "SPACE", "TAB", "BACKSPACE",
            "ESCAPE", "ESC", "PRINTSCREEN", "SCROLLLOCK",
            "PAUSE", "BREAK", "MENU", "APP",
            "CAPSLOCK", "NUMLOCK", "POWER",
        ):
            assert hasattr(ActionKey, name), f"Missing editing key: {name}"

    def test_function_keys_present(self) -> None:
        for i in range(1, 13):
            name = f"F{i}"
            assert hasattr(ActionKey, name), f"Missing function key: {name}"

    def test_numpad_present(self) -> None:
        for name in (
            "KP_SLASH", "KP_ASTERISK", "KP_MINUS", "KP_PLUS", "KP_ENTER",
            "KP_DOT", "KP_EQUAL", "KP_COMMA", "KP_00", "KP_000",
        ):
            assert hasattr(ActionKey, name), f"Missing numpad key: {name}"
        for i in range(10):
            name = f"KP_{i}"
            assert hasattr(ActionKey, name), f"Missing numpad key: {name}"

    def test_extended_present(self) -> None:
        for name in ("KEY_102ND", "COMPOSE", "KPEQUAL", "PROPS", "UNDO", "PASTE"):
            assert hasattr(ActionKey, name), f"Missing extended key: {name}"


class TestImportHygiene:
    """The token module must not import from outside the standard library."""

    def test_no_external_imports(self) -> None:
        source = inspect.getsource(
            __import__("ducky.tokens", fromlist=[""])  # noqa: F811
        )
        tree = ast.parse(source)

        allowed_top_level = {"enum", "dataclasses", "__future__"}

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    top = alias.name.split(".")[0]
                    assert top in allowed_top_level, (
                        f"Illegal import: {alias.name!r}"
                    )
            elif isinstance(node, ast.ImportFrom):
                assert node.module is not None
                top = node.module.split(".")[0]
                assert top in allowed_top_level, (
                    f"Illegal import: {node.module!r}"
                )
