#!/usr/bin/env python3
"""Deploy kducky files to a CIRCUITPY drive for Raspberry Pi Pico 2 W.

Auto-discovers all .py and .json files under src/ — no manual manifest needed.

Usage:
    python deploy.py <CIRCUITPY_PATH>
    python deploy.py E:\
    python deploy.py --dry-run E:\
"""

from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import sys

# ── File discovery ─────────────────────────────────────────────────────


def _discover_files(repo_root: str) -> list[tuple[str, str]]:
    """Walk ``src/`` and yield ``(src_rel, dst_rel)`` pairs.

    Special destination mappings:
    - ``src/platform/pico/boot.py``  → ``boot.py``
    - ``src/platform/pico/main.py``  → ``code.py`` *and* ``main.py``

    All other files keep their path relative to ``src/``.
    """
    src_root = os.path.join(repo_root, "src")
    files: list[tuple[str, str]] = []

    for dirpath, dirnames, filenames in os.walk(src_root):
        # Skip __pycache__ entirely
        dirnames[:] = [d for d in dirnames if d != "__pycache__"]

        for fname in filenames:
            if not (fname.endswith(".py") or fname.endswith(".json")) or fname.endswith(".pyc"):
                continue

            full = os.path.join(dirpath, fname)
            rel = os.path.relpath(full, src_root).replace(os.sep, "/")

            # Special destinations
            if rel == "platform/pico/boot.py":
                files.append((os.path.join("src", rel), "boot.py"))
            elif rel == "platform/pico/main.py":
                files.append((os.path.join("src", rel), "code.py"))
                files.append((os.path.join("src", rel), "main.py"))
            else:
                files.append((os.path.join("src", rel), rel))

    # Payload file (flattened — no subdirectory on Pico)
    files.append((os.path.join("payloads", "payload.dd"), "payload.dd"))

    return files


def _file_hash(path: str) -> str:
    """Return MD5 hex digest of *path* contents."""
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _needs_update(src: str, dst: str) -> bool:
    """Return True when *dst* is missing or differs from *src*."""
    if not os.path.exists(dst):
        return True
    # ponytail: hash comparison over mtime — CIRCUITPY FAT timestamps
    # are unreliable, so content hash is the safer check.
    return _file_hash(src) != _file_hash(dst)


def deploy(circuitpy_path: str, dry_run: bool = False) -> None:
    """Copy kducky files to *circuitpy_path*.

    Args:
        circuitpy_path: Root of the mounted CIRCUITPY drive.
        dry_run: When True, log intended actions without writing.

    Raises:
        SystemExit: On copy errors (permission, missing source).
    """
    repo_root = os.path.dirname(os.path.abspath(__file__))
    total_bytes = 0
    copied = 0
    skipped = 0
    errors: list[str] = []

    for src_rel, dst_rel in _discover_files(repo_root):
        src = os.path.join(repo_root, src_rel)
        dst = os.path.join(circuitpy_path, dst_rel)

        if not os.path.isfile(src):
            errors.append(f"Source not found: {src_rel}")
            continue

        dst_dir = os.path.dirname(dst)
        if not os.path.isdir(dst_dir):
            if dry_run:
                print(f"  MKDIR {_display(dst_dir, circuitpy_path)}")
            else:
                os.makedirs(dst_dir, exist_ok=True)

        if not _needs_update(src, dst):
            print(f"  SKIP  {_display(dst, circuitpy_path)}  (up to date)")
            skipped += 1
            continue

        size = os.path.getsize(src)
        total_bytes += size
        copied += 1

        if dry_run:
            print(f"  COPY  {_display(dst, circuitpy_path)}  ({size} bytes)")
        else:
            try:
                shutil.copy2(src, dst)
                print(f"  COPY  {_display(dst, circuitpy_path)}  ({size} bytes)")
            except (OSError, PermissionError) as e:
                errors.append(f"Failed to copy {_display(dst, circuitpy_path)}: {e}")

    # ── Summary ────────────────────────────────────────────────────
    print()
    action = "Would copy" if dry_run else "Copied"
    print(f"{action} {copied} file(s) ({_human_bytes(total_bytes)}), {skipped} already up to date")

    if errors:
        print("\nErrors:")
        for err in errors:
            print(f"  ! {err}")
        sys.exit(1)


def _display(path: str, base: str) -> str:
    """Return *path* relative to *base*, using forward slashes."""
    rel = os.path.relpath(path, base)
    return rel.replace(os.sep, "/")


def _human_bytes(n: int) -> str:
    """Format byte count for human reading."""
    for unit in ("B", "KB", "MB"):
        if n < 1024:
            return f"{n}{unit}"
        n //= 1024
    return f"{n}GB"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Deploy kducky files to a CIRCUITPY drive.",
    )
    parser.add_argument(
        "circuitpy_path",
        help="Path to the mounted CIRCUITPY drive (e.g. E:\\)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be copied without writing any files",
    )
    args = parser.parse_args()

    if not os.path.isdir(args.circuitpy_path):
        _msg = f"Error: {args.circuitpy_path} is not a valid directory"
        print(_msg, file=sys.stderr)
        sys.exit(1)

    deploy(args.circuitpy_path, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
