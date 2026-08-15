# Compatibility Plan — Off-the-Shelf DuckyScript Payloads

> Status: PLANNED — design approved, implementation not started. Awaiting go signal.
> Target: Accept payloads written for the official Hak5 USB Rubber Ducky (and compatible tools) without hand-rewriting.

## Background

kducky implements the DuckyScript 3 language and already covers most of what real-world payloads use (blocks, EXTENSION bundles, DEFINE, control flow, MOUSE, REPLAY/REBOOT/JITTER, and more — ~800 passing tests). Remaining gaps block off-the-shelf payloads: certain block keywords, F13–F24, media keys, EXFIL, and legacy 1.0 dialect quirks. There is currently no dialect detection, so an unknown command dies at runtime with `InterpreterError`.

Research findings that shape this plan:
- STRING_POWERSHELL / STRINGLN_* and friends are NOT separate runtime commands — they are block forms of STRING/STRINGLN with editor language modes. Semantics identical; close with END_STRING / END_STRINGLN.
- RANDOM_LINE and RANDOM_STRING do not exist in any Hak5 dialect — not targeted.
- inject.bin is closed/undocumented compiled bytecode — not portable; only source .txt is usable.
- Rubber Ducky payloads never specify keyboard layout (compile-time default US) — matches kducky's default.
- Official stance: DS 1.0 payloads are valid DS 3.0; deprecated 1.0 quirks are bare-char lines and implicit modifiers in combos (CONTROL S meant CTRL+SHIFT+S).
- Payload Studio exports only inject.bin or payload.txt. No official converter exists.

## Strategy: Hybrid

Split by cost and where human judgment is needed:

- **Phase 1 — Runtime (Pico side):** cheap wins go straight into the interpreter so common payloads run with zero extra steps. Small, safe additions.
- **Phase 2 — Converter (desktop tool):** a new component inside kducky that translates legacy/foreign payloads into kducky-compatible source, with semi-automated user interaction and built-in verification. Handles the structural work that needs human decisions.
- **Later — Documentation:** after the whole feature has gone through rigorous testing and review, update README and related docs.

## Phase 1 — Runtime additions

1. **STRING_* block aliases** — map `STRING_POWERSHELL`, `STRING_BATCH`, `STRING_BASH`, `STRING_JAVASCRIPT`, `STRING_PYTHON`, `STRING_RUBY`, `STRING_HTML` (and `STRINGLN_*` variants) to the existing block mode in the lexer. No new token types, no AST changes. (~15 lines.)
   - NOTE: also reconcile STRINGLN whitespace handling — official rule strips only the FIRST tab per line and preserves other formatting; current kducky behavior lstrips all leading whitespace. Verify/fix for byte-exact compatibility.
2. **F13–F24** — add HID usage IDs to `_ACTION_KEY_MAP` in the Pico backend (~10 keycodes).
3. **Basic media keys** — volume up/down/mute, play/pause, stop, next/previous track (consumer page codes).
4. **EXFIL** — `EXFIL $var` writes collected data to loot.bin in the Hak5 format, so official exfil payloads behave identically.
5. **Spec amendment** — STRING_*, F13+, media keys, and EXFIL are currently listed as unsupported in Engineering Spec §1.13. Move them to §1.14 project extensions (deliberate, approved change).

Runtime stays deliberately dumb — no dialect logic on the Pico.

## Phase 2 — Converter (desktop tool)

New folder inside kducky: `src/ducky/compat/`.

Proposed layout:

```
src/ducky/compat/
  dialect.py       detect 3.0 / classic 1.0 / Key Croc / Bash Bunny / inject.bin
  rules.py         rule engine: detector + transformer + severity
  transforms.py    rule implementations
  convert.py       pipeline orchestration
  prompts.py       semi-automated interaction
tests/test_compat.py
```

### Sources accepted

Ducky-only: DuckyScript 3.0 + classic 1.0. O.MG payloads that are valid ducky pass through. Rejected with clear reasons: Key Croc (Q-prefix), Bash Bunny (bash), inject.bin (closed binary format).

### Rule engine model

Each rule = match + action + severity:

| Severity | Behavior                                    |
| -------- | ------------------------------------------- |
| auto     | rewrite silently, log it                    |
| ask      | stop, prompt user (interactive) or use flag |
| warn     | keep as-is, note in report                  |
| reject   | refuse conversion, explain why              |

### Initial transform rules

- `STRING_POWERSHELL` → `STRING` block (whitespace normalized per spec: STRING strips leading whitespace + ignores newlines; STRINGLN strips first tab only, preserves rest).
- bare-char line → `STRING "c"` (ask — ambiguous with identifiers).
- implicit modifier `CONTROL S` → `CTRL SHIFT S` (ask).
- `ATTACKMODE` params → warn "no-op on Pico" (physical CircuitPython constraint: USB descriptors fixed at boot).
- Key Croc `Q ` prefix strip → ducky lines (auto, if requested).

### Semi-automated interaction

CLI named `ducky-convert`, three modes over one rule table:

```
ducky-convert payload.txt           # interactive: stops at ask rules
ducky-convert payload.txt --auto    # safe defaults for ask rules
ducky-convert payload.txt --report  # lint only, no output file
```

Session answers cached in a `.ducky-convert` config. Headless/CI friendly.

### Verification

After emit, converter runs the converted payload through a desktop dry-run (existing interpreter + DesktopPlatform) and includes the event log in the report. "Converted AND executes clean" = green acceptance.

## Later — Documentation pass

After the whole feature has gone through rigorous testing, review, and any other hardening: update README (test counts, feature lists, roadmap tiers), review DEPLOYMENT.md and any stale planning docs, and refresh the Session Handoff.

## Deliberate non-goals

- RANDOM_LINE / RANDOM_STRING (do not exist in ecosystem)
- KEYCODE (not a ducky command; only C2-internal)
- DUCKYPORTAL (does not exist)
- JIGGLER (O.MG-only, zero usage in payload libraries)
- Web UI for converter (CLI now; possible thin web wrapper later)
- inject.bin decoding (closed format, not reversible)
