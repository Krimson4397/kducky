"""Tests for interpreter keyboard commands (STRING, STRINGLN, key combos, etc.)."""

import pytest

from ducky.ast import (
    ComboStmt,
    DefaultCharDelayStmt,
    DefaultDelayStmt,
    HoldStmt,
    InjectModStmt,
    IntegerExpr,
    KeyStmt,
    RandomStmt,
    RandomType,
    ReleaseStmt,
    Script,
    StringLnStmt,
    StringStmt,
)
from ducky.interpreter import Interpreter
from ducky.platform.desktop import DesktopPlatform
from ducky.tokens import ActionKey, ModifierKey


class TestStringStmt:
    """STRING <text> — type a literal string."""

    def test_string_types_text(self) -> None:
        """STRING "hello" calls type_string("hello")."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        script = Script((StringStmt("hello"),))
        interpreter.interpret(script)
        assert ("type_string", "hello") in platform.calls

    def test_string_with_char_delay(self) -> None:
        """With DEFAULTCHARDELAY, each char is typed individually."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        script = Script((
            DefaultCharDelayStmt(IntegerExpr(10)),
            StringStmt("ab"),
        ))
        interpreter.interpret(script)
        # Expected: type_string("a"), delay_ms(10), type_string("b"), delay_ms(10)
        assert platform.calls == [
            ("type_string", "a"),
            ("delay_ms", 10),
            ("type_string", "b"),
            ("delay_ms", 10),
        ]

    def test_string_no_char_delay(self) -> None:
        """Without DEFAULTCHARDELAY, type_string is called once."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        script = Script((StringStmt("hello"),))
        interpreter.interpret(script)
        assert platform.calls == [("type_string", "hello")]


class TestStringLnStmt:
    """STRINGLN <text> — type text then press ENTER."""

    def test_stringln_types_text_and_enter(self) -> None:
        """STRINGLN "hello" types text then presses ENTER."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        script = Script((StringLnStmt("hello"),))
        interpreter.interpret(script)
        assert platform.calls == [
            ("type_string", "hello"),
            ("press_key", (), ActionKey.ENTER),
        ]

    def test_stringln_with_char_delay(self) -> None:
        """With DEFAULTCHARDELAY, each char is typed individually before ENTER."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        script = Script((
            DefaultCharDelayStmt(IntegerExpr(10)),
            StringLnStmt("ab"),
        ))
        interpreter.interpret(script)
        # Expected: per-char type+delay then press_key((), ENTER)
        assert platform.calls == [
            ("type_string", "a"),
            ("delay_ms", 10),
            ("type_string", "b"),
            ("delay_ms", 10),
            ("press_key", (), ActionKey.ENTER),
        ]


class TestKeyStmt:
    """Single action key press."""

    def test_key_press(self) -> None:
        """KeyStmt(ENTER) calls press_key with empty modifiers."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        script = Script((KeyStmt(ActionKey.ENTER),))
        interpreter.interpret(script)
        assert platform.calls == [("press_key", (), ActionKey.ENTER)]

    def test_key_press_function_key(self) -> None:
        """KeyStmt(F1) presses F1."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        script = Script((KeyStmt(ActionKey.F1),))
        interpreter.interpret(script)
        assert platform.calls == [("press_key", (), ActionKey.F1)]


class TestComboStmt:
    """Modifier + key combos."""

    def test_combo_with_modifiers_and_key(self) -> None:
        """CTRL SHIFT ESC presses modifiers + key."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        script = Script((
            ComboStmt((ModifierKey.CTRL, ModifierKey.SHIFT), ActionKey.ESC),
        ))
        interpreter.interpret(script)
        assert platform.calls == [
            ("press_key", (ModifierKey.CTRL, ModifierKey.SHIFT), ActionKey.ESC),
        ]

    def test_combo_modifier_only(self) -> None:
        """GUI alone (no action key) presses modifier only."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        script = Script((ComboStmt((ModifierKey.GUI,), None),))
        interpreter.interpret(script)
        assert platform.calls == [("press_key", (ModifierKey.GUI,), None)]

    def test_combo_single_modifier(self) -> None:
        """CTRL ENTER presses CTRL + ENTER."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        script = Script((
            ComboStmt((ModifierKey.CTRL,), ActionKey.ENTER),
        ))
        interpreter.interpret(script)
        assert platform.calls == [
            ("press_key", (ModifierKey.CTRL,), ActionKey.ENTER),
        ]


class TestHoldRelease:
    """HOLD and RELEASE key semantics."""

    def test_hold_then_release(self) -> None:
        """HOLD ENTER then RELEASE ENTER."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        script = Script((
            HoldStmt(ActionKey.ENTER),
            ReleaseStmt(ActionKey.ENTER),
        ))
        interpreter.interpret(script)
        assert platform.calls == [
            ("hold_key", ActionKey.ENTER),
            ("release_key", ActionKey.ENTER),
        ]


class TestInjectMod:
    """INJECT_MOD — release all held keys."""

    def test_inject_mod_releases_all(self) -> None:
        """INJECT_MOD calls release_all()."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        script = Script((InjectModStmt(),))
        interpreter.interpret(script)
        assert ("release_all",) in platform.calls


class TestRandomStmt:
    """RANDOM_CHAR / RANDOM_LETTER / etc."""

    def test_random_char(self) -> None:
        """RANDOM_CHAR generates a printable ASCII char (0x21-0x7E)."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        script = Script((RandomStmt(RandomType.CHAR),))
        interpreter.interpret(script)
        # Find the random_int call and verify range
        random_calls = [c for c in platform.calls if c[0] == "random_int"]
        assert len(random_calls) == 1
        assert random_calls[0] == ("random_int", 0x21, 0x7E)
        # Verify a type_string call happened with a single char
        type_calls = [c for c in platform.calls if c[0] == "type_string"]
        assert len(type_calls) == 1
        ch = type_calls[0][1]
        assert isinstance(ch, str) and len(ch) == 1
        assert 0x21 <= ord(ch) <= 0x7E

    def test_random_lowercase(self) -> None:
        """RANDOM_LOWERCASE_LETTER generates a-z."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        script = Script((RandomStmt(RandomType.LOWERCASE_LETTER),))
        interpreter.interpret(script)
        random_calls = [c for c in platform.calls if c[0] == "random_int"]
        assert random_calls[0] == ("random_int", 0x61, 0x7A)
        ch = [c for c in platform.calls if c[0] == "type_string"][0][1]
        assert "a" <= ch <= "z"

    def test_random_uppercase(self) -> None:
        """RANDOM_UPPERCASE_LETTER generates A-Z."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        script = Script((RandomStmt(RandomType.UPPERCASE_LETTER),))
        interpreter.interpret(script)
        random_calls = [c for c in platform.calls if c[0] == "random_int"]
        assert random_calls[0] == ("random_int", 0x41, 0x5A)
        ch = [c for c in platform.calls if c[0] == "type_string"][0][1]
        assert "A" <= ch <= "Z"

    def test_random_letter(self) -> None:
        """RANDOM_LETTER generates a-z or A-Z."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        script = Script((RandomStmt(RandomType.LETTER),))
        interpreter.interpret(script)
        random_calls = [c for c in platform.calls if c[0] == "random_int"]
        assert len(random_calls) == 1
        min_v, max_v = random_calls[0][1], random_calls[0][2]
        assert min_v == 0
        assert max_v == 51
        ch = [c for c in platform.calls if c[0] == "type_string"][0][1]
        assert len(ch) == 1
        assert ch.isalpha()

    def test_random_number(self) -> None:
        """RANDOM_NUMBER generates 0-9."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        script = Script((RandomStmt(RandomType.NUMBER),))
        interpreter.interpret(script)
        random_calls = [c for c in platform.calls if c[0] == "random_int"]
        assert random_calls[0] == ("random_int", 0x30, 0x39)
        ch = [c for c in platform.calls if c[0] == "type_string"][0][1]
        assert "0" <= ch <= "9"

    def test_random_special(self) -> None:
        """RANDOM_SPECIAL generates a char from the spec's !@#$%^&*() set."""
        specials = "!@#$%^&*()"
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        script = Script((RandomStmt(RandomType.SPECIAL),))
        interpreter.interpret(script)
        random_calls = [c for c in platform.calls if c[0] == "random_int"]
        assert len(random_calls) == 1
        assert random_calls[0] == ("random_int", 0, len(specials) - 1)
        ch = [c for c in platform.calls if c[0] == "type_string"][0][1]
        assert len(ch) == 1
        assert ch in specials


class TestErrorPathKeyRelease:
    """Error during keyboard operation releases all keys."""

    def test_error_during_string_releases_all(self) -> None:
        """Error during STRING calls release_all before propagating."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)

        # Monkey-patch platform.type_string to raise
        def _fail(_text: str) -> None:
            raise RuntimeError("boom")

        platform.type_string = _fail  # type: ignore[assignment]
        script = Script((StringStmt("hello"),))
        with pytest.raises(RuntimeError, match="boom"):
            interpreter.interpret(script)
        assert ("release_all",) in platform.calls

    def test_error_during_combo_releases_all(self) -> None:
        """Error during combo calls release_all before propagating."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)

        def _fail(*_args: object) -> None:
            raise RuntimeError("boom")

        platform.press_key = _fail  # type: ignore[assignment]
        script = Script((ComboStmt((ModifierKey.CTRL,), ActionKey.ENTER),))
        with pytest.raises(RuntimeError, match="boom"):
            interpreter.interpret(script)
        assert ("release_all",) in platform.calls


class TestDefaultDelayWithKeyboard:
    """Default delay applies after keyboard statements."""

    def test_default_delay_after_string(self) -> None:
        """Default delay fires after STRING."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        script = Script((
            DefaultDelayStmt(IntegerExpr(50)),
            StringStmt("hello"),
        ))
        interpreter.interpret(script)
        delay_calls = [c for c in platform.calls if c[0] == "delay_ms"]
        assert len(delay_calls) == 1
        assert delay_calls[0] == ("delay_ms", 50)

    def test_default_delay_after_key(self) -> None:
        """Default delay fires after single key press."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        script = Script((
            DefaultDelayStmt(IntegerExpr(30)),
            KeyStmt(ActionKey.ENTER),
        ))
        interpreter.interpret(script)
        delay_calls = [c for c in platform.calls if c[0] == "delay_ms"]
        assert len(delay_calls) == 1
        assert delay_calls[0] == ("delay_ms", 30)


class TestCallOrder:
    """Verify call order matches expected sequence."""

    def test_mixed_keyboard_sequence(self) -> None:
        """Mixed keyboard commands execute in correct order."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        script = Script((
            StringStmt("hello"),
            KeyStmt(ActionKey.ENTER),
            ComboStmt((ModifierKey.CTRL,), ActionKey.ENTER),
            InjectModStmt(),
        ))
        interpreter.interpret(script)
        expected = [
            ("type_string", "hello"),
            ("press_key", (), ActionKey.ENTER),
            ("press_key", (ModifierKey.CTRL,), ActionKey.ENTER),
            ("release_all",),
        ]
        assert platform.calls == expected
