"""Contract tests for PicoPlatform — verify interface compliance.

These tests run on desktop Python (where CircuitPython is not available)
so the contract checks are structural: method existence, signature
compatibility, and key-map completeness.  The class itself cannot be
instantiated on the desktop — it will raise ``ImportError``.

.. note::
    The ``platform.pico`` namespace conflicts with the stdlib ``platform``
    module on desktop Python.  We avoid the conflict by loading the
    backends module via ``importlib`` file-path import rather than a
    dotted-name import.
"""

from __future__ import annotations

import importlib.util
import inspect
import sys
from pathlib import Path

import pytest

from ducky.ast import LedState
from ducky.platform import (
    PlatformInterface,
    RestartPayloadSignal,
    StopPayloadSignal,
)
from ducky.tokens import ActionKey, ModifierKey

# ── Load backends module by file path (avoids stdlib platform conflict) ───

_BACKENDS_PATH = (
    Path(__file__).resolve().parent.parent / "src" / "platform" / "pico" / "backends.py"
)
_HAS_PICO = False
if _BACKENDS_PATH.is_file():
    spec = importlib.util.spec_from_file_location(
        "platform.pico.backends",
        str(_BACKENDS_PATH),
    )
    if spec is not None:
        _mod = importlib.util.module_from_spec(spec)
        sys.modules["platform.pico.backends"] = _mod
        spec.loader.exec_module(_mod)  # type: ignore[union-attr]
        _HAS_PICO = True

if _HAS_PICO:
    PicoPlatform = _mod.PicoPlatform
    _ACTION_KEY_MAP = _mod._ACTION_KEY_MAP
    _HAS_HW = _mod._HAS_HW
    _MODIFIER_KEY_MAP = _mod._MODIFIER_KEY_MAP
    _MEDIA_ACTION_KEYS = _mod._MEDIA_ACTION_KEYS
    _validate_media_key_press = _mod._validate_media_key_press
else:
    PicoPlatform = None
    _ACTION_KEY_MAP = {}
    _HAS_HW = True
    _MODIFIER_KEY_MAP = {}
    _MEDIA_ACTION_KEYS = frozenset()
    _validate_media_key_press = None


# ── Protocol method set (for completeness checks) ──────────────────────

_PROTOCOL_METHODS = frozenset(
    name
    for name, fn in inspect.getmembers(PlatformInterface, inspect.isfunction)
    if not name.startswith("_")
)


class TestPicoPlatformContract:
    """Structural contract: PicoPlatform must satisfy PlatformInterface."""

    def test_module_importable(self) -> None:
        """The backends module is importable on desktop (guarded imports)."""
        assert _HAS_PICO, "Could not load platform.pico.backends module"

    def test_has_hw_is_false_on_desktop(self) -> None:
        """``_HAS_HW`` is ``False`` when not running on CircuitPython."""
        assert _HAS_HW is False

    def test_class_exists(self) -> None:
        """``PicoPlatform`` class is defined."""
        assert PicoPlatform is not None

    def test_instantiation_raises_on_desktop(self) -> None:
        """Constructing ``PicoPlatform`` on desktop raises ``ImportError``."""
        with pytest.raises(ImportError):
            PicoPlatform()

    def test_all_protocol_methods_implemented(self) -> None:
        """``PicoPlatform`` has a public method for every protocol method."""
        pico_methods = {
            name
            for name, fn in inspect.getmembers(PicoPlatform, inspect.isfunction)
            if not name.startswith("_")
        }
        missing = _PROTOCOL_METHODS - pico_methods
        assert not missing, f"PicoPlatform missing: {sorted(missing)}"

    def test_no_extra_public_methods(self) -> None:
        """``PicoPlatform`` exposes only the protocol methods publicly."""
        pico_methods = {
            name
            for name, fn in inspect.getmembers(PicoPlatform, inspect.isfunction)
            if not name.startswith("_")
        }
        extra = pico_methods - _PROTOCOL_METHODS
        assert not extra, f"PicoPlatform has extra public methods: {sorted(extra)}"

    def test_method_signatures_match(self) -> None:
        """Public method signatures match the protocol (arity + parameter names)."""
        for name in _PROTOCOL_METHODS:
            proto_sig = inspect.signature(getattr(PlatformInterface, name))
            pico_sig = inspect.signature(getattr(PicoPlatform, name))
            # Compare parameter lists (excluding self)
            proto_params = list(proto_sig.parameters.values())[1:]  # skip self
            pico_params = list(pico_sig.parameters.values())[1:]
            assert len(proto_params) == len(pico_params), (
                f"{name}: expected {len(proto_params)} params, "
                f"got {len(pico_params)}"
            )
            for pp, pc in zip(proto_params, pico_params):
                assert pp.name == pc.name, (
                    f"{name}: param '{pp.name}' vs '{pc.name}'"
                )


class TestActionKeyMap:
    """Verify the ActionKey → HID keycode map is exhaustive."""

    def test_all_action_keys_mapped(self) -> None:
        """Every ``ActionKey`` member has a corresponding HID keycode.

        .. note::
            This test only applies when ``_HAS_HW`` is ``True`` because
            the keycode map is populated from ``adafruit_hid`` which
            is only available on CircuitPython.
        """
        if not _HAS_HW:
            pytest.skip("Keycode maps only populated when CircuitPython is available")
        for key in ActionKey.members():
            assert key in _ACTION_KEY_MAP, f"ActionKey.{key.name} not mapped"
            assert isinstance(_ACTION_KEY_MAP[key], int), (
                f"ActionKey.{key.name} mapping is not an int"
            )

    def test_no_extra_keys(self) -> None:
        """No extra entries beyond ``ActionKey`` members."""
        if not _HAS_HW:
            pytest.skip("Keycode maps only populated when CircuitPython is available")
        for key in _ACTION_KEY_MAP:
            assert isinstance(key, ActionKey), (
                f"Unexpected key type: {type(key).__name__} ({key!r})"
            )

    def test_mapping_values_are_ints(self) -> None:
        """All mapping values are integers (HID keycodes)."""
        if not _HAS_HW:
            pytest.skip("Keycode maps only populated when CircuitPython is available")
        assert all(isinstance(v, int) for v in _ACTION_KEY_MAP.values())


class TestModifierKeyMap:
    """Verify the ModifierKey → HID keycode map is exhaustive."""

    def test_all_modifier_keys_mapped(self) -> None:
        """Every ``ModifierKey`` member has a corresponding HID keycode.

        .. note::
            This test only applies when ``_HAS_HW`` is ``True`` because
            the keycode map is populated from ``adafruit_hid`` which
            is only available on CircuitPython.
        """
        if not _HAS_HW:
            pytest.skip("Keycode maps only populated when CircuitPython is available")
        for key in ModifierKey.members():
            assert key in _MODIFIER_KEY_MAP, (
                f"ModifierKey.{key.name} not mapped"
            )
            assert isinstance(_MODIFIER_KEY_MAP[key], int), (
                f"ModifierKey.{key.name} mapping is not an int"
            )

    def test_no_extra_modifier_keys(self) -> None:
        """No extra entries beyond ``ModifierKey`` members."""
        if not _HAS_HW:
            pytest.skip("Keycode maps only populated when CircuitPython is available")
        for key in _MODIFIER_KEY_MAP:
            assert isinstance(key, ModifierKey), (
                f"Unexpected key type: {type(key).__name__} ({key!r})"
            )

    def test_modifier_values_are_ints(self) -> None:
        """All modifier mapping values are integers (HID keycodes)."""
        if not _HAS_HW:
            pytest.skip("Keycode maps only populated when CircuitPython is available")
        assert all(
            isinstance(v, int) for v in _MODIFIER_KEY_MAP.values()
        )


class TestPicoPlatformSignalBehavior:
    """Signal-raising methods work identically to DesktopPlatform."""

    def test_restart_payload_raises(self) -> None:
        """``restart_payload()`` raises ``RestartPayloadSignal``."""
        with pytest.raises(RestartPayloadSignal):
            PicoPlatform.restart_payload(None)

    def test_stop_payload_raises(self) -> None:
        """``stop_payload()`` raises ``StopPayloadSignal``."""
        with pytest.raises(StopPayloadSignal):
            PicoPlatform.stop_payload(None)


class TestPicoPlatformLedState:
    """LED enum integration (static check, no hardware needed)."""

    def test_led_state_enum_importable(self) -> None:
        """``LedState`` is importable from ``ducky.ast``."""
        assert LedState is not None

    def test_led_state_values(self) -> None:
        """All four ``LedState`` members exist."""
        assert LedState.OFF.name == "OFF"
        assert LedState.R.name == "R"
        assert LedState.G.name == "G"
        assert LedState.B.name == "B"


class _FakeKeyboard:
    """Stand-in for ``adafruit_hid.keyboard.Keyboard``."""

    def __init__(self) -> None:
        self.release_all_calls = 0

    def release_all(self) -> None:
        self.release_all_calls += 1


class _FakeConsumerControlWithReleaseAll:
    """ConsumerControl that exposes ``release_all``."""

    def __init__(self) -> None:
        self.release_all_calls = 0

    def release_all(self) -> None:
        self.release_all_calls += 1


class _FakeConsumerControlNoReleaseAll:
    """Older ConsumerControl lacking ``release_all`` (only ``send``)."""

    def __init__(self) -> None:
        self.send_calls: list[int] = []

    def send(self, code: int) -> None:
        self.send_calls.append(code)


class TestPicoPlatformReleaseAll:
    """``release_all()`` must release both keyboard and consumer endpoints."""

    def test_release_all_reaches_both_endpoints(self) -> None:
        """Keyboard and consumer endpoints both receive ``release_all``."""
        instance = object.__new__(PicoPlatform)
        instance._hid_keyboard = _FakeKeyboard()
        instance._cc = _FakeConsumerControlWithReleaseAll()
        instance.release_all()
        assert instance._hid_keyboard.release_all_calls == 1
        assert instance._cc.release_all_calls == 1

    def test_release_all_falls_back_to_zeroed_report(self) -> None:
        """A ConsumerControl without ``release_all`` gets a zeroed send."""
        instance = object.__new__(PicoPlatform)
        instance._hid_keyboard = _FakeKeyboard()
        instance._cc = _FakeConsumerControlNoReleaseAll()
        instance.release_all()
        assert instance._hid_keyboard.release_all_calls == 1
        assert instance._cc.send_calls == [0]


class TestMediaKeyGuard:
    """Media keys cannot be combined with keyboard modifiers."""

    def test_media_key_with_modifier_raises(self) -> None:
        """A media key plus a modifier raises ``ValueError``."""
        with pytest.raises(ValueError):
            _validate_media_key_press(ActionKey.VOLUME_UP, (ModifierKey.CTRL,))

    def test_media_key_alone_is_allowed(self) -> None:
        """A media key without modifiers passes validation."""
        _validate_media_key_press(ActionKey.VOLUME_UP, ())

    def test_non_media_key_with_modifier_is_allowed(self) -> None:
        """A normal key plus a modifier passes validation."""
        _validate_media_key_press(ActionKey.ENTER, (ModifierKey.CTRL,))

    def test_all_media_keys_classified(self) -> None:
        """Every media ``ActionKey`` member is in ``_MEDIA_ACTION_KEYS``."""
        expected = {
            ActionKey.VOLUME_UP,
            ActionKey.VOLUME_DOWN,
            ActionKey.MUTE,
            ActionKey.PLAY_PAUSE,
            ActionKey.STOP,
            ActionKey.NEXT_TRACK,
            ActionKey.PREV_TRACK,
        }
        assert set(_MEDIA_ACTION_KEYS) == expected
