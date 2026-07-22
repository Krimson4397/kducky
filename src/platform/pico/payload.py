"""Payload file manager for Pico runtime — atomic updates with CRC32 fingerprinting.

Provides module-level functions to read, validate, and atomically update
the DuckyScript payload file on the Pico's internal filesystem.
"""

import binascii
import os

from ducky.lexer import DuckyLexer
from ducky.parser import DuckyParser
from ducky.preprocessor import Preprocessor

PAYLOAD_PATH: str = "/payload.dd"
TMP_PATH: str = "/payload.tmp"


def read() -> str:
    """Read payload file content, return ``""`` if missing."""
    try:
        with open(PAYLOAD_PATH) as f:
            return f.read()
    except OSError:
        return ""


def exists() -> bool:
    """Check if the payload file exists."""
    try:
        os.stat(PAYLOAD_PATH)
        return True
    except OSError:
        return False


def fingerprint() -> str:
    """Return 8-char lowercase hex CRC32 of payload file, or ``"00000000"``."""
    try:
        with open(PAYLOAD_PATH, "rb") as f:
            data = f.read()
        return "{:08x}".format(binascii.crc32(data))
    except OSError:
        return "00000000"


def update(content: str) -> bool:
    """Atomically update the payload file — write, validate, rename.

    Writes *content* to a temporary file, validates it through the full
    preprocess → lex → parse pipeline, then atomically renames the temp
    file over the real payload.  Returns ``True`` on success, ``False`` if
    validation fails or the filesystem is read-only.
    """
    try:
        with open(TMP_PATH, "w") as f:
            f.write(content)
    except OSError:
        return False

    # Validate: preprocess → lex → parse
    # ponytail: parse-only validation, no interpreter or platform needed
    try:
        source = Preprocessor().preprocess(content)
        tokens = DuckyLexer().tokenize(source)
        DuckyParser(tokens).parse()
    except Exception:
        # Validation failed — remove tmp file, don't touch the real one
        try:
            os.remove(TMP_PATH)
        except OSError:
            pass
        return False

    # Atomic rename
    try:
        os.rename(TMP_PATH, PAYLOAD_PATH)
        return True
    except OSError:
        return False


def delete() -> None:
    """Delete the payload file if it exists."""
    try:
        os.remove(PAYLOAD_PATH)
    except OSError:
        pass
