"""Tests for interpreter keyboard commands (STRING, STRINGLN, key combos, etc.)."""

import pytest

from ducky.ast import (
    AttackModeStmt,
    ButtonDefStmt,
    ComboStmt,
    DefaultCharDelayStmt,
    DefaultDelayStmt,
    DisableButtonStmt,
    EnableButtonStmt,
    HidePayloadStmt,
    HoldStmt,
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
    RestoreAttackModeStmt,
    RestoreHostLockStateStmt,
    RestorePayloadStmt,
    SaveAttackModeStmt,
    SaveHostLockStateStmt,
    Script,
    StringLnStmt,
    StringStmt,
    WaitForButtonPressStmt,
    WaitForKeyStmt,
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
            ("get_caps_lock",),
            ("get_num_lock",),
            ("get_scroll_lock",),
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
        assert platform.calls == [
            ("get_caps_lock",),
            ("get_num_lock",),
            ("get_scroll_lock",),
            ("type_string", "hello"),
        ]


class TestStringLnStmt:
    """STRINGLN <text> — type text then press ENTER."""

    def test_stringln_types_text_and_enter(self) -> None:
        """STRINGLN "hello" types text then presses ENTER."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        script = Script((StringLnStmt("hello"),))
        interpreter.interpret(script)
        assert platform.calls == [
            ("get_caps_lock",),
            ("get_num_lock",),
            ("get_scroll_lock",),
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
            ("get_caps_lock",),
            ("get_num_lock",),
            ("get_scroll_lock",),
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
        assert platform.calls == [
            ("get_caps_lock",),
            ("get_num_lock",),
            ("get_scroll_lock",),
            ("press_key", (), ActionKey.ENTER),
        ]

    def test_key_press_function_key(self) -> None:
        """KeyStmt(F1) presses F1."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        script = Script((KeyStmt(ActionKey.F1),))
        interpreter.interpret(script)
        assert platform.calls == [
            ("get_caps_lock",),
            ("get_num_lock",),
            ("get_scroll_lock",),
            ("press_key", (), ActionKey.F1),
        ]


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
            ("get_caps_lock",),
            ("get_num_lock",),
            ("get_scroll_lock",),
            ("press_key", (ModifierKey.CTRL, ModifierKey.SHIFT), ActionKey.ESC),
        ]

    def test_combo_modifier_only(self) -> None:
        """GUI alone (no action key) presses modifier only."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        script = Script((ComboStmt((ModifierKey.GUI,), None),))
        interpreter.interpret(script)
        assert platform.calls == [
            ("get_caps_lock",),
            ("get_num_lock",),
            ("get_scroll_lock",),
            ("press_key", (ModifierKey.GUI,), None),
        ]

    def test_combo_single_modifier(self) -> None:
        """CTRL ENTER presses CTRL + ENTER."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        script = Script((
            ComboStmt((ModifierKey.CTRL,), ActionKey.ENTER),
        ))
        interpreter.interpret(script)
        assert platform.calls == [
            ("get_caps_lock",),
            ("get_num_lock",),
            ("get_scroll_lock",),
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
            ("get_caps_lock",),
            ("get_num_lock",),
            ("get_scroll_lock",),
            ("hold_key", ActionKey.ENTER),
            ("release_key", ActionKey.ENTER),
        ]

    def test_hold_release_modifier_key(self) -> None:
        """INJECT_MOD + HOLD CTRL, then INJECT_MOD + RELEASE CTRL."""
        platform = DesktopPlatform()
        interpreter = Interpreter(platform)
        script = Script((
            InjectModStmt(),
            HoldStmt(ModifierKey.CTRL),
            StringStmt("hello"),
            InjectModStmt(),
            ReleaseStmt(ModifierKey.CTRL),
        ))
        interpreter.interpret(script)
        assert ("hold_key", ModifierKey.CTRL) in platform.calls
        assert ("release_key", ModifierKey.CTRL) in platform.calls


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
            ("get_caps_lock",),
            ("get_num_lock",),
            ("get_scroll_lock",),
            ("type_string", "hello"),
            ("press_key", (), ActionKey.ENTER),
            ("press_key", (ModifierKey.CTRL,), ActionKey.ENTER),
            ("release_all",),
        ]
        assert platform.calls == expected


class TestInterpreterKeyboard:
    """Tests for interpreter keyboard commands (LED, attack mode, lock key, button, payload)."""

    def setup_method(self) -> None:
        """Create fresh platform and interpreter for each test."""
        self.platform = DesktopPlatform()
        self.interp = Interpreter(self.platform)

    # ── LED ────────────────────────────────────────────────────────────────

    def test_led_r(self) -> None:
        """LED_R calls set_led(LedState.R)."""
        self.interp.interpret(Script((LedStmt(LedState.R),)))
        assert ("set_led", LedState.R) in self.platform.calls

    def test_led_g(self) -> None:
        """LED_G calls set_led(LedState.G)."""
        self.interp.interpret(Script((LedStmt(LedState.G),)))
        assert ("set_led", LedState.G) in self.platform.calls

    def test_led_b(self) -> None:
        """LED_B calls set_led(LedState.B)."""
        self.interp.interpret(Script((LedStmt(LedState.B),)))
        assert ("set_led", LedState.B) in self.platform.calls

    def test_led_off(self) -> None:
        """LED_OFF calls set_led(LedState.OFF)."""
        self.interp.interpret(Script((LedStmt(LedState.OFF),)))
        assert ("set_led", LedState.OFF) in self.platform.calls

    # ── Attack mode ────────────────────────────────────────────────────────

    def test_attack_mode(self) -> None:
        """ATTACKMODE HID STORAGE calls set_attack_mode with params."""
        self.interp.interpret(Script((AttackModeStmt(("HID", "STORAGE")),)))
        assert ("set_attack_mode", ("HID", "STORAGE")) in self.platform.calls

    def test_save_attack_mode(self) -> None:
        """SAVE_ATTACKMODE calls save_attack_mode()."""
        self.interp.interpret(Script((SaveAttackModeStmt(),)))
        assert ("save_attack_mode",) in self.platform.calls

    def test_restore_attack_mode(self) -> None:
        """RESTORE_ATTACKMODE calls restore_attack_mode()."""
        self.interp.interpret(Script((RestoreAttackModeStmt(),)))
        assert ("restore_attack_mode",) in self.platform.calls

    # ── Lock key state ─────────────────────────────────────────────────────

    def test_save_host_lock_state(self) -> None:
        """SAVE_HOST_KEYBOARD_LOCK_STATE calls save_lock_state()."""
        self.interp.interpret(Script((SaveHostLockStateStmt(),)))
        assert ("save_lock_state",) in self.platform.calls

    def test_restore_host_lock_state(self) -> None:
        """RESTORE_HOST_KEYBOARD_LOCK_STATE calls restore_lock_state()."""
        self.interp.interpret(Script((RestoreHostLockStateStmt(),)))
        assert ("restore_lock_state",) in self.platform.calls

    def test_wait_for_caps_on(self) -> None:
        """WAIT_FOR_CAPS_ON polls get_caps_lock (pre-set caps on so poll loop exits)."""
        self.platform._caps_lock = True
        self.interp.interpret(Script((WaitForKeyStmt(LockKeyType.CAPS, LockKeyState.ON),)))
        assert ("get_caps_lock",) in self.platform.calls

    def test_wait_for_caps_off(self) -> None:
        """WAIT_FOR_CAPS_OFF polls get_caps_lock (pre-set caps off so poll loop exits)."""
        self.platform._caps_lock = False
        self.interp.interpret(Script((WaitForKeyStmt(LockKeyType.CAPS, LockKeyState.OFF),)))
        assert ("get_caps_lock",) in self.platform.calls

    def test_wait_for_num_on(self) -> None:
        """WAIT_FOR_NUM_ON polls get_num_lock (pre-set num on so poll loop exits)."""
        self.platform._num_lock = True
        self.interp.interpret(Script((WaitForKeyStmt(LockKeyType.NUM, LockKeyState.ON),)))
        assert ("get_num_lock",) in self.platform.calls

    # ── Button ─────────────────────────────────────────────────────────────

    def test_button_def_registers_handler(self) -> None:
        """BUTTON_DEF registers body but does NOT execute it during interpret."""
        self.interp.interpret(Script((
            ButtonDefStmt("my_btn", (StringLnStmt("pressed"),)),
        )))
        # Body must not have been executed (no typing or key press calls)
        assert not any(
            c[0] in ("type_string", "press_key") for c in self.platform.calls
        )

    def test_enable_button(self) -> None:
        """ENABLE_BUTTON calls enable_button()."""
        self.interp.interpret(Script((EnableButtonStmt(),)))
        assert ("enable_button",) in self.platform.calls

    def test_disable_button(self) -> None:
        """DISABLE_BUTTON calls disable_button()."""
        self.interp.interpret(Script((DisableButtonStmt(),)))
        assert ("disable_button",) in self.platform.calls

    def test_wait_for_button_press(self) -> None:
        """WAIT_FOR_BUTTON_PRESS calls wait_for_button_press()."""
        self.interp.interpret(Script((WaitForButtonPressStmt(),)))
        assert ("wait_for_button_press",) in self.platform.calls

    # ── Payload hide / restore ─────────────────────────────────────────────

    def test_hide_payload(self) -> None:
        """HIDE_PAYLOAD calls hide_payload()."""
        self.interp.interpret(Script((HidePayloadStmt(),)))
        assert ("hide_payload",) in self.platform.calls

    def test_restore_payload(self) -> None:
        """RESTORE_PAYLOAD calls restore_payload()."""
        self.interp.interpret(Script((RestorePayloadStmt(),)))
        assert ("restore_payload",) in self.platform.calls
