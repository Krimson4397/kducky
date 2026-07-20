"""Unified error hierarchy for DuckyScript 3."""


class DuckyError(Exception):
    """Base class for all DuckyScript errors."""

    def __init__(
        self,
        message: str,
        line: int | None = None,
        column: int | None = None,
        source_snippet: str | None = None,
        cause: Exception | None = None,
    ) -> None:
        self.message = message
        self.line = line
        self.column = column
        self.source_snippet = source_snippet
        self.cause = cause

        parts = ["[ERROR]"]
        if line is not None and column is not None:
            parts.append(f"line {line}, col {column}:")
        elif line is not None:
            parts.append(f"line {line}:")
        parts.append(message)
        super().__init__(" ".join(parts))


class LexerError(DuckyError):
    """Lexer encountered invalid input."""

    def __init__(self, message: str, line: int, column: int) -> None:
        super().__init__(message, line=line, column=column)


class ParseError(DuckyError):
    """Parser encountered invalid syntax."""

    def __init__(self, message: str, line: int | None = None, column: int | None = None) -> None:
        super().__init__(message, line=line, column=column)


class InterpreterError(DuckyError):
    """Runtime error during payload execution.

    Line/column are NOT available because AST nodes don't carry source positions.
    """


class PreprocessorError(DuckyError):
    """Preprocessor error with line number."""

    def __init__(self, message: str, line: int) -> None:
        super().__init__(message, line=line)
