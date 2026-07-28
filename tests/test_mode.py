"""Pure-logic tests for boot mode selection — no hardware, no CircuitPython.

Loads ``src/platform/pico/mode.py`` by file path to avoid the stdlib
``platform`` namespace conflict (same approach as test_pico_platform.py).
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_MODE_PATH = (
    Path(__file__).resolve().parent.parent / "src" / "platform" / "pico" / "mode.py"
)

_HAS_MODE = False
if _MODE_PATH.is_file():
    _spec = importlib.util.spec_from_file_location("platform.pico.mode", str(_MODE_PATH))
    if _spec is not None:
        _mod = importlib.util.module_from_spec(_spec)
        sys.modules["platform.pico.mode"] = _mod
        _spec.loader.exec_module(_mod)  # type: ignore[union-attr]
        _HAS_MODE = True

if _HAS_MODE:
    select_mode = _mod.select_mode
    is_executable = _mod.is_executable
    MODE_NS = _mod.MODE_NS
    MODE_EWOS = _mod.MODE_EWOS
    MODE_EWIS = _mod.MODE_EWIS
    EXECUTABLE_MODES = _mod.EXECUTABLE_MODES
else:
    select_mode = None  # type: ignore[assignment]
    is_executable = None  # type: ignore[assignment]
    MODE_NS = ""  # type: ignore[assignment]
    MODE_EWOS = ""  # type: ignore[assignment]
    MODE_EWIS = ""  # type: ignore[assignment]
    EXECUTABLE_MODES = frozenset()  # type: ignore[assignment]


class TestSelectMode:
    def test_no_jumper_is_ewos(self) -> None:
        # no-jumper default is now EWOS (payload runs, HID, MSC read-only)
        assert select_mode(True, True) == MODE_EWOS

    def test_gp0_jumper_is_ewos(self) -> None:
        assert select_mode(False, True) == MODE_EWOS

    def test_gp15_jumper_is_ewis(self) -> None:
        assert select_mode(True, False) == MODE_EWIS

    def test_both_jumpers_is_ns(self) -> None:
        # ponytail: both-low treated as NS for safe default
        assert select_mode(False, False) == MODE_NS


class TestIsExecutable:
    def test_ns_not_executable(self) -> None:
        assert not is_executable(MODE_NS)

    def test_ewos_executable(self) -> None:
        assert is_executable(MODE_EWOS)

    def test_ewis_executable(self) -> None:
        assert is_executable(MODE_EWIS)

    def test_unknown_mode_not_executable(self) -> None:
        assert not is_executable("garbage")

    def test_executable_modes_set(self) -> None:
        assert EXECUTABLE_MODES == frozenset({MODE_EWOS, MODE_EWIS})
