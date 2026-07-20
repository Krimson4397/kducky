"""Diagnostic: trace the full STRING pipeline for keyboard layout investigation."""

import sys
import os

# Ensure the src directory is on the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from ducky.layouts import load, Layout


def trace_char(layout: Layout, ch: str) -> None:
    """Trace a single character through the layout pipeline."""
    mod_byte, kc_byte = layout.keycode_for(ch)
    shift = bool(mod_byte & 0x02)
    print(f"  CHAR={ch!r}  mod_byte=0x{mod_byte:02X}  kc_byte=0x{kc_byte:02X}  shift={shift}")


def main():
    print("=" * 60)
    print("DIAGNOSTIC: Keyboard Layout STRING Pipeline")
    print("=" * 60)

    # 1. Load the US layout
    print("\n[1] Loading US layout...")
    try:
        layout = load("US")
        print(f"    OK — Layout loaded: code={layout.code}, map_size={len(layout._map)}")
    except Exception as e:
        print(f"    FAIL — {type(e).__name__}: {e}")
        return

    # 2. Test all characters in "notepad"
    print("\n[2] Tracing 'notepad':")
    for ch in "notepad":
        trace_char(layout, ch)

    # 3. Test every printable ASCII character (0x20-0x7E)
    print("\n[3] Testing all printable ASCII characters...")
    missing = []
    for code in range(0x20, 0x7F):
        ch = chr(code)
        mod_byte, kc_byte = layout.keycode_for(ch)
        if mod_byte == 0 and kc_byte == 0:
            missing.append(ch)
    
    if missing:
        print(f"    MISSING ({len(missing)}): {''.join(repr(c) for c in missing)}")
    else:
        print(f"    All {0x7F - 0x20} printable ASCII characters mapped OK")

    # 4. Verify specific keycodes match HID spec
    print("\n[4] Spot-checking expected HID keycodes:")
    checks = {
        'a': 0x04, 'b': 0x05, 'n': 0x11, 'z': 0x1D,
        'A': 0x04, 'N': 0x11, 'Z': 0x1D,
        '0': 0x27, '9': 0x26,
        ' ': 0x2C, '!': 0x1E, '@': 0x1F, '#': 0x20,
        '.': 0x37, ',': 0x36,
    }
    all_ok = True
    for ch, expected_kc in checks.items():
        mod_byte, kc_byte = layout.keycode_for(ch)
        expected_mod = 0x02 if 'A' <= ch <= 'Z' else 0x00
        # Special cases for shifted symbols
        if ch in '!@#':
            expected_mod = 0x02
        elif ch == ' ':
            expected_mod = 0x00
        
        kc_ok = kc_byte == expected_kc
        mod_ok = mod_byte == expected_mod
        if not (kc_ok and mod_ok):
            print(f"    MISMATCH: {ch!r} got (mod=0x{mod_byte:02X}, kc=0x{kc_byte:02X}) "
                  f"expected (mod=0x{expected_mod:02X}, kc=0x{expected_kc:02X})")
            all_ok = False
    
    if all_ok:
        print("    All spot checks passed")

    # 5. Test the fixup commit: check US.json path resolution
    print("\n[5] Path resolution check:")
    from ducky.layouts import _LAYOUT_DIR
    import glob
    json_files = glob.glob(os.path.join(_LAYOUT_DIR, "*.json"))
    print(f"    Layout dir: {_LAYOUT_DIR}")
    print(f"    Files found: {len(json_files)}")
    us_path = os.path.join(_LAYOUT_DIR, "US.json")
    if os.path.exists(us_path):
        print(f"    US.json exists at: {us_path}")
    else:
        print(f"    US.json NOT FOUND at: {us_path}")

    # 6. Simulate the old KeyboardLayoutUS path for comparison
    print("\n[6] Old vs new comparison (simulated):")
    old_code = """
    # OLD: KeyboardLayoutUS(self._hid_keyboard).write("notepad")
    # This used adafruit_hid's internal mapping
    # It called keyboard.press(modifier, keycode) for each char
    # Each press was followed by release_all()
    """
    print(old_code)
    
    new_code_lines = []
    for ch in "notepad":
        mod_byte, kc_byte = layout.keycode_for(ch)
        kcs = []
        if mod_byte & 0x02:
            kcs.append("_KC.SHIFT (0xE1)")
        kcs.append(f"0x{kc_byte:02X}")
        new_code_lines.append(f"    {ch!r}: press({', '.join(kcs)}), release_all()")
    
    print("    NEW: Current PicoPlatform.type_string produces:")
    for line in new_code_lines:
        print(line)

    print("\n" + "=" * 60)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
