"""Keyboard layout loader — maps characters to HID keycodes via JSON layout files.

Format per Engineering Spec Appendix B:
  Layout JSON files map characters to HID scancode triplets:
    "char": "mm,00,kk"  — modifier byte, reserved, keycode byte (all hex)

Modifier byte bitmap: 0x01=CTRL, 0x02=SHIFT, 0x04=ALT, 0x08=GUI
"""

import json
import os

__all__ = [
    "Layout",
    "load",
    "available",
]

# CircuitPython: os.path doesn't exist; use simple string split
_LAYOUT_DIR: str = (
    __file__.rsplit("/", 1)[0]
    if "/" in __file__
    else __file__.rsplit("\\", 1)[0]
    if "\\" in __file__
    else "."
)
_cache: dict[str, "Layout"] = {}
_DEFAULT_LAYOUT: str = "US"


def _parse_triplet(triplet: str) -> tuple[int, int]:
    """Parse 'mm,rr,kk' hex triplet → (modifier_byte, keycode_byte)."""
    parts = triplet.split(",")
    return (int(parts[0], 16), int(parts[2], 16))


def _make_triplet(modifier: int, keycode: int) -> str:
    """Build 'mm,00,kk' hex triplet string."""
    return f"{modifier:02X},00,{keycode:02X}"


class Layout:
    """A keyboard layout mapping characters to HID scancodes."""

    __slots__ = ("_map", "_code")

    def __init__(self, code: str, data: dict[str, tuple[int, int]]) -> None:
        self._code: str = code
        self._map: dict[str, tuple[int, int]] = data

    @property
    def code(self) -> str:
        """Return the language code (e.g. "US", "DE")."""
        return self._code

    def keycode_for(self, char: str) -> tuple[int, int]:
        """Return (modifier_byte, keycode_byte) for a character.

        Returns (0, 0) for unmapped characters.
        """
        return self._map.get(char, (0, 0))

    def has(self, char: str) -> bool:
        """Return True if *char* has a mapping in this layout."""
        return char in self._map


def load(code: str = _DEFAULT_LAYOUT) -> Layout:
    """Load a layout by language code (case-insensitive).

    Non-US layouts define only characters that differ from US.
    Unmapped characters inherit the US mapping.
    """
    code_upper = code.upper()

    # Return cached
    cached = _cache.get(code_upper)
    if cached is not None:
        return cached

    # Load the layout JSON
    path = f"{_LAYOUT_DIR}/{code_upper}.json"
    try:
        with open(path, encoding="utf-8") as f:
            raw: dict[str, str] = json.load(f)
    except OSError:
        raise ValueError(f"Unknown keyboard layout: {code!r}") from None

    # Parse into (modifier, keycode) tuples
    data: dict[str, tuple[int, int]] = {}
    for char, triplet in raw.items():
        data[char] = _parse_triplet(triplet)

    # Merge US fallback for non-US layouts
    if code_upper != "US":
        us = load("US")
        for char, kc in us._map.items():
            data.setdefault(char, kc)

    layout = Layout(code_upper, data)
    _cache[code_upper] = layout
    return layout


def available() -> list[str]:
    """Return sorted list of available layout codes."""
    codes: list[str] = []
    for name in os.listdir(_LAYOUT_DIR):
        if name.endswith(".json") and len(name) == 7:  # e.g. "US.json"
            codes.append(name[:2].upper())
    return sorted(codes)


def add_layout(code: str, mapping: dict[str, str]) -> None:
    """Register an in-memory layout (for testing)."""
    data: dict[str, tuple[int, int]] = {}
    for char, triplet in mapping.items():
        data[char] = _parse_triplet(triplet)
    _cache[code.upper()] = Layout(code.upper(), data)
