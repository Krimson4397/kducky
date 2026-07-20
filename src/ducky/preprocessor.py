"""Preprocessor for DuckyScript 3 — compile-time DEFINE constant substitution.

Operates on raw source text *before* lexing:

1. Scans lines for ``DEFINE #NAME value`` declarations
2. Replaces DEFINE lines with blank lines (preserves line numbering)
3. Substitutes ``#NAME`` references in all other lines with their literal values
4. Skips substitution inside ``"..."`` quoted strings
"""

from ducky.errors import PreprocessorError


class Preprocessor:
    """Text-level DEFINE constant substitution.

    Call ``preprocess(source)`` before passing the result to the lexer.
    """

    def __init__(self) -> None:
        self._defines: dict[str, str] = {}

    def preprocess(self, source: str) -> str:
        """Preprocess *source*, returning text with DEFINE applied."""
        self._defines.clear()
        lines = source.split("\n")
        out: list[str] = []
        for i, line in enumerate(lines):
            line_num = i + 1
            if self._is_define(line):
                self._parse_define(line, line_num)
                out.append("")  # blank preserves line numbers
            else:
                out.append(self._substitute(line, line_num))
        return "\n".join(out)

    # ── Private helpers ────────────────────────────────────────────────────

    def _is_define(self, line: str) -> bool:
        """Return True if *line* is a DEFINE declaration (case-insensitive)."""
        return line.strip().upper().startswith("DEFINE")

    def _parse_define(self, line: str, line_num: int) -> None:
        """Parse ``DEFINE #NAME value`` from *line* and store in symbol table."""
        s = line.strip()
        rest = s[6:].lstrip()  # everything after "DEFINE"
        if not rest or not rest.startswith("#"):
            raise PreprocessorError("Expected #NAME after DEFINE", line_num)
        # Scan identifier after '#'
        end = 1
        while end < len(rest) and (
            rest[end].isalpha() or rest[end].isdigit() or rest[end] == "_"
        ):
            end += 1
        name = rest[1:end]
        if not name:
            raise PreprocessorError("Expected #NAME after DEFINE", line_num)
        self._defines[name] = rest[end:].strip()

    def _substitute(self, line: str, line_num: int) -> str:
        """Replace ``#NAME`` references in *line* with their defined values."""
        out: list[str] = []
        i = 0
        while i < len(line):
            if line[i] == '"':
                # Copy quoted string verbatim (no substitution inside)
                j = i + 1
                while j < len(line):
                    if line[j] == "\\" and j + 1 < len(line):
                        j += 2  # skip escaped character
                    elif line[j] == '"':
                        j += 1
                        break
                    else:
                        j += 1
                out.append(line[i:j])
                i = j
            elif line[i] == "#":
                # Check for #NAME pattern
                if i + 1 < len(line) and (
                    line[i + 1].isalpha() or line[i + 1] == "_"
                ):
                    j = i + 1
                    while j < len(line) and (
                        line[j].isalpha() or line[j].isdigit() or line[j] == "_"
                    ):
                        j += 1
                    name = line[i + 1 : j]
                    if name in self._defines:
                        out.append(self._defines[name])
                    else:
                        raise PreprocessorError(
                            f"Undefined constant '#{name}'", line_num
                        )
                    i = j
                else:
                    out.append(line[i])
                    i += 1
            else:
                out.append(line[i])
                i += 1
        return "".join(out)
