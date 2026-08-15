---

# Mypy Hardening Plan

> Status: PLANNED — decision to schedule parked by user. No implementation started.
> Goal: Make `mypy` genuinely green repo-wide, so the checks documented in AGENTS.md and README are real.

## Background

AGENTS.md §7 and README document `mypy src/ tests/` as a required pre-commit check and claim the repo is clean under mypy. Both claims are false:

1. **The documented command silently checks nothing.** `pyproject.toml` has `exclude = ["tests/"]` while the command passes `tests/` as an argument. mypy refuses to check an explicitly-excluded path, exits with code 2 and prints `There are no .py[i] files in directory 'tests'` — checking zero files. Anyone running the documented command sees a "failure" that looks like a pass and learns nothing.
2. **The real check fails.** Run correctly (`mypy src/`), the repo reports 633 errors at HEAD~1 (before Phase 1 compatibility work) and 692 at the Phase 1 commit — a +59 delta in the same pre-existing error categories, not new categories.

Root causes of the 633-error baseline:
- `src/ducky/utils/compat.py` defines custom untyped `@enum` / `@dataclass` decorator wrappers (for CircuitPython compatibility). mypy cannot see through them, producing `no-untyped-call`, `call-arg`, and `dict-item` noise on every wrapped enum/dataclass in the codebase.
- CircuitPython hardware modules (`board`, `storage`, `usb_hid`, `adafruit_hid`, etc.) have no type information, producing `import-not-found` and related errors in `src/platform/pico/`.
- Config runs `strict = true` (python_version 3.10), so every category is at full volume.

Environment note: mypy 1.14.1, ruff 0.16.3, pytest 9.1.1 (Python 3.14 in the dev toolchain). mypy itself is not broken — a reinstall changes nothing. This is a config + code problem, not a tool problem.

## Fix plan (three layers)

### Layer A — Make the check actually run (5 minutes)

Fix the config/command contradiction in `pyproject.toml`:
- Either drop `exclude = ["tests/"]` and let `tests/` be checked (more coverage, more errors to fix), or
- Change the documented command to `mypy src/` (drop the `tests/` argument).

Whichever choice, the documented command must genuinely check the code and the README/AGENTS.md wording must be corrected. Verify: `mypy src/` visibly reports the error list every run.

### Layer B — Clear the baseline errors (estimated 1–2 focused days)

1. **`src/ducky/utils/compat.py` first** — annotate the decorator wrappers with proper signatures (`TypeVar`, `@overload`) so mypy sees through them. This eliminates the majority of the noise (`no-untyped-call`, `call-arg`, `dict-item`). Touches every wrapped type, so this is the trickiest part; low runtime risk (types only).
2. **CircuitPython stubs second** — provide type information for the ~15 hardware modules used (`board`, `storage`, `usb_hid`, `adafruit_hid`, etc.). Two options: write proper `.pyi` stub files (more work, correct), or `# type: ignore[import-not-found]` / `Any` shims (fast, weaker). Prefer proper stubs where feasible.
3. **Mop-up third** — clear remaining stragglers. The ~59 Phase 1 errors (media-key dict entries, `consumer_control` import, EXFIL node) are in the same categories and disappear with A + B.

### Verification (each milestone)

- `mypy src/` → 0 errors (or a documented, justified allowlist)
- `ruff check src/ tests/` → clean
- `python -m pytest tests/ -x -q` → full suite green (839 passed / 6 skipped at Phase 1)
- Zero runtime behavior change — types and config only

## Ordering

Parked until after Phase 2 (converter) per user decision. Single separate milestone, one commit, run through the normal review process. Not a blocker for any feature work.

## Deliberate non-goals

- Not a mypy reinstall ("fix") — the tool is not broken.
- Not a blanket `# type: ignore` sweep — would hide real errors.
- Not a silent relaxation to non-strict mode without an explicit user decision.

---
