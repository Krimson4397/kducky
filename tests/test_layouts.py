"""Tests for keyboard layout loader (Milestone 15)."""

from ducky.layouts import add_layout, available, load


def test_available_includes_expected_layouts():
    """All 16 required layouts are available."""
    codes = available()
    expected = {"US", "GB", "DE", "FR", "ES", "IT", "JP",
                "DK", "NO", "SE", "FI", "PT", "BR", "RU", "PL", "CZ"}
    assert expected.issubset(set(codes)), f"Missing layouts: {expected - set(codes)}"
    assert len(codes) >= 16


def test_load_us():
    """US layout loads and maps 'a' correctly."""
    layout = load("US")
    assert layout.code == "US"
    assert layout.keycode_for("a") == (0, 4)
    assert layout.has("a")
    assert not layout.has("\x00")


def test_load_case_insensitive():
    """Layout codes are case-insensitive."""
    upper = load("US")
    lower = load("us")
    mixed = load("uS")
    assert upper is lower is mixed
    assert upper.code == "US"


def test_all_ascii_mapped():
    """All 95 printable ASCII characters (0x20-0x7E) map to non-zero keycodes."""
    layout = load("US")
    for code in range(0x20, 0x7F):
        char = chr(code)
        mod, kc = layout.keycode_for(char)
        assert kc != 0, f"US layout missing mapping for {char!r} (0x{code:02X})"


def test_non_us_inherits_us():
    """Non-US layouts inherit US mappings for characters they don't override."""
    gb = load("GB")
    de = load("DE")
    assert gb.keycode_for("a") == (0, 4)
    assert de.keycode_for("a") == (0, 4)


def test_unknown_layout_raises():
    """Loading an unknown layout raises ValueError."""
    try:
        load("XX")
        assert False, "Expected ValueError"
    except ValueError:
        pass


def test_add_layout_in_memory():
    """add_layout registers a layout for testing without a JSON file."""
    add_layout("TEST", {"A": "02,00,04"})
    layout = load("TEST")
    assert layout.code == "TEST"
    assert layout.keycode_for("A") == (2, 4)


def test_set_layout_desktop():
    """DesktopPlatform set_layout/get_layout work."""
    from ducky.platform.desktop import DesktopPlatform
    p = DesktopPlatform()
    assert p.get_layout() == "US"
    p.set_layout("DE")
    assert p.get_layout() == "DE"
    # Verify it's recorded in calls
    assert ("set_layout", "DE") in p.calls


def test_ducky_lang_interpreter():
    """Interpreter visit_DuckyLangStmt calls platform.set_layout."""
    from ducky.ast.nodes import DuckyLangStmt
    from ducky.interpreter import Interpreter
    from ducky.platform.desktop import DesktopPlatform

    platform = DesktopPlatform()
    interp = Interpreter(platform)

    # Wire through DuckyLangStmt via interpreter
    interp.visit_DuckyLangStmt(DuckyLangStmt(language="DE"))
    assert platform.get_layout() == "DE"

    interp.visit_DuckyLangStmt(DuckyLangStmt(language="FR"))
    assert platform.get_layout() == "FR"
