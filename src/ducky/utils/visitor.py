"""AST node visitor base class."""

from __future__ import annotations


class NodeVisitor:
    """Base class for AST visitors.

    Subclass and define ``visit_ClassName`` methods for each node type.
    Falls back to ``generic_visit`` for unhandled nodes.
    """

    def visit(self, node: object) -> object:
        method = getattr(self, f"visit_{type(node).__name__}", self.generic_visit)
        return method(node)

    def generic_visit(self, node: object) -> object:
        raise NotImplementedError(f"No visit method for {type(node).__name__}")
